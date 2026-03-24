"""Scenario agent: Enable dynamic what-if scenario modeling."""

from datetime import datetime
from ..agents.state import ArthAgentState
from ..calculations.investments import calculate_fire_plan
from ..calculations.tax import compare_tax_regimes, calculate_hra_exemption


async def scenario_agent(state: ArthAgentState) -> ArthAgentState:
    """ScenarioAgent node: Pre-compute what-if scenarios without full re-run."""
    state["current_step"] = "scenario_agent"
    state["audit_log"].append({
        "timestamp": datetime.utcnow().isoformat(),
        "step": "scenario_agent",
        "status": "started",
    })

    try:
        profile = state.get("profile", {})
        scenarios_result = {}

        if not profile:
            state["audit_log"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "step": "scenario_agent",
                "status": "completed",
                "detail": "No scenarios to compute (missing profile)",
            })
            return state

        # Scenario 1: Early retirement (age - 2)
        age = profile.get("age", 35)
        retire_age = profile.get("goals", {}).get("retirement_age", 60)
        early_retire = max(age + 1, retire_age - 2)  # Can't retire before age+1
        
        try:
            income_data = profile.get("income", {})
            expense_data = profile.get("expenses", {})
            invest_data = profile.get("investments", {})
            goal_data = profile.get("goals", {})

            fire_early = calculate_fire_plan(
                age=age,
                income=income_data.get("basic_salary", 0) + income_data.get("hra_received", 0),
                monthly_expenses=expense_data.get("monthly_expenses", 0),
                existing_mf=invest_data.get("mutual_funds_value", 0),
                existing_ppf=invest_data.get("ppf_balance", 0),
                target_monthly_retirement=goal_data.get("monthly_retirement_corpus", 0),
                retire_at=early_retire,
            )
            scenarios_result["early_retirement"] = {
                "retirement_age": early_retire,
                "monthly_sip_needed": fire_early["monthly_sip_needed"],
                "corpus_needed": fire_early["target_corpus"],
            }
        except Exception as e:
            scenarios_result["early_retirement"] = {"error": str(e)}

        # Scenario 2: Increased SIP (10% more income)
        try:
            income_data = profile.get("income", {})
            gross_increased = (income_data.get("basic_salary", 0) + income_data.get("hra_received", 0)) * 1.1

            fire_more_income = calculate_fire_plan(
                age=age,
                income=gross_increased,
                monthly_expenses=profile.get("expenses", {}).get("monthly_expenses", 0),
                existing_mf=profile.get("investments", {}).get("mutual_funds_value", 0),
                existing_ppf=profile.get("investments", {}).get("ppf_balance", 0),
                target_monthly_retirement=profile.get("goals", {}).get("monthly_retirement_corpus", 0),
                retire_at=retire_age,
            )
            scenarios_result["income_increase_10pct"] = {
                "new_gross_income": gross_increased,
                "monthly_sip_needed": fire_more_income["monthly_sip_needed"],
            }
        except Exception as e:
            scenarios_result["income_increase_10pct"] = {"error": str(e)}

        # Scenario 3: Tax regime switch
        try:
            deduct_data = profile.get("deductions", {})
            income_data = profile.get("income", {})
            basic = income_data.get("basic_salary", 0)
            hra = income_data.get("hra_received", 0)
            gross = basic + hra + income_data.get("other_income", 0)

            hra_ex = calculate_hra_exemption(
                basic_salary=basic,
                hra_received=hra,
                rent_paid=deduct_data.get("rent_paid_annual", 0),
                is_metro_city=income_data.get("is_metro_city", True),
            )

            tax_switch = compare_tax_regimes(
                gross_income=gross,
                hra_exemption=hra_ex,
                deduction_80c=deduct_data.get("deduction_80c", 0),
                deduction_80d=deduct_data.get("deduction_80d", 0),
                nps_80ccd_1b=deduct_data.get("nps_80ccd_1b", 0),
                home_loan_interest=deduct_data.get("home_loan_interest", 0),
            )
            
            current_regime = state.get("calculations", {}).get("tax_analysis", {}).get("recommended", "new")
            opposite_regime = "old" if current_regime == "new" else "new"
            other_tax = tax_switch["old_regime"]["total_tax"] if opposite_regime == "old" else tax_switch["new_regime"]["total_tax"]

            scenarios_result["tax_regime_switch"] = {
                "current_regime": current_regime,
                "alternative_regime": opposite_regime,
                "current_tax": state.get("calculations", {}).get("tax_analysis", {}).get(f"{current_regime}_regime", {}).get("total_tax", 0),
                "alternative_tax": other_tax,
                "additional_cost_or_saving": other_tax,
            }
        except Exception as e:
            scenarios_result["tax_regime_switch"] = {"error": str(e)}

        state["scenarios"] = scenarios_result

        state["audit_log"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "step": "scenario_agent",
            "status": "completed",
            "detail": f"Scenarios computed: {list(scenarios_result.keys())}",
        })

    except Exception as e:
        state["error"] = f"Scenario computation error: {str(e)}"
        state["audit_log"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "step": "scenario_agent",
            "status": "error",
            "detail": str(e),
        })

    return state
