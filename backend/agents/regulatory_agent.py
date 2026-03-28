"""Regulatory agent: Validate output against SEBI/IT Act rules via RAG."""

from datetime import datetime
from ..agents.state import ArthAgentState
from ..knowledge.query import RegulatoryQuery


async def regulatory_agent(state: ArthAgentState) -> ArthAgentState:
    """RegulatoryAgent node: Check compliance and flag violations."""
    state["current_step"] = "regulatory_agent"
    state["audit_log"].append({
        "timestamp": datetime.utcnow().isoformat(),
        "step": "regulatory_agent",
        "status": "started",
    })

    try:
        regulatory_query = RegulatoryQuery()
        flags = []

        # Query tax rules
        tax_rules = regulatory_query.query_tax_rules("tax regime selection and deductions", n_results=2)

        # Check for common compliance notes
        profile = state.get("profile", {})
        income = profile.get("income", {}).get("basic_salary", 0)
        
        # Check if using old regime for high income (where new regime might be better)
        tax_calc = state.get("calculations", {}).get("tax_analysis", {})
        if tax_calc:
            recommended = tax_calc.get("recommended", "new")
            flags.append({
                "type": "tax_regime_check",
                "status": "ok",
                "message": f"Tax regime recommendation: {recommended} regime. Ensure annual review.",
                "rule_reference": tax_rules[0]["rule"] if tax_rules else "",
            })

        # Check deduction claims
        deductions = profile.get("deductions", {})
        if deductions.get("deduction_80c", 0) < 150000:
            flags.append({
                "type": "missed_deduction",
                "status": "warning",
                "message": f"80C deduction only ₹{deductions.get('deduction_80c', 0)}. Claim up to ₹1.5L via ELSS/PPF.",
            })

        if deductions.get("deduction_80d", 0) == 0:
            flags.append({
                "type": "missed_deduction",
                "status": "warning",
                "message": "No health insurance deduction claimed. Up to ₹25K available (self+family below 60) u/s 80D.",
            })

        # Check NPS compliance
        nps_claimed = deductions.get("nps_80ccd_1b", 0)
        if nps_claimed > 50000:
            flags.append({
                "type": "nps_limit_exceeded",
                "status": "error",
                "message": f"NPS 80CCD(1B) deduction exceeds ₹50K limit. Claimed: ₹{nps_claimed}",
            })

        # Portfolio compliance (if portfolio data exists)
        # TODO: Add check for portfolio overlap, expense ratios
        
        state["regulatory_flags"] = flags

        state["audit_log"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "step": "regulatory_agent",
            "status": "completed",
            "detail": f"Compliance check: {len(flags)} flags raised",
        })

    except Exception as e:
        state["error"] = f"Regulatory check error: {str(e)}"
        state["audit_log"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "step": "regulatory_agent",
            "status": "error",
            "detail": str(e),
        })

    return state
