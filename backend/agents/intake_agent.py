"""Intake agent: Extract user profile via conversational LLM (Groq/Llama)."""

import json
from typing import Any, Dict
from groq import Groq
from ..agents.state import ArthAgentState
from ..models.profile import UserProfile

# Initialize Groq client
groq_client = Groq()

INTAKE_SYSTEM_PROMPT = """You are an expert financial advisor intake assistant. Your job is to extract structured financial information from user responses.

You will receive user input and must return a valid JSON object matching this schema:
{
    "age": number,
    "basic_salary": number,
    "hra_received": number,
    "other_income": number,
    "is_metro_city": boolean,
    "monthly_expenses": number,
    "deduction_80c": number,
    "deduction_80d": number,
    "nps_80ccd_1b": number,
    "home_loan_interest": number,
    "other_deductions": number,
    "rent_paid_annual": number,
    "mutual_funds_value": number,
    "ppf_balance": number,
    "nps_balance": number,
    "fd_balance": number,
    "stocks_value": number,
    "gold_value": number,
    "real_estate_loans": number,
    "other_debts": number,
    "emergency_fund_months": number,
    "retirement_age": number,
    "monthly_retirement_corpus": number,
    "children_education_goal": number,
    "home_purchase_goal": number,
    "years_to_goal": number,
    "risk_tolerance": "conservative|moderate|aggressive"
}

If a value is not provided or unclear, use a reasonable default or zero. Ask clarifying questions if critical values (age, salary, expenses) are missing.

Return ONLY valid JSON—no markdown, no explanation."""


async def extract_profile_via_llm(user_input: str, session_id: str) -> Dict[str, Any]:
    """Call Groq/Llama to extract structured profile from freeform user input."""
    try:
        message = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": INTAKE_SYSTEM_PROMPT},
                {"role": "user", "content": f"Extract financial profile from this input: {user_input}"},
            ],
            temperature=0.0,  # Deterministic for parsing
            max_tokens=1024,
        )

        response_text = message.choices[0].message.content.strip()
        # Extract JSON from potential markdown wrapping
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        
        profile_dict = json.loads(response_text)
        return profile_dict
    except Exception as e:
        return {"error": f"LLM extraction failed: {str(e)}", "session_id": session_id}


async def intake_agent(state: ArthAgentState) -> ArthAgentState:
    """IntakeAgent node: Extract user profile from conversational input."""
    state["current_step"] = "intake_agent"
    state["audit_log"].append({
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        "step": "intake_agent",
        "status": "started",
    })

    try:
        # Extract profile from profile dict if it exists
        if state.get("profile") and isinstance(state["profile"], dict):
            user_input = state["profile"].get("user_input", "")
            
            if user_input:
                extracted = await extract_profile_via_llm(user_input, state["session_id"])
                
                if "error" in extracted:
                    state["error"] = extracted["error"]
                    state["audit_log"].append({
                        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
                        "step": "intake_agent",
                        "status": "error",
                        "detail": extracted["error"],
                    })
                    return state
                
                # Build structured UserProfile
                profile = UserProfile(
                    session_id=state["session_id"],
                    age=extracted.get("age", 35),
                    income__dict__(
                        basic_salary=extracted.get("basic_salary", 1800000),
                        hra_received=extracted.get("hra_received", 360000),
                        other_income=extracted.get("other_income", 0),
                        is_metro_city=extracted.get("is_metro_city", True),
                    ),
                    deductions=dict(
                        deduction_80c=extracted.get("deduction_80c", 150000),
                        deduction_80d=extracted.get("deduction_80d", 25000),
                        nps_80ccd_1b=extracted.get("nps_80ccd_1b", 50000),
                        home_loan_interest=extracted.get("home_loan_interest", 0),
                        other_deductions=extracted.get("other_deductions", 0),
                        rent_paid_annual=extracted.get("rent_paid_annual", 300000),
                    ),
                    expenses=dict(
                        monthly_expenses=extracted.get("monthly_expenses", 120000),
                        emergency_fund_months=extracted.get("emergency_fund_months", 6),
                    ),
                    investments=dict(
                        mutual_funds_value=extracted.get("mutual_funds_value", 0),
                        ppf_balance=extracted.get("ppf_balance", 0),
                        nps_balance=extracted.get("nps_balance", 0),
                        fd_balance=extracted.get("fd_balance", 0),
                        stocks_value=extracted.get("stocks_value", 0),
                        gold_value=extracted.get("gold_value", 0),
                        real_estate_loans=extracted.get("real_estate_loans", 0),
                        other_debts=extracted.get("other_debts", 0),
                    ),
                    goals=dict(
                        retirement_age=extracted.get("retirement_age", 60),
                        monthly_retirement_corpus=extracted.get("monthly_retirement_corpus"),
                        children_education_goal=extracted.get("children_education_goal", 0),
                        home_purchase_goal=extracted.get("home_purchase_goal", 0),
                        years_to_goal=extracted.get("years_to_goal", 5),
                        risk_tolerance=extracted.get("risk_tolerance", "moderate"),
                    ),
                )
                state["profile"] = profile.dict()

        state["audit_log"].append({
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
            "step": "intake_agent",
            "status": "completed",
            "detail": "Profile extracted and validated",
        })

    except Exception as e:
        state["error"] = f"Intake agent error: {str(e)}"
        state["audit_log"].append({
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
            "step": "intake_agent",
            "status": "error",
            "detail": str(e),
        })

    return state
