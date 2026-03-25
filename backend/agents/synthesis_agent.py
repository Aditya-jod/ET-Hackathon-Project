"""Synthesis agent: Generate structured financial plan using Claude or local Ollama."""

from datetime import datetime
import json
import os
from ..agents.state import ArthAgentState

# Try Anthropic first, fall back to Ollama if no API key
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
USE_OLLAMA = not ANTHROPIC_API_KEY or os.getenv("USE_OLLAMA", "false").lower() == "true"

if USE_OLLAMA:
    import requests
    OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
    client = None  # We'll use requests directly
else:
    from anthropic import Anthropic
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
    """SynthesisAgent node: Generate final plan using Claude or Ollama."""
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

        # Prepare context for LLM
        prompt = SYNTHESIS_PROMPT.format(
            profile=json.dumps(profile, indent=2, default=str),
            tax_analysis=json.dumps(calculations.get("tax_analysis", {}), indent=2, default=str),
            fire_plan=json.dumps(calculations.get("fire_plan", {}), indent=2, default=str),
            scenarios=json.dumps(scenarios, indent=2, default=str),
            flags=json.dumps(flags, indent=2, default=str),
        )

        # Call LLM (Claude or Ollama)
        if USE_OLLAMA:
            response_text = await _call_ollama(prompt)
        else:
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
            "detail": f"Plan synthesized via {'Ollama' if USE_OLLAMA else 'Claude'}",
        })

    except Exception as e:
        state["error"] = f"Synthesis error: {str(e)}"
        # Fallback to simple plan if LLM fails
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


async def _call_ollama(prompt: str) -> str:
    """Call local Ollama API for synthesis."""
    import requests
    
    try:
        response = requests.post(
            f"{OLLAMA_API_URL}/api/generate",
            json={
                "model": "mistral",  # or "llama2", "neural-chat", etc.
                "prompt": prompt,
                "stream": False,
                "temperature": 0.0,
            },
            timeout=120,
        )
        response.raise_for_status()
        return response.json()["response"]
    except Exception as e:
        raise RuntimeError(f"Ollama API error: {str(e)}. Is Ollama running? Start with: ollama serve")
