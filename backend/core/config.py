"""
JeevanSetu.AI — Core Configuration
Manages environment variables, API keys, and service initialization.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_name: str = "JeevanSetu.AI"
    app_version: str = "1.0.0"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "info"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Gemini
    gemini_api_key: Optional[str] = None

    # Ollama Fallback
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    use_ollama_fallback: bool = True

    # Google Cloud
    google_cloud_project_id: Optional[str] = None
    google_application_credentials: Optional[str] = None

    # Google Maps
    google_maps_api_key: Optional[str] = None

    # Rate Limiting
    rate_limit_per_minute: int = 30

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_gemini_available(self) -> bool:
        return self.gemini_api_key is not None and len(self.gemini_api_key) > 5

    @property
    def is_ollama_available(self) -> bool:
        return self.use_ollama_fallback

    @property
    def is_maps_available(self) -> bool:
        return self.google_maps_api_key is not None and len(self.google_maps_api_key) > 5



@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
