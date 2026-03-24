"""Calculation agent: Run all financial computations."""

from datetime import datetime
from ..agents.state import ArthAgentState
from ..calculations.tax import compare_tax_regimes, calculate_hra_exemption
from ..calculations.investments import calculate_fire_plan


async def calculation_agent(state: ArthAgentState) -> ArthAgentState:
    """CalculationAgent node: Run tax, FIRE, portfolio calculations."""
    state["current_step"] = "calculation_agent"
    state["audit_log"].append({
        "timestamp": datetime.utcnow().isoformat(),
        "step": "calculation_agent",
        "status": "started",
    })

    try:
        profile = state.get("profile", {})
        
        if not profile:
            state["error"] = "No profile data available for calculation"
            return state

        # Extract profile fields
        income = profile.get("income", {})
        deductions = profile.get("deductions", {})
        expenses = profile.get("expenses", {})
        investments = profile.get("investments", {})
        goals = profile.get("goals", {})

        basic_salary = income.get("basic_salary", 0)
        hra_received = income.get("hra_received", 0)
        is_metro = income.get("is_metro_city", True)
        gross_income = basic_salary + hra_received + income.get("other_income", 0)

        # === TAX CALCULATIONS ===
        hra_exemption = calculate_hra_exemption(
            basic_salary=basic_salary,
            hra_received=hra_received,
            rent_paid=deductions.get("rent_paid_annual", 0),
            is_metro_city=is_metro,
        )

        tax_analysis = compare_tax_regimes(
            gross_income=gross_income,
            hra_exemption=hra_exemption,
            deduction_80c=deductions.get("deduction_80c", 0),
            deduction_80d=deductions.get("deduction_80d", 0),
            nps_80ccd_1b=deductions.get("nps_80ccd_1b", 0),
            home_loan_interest=deductions.get("home_loan_interest", 0),
        )

        # === FIRE CALCULATIONS ===
        age = profile.get("age", 35)
        monthly_exp = expenses.get("monthly_expenses", 0)
        existing_mf = investments.get("mutual_funds_value", 0)
        existing_ppf = investments.get("ppf_balance", 0)
        retirement_age = goals.get("retirement_age", 60)
        target_monthly = goals.get("monthly_retirement_corpus", monthly_exp * 1.25)

        fire_plan = calculate_fire_plan(
            age=age,
            income=gross_income,
            monthly_expenses=monthly_exp,
            existing_mf=existing_mf,
            existing_ppf=existing_ppf,
            target_monthly_retirement=target_monthly,
            retire_at=retirement_age,
        )

        # Store calculations
        state["calculations"] = {
            "tax_analysis": tax_analysis,
            "fire_plan": fire_plan,
            "hra_exemption": hra_exemption,
            "gross_income": gross_income,
        }

        state["audit_log"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "step": "calculation_agent",
            "status": "completed",
            "detail": f"Tax: {tax_analysis['recommended']} regime recommended. FIRE SIP: ₹{fire_plan['monthly_sip_needed']:.0f}/month",
        })

    except Exception as e:
        state["error"] = f"Calculation error: {str(e)}"
        state["audit_log"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "step": "calculation_agent",
            "status": "error",
            "detail": str(e),
        })

    return state
