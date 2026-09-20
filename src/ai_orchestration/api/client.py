"""Client HTTP pour l'API Partenaire Jumbo Pneus."""
from typing import Optional, Dict, Any
import httpx
from ai_orchestration.config import settings
from ai_orchestration.schemas.api_models import TireSearchResponse, BrandsResponse


class JumboAPIError(Exception):
    """Exception de base pour les erreurs de l'API Jumbo Pneus."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class JumboAuthError(JumboAPIError):
    """Erreur d'authentification (401)."""
    pass


class JumboBadRequestError(JumboAPIError):
    """Requête invalide ou manque de filtres (400)."""
    pass


class JumboServerError(JumboAPIError):
    """Erreur serveur ou base indisponible (500/503)."""
    pass


class JumboPneusClient:
    """Client HTTP encapsulant les appels à l'API Jumbo Pneus."""

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = (base_url or settings.jumbo_base_url).rstrip("/")
        self.api_key = api_key or settings.jumbo_api_key
        if not self.api_key:
            raise ValueError("Clé API Jumbo manquante dans la configuration.")

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "User-Agent": "AI-Orchestration-Client/1.0",
        }

    def _handle_response_error(self, response: httpx.Response) -> None:
        if response.is_success:
            return

        status = response.status_code
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text

        if status == 401:
            raise JumboAuthError(f"Échec d'authentification (401): {detail}", status_code=401)
        elif status == 400:
            raise JumboBadRequestError(f"Requête invalide (400): {detail}", status_code=400)
        elif status in (500, 503):
            raise JumboServerError(f"Erreur serveur ({status}): {detail}", status_code=status)
        else:
            raise JumboAPIError(f"Erreur HTTP {status}: {detail}", status_code=status)

    def check_health(self) -> Dict[str, str]:
        """Vérifie la santé de l'API et la connexion à la base."""
        url = f"{self.base_url}/api/v1/health"
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url, headers=self._get_headers())
            self._handle_response_error(resp)
            return resp.json()

    def get_brands(self) -> BrandsResponse:
        """Récupère la liste des marques et leur répartition par gamme."""
        url = f"{self.base_url}/api/v1/brands"
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url, headers=self._get_headers())
            self._handle_response_error(resp)
            return BrandsResponse.model_validate(resp.json())

    def search_tires(
        self,
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
    ) -> TireSearchResponse:
        """Recherche dans le catalogue de pneus et renvoie le stock en temps réel."""
        url = f"{self.base_url}/api/v1/tire-search"
        params: Dict[str, Any] = {"limit": limit, "in_stock_only": in_stock_only}

        if width is not None:
            params["width"] = width
        if aspect is not None:
            params["aspect"] = aspect
        if diameter is not None:
            params["diameter"] = diameter
        if brand:
            params["brand"] = brand
        if q:
            params["q"] = q
        if season:
            params["season"] = season
        if runflat is not None:
            params["runflat"] = runflat
        if tier:
            params["tier"] = tier
        if ean:
            params["ean"] = ean

        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url, params=params, headers=self._get_headers())
            self._handle_response_error(resp)
            return TireSearchResponse.model_validate(resp.json())
