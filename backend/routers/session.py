"""Session management router."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid
from datetime import datetime

router = APIRouter(prefix="/api", tags=["sessions"])


class SessionRequest(BaseModel):
    """Request to create a new session."""

    user_name: str = None
    metadata: dict = None


@router.post("/session")
async def create_session(request: SessionRequest):
    """Create a new planning session."""
    session_id = str(uuid.uuid4())
    return {
        "session_id": session_id,
        "created_at": datetime.utcnow().isoformat(),
        "user_name": request.user_name,
        "status": "active",
    }


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """Retrieve session metadata."""
    return {
        "session_id": session_id,
        "status": "active",
        "created_at": datetime.utcnow().isoformat(),
    }
