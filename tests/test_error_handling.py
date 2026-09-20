"""Tests unitaires pour la gestion d'erreurs d'infrastructure 401 et 503."""
import json
from langchain_core.messages import ToolMessage
from ai_orchestration.graph.nodes import guardrail_node, error_handling_node


def test_guardrail_detects_401_error():
    """Vérifie la détection d'une erreur 401 d'authentification."""
    payload = {"error": "Échec d'authentification (401): Token invalide"}
    tool_msg = ToolMessage(content=json.dumps(payload), tool_call_id="call_401")
    state = {"messages": [tool_msg]}

    res = guardrail_node(state)
    assert res.get("error_status") == "401_auth_error"

    fallback = error_handling_node(res)
    assert "authentification" in fallback["messages"][0].content.lower()


def test_guardrail_detects_503_error():
    """Vérifie la détection d'une erreur 503 d'indisponibilité du service."""
    payload = {"error": "Erreur serveur (503): Service indisponible"}
    tool_msg = ToolMessage(content=json.dumps(payload), tool_call_id="call_503")
    state = {"messages": [tool_msg]}

    res = guardrail_node(state)
    assert res.get("error_status") == "503_service_unavailable"

    fallback = error_handling_node(res)
    assert "indisponibles" in fallback["messages"][0].content.lower()
