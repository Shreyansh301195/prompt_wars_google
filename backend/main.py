"""
JeevanSetu.AI — FastAPI Application
Universal bridge between human intent and complex systems.
Powered by Google Gemini with Ollama fallback.
"""

import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load .env from project root BEFORE anything else
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)
print(f"✅ Loaded .env from: {env_path}")
print(f"   GEMINI_API_KEY set: {bool(os.getenv('GEMINI_API_KEY'))}")
print(f"   Key length: {len(os.getenv('GEMINI_API_KEY', ''))}")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import get_settings
from backend.core.security import RateLimitMiddleware
from backend.api.routes import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    settings = get_settings()
    logger.info("=" * 60)
    logger.info("🌉 JeevanSetu.AI — Universal Intent-to-Action Bridge")
    logger.info(f"   Version: {settings.app_version}")
    logger.info(f"   Gemini Available: {settings.is_gemini_available}")
    logger.info(f"   Ollama Fallback: {settings.use_ollama_fallback}")
    logger.info(f"   Maps Available: {settings.is_maps_available}")
    logger.info("=" * 60)

    # Pre-initialize services
    from backend.services.gemini_service import get_gemini_service
    from backend.services.speech_service import get_speech_service
    from backend.services.tts_service import get_tts_service
    from backend.services.nlp_service import get_nlp_service
    from backend.services.vision_service import get_vision_service
    from backend.services.maps_service import get_maps_service

    get_gemini_service()
    get_speech_service()
    get_tts_service()
    get_nlp_service()
    get_vision_service()
    get_maps_service()

    logger.info("✅ All services initialized")
    yield
    logger.info("👋 JeevanSetu.AI shutting down")


# Create FastAPI app
app = FastAPI(
    title="JeevanSetu.AI",
    description=(
        "Universal bridge between human intent and complex systems. "
        "Takes unstructured inputs (voice, images, text, documents) and "
        "converts them into structured, verified, life-saving actions. "
        "Powered by Google Gemini with Ollama open-source fallback."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.rate_limit_per_minute)

# Routes
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint — redirect info."""
    return {
        "app": "JeevanSetu.AI",
        "tagline": "Universal Intent-to-Action Bridge",
        "docs": "/docs",
        "api": "/api/health",
        "version": "1.0.0"
    }
