"""Modèles Pydantic pour l'extraction de paramètres et la gestion d'état."""
from typing import Optional
from pydantic import BaseModel, Field


class SearchParamsInput(BaseModel):
    """Paramètres de recherche de pneu extraits de la requête utilisateur."""
    width: Optional[int] = Field(None, description="Largeur du pneu en mm (ex: 205)")
    aspect: Optional[int] = Field(None, description="Hauteur ou série en % (ex: 55)")
    diameter: Optional[int] = Field(None, description="Diamètre de la jante en pouces (ex: 16)")
    brand: Optional[str] = Field(None, description="Nom de la marque ou code marque")
    season: Optional[str] = Field(None, description="Saison: summer, winter, ou 4s")
    tier: Optional[str] = Field(None, description="Gamme: premium, moyenne_gamme, ou premier_prix")
    q: Optional[str] = Field(None, description="Recherche libre sur le modèle")
    ean: Optional[str] = Field(None, description="Code-barres EAN-13")
    runflat: Optional[bool] = Field(None, description="Pneu Run-Flat si vrai")
