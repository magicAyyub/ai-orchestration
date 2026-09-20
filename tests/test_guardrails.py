"""Tests unitaires pour la validation des garde-fous métiers dans le graphe."""
import json
from langchain_core.messages import ToolMessage
from ai_orchestration.graph.nodes import guardrail_node


def test_guardrail_node_filters_low_stock():
    """Vérifie que le nœud de garde-fou ne conserve que les articles avec un stock au moins égal à 2."""
    payload = {
        "items": [
            {"sku": "A1", "in_stock": True, "stock_qty": 5},
            {"sku": "B2", "in_stock": True, "stock_qty": 1},
            {"sku": "C3", "in_stock": False, "stock_qty": 0},
            {"sku": "D4", "in_stock": True, "stock_qty": 2},
        ]
    }
    tool_msg = ToolMessage(content=json.dumps(payload), tool_call_id="call_123")
    state = {"messages": [tool_msg]}

    res = guardrail_node(state)
    assert "validated_items" in res
    validated = res["validated_items"]
    assert len(validated) == 2
    skus = [item["sku"] for item in validated]
    assert skus == ["A1", "D4"]
