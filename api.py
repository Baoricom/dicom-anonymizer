"""
DICOM Anonymizer - REST API
FastAPI endpoint for on-the-fly DICOM anonymization.
"""

import io
import logging
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from anonymizer import DICOMAnonymizer

logger = logging.getLogger(__name__)

app = FastAPI(
    title="DICOM Anonymizer API",
    description="HIPAA Safe Harbor compliant DICOM de-identification service.",
    version="1.0.0",
    contact={
        "name": "Baurzhan Ibrayev",
        "url": "https://github.com/yourusername/dicom-anonymizer",
    },
    license_info={"name": "MIT"},
)


@app.get("/health", tags=["System"])
def health():
    """Service health check."""
    return {"status": "ok", "service": "dicom-anonymizer"}


@app.post(
    "/anonymize",
    tags=["Anonymization"],
    summary="Anonymize a DICOM file",
    response_description="Anonymized .dcm file",
)
async def anonymize_dicom(
    file: UploadFile = File(..., description="DICOM file (.dcm)"),
    retain_uids: bool = Query(False, description="Use deterministic UID remapping"),
    patient_id_prefix: str = Query("ANON", description="Prefix for anonymized Patient ID"),
):
    """
    Upload a DICOM file and receive an anonymized version.

    - Removes all 18 HIPAA Safe Harbor PHI identifiers
    - Remaps UIDs (random or deterministic)
    - Strips private tags
    - Returns anonymized .dcm file
    """
    if not file.filename.lower().endswith((".dcm", ".dicom")):
        raise HTTPException(
            status_code=400,
            detail="Only .dcm / .dicom files are accepted.",
        )

    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.dcm"
            output_path = Path(tmpdir) / "anon_output.dcm"

            input_path.write_bytes(contents)

            anon = DICOMAnonymizer(
                retain_uids=retain_uids,
                patient_id_prefix=patient_id_prefix,
            )
            anon.anonymize_file(input_path, output_path, overwrite=True)

            output_bytes = output_path.read_bytes()

        return FileResponse(
            path=None,
            media_type="application/dicom",
            filename=f"anon_{file.filename}",
            content=output_bytes,
        )
    except Exception as exc:
        logger.exception("Anonymization failed")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/tags", tags=["Reference"])
def list_phi_tags():
    """Return the list of PHI tags handled by this service."""
    from anonymizer.hipaa_tags import TAGS_TO_REMOVE, TAGS_TO_REPLACE

    return {
        "removed": [f"({g:04X},{e:04X})" for g, e in TAGS_TO_REMOVE],
        "replaced": [f"({g:04X},{e:04X})" for g, e in TAGS_TO_REPLACE],
        "total": len(TAGS_TO_REMOVE) + len(TAGS_TO_REPLACE),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
