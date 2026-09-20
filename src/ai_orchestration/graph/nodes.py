"""Définition des nœuds et garde-fous pour le graphe d'agent LangGraph."""
import json
from typing import Dict, Any
from langchain_core.messages import SystemMessage, ToolMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode

from ai_orchestration.config import settings
from ai_orchestration.tools import all_tools
from ai_orchestration.graph.state import AgentState
from ai_orchestration.observability import JumboTelemetryCallbackHandler, logger

SYSTEM_PROMPT = """Tu es un assistant virtuel expert pour Jumbo Pneus.
Ton rôle est de conseiller les clients et de rechercher des pneus dans le catalogue en temps réel.

CRITÈRES DE RECHERCHE CATALOGUE ET LEURS VALEURS VALIDES :
* Dimension :
  - Largeur (`width`) : exprimée en mm (ex: 205, 225, 195).
  - Hauteur / Série (`aspect`) : exprimée en pourcentage (ex: 55, 45, 60).
  - Diamètre (`diameter`) : exprimé en pouces (ex: 16, 17, 18).
* Marque (`brand`) : nom commercial (ex: Michelin, Continental) ou code marque (ex: MICH, CONT).
* Saison (`season`) : 'summer' (été), 'winter' (hiver), ou '4s' (toutes saisons).
* Gamme (`tier`) : 
  - 'premium' (Haut de gamme: Michelin, Continental, Bridgestone, Pirelli, Goodyear, Dunlop, Hankook).
  - 'moyenne_gamme' (Milieu de gamme: Kumho, Yokohama, Nokian, Falken, Nexen, Vredestein, Kleber, Uniroyal, Firestone, etc.).
  - 'premier_prix' (Entrée de gamme / budget: toutes les autres marques).
* Option Run-Flat (`runflat`) : vrai (`true`) si l'utilisateur demande des pneus de roulement à plat.
* Recherche Modèle (`q`) : recherche libre sur le nom du modèle (ex: "Primacy 4", "CrossClimate").
* Code-barres EAN (`ean`) : code EAN-13 à 13 chiffres.

DIRECTIVES DE COMPORTEMENT CONVERSATIONNEL :

CAS 1 - COLLECTE GUIDÉE ET CRITÈRES INCOMPLETS :
Pour effectuer une recherche par dimension, la combinaison complète (Largeur / Série / Diamètre) est nécessaire (ex: 205/55R16).
Si l'utilisateur donne une dimension incomplète (ex: "Je veux du 205" ou "Jantes en 16"), réponds de façon naturelle et bienveillante pour expliquer ce qu'il manque et lui demander la série ou la largeur manquante avant d'interroger le stock. Ne déclenche aucun outil tant qu'au moins un critère de recherche valide n'est pas fourni.

CAS 2 - DEMANDES MÉTIER COMPLEXES OU INSTITUTIONNELLES (ESCALADE HUMAIN) :
Si la demande concerne le domaine Jumbo Pneus mais qu'elle est trop complexe ou spécifique pour un traitement automatique (ex: devis pour une flotte de véhicules d'entreprise, demande grand compte, partenariat commercial, litige de garantie, demande de raccordement réseau), NE DÉCLENCHE AUCUN OUTIL et réponds exactement :
"Votre demande nécessite l'intervention d'un conseiller spécialisé. Un expert Jumbo Pneus prend en charge votre dossier."

CAS 3 - RECADRAGE HORS-SUJET :
Si la demande n'a aucun rapport avec les pneumatiques ou le service Jumbo Pneus (ex: recette de cuisine, programmation informatique, politique, propos incohérents), NE DÉCLENCHE AUCUN OUTIL et réponds exactement :
"Je suis l'assistant virtuel Jumbo Pneus, spécialisé uniquement dans le conseil et la recherche de pneus."

CAS 4 - RECHERCHE STANDARD ET PRÉSENTATION DES RÉSULTATS :
Dès que vous disposez de critères valides, déclenche l'outil `search_tires` ou `lookup_by_ean`. Présente uniquement les articles retournés en indiquant clairement la marque, le modèle, la dimension complète, le prix TTC et la quantité disponible.
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
    """Invoque le modèle LLM avec les outils et le callback de télémesure."""
    llm = get_llm()
    telemetry_handler = JumboTelemetryCallbackHandler()
    llm_with_tools = llm.bind_tools(all_tools)
    
    messages = state["messages"]
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)

    response = llm_with_tools.invoke(messages, config={"callbacks": [telemetry_handler]})

    # Analyse de la réponse pour détecter une escalade vers un humain
    is_escalated = False
    if isinstance(response, AIMessage) and "conseiller spécialisé" in str(response.content):
        is_escalated = True
        logger.info("Escalade vers un conseiller humain détectée.")

    return {
        "messages": [response],
        "escalated_to_human": is_escalated,
    }


def guardrail_node(state: AgentState) -> Dict[str, Any]:
    """Applique les garde-fous métiers (stock minimal >= 2) et détecte les erreurs d'infrastructure."""
    messages = state.get("messages", [])
    if not messages:
        return {}

    last_message = messages[-1]
    if not isinstance(last_message, ToolMessage):
        return {}

    try:
        content_data = json.loads(last_message.content)
    except Exception:
        return {}

    if isinstance(content_data, dict) and "error" in content_data:
        error_msg = str(content_data["error"])
        if "401" in error_msg or "Authentification" in error_msg:
            logger.critical(f"Alerte critique d'authentification 401: {error_msg}")
            return {"error_status": "401_auth_error"}
        elif "503" in error_msg or "500" in error_msg or "serveur" in error_msg.lower():
            logger.warning(f"Indisponibilité du service 503/500: {error_msg}")
            return {"error_status": "503_service_unavailable"}

    if isinstance(content_data, dict) and "items" in content_data:
        raw_items = content_data["items"]
        validated = [
            item for item in raw_items
            if item.get("in_stock") is True and item.get("stock_qty", 0) >= 2
        ]
        logger.info(f"Garde-fou appliqué: {len(validated)} articles conservés sur {len(raw_items)} (stock >= 2)")
        return {"validated_items": validated, "error_status": None}

    return {}


def error_handling_node(state: AgentState) -> Dict[str, Any]:
    """Génère un message de réponse contrôlé en cas d'erreur d'infrastructure."""
    error_status = state.get("error_status")
    if error_status == "401_auth_error":
        fallback = "Une erreur d'authentification système s'est produite. Les équipes techniques ont été notifiées."
    elif error_status == "503_service_unavailable":
        fallback = "Notre catalogue et état des stocks sont momentanément indisponibles. Veuillez réessayer dans quelques instants."
    else:
        fallback = "Le service de recherche rencontre une indisponibilité temporaire."

    return {"messages": [AIMessage(content=fallback)]}


tools_node = ToolNode(all_tools)
