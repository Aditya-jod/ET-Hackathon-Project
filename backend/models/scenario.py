"""Pydantic models for scenario requests (what-if analysis)."""

from typing import Optional
from pydantic import BaseModel, Field


class ScenarioRequest(BaseModel):
    """What-if scenario for re-computation without full re-run."""

    session_id: str = Field(..., description="Session to update")
    scenario_name: str = Field(..., description="Human-readable scenario name")
    scenario_type: str = Field(
        ...,
        pattern="^(retirement_age_change|income_change|expense_change|investment_change|goal_change)$",
        description="Type of change",
    )
    
    # Optional changes - at least one should be provided
    retirement_age: Optional[int] = Field(None, ge=40, le=75, description="New retirement age")
    annual_income: Optional[float] = Field(None, gt=0, description="New annual income")
    monthly_expenses: Optional[float] = Field(None, gt=0, description="New monthly expenses")
    new_investment_amount: Optional[float] = Field(None, ge=0, description="Additional investment corpus")
    new_retirement_corpus_target: Optional[float] = Field(None, gt=0, description="New retirement corpus target")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "session_id": "sess_123",
                    "scenario_name": "Retire at 48 instead of 50",
                    "scenario_type": "retirement_age_change",
                    "retirement_age": 48,
                },
                {
                    "session_id": "sess_123",
                    "scenario_name": "10% salary bump next year",
                    "scenario_type": "income_change",
                    "annual_income": 2640000,
                },
            ]
        }
