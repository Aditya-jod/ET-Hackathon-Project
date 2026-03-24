"""CAMS PDF upload and portfolio analysis router."""

from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
from pathlib import Path

router = APIRouter(prefix="/api", tags=["uploads"])

UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/cams-upload")
async def upload_cams_statement(file: UploadFile = File(...), session_id: str = None):
    """
    Upload CAMS or KFintech mutual fund statement PDF for portfolio analysis.
    
    Returns session ID and analysis status. Use WebSocket to get detailed X-ray.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files accepted")

    try:
        # Save file temporarily
        file_path = UPLOAD_DIR / f"{session_id}_{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {
            "session_id": session_id,
            "file_name": file.filename,
            "status": "uploaded",
            "message": "Portfolio X-ray analysis starting. Connect to WebSocket for results.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
