from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
import json
import uuid
from datetime import datetime

from .agents.graph import app as graph_app
from .agents.state import ArthAgentState
from .knowledge.loader import initialize_knowledge_base

# Load environment variables
load_dotenv()

app = FastAPI(
    title="ArthAgent API",
    version="0.1.0",
    description="AI-powered personal finance planning multi-agent system.",
)

# CORS configuration
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize knowledge base on startup
@app.on_event("startup")
async def startup_event():
    """Initialize ChromaDB knowledge base."""
    initialize_knowledge_base()


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.websocket("/ws/agent-stream")
async def websocket_endpoint(websocket: WebSocket, session_id: str = None):
    """WebSocket endpoint for real-time agent execution stream."""
    await websocket.accept()
    
    if not session_id:
        session_id = str(uuid.uuid4())
    
    try:
        # Initialize state
        initial_state: ArthAgentState = {
            "session_id": session_id,
            "profile": {},
            "calculations": {},
            "regulatory_flags": [],
            "scenarios": {},
            "final_plan": None,
            "disclaimer_appended": False,
            "audit_log": [],
            "error": None,
            "current_step": "init",
        }

        # Send initialization message
        await websocket.send_text(json.dumps({
            "type": "init",
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
        }))

        # Invoke the LangGraph pipeline
        final_state = graph_app.invoke(initial_state)

        # Stream each audit log entry to the client
        for log_entry in final_state.get("audit_log", []):
            await websocket.send_text(json.dumps({
                "type": "agent_step",
                "step": log_entry.get("step"),
                "status": log_entry.get("status"),
                "detail": log_entry.get("detail", ""),
                "timestamp": log_entry.get("timestamp"),
            }))

        # Send final plan
        await websocket.send_text(json.dumps({
            "type": "plan_complete",
            "plan": final_state.get("final_plan", {}),
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
        }))

        # Send any errors
        if final_state.get("error"):
            await websocket.send_text(json.dumps({
                "type": "error",
                "error": final_state.get("error"),
                "timestamp": datetime.utcnow().isoformat(),
            }))

    except WebSocketDisconnect:
        print(f"Client disconnected: {session_id}")
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }))
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass

