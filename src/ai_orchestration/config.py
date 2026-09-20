"""Gestion de la configuration et des variables d'environnement."""
import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    jumbo_api_key: str = os.getenv("JUMBO_API_KEY") or os.getenv("API_KEY", "")
    jumbo_base_url: str = os.getenv("JUMBO_BASE_URL", "https://api.jumbopneus.shop")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
