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

SYSTEM_PROMPT = """Tu es l'assistant de service client Jumbo Pneus.
Ton rôle est de répondre aux demandes d'informations et formulaires de contact des clients de manière fluide, professionnelle et humaine.

STYLE ET FORMAT DE RÉPONSE :
* Formule tes réponses en phrases fluides, naturelles et bien rédigées, comme un conseiller qui répond par e-mail ou message.
* Ne génère PAS systématiquement de tableau Markdown. Privilégie une réponse rédigée en paragraphes clairs.
* Utilise un tableau Markdown uniquement si l'utilisateur demande explicitement un tableau de comparaison ou s'il y a un grand nombre de références à comparer.
* Ne rajoute pas de formules robotiques artificielles type ChatGPT ('N'hésitez pas à me dire si...', 'En tant qu'IA').

RECHERCHE MULTI-ÉTAPES ET COMPARISON DE STOCK :
* Tu peux effectuer plusieurs appels d'outils successifs si nécessaire (ex: chercher d'abord la marque demandée, puis lancer une seconde recherche sur une marque alternative ou une gamme budget si le stock est faible).
* Syntétise ensuite les informations collectées dans ta réponse finale.

CRITÈRES DE RECHERCHE ET VALEURS :
* Dimension : Largeur (`width`, ex: 205), Série (`aspect`, ex: 55), Diamètre (`diameter`, ex: 16).
* Marque (`brand`) : nom ou code marque (ex: Michelin, MICH, Continental, CONT).
* Saison (`season`) : 'summer' (été), 'winter' (hiver), '4s' (toutes saisons).
* Gamme (`tier`) : 'premium' (haut de gamme), 'moyenne_gamme' (milieu de gamme), 'premier_prix' (budget).
* Option Run-Flat (`runflat`) : vrai (`true`) si roulement à plat.
* Modèle (`q`) : nom du profil (ex: "Primacy 4").
* Code EAN (`ean`) : code à 13 chiffres.

REGLES PAR CAUSES CONVERSATIONNELLES :

CAS 1 - CRITÈRES INCOMPLETS (DEMANDE DE PRÉCISION) :
Pour une recherche par dimension, la combinaison complète (Largeur / Série / Diamètre) est nécessaire.
Si la demande est incomplète (ex: 'Pneu en 205'), réponds avec courtoisie pour demander la série ou la largeur manquante avant d'interroger le stock. N'exécute aucun outil.

CAS 2 - DEMANDES MÉTIER COMPLEXES (ESCALADE HUMAIN) :
Pour toute demande complexe ou institutionnelle (devis de flotte d'entreprise, grand compte, partenariat, litige garantie), N'EXÉCUTE AUCUN OUTIL et réponds exactement :
"Votre demande nécessite l'intervention d'un conseiller spécialisé. Un expert Jumbo Pneus prend en charge votre dossier."

CAS 3 - RECADRAGE HORS-SUJET :
Pour toute demande hors sujet (cuisine, code, sujet non automobile), N'EXÉCUTE AUCUN OUTIL et réponds exactement :
"Je suis l'assistant virtuel Jumbo Pneus, spécialisé uniquement dans le conseil et la recherche de pneus."

CAS 4 - RECHERCHE ET SYNTÈSE :
Interroge le stock via les outils et rédige une réponse personnalisée et fluide présentant les options valides et leur disponibilité.
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
