"""LangGraph StateGraph definition for the ArthAgent multi-agent system."""

import asyncio
from langgraph.graph import StateGraph, END
from .state import ArthAgentState
from .intake_agent import intake_agent
from .calculation_agent import calculation_agent
from .regulatory_agent import regulatory_agent
from .scenario_agent import scenario_agent
from .synthesis_agent import synthesis_agent
from .disclaimer_agent import disclaimer_agent


def _async_wrap(async_fn):
    """Wrap async function for sync graph."""
    def sync_wrapper(state: ArthAgentState) -> ArthAgentState:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(async_fn(state))
        loop.close()
        return result
    return sync_wrapper


# Wrap async agents for synchronous graph execution
intake_node = _async_wrap(intake_agent)
calculation_node = _async_wrap(calculation_agent)
regulatory_node = _async_wrap(regulatory_agent)
scenario_node = _async_wrap(scenario_agent)
synthesis_node = _async_wrap(synthesis_agent)
disclaimer_node = _async_wrap(disclaimer_agent)

# Define the graph
workflow = StateGraph(ArthAgentState)

workflow.add_node("intake", intake_node)
workflow.add_node("calculation", calculation_node)
workflow.add_node("regulatory", regulatory_node)
workflow.add_node("scenario", scenario_node)
workflow.add_node("synthesis", synthesis_node)
workflow.add_node("disclaimer", disclaimer_node)

# Define the edges
workflow.set_entry_point("intake")
workflow.add_edge("intake", "calculation")
workflow.add_edge("calculation", "regulatory")
workflow.add_edge("regulatory", "scenario")
workflow.add_edge("scenario", "synthesis")
workflow.add_edge("synthesis", "disclaimer")
workflow.add_edge("disclaimer", END)

# Compile the graph
app = workflow.compile()
