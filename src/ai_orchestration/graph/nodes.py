"""Définition des nœuds pour le graphe d'agent LangGraph."""
from typing import Dict, Any
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode

from ai_orchestration.config import settings
from ai_orchestration.tools import all_tools
from ai_orchestration.graph.state import AgentState

SYSTEM_PROMPT = """Tu es un assistant virtuel expert pour Jumbo Pneus.
Ton rôle est d'aider les clients et téléconseillers à rechercher des pneus dans le catalogue en temps réel.

Directives:
* Pour rechercher un pneu, valide idealement la dimension complète: Largeur (ex: 205), Série/Hauteur (ex: 55), Diamètre (ex: 16).
* Si la dimension est incomplète, demande poliment les éléments manquants avant la recherche si nécessaire.
* Utilise l'outil `search_tires` dès que tu as des critères valides.
* Si le client demande du premier prix ou budget, utilise tier='premier_prix'. Pour du haut de gamme, tier='premium'. Pour du milieu de gamme, tier='moyenne_gamme'.
* Présente toujours les résultats de manière claire avec la marque, le modèle, la dimension, le prix TTC et la quantité disponible.
"""


def get_llm() -> ChatOpenAI:
    """Initialise le modèle LLM compatible OpenAI via l'API Groq."""
    return ChatOpenAI(
        api_key=settings.groq_api_key,
        base_url="https://api.groq.com/openai/v1",
        model=settings.groq_model,
        temperature=0.1,
    )


def agent_node(state: AgentState) -> Dict[str, Any]:
    """Invoque le modèle LLM avec les outils et le prompt système."""
    llm = get_llm()
    llm_with_tools = llm.bind_tools(all_tools)
    
    messages = state["messages"]
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)

    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


tools_node = ToolNode(all_tools)
