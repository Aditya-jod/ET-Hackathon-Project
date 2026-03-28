"""Synthesis agent: Generate structured financial plan using Claude, Ollama, or Groq."""

import asyncio
from datetime import datetime
import json
import os
from ..agents.state import ArthAgentState

import httpx
from groq import Groq

OLLAMA_BASE_URL   = "http://localhost:11434"
OLLAMA_MODEL      = "llama3.1:8b"
OLLAMA_TIMEOUT    = 45.0   # seconds — covers cold start
GROQ_MODEL        = "llama-3.1-8b-instant"
MAX_RETRIES       = 2

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


async def _call_ollama_async(prompt: str) -> str:
    """
    Call Ollama with a hard timeout.
    Raises asyncio.TimeoutError if Ollama doesn't respond in time.
    """
    async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
            },
        )
        response.raise_for_status()
        return response.json()["response"]


async def _call_groq(prompt: str) -> str:
    """Groq free-tier fallback. Runs in thread pool (SDK is sync)."""
    client = Groq()  # reads GROQ_API_KEY from env
    loop   = asyncio.get_event_loop()

    def _sync_call():
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
            temperature=0.3,
        )
        return completion.choices[0].message.content

    return await loop.run_in_executor(None, _sync_call)


async def call_llm_with_fallback(prompt: str) -> tuple[str, str]:
    """
    Try Ollama first (local, zero cost).
    If timeout or any error → fall back to Groq (free API).

    Returns:
        (response_text, provider_used)
        provider_used is "ollama" or "groq" — log this in audit_trail.
    """
    for attempt in range(MAX_RETRIES):
        try:
            text = await asyncio.wait_for(
                _call_ollama_async(prompt),
                timeout=OLLAMA_TIMEOUT,
            )
            return text, "ollama"

        except (asyncio.TimeoutError, httpx.ConnectError, httpx.HTTPError) as e:
            # Ollama not running or too slow — fall through to Groq
            error_type = type(e).__name__
            # Log but don't crash — Groq is the fallback
            print(f"[synthesis_agent] Ollama attempt {attempt+1} failed: {error_type}. "
                  f"{'Retrying...' if attempt < MAX_RETRIES - 1 else 'Switching to Groq.'}")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(1)

    # All Ollama attempts failed — use Groq
    try:
        text = await _call_groq(prompt)
        return text, "groq"
    except Exception as e:
        raise RuntimeError(
            f"Both Ollama and Groq failed. Groq error: {e}. "
            f"Check GROQ_API_KEY in .env and internet connectivity."
        ) from e


async def synthesis_agent(state: ArthAgentState) -> ArthAgentState:
    """SynthesisAgent node: Generate final plan using Ollama or Groq."""
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
        synthesis_prompt = SYNTHESIS_PROMPT.format(
            profile=json.dumps(profile, indent=2, default=str),
            tax_analysis=json.dumps(calculations.get("tax_analysis", {}), indent=2, default=str),
            fire_plan=json.dumps(calculations.get("fire_plan", {}), indent=2, default=str),
            scenarios=json.dumps(scenarios, indent=2, default=str),
            flags=json.dumps(flags, indent=2, default=str),
        )

        # Call LLM with proper fallback chain
        llm_response, provider = await call_llm_with_fallback(synthesis_prompt)
        state["audit_log"].append({
            "agent": "synthesis_agent",
            "llm_provider": provider,
            "timestamp": datetime.utcnow().isoformat(),
        })

        # Parse JSON from response (handle markdown wrapping)
        response_text = llm_response.strip()
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
            "detail": f"Plan synthesized via {provider}",
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
