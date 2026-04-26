# DICOM Anonymizer

> HIPAA Safe Harbor compliant DICOM de-identification — Python library, CLI, and REST API.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![HIPAA Safe Harbor](https://img.shields.io/badge/HIPAA-Safe%20Harbor-green.svg)](https://www.hhs.gov/hipaa/for-professionals/privacy/special-topics/de-identification/index.html)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Overview

`dicom-anonymizer` removes or replaces all **18 PHI identifiers** defined in [45 CFR §164.514(b)](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-E/section-164.514) (HIPAA Safe Harbor method) from DICOM files. It is designed for radiology informatics workflows where patient data must be de-identified before:

- Research dataset creation
- Integration testing with production data
- PACS-to-cloud migration (e.g., AWS HealthLake)
- Vendor demos and QA environments

### What gets removed / replaced

| Category | Action | Examples |
|---|---|---|
| Patient demographics | Removed / replaced | Name, DOB, Sex, Age |
| Dates | Shifted to `1900-01-01` | Study Date, Series Date |
| Institution | Replaced | Institution Name, Address |
| UIDs | Remapped | Study, Series, SOP Instance UID |
| Free-text fields | Cleared | Comments, History, Occupation |
| Private tags | Removed entirely | All manufacturer private tags |

---

## Features

- ✅ Handles single files and entire directory trees
- ✅ UID remapping with **referential integrity** (UIDs within a study stay consistent)
- ✅ Deterministic mode (`--retain-uids`) — same input always produces the same anonymized UIDs
- ✅ Configurable Patient ID prefix
- ✅ REST API (FastAPI) for integration into existing pipelines
- ✅ Docker support
- ✅ 10+ pytest tests

---

## Installation

```bash
git clone https://github.com/yourusername/dicom-anonymizer.git
cd dicom-anonymizer
pip install -r requirements.txt
```

---

## Usage

### 1. Python library

```python
from anonymizer import DICOMAnonymizer

anon = DICOMAnonymizer(retain_uids=False, patient_id_prefix="RESEARCH")

# Single file
anon.anonymize_file("patient.dcm", "anon_patient.dcm", overwrite=True)

# Entire study folder
summary = anon.anonymize_folder("/data/study_001", "/data/anon/study_001")
print(summary)
# {'processed': 312, 'skipped': 0, 'failed': 0, 'errors': []}
```

### 2. CLI

```bash
# Single file
python cli.py file input.dcm output.dcm

# Directory (recursive)
python cli.py folder /path/to/study /path/to/output --overwrite

# Deterministic UID remapping
python cli.py --retain-uids file input.dcm output.dcm

# Custom Patient ID prefix
python cli.py --prefix TRIAL file input.dcm output.dcm
```

### 3. REST API

```bash
# Start the server
uvicorn api:app --host 0.0.0.0 --port 8000

# Or with Docker
docker-compose up
```

**Anonymize via HTTP:**

```bash
curl -X POST "http://localhost:8000/anonymize" \
  -F "file=@patient.dcm" \
  -o anon_patient.dcm
```

**List handled PHI tags:**

```bash
curl http://localhost:8000/tags
```

**Interactive API docs:** `http://localhost:8000/docs`

---

## Running tests

```bash
pytest tests/ -v
```

---

## Architecture

```
dicom-anonymizer/
├── anonymizer/
│   ├── anonymizer.py      # Core DICOMAnonymizer class
│   ├── hipaa_tags.py      # HIPAA Safe Harbor tag definitions (45 CFR §164.514)
│   └── __init__.py
├── api.py                 # FastAPI REST service
├── cli.py                 # Command-line interface
├── tests/
│   └── test_anonymizer.py
├── Dockerfile
└── docker-compose.yml
```

---

## Compliance notes

This tool implements the **Safe Harbor** method of de-identification (45 CFR §164.514(b)(2)). It is **not** a substitute for a legal review of your specific use case. For covered entities and business associates, consult with your compliance officer before using de-identified data in research or cross-organizational workflows.

---

## Author

**Baurzhan Ibrayev** — DICOM Integration Engineer  
5+ years in medical imaging systems: Orthanc, OHIF, MedDream, DCMTK, HL7, DICOMweb  
[LinkedIn](https://linkedin.com/in/yourprofile) · [GitHub](https://github.com/yourusername)

---

## License

MIT — free to use in commercial and research projects.
