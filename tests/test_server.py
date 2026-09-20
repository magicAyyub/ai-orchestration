"""Tests unitaires et d'intégration pour le serveur FastAPI."""
from fastapi.testclient import TestClient
from ai_orchestration.server import app
from ai_orchestration.config import settings

client = TestClient(app)


def test_health_endpoint():
    """Vérifie que l'endpoint public /health réponds sans authentification."""
    response = client.get("/health")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data.get("status") == "ok"


def test_chat_endpoint_unauthorized():
    """Vérifie le rejet HTTP 401 si le Token Bearer est absent ou invalide."""
    response = client.post("/api/v1/chat", json={"message": "Bonjour"})
    assert response.status_code == 401

    invalid_headers = {"Authorization": "Bearer token_invalide"}
    response = client.post("/api/v1/chat", json={"message": "Bonjour"}, headers=invalid_headers)
    assert response.status_code == 401


def test_chat_endpoint_authorized():
    """Vérifie le fonctionnement de l'endpoint avec un Token Bearer valide."""
    valid_headers = {"Authorization": f"Bearer {settings.jumbo_api_key}"}
    response = client.post("/api/v1/chat", json={"message": "Recette de cuisine ?"}, headers=valid_headers)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data.get("status") == "success"
    assert "response" in json_data
