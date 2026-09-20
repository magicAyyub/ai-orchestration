"""Définition de l'état partagé du graphe d'agent LangGraph."""
from typing import Annotated, Sequence, Optional, Dict, Any, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Schéma de l'état partagé entre les nœuds du graphe."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    extracted_params: Optional[Dict[str, Any]]
    status: Optional[str]
