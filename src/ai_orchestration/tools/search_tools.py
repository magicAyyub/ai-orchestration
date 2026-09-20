"""Outils LangChain pour la recherche de pneus."""
from typing import Optional, Dict, Any
from langchain_core.tools import tool
from ai_orchestration.api.client import JumboPneusClient


@tool
def search_tires(
    width: Optional[int] = None,
    aspect: Optional[int] = None,
    diameter: Optional[int] = None,
    brand: Optional[str] = None,
    q: Optional[str] = None,
    season: Optional[str] = None,
    runflat: Optional[bool] = None,
    tier: Optional[str] = None,
    ean: Optional[str] = None,
    in_stock_only: bool = True,
    limit: int = 10,
) -> Dict[str, Any]:
    """Recherche les pneus dans le catalogue et consulte le stock en temps réel.

    Args:
        width: Largeur du pneu en mm (ex: 205).
        aspect: Hauteur ou série en % (ex: 55).
        diameter: Diamètre de jante en pouces (ex: 16).
        brand: Marque ou code marque (ex: Michelin ou MICH).
        q: Recherche libre sur le modèle.
        season: Saison: summer, winter, ou 4s.
        runflat: Vrai pour filtrer les pneus Run-Flat.
        tier: Gamme: premium, moyenne_gamme, ou premier_prix.
        ean: Code-barres EAN-13.
        in_stock_only: Vrai pour ne retourner que les articles en stock.
        limit: Nombre maximal de résultats.
    """
    if not any([width, aspect, diameter, brand, q, tier, ean]):
        return {
            "error": "Veuillez fournir au moins un critère de filtrage."
        }

    client = JumboPneusClient()
    try:
        res = client.search_tires(
            width=width,
            aspect=aspect,
            diameter=diameter,
            brand=brand,
            q=q,
            season=season,
            runflat=runflat,
            tier=tier,
            ean=ean,
            in_stock_only=in_stock_only,
            limit=limit,
        )
        return res.model_dump()
    except Exception as e:
        return {"error": str(e)}


@tool
def lookup_by_ean(ean: str) -> Dict[str, Any]:
    """Recherche directement un pneu via son code-barres EAN-13.

    Args:
        ean: Code-barres EAN-13.
    """
    cleaned_ean = "".join(filter(str.isdigit, ean))
    if not cleaned_ean:
        return {"error": "Code EAN-13 invalide: doit contenir uniquement des chiffres."}

    client = JumboPneusClient()
    try:
        res = client.search_tires(ean=cleaned_ean, limit=1)
        return res.model_dump()
    except Exception as e:
        return {"error": str(e)}
