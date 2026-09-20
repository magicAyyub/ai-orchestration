"""Construction et compilation du graphe de workflow LangGraph."""
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import tools_condition

from ai_orchestration.graph.state import AgentState
from ai_orchestration.graph.nodes import agent_node, tools_node


def create_workflow():
    """Assemble et compile le graphe d'agent LangGraph."""
    workflow = StateGraph(AgentState)

    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tools_node)

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", tools_condition)
    workflow.add_edge("tools", "agent")

    return workflow.compile()
