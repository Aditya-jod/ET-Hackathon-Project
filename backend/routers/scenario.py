"""Scenario (what-if) analysis router."""

from fastapi import APIRouter
from ..models.scenario import ScenarioRequest

router = APIRouter(prefix="/api", tags=["scenarios"])


@router.post("/scenario")
async def compute_scenario(request: ScenarioRequest):
    """
    Submit a what-if scenario to recompute plan without full re-run.
    
    E.g., "What if I retire at 48 instead of 50?" or "What if my income increases by 20%?"
    
    Returns session ID and indicates computation status. Use WebSocket to see live updates.
    """
    return {
        "session_id": request.session_id,
        "scenario_name": request.scenario_name,
        "status": "computing",
        "message": f"Scenario '{request.scenario_name}' queued. Connect to WebSocket for updates.",
    }


@router.get("/scenarios/{session_id}")
async def list_scenarios(session_id: str):
    """Retrieve all scenarios computed for a session."""
    return {
        "session_id": session_id,
        "scenarios": [],
        "message": "Scenario retrieval not yet implemented.",
    }
