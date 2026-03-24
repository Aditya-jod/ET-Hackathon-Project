"""Financial plan submission and retrieval router."""

from fastapi import APIRouter, HTTPException
from ..models.profile import UserProfile

router = APIRouter(prefix="/api", tags=["plans"])


@router.post("/profile")
async def submit_profile(profile: UserProfile):
    """
    Submit user financial profile for analysis.
    
    Returns session ID and indicates plan is being computed.
    Client should connect to WebSocket /ws/agent-stream?session_id=<id> to see live updates.
    """
    return {
        "session_id": profile.session_id,
        "status": "processing",
        "message": "Connect to WebSocket for live agent updates: ws://localhost:8000/ws/agent-stream?session_id=" + profile.session_id,
    }


@router.get("/plan/{session_id}")
async def get_plan(session_id: str):
    """Retrieve completed financial plan for a session."""
    return {
        "session_id": session_id,
        "status": "completed",
        "message": "Financial plan retrieval not yet implemented. Use WebSocket for full execution.",
    }
