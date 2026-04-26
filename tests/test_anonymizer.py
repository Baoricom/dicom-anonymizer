"""
Tests for DICOM Anonymizer
"""

import io
import tempfile
from pathlib import Path

import pydicom
import pytest
from pydicom.dataset import Dataset, FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid

from anonymizer import DICOMAnonymizer


def create_test_dicom(tmp_path: Path, patient_name="Doe^John", patient_id="123456") -> Path:
    """Create a minimal synthetic DICOM file for testing."""
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.2"
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

    ds = FileDataset(None, {}, file_meta=file_meta, preamble=b"\x00" * 128)
    ds.is_implicit_VR = False
    ds.is_little_endian = True

    ds.PatientName = patient_name
    ds.PatientID = patient_id
    ds.PatientBirthDate = "19800101"
    ds.PatientSex = "M"
    ds.StudyDate = "20230601"
    ds.StudyTime = "120000"
    ds.AccessionNumber = "ACC-001"
    ds.InstitutionName = "General Hospital"
    ds.StudyInstanceUID = generate_uid()
    ds.SeriesInstanceUID = generate_uid()
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
    ds.Modality = "CT"

    out = tmp_path / "test.dcm"
    ds.save_as(str(out))
    return out


class TestDICOMAnonymizer:
    def test_patient_name_replaced(self, tmp_path):
        src = create_test_dicom(tmp_path)
        dst = tmp_path / "anon.dcm"
        anon = DICOMAnonymizer()
        anon.anonymize_file(src, dst, overwrite=True)
        result = pydicom.dcmread(str(dst))
        assert str(result.PatientName) != "Doe^John"
        assert "ANON" in str(result.PatientName).upper()

    def test_patient_id_hashed(self, tmp_path):
        src = create_test_dicom(tmp_path, patient_id="123456")
        dst = tmp_path / "anon.dcm"
        anon = DICOMAnonymizer()
        anon.anonymize_file(src, dst, overwrite=True)
        result = pydicom.dcmread(str(dst))
        assert result.PatientID != "123456"
        assert result.PatientID.startswith("ANON-")

    def test_birth_date_removed(self, tmp_path):
        src = create_test_dicom(tmp_path)
        dst = tmp_path / "anon.dcm"
        anon = DICOMAnonymizer()
        anon.anonymize_file(src, dst, overwrite=True)
        result = pydicom.dcmread(str(dst))
        assert (0x0010, 0x0030) not in result

    def test_uids_changed(self, tmp_path):
        src = create_test_dicom(tmp_path)
        original = pydicom.dcmread(str(src))
        dst = tmp_path / "anon.dcm"
        anon = DICOMAnonymizer()
        anon.anonymize_file(src, dst, overwrite=True)
        result = pydicom.dcmread(str(dst))
        assert result.StudyInstanceUID != original.StudyInstanceUID
        assert result.SeriesInstanceUID != original.SeriesInstanceUID
        assert result.SOPInstanceUID != original.SOPInstanceUID

    def test_deterministic_uids_with_retain_flag(self, tmp_path):
        src = create_test_dicom(tmp_path)
        dst1 = tmp_path / "anon1.dcm"
        dst2 = tmp_path / "anon2.dcm"
        anon1 = DICOMAnonymizer(retain_uids=True)
        anon2 = DICOMAnonymizer(retain_uids=True)
        anon1.anonymize_file(src, dst1, overwrite=True)
        anon2.anonymize_file(src, dst2, overwrite=True)
        r1 = pydicom.dcmread(str(dst1))
        r2 = pydicom.dcmread(str(dst2))
        assert r1.StudyInstanceUID == r2.StudyInstanceUID

    def test_institution_name_replaced(self, tmp_path):
        src = create_test_dicom(tmp_path)
        dst = tmp_path / "anon.dcm"
        anon = DICOMAnonymizer()
        anon.anonymize_file(src, dst, overwrite=True)
        result = pydicom.dcmread(str(dst))
        assert result.InstitutionName != "General Hospital"

    def test_overwrite_protection(self, tmp_path):
        src = create_test_dicom(tmp_path)
        dst = tmp_path / "anon.dcm"
        anon = DICOMAnonymizer()
        anon.anonymize_file(src, dst)
        with pytest.raises(FileExistsError):
            anon.anonymize_file(src, dst, overwrite=False)

    def test_folder_anonymization(self, tmp_path):
        in_dir = tmp_path / "input"
        out_dir = tmp_path / "output"
        in_dir.mkdir()

        # Create 3 properly named DICOM files
        for i in range(3):
            src = create_test_dicom(in_dir)
            src.rename(in_dir / f"study_{i}.dcm")

        anon = DICOMAnonymizer()
        summary = anon.anonymize_folder(in_dir, out_dir)
        assert summary["processed"] == 3
        assert summary["failed"] == 0

    def test_custom_patient_prefix(self, tmp_path):
        src = create_test_dicom(tmp_path)
        dst = tmp_path / "anon.dcm"
        anon = DICOMAnonymizer(patient_id_prefix="RESEARCH")
        anon.anonymize_file(src, dst, overwrite=True)
        result = pydicom.dcmread(str(dst))
        assert result.PatientID.startswith("RESEARCH-")

    def test_burned_in_annotation_flag(self, tmp_path):
        src = create_test_dicom(tmp_path)
        dst = tmp_path / "anon.dcm"
        anon = DICOMAnonymizer()
        anon.anonymize_file(src, dst, overwrite=True)
        result = pydicom.dcmread(str(dst))
        assert result.BurnedInAnnotation == "NO"
