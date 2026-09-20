"""Construction et compilation du graphe de workflow LangGraph avec garde-fous."""
from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import tools_condition

from ai_orchestration.graph.state import AgentState
from ai_orchestration.graph.nodes import agent_node, tools_node, guardrail_node, error_handling_node


def check_guardrail_outcome(state: AgentState) -> Literal["error_handler", "agent"]:
    """Détermine si le garde-fou a détecté une erreur d'infrastructure nécessitant un traitement."""
    if state.get("error_status"):
        return "error_handler"
    return "agent"


def create_workflow():
    """Assemble et compile le graphe d'agent LangGraph enrichi de garde-fous."""
    workflow = StateGraph(AgentState)

    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tools_node)
    workflow.add_node("guardrail", guardrail_node)
    workflow.add_node("error_handler", error_handling_node)

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", tools_condition)
    workflow.add_edge("tools", "guardrail")
    workflow.add_conditional_edges("guardrail", check_guardrail_outcome)
    workflow.add_edge("error_handler", END)

    return workflow.compile()
