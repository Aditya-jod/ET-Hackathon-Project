from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import json
import uuid

# This would in reality trigger the full LangGraph pipeline
# For now, we simulate the stream
async def run_agent_pipeline(session_id: str, websocket: WebSocket):
    """Simulates an agent pipeline, streaming updates."""
    steps = [
        {"step": "intake_agent", "status": "running", "detail": "Extracting user profile..."},
        {"step": "intake_agent", "status": "complete", "detail": "Profile extracted."},
        {"step": "calculation_agent", "status": "running", "detail": "Computing XIRR..."},
        {"step": "calculation_agent", "status": "complete", "detail": "XIRR: 18.4%"},
        {"step": "regulatory_agent", "status": "running", "detail": "Checking SEBI guidelines..."},
        {"step": "regulatory_agent", "status": "complete", "detail": "No violations found."},
        {"step": "synthesis_agent", "status": "running", "detail": "Generating financial plan..."},
        {"step": "synthesis_agent", "status": "complete", "detail": "Plan generated."},
        {"step": "disclaimer_agent", "status": "running", "detail": "Appending SEBI disclaimer..."},
        {"step": "disclaimer_agent", "status": "complete", "detail": "Disclaimer appended."},
    ]
    for step in steps:
        await websocket.send_text(json.dumps(step))

router = APIRouter()

@router.websocket("/ws/agent-stream")
async def websocket_endpoint(websocket: WebSocket, session_id: str = None):
    await websocket.accept()
    if not session_id:
        session_id = str(uuid.uuid4())
    
    try:
        await run_agent_pipeline(session_id, websocket)
    except WebSocketDisconnect:
        print(f"Client disconnected from session {session_id}")
    finally:
        await websocket.close()
