"""Outils LangChain pour la consultation des marques et gammes."""
from typing import Dict, Any
from langchain_core.tools import tool
from ai_orchestration.api.client import JumboPneusClient


@tool
def get_brand_list() -> Dict[str, Any]:
    """Retourne la liste des marques actives avec leur classification de gamme."""
    client = JumboPneusClient()
    try:
        res = client.get_brands()
        return res.model_dump()
    except Exception as e:
        return {"error": str(e)}
