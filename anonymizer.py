"""
DICOM Anonymizer - Core Module
HIPAA Safe Harbor compliant de-identification of DICOM files.
"""

import hashlib
import logging
import shutil
import uuid
from pathlib import Path
from typing import Optional

import pydicom
from pydicom.uid import generate_uid

from .hipaa_tags import TAGS_TO_REMOVE, TAGS_TO_REPLACE

logger = logging.getLogger(__name__)


class DICOMAnonymizer:
    """
    HIPAA Safe Harbor compliant DICOM anonymizer.

    Removes or replaces the 18 PHI identifiers defined in 45 CFR §164.514(b).
    UIDs are replaced with deterministic or random new UIDs to maintain
    referential integrity within a study.
    """

    def __init__(
        self,
        retain_uids: bool = False,
        uid_prefix: str = "2.25",
        patient_id_prefix: str = "ANON",
    ):
        """
        Args:
            retain_uids: If True, regenerate UIDs deterministically (same input = same output).
                         If False, use random UIDs each run.
            uid_prefix:  Prefix for generated UIDs.
            patient_id_prefix: Prefix used for anonymized Patient ID.
        """
        self.retain_uids = retain_uids
        self.uid_prefix = uid_prefix
        self.patient_id_prefix = patient_id_prefix
        self._uid_map: dict[str, str] = {}  # original -> anonymized

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def anonymize_file(
        self,
        input_path: str | Path,
        output_path: str | Path,
        overwrite: bool = False,
    ) -> pydicom.Dataset:
        """
        Anonymize a single DICOM file.

        Args:
            input_path:  Path to source .dcm file.
            output_path: Destination path for anonymized file.
            overwrite:   Allow overwriting existing output file.

        Returns:
            The anonymized pydicom Dataset.

        Raises:
            FileNotFoundError: If input file does not exist.
            FileExistsError:   If output exists and overwrite=False.
        """
        input_path = Path(input_path)
        output_path = Path(output_path)

        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        if output_path.exists() and not overwrite:
            raise FileExistsError(
                f"Output file already exists: {output_path}. Use overwrite=True."
            )

        ds = pydicom.dcmread(str(input_path))
        ds = self._anonymize_dataset(ds)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        ds.save_as(str(output_path))
        logger.info(f"Anonymized: {input_path} -> {output_path}")
        return ds

    def anonymize_folder(
        self,
        input_dir: str | Path,
        output_dir: str | Path,
        overwrite: bool = False,
    ) -> dict:
        """
        Recursively anonymize all DICOM files in a directory.

        Args:
            input_dir:  Source directory.
            output_dir: Destination directory (mirrors input structure).
            overwrite:  Allow overwriting existing output files.

        Returns:
            Summary dict with counts of processed/skipped/failed files.
        """
        input_dir = Path(input_dir)
        output_dir = Path(output_dir)

        if not input_dir.is_dir():
            raise NotADirectoryError(f"Not a directory: {input_dir}")

        summary = {"processed": 0, "skipped": 0, "failed": 0, "errors": []}

        dcm_files = list(input_dir.rglob("*.dcm")) + list(input_dir.rglob("*.DCM"))
        # Also try files without extension (common in DICOM)
        for f in input_dir.rglob("*"):
            if f.is_file() and f.suffix == "" and self._is_dicom(f):
                dcm_files.append(f)

        dcm_files = list(set(dcm_files))
        logger.info(f"Found {len(dcm_files)} DICOM file(s) in {input_dir}")

        for src in dcm_files:
            rel = src.relative_to(input_dir)
            dst = output_dir / rel
            try:
                self.anonymize_file(src, dst, overwrite=overwrite)
                summary["processed"] += 1
            except FileExistsError:
                logger.warning(f"Skipped (exists): {dst}")
                summary["skipped"] += 1
            except Exception as exc:
                logger.error(f"Failed {src}: {exc}")
                summary["failed"] += 1
                summary["errors"].append({"file": str(src), "error": str(exc)})

        return summary

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _anonymize_dataset(self, ds: pydicom.Dataset) -> pydicom.Dataset:
        """Apply all anonymization rules to a Dataset."""

        # 1. Remove tags
        for tag in TAGS_TO_REMOVE:
            if tag in ds:
                del ds[tag]

        # 2. Replace tags
        for tag, (vr, value) in TAGS_TO_REPLACE.items():
            if tag in ds:
                if vr == "SQ":
                    ds[tag].value = pydicom.Sequence([])
                elif value is not None:
                    ds[tag].value = value

        # 3. Remap UIDs to maintain internal referential integrity
        self._remap_uids(ds)

        # 4. Generate deterministic anonymized Patient ID
        original_id = getattr(ds, "PatientID", "UNKNOWN")
        ds.PatientID = self._anonymize_patient_id(original_id)

        # 5. Burn-in annotation removal flag (best effort)
        ds.BurnedInAnnotation = "NO"

        # 6. Remove private tags (may contain PHI)
        ds.remove_private_tags()

        return ds

    def _remap_uids(self, ds: pydicom.Dataset) -> None:
        """Replace Study/Series/Instance UIDs with new ones, preserving links."""
        uid_tags = [
            "StudyInstanceUID",
            "SeriesInstanceUID",
            "SOPInstanceUID",
            "FrameOfReferenceUID",
            "ReferencedSOPInstanceUID",
        ]
        for attr in uid_tags:
            if hasattr(ds, attr):
                original = getattr(ds, attr)
                setattr(ds, attr, self._get_or_create_uid(original))

    def _get_or_create_uid(self, original_uid: str) -> str:
        """Return a consistent anonymized UID for the given original."""
        if original_uid not in self._uid_map:
            if self.retain_uids:
                # Deterministic: hash of original UID
                hash_hex = hashlib.md5(original_uid.encode()).hexdigest()
                new_uid = generate_uid(prefix=f"{self.uid_prefix}.", entropy_srcs=[hash_hex])
            else:
                new_uid = generate_uid(prefix=f"{self.uid_prefix}.")
            self._uid_map[original_uid] = new_uid
        return self._uid_map[original_uid]

    def _anonymize_patient_id(self, original_id: str) -> str:
        """Generate a repeatable anonymized Patient ID."""
        short_hash = hashlib.sha256(original_id.encode()).hexdigest()[:8].upper()
        return f"{self.patient_id_prefix}-{short_hash}"

    @staticmethod
    def _is_dicom(path: Path) -> bool:
        """Quick check for DICOM magic bytes (DICM at offset 128)."""
        try:
            with open(path, "rb") as f:
                f.seek(128)
                return f.read(4) == b"DICM"
        except Exception:
            return False
