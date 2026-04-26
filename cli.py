#!/usr/bin/env python3
"""
DICOM Anonymizer CLI
Usage:
    python cli.py file   input.dcm output.dcm
    python cli.py folder /input_dir /output_dir --overwrite
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from anonymizer import DICOMAnonymizer

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)


def cmd_file(args):
    anon = DICOMAnonymizer(
        retain_uids=args.retain_uids,
        patient_id_prefix=args.prefix,
    )
    try:
        anon.anonymize_file(args.input, args.output, overwrite=args.overwrite)
        print(f"✓ Anonymized: {args.output}")
    except FileExistsError as e:
        print(f"✗ Error: {e}. Use --overwrite to force.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_folder(args):
    anon = DICOMAnonymizer(
        retain_uids=args.retain_uids,
        patient_id_prefix=args.prefix,
    )
    summary = anon.anonymize_folder(args.input, args.output, overwrite=args.overwrite)
    print(f"\n─── Summary ───────────────────────")
    print(f"  Processed : {summary['processed']}")
    print(f"  Skipped   : {summary['skipped']}")
    print(f"  Failed    : {summary['failed']}")
    if summary["errors"]:
        print("\nErrors:")
        for err in summary["errors"]:
            print(f"  {err['file']}: {err['error']}")


def main():
    parser = argparse.ArgumentParser(
        description="DICOM Anonymizer — HIPAA Safe Harbor compliant de-identification"
    )
    parser.add_argument(
        "--retain-uids",
        action="store_true",
        help="Use deterministic UID remapping (same input → same output UIDs)",
    )
    parser.add_argument(
        "--prefix",
        default="ANON",
        help="Prefix for anonymized Patient ID (default: ANON)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # file subcommand
    p_file = subparsers.add_parser("file", help="Anonymize a single DICOM file")
    p_file.add_argument("input", type=Path, help="Input .dcm file")
    p_file.add_argument("output", type=Path, help="Output .dcm file")
    p_file.add_argument("--overwrite", action="store_true")
    p_file.set_defaults(func=cmd_file)

    # folder subcommand
    p_folder = subparsers.add_parser("folder", help="Anonymize a directory of DICOM files")
    p_folder.add_argument("input", type=Path, help="Input directory")
    p_folder.add_argument("output", type=Path, help="Output directory")
    p_folder.add_argument("--overwrite", action="store_true")
    p_folder.set_defaults(func=cmd_folder)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
