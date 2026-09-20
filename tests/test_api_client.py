"""Tests d'intégration pour le client HTTP JumboPneusClient."""
import pytest
from ai_orchestration.api.client import JumboPneusClient


def test_client_health():
    """Vérifie la réponse de l'endpoint de santé."""
    client = JumboPneusClient()
    health = client.check_health()
    assert health.get("status") == "ok"


def test_client_brands():
    """Vérifie la récupération de la liste des marques."""
    client = JumboPneusClient()
    brands_resp = client.get_brands()
    assert brands_resp.count > 0
    assert len(brands_resp.brands) > 0


def test_client_search_tires():
    """Vérifie la recherche de pneus par dimension."""
    client = JumboPneusClient()
    res = client.search_tires(width=205, aspect=55, diameter=16, limit=3)
    assert res.count > 0
    assert len(res.items) <= 3
    assert res.items[0].width == 205
    assert res.items[0].aspect_ratio == 55
    assert res.items[0].diameter == 16
