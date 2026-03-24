from typing import Optional, TypedDict


class ArthAgentState(TypedDict):
    """Shared state passed between ArthAgent LangGraph nodes."""

    session_id: str
    profile: dict  # Populated by IntakeAgent
    calculations: dict  # Populated by CalculationAgent
    regulatory_flags: list[dict]  # Populated by RegulatoryAgent
    scenarios: dict  # Populated by ScenarioAgent
    final_plan: Optional[dict]  # Populated by SynthesisAgent
    disclaimer_appended: bool  # Set True by DisclaimerAgent
    audit_log: list[dict]  # Every agent decision logged here
    error: Optional[str]  # Set if any agent fails
    current_step: str  # Track which agent is running
