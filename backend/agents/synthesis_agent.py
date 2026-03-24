"""Synthesis agent: Generate structured financial plan using Claude."""

from datetime import datetime
import json
from anthropic import Anthropic
from ..agents.state import ArthAgentState

client = Anthropic()

SYNTHESIS_PROMPT = """You are an expert financial advisor synthesizing a comprehensive financial plan.

Given the following financial analysis, generate a structured JSON plan with specific, actionable recommendations:

PROFILE:
{profile}

TAX ANALYSIS:
{tax_analysis}

FIRE PLAN:
{fire_plan}

SCENARIOS:
{scenarios}

COMPLIANCE FLAGS:
{flags}

Generate a JSON response with this structure:
{{
    "executive_summary": "2-3 sentence overview",
    "immediate_actions": ["Action 1", "Action 2", ...],
    "tax_optimization": {{
        "recommendation": "old|new regime",
        "reasoning": "Why this regime",
        "implementation": ["Step 1", "Step 2", ...]
    }},
    "retirement_plan": {{
        "monthly_sip": number,
        "asset_allocation": "70% equity, 20% debt, 10% gold",
        "risk_factors": ["Factor 1", "Factor 2"],
        "milestone_timeline": ["Age X: Checkpoint", ...]
    }},
    "next_review": "When to revisit plan (e.g., '6 months' or 'After salary change')",
    "compliance_notes": ["Note 1", "Note 2", ...]
}}

Return ONLY valid JSON."""


async def synthesis_agent(state: ArthAgentState) -> ArthAgentState:
    """SynthesisAgent node: Generate final plan using Claude."""
    state["current_step"] = "synthesis_agent"
    state["audit_log"].append({
        "timestamp": datetime.utcnow().isoformat(),
        "step": "synthesis_agent",
        "status": "started",
    })

    try:
        profile = state.get("profile", {})
        calculations = state.get("calculations", {})
        scenarios = state.get("scenarios", {})
        flags = state.get("regulatory_flags", [])

        # Prepare context for Claude
        prompt = SYNTHESIS_PROMPT.format(
            profile=json.dumps(profile, indent=2, default=str),
            tax_analysis=json.dumps(calculations.get("tax_analysis", {}), indent=2, default=str),
            fire_plan=json.dumps(calculations.get("fire_plan", {}), indent=2, default=str),
            scenarios=json.dumps(scenarios, indent=2, default=str),
            flags=json.dumps(flags, indent=2, default=str),
        )

        # Call Claude Sonnet
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        response_text = response.content[0].text.strip()
        
        # Parse JSON from response (handle markdown wrapping)
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]

        plan_data = json.loads(response_text)
        state["final_plan"] = plan_data

        state["audit_log"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "step": "synthesis_agent",
            "status": "completed",
            "detail": "Financial plan synthesized successfully",
        })

    except Exception as e:
        state["error"] = f"Synthesis error: {str(e)}"
        # Fallback to simple plan if Claude fails
        state["final_plan"] = {
            "executive_summary": "Financial plan generated (synthesis pending)",
            "immediate_actions": ["Review tax optimization", "Set up SIP"],
            "tax_optimization": {
                "recommendation": state.get("calculations", {}).get("tax_analysis", {}).get("recommended", "new"),
                "reasoning": "Based on income and deductions",
            },
            "retirement_plan": {
                "monthly_sip": state.get("calculations", {}).get("fire_plan", {}).get("monthly_sip_needed", 0),
                "asset_allocation": "70% equity, 20% debt, 10% gold",
            },
        }
        state["audit_log"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "step": "synthesis_agent",
            "status": "error_fallback",
            "detail": str(e),
        })

    return state
