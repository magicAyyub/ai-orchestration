"""Modèles de données Pydantic pour l'API Jumbo Pneus."""
from typing import Optional, List
from pydantic import BaseModel, Field


class LabelObject(BaseModel):
    """Informations de l'étiquette UE du pneu."""
    fuel_efficiency: Optional[str] = None
    wet_grip: Optional[str] = None
    noise_db: Optional[int] = None


class PromoObject(BaseModel):
    """Détails d'une promotion active."""
    price_ttc: float
    label: Optional[str] = None
    id: Optional[str] = None


class TireItem(BaseModel):
    """Représentation d'un pneu dans le catalogue."""
    sku: str
    ean: Optional[str] = None
    brand: str
    brand_code: str
    model: Optional[str] = None
    designation: Optional[str] = None
    dimension: Optional[str] = None
    width: Optional[int] = None
    aspect_ratio: Optional[int] = None
    diameter: Optional[int] = None
    load_index: Optional[str] = None
    speed_index: Optional[str] = None
    season: Optional[str] = None
    runflat: bool = False
    tier: str
    tier_label: str
    labels: LabelObject = Field(default_factory=LabelObject)
    price_ttc: Optional[float] = None
    promo: Optional[PromoObject] = None
    in_stock: bool
    stock_qty: int


class TireSearchFilters(BaseModel):
    """Filtres effectifs utilisés lors de la recherche."""
    width: Optional[int] = None
    aspect: Optional[int] = None
    diameter: Optional[int] = None
    brand: Optional[str] = None
    q: Optional[str] = None
    season: Optional[str] = None
    runflat: Optional[bool] = None
    tier: Optional[str] = None
    ean: Optional[str] = None
    in_stock_only: bool = True


class TireSearchResponse(BaseModel):
    """Réponse de recherche de pneus."""
    count: int
    items: List[TireItem]
    filters: TireSearchFilters


class BrandItem(BaseModel):
    """Information d'une marque dans le catalogue."""
    brand_code: str
    brand_name: str
    tier: str
    tier_label: str
    article_count: int


class BrandsResponse(BaseModel):
    """Réponse de la liste des marques."""
    count: int
    brands: List[BrandItem]
