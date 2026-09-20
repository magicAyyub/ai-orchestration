"""Tests unitaires pour les outils LangChain."""
from ai_orchestration.tools import search_tires, lookup_by_ean, get_brand_list


def test_search_tires_tool():
    """Vérifie l'exécution de l'outil search_tires."""
    res = search_tires.invoke({"width": 205, "aspect": 55, "diameter": 16, "limit": 2})
    assert "items" in res
    assert res["count"] > 0


def test_lookup_ean_tool():
    """Vérifie l'exécution de l'outil lookup_by_ean."""
    res = lookup_by_ean.invoke({"ean": "3528705349843"})
    assert "items" in res


def test_get_brand_list_tool():
    """Vérifie l'exécution de l'outil get_brand_list."""
    res = get_brand_list.invoke({})
    assert "brands" in res
    assert res["count"] > 0
