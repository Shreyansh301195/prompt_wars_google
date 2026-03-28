"""
JeevanSetu.AI — Pydantic Models & Schemas
Request/response models for the API.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class InputType(str, Enum):
    TEXT = "text"
    VOICE = "voice"
    IMAGE = "image"
    DOCUMENT = "document"
    MULTIMODAL = "multimodal"


class Domain(str, Enum):
    MEDICAL = "medical"
    DISASTER = "disaster"
    TRAFFIC = "traffic"
    SAFETY = "safety"
    GENERAL = "general"


class UrgencyLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ActionPriority(str, Enum):
    IMMEDIATE = "immediate"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ActionItem(BaseModel):
    """A single actionable item generated from processing."""
    id: int
    title: str
    description: str
    priority: ActionPriority
    category: str
    is_verified: bool = False
    verification_notes: Optional[str] = None
    contact_info: Optional[str] = None
    location: Optional[dict] = None  # {lat, lng, address}


class EntityInfo(BaseModel):
    """An extracted entity from the input."""
    name: str
    type: str  # person, location, organization, date, medical_term, etc.
    value: str
    confidence: float = 0.0


class StructuredData(BaseModel):
    """Structured data extracted from unstructured input."""
    entities: list[EntityInfo] = []
    key_facts: list[str] = []
    relationships: list[str] = []
    summary: str = ""
    raw_text: Optional[str] = None


class LocationData(BaseModel):
    """Location data for map display."""
    name: str
    lat: float
    lng: float
    type: str  # hospital, fire_station, shelter, incident, etc.
    address: Optional[str] = None
    phone: Optional[str] = None
    distance_km: Optional[float] = None


class ProcessingResponse(BaseModel):
    """Full response from the processing pipeline."""
    request_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    status: str = "success"

    # Classification
    input_type: InputType
    domain: Domain
    urgency: UrgencyLevel
    confidence: float

    # Structured output
    structured_data: StructuredData
    action_plan: list[ActionItem] = []
    locations: list[LocationData] = []

    # Metadata
    ai_engine_used: str = "gemini"  # "gemini" or "ollama"
    processing_stages: list[dict] = []
    audio_available: bool = False

    # Original input summary
    input_summary: str = ""


class ProcessingHistoryItem(BaseModel):
    """A historical processing record."""
    request_id: str
    timestamp: str
    domain: Domain
    urgency: UrgencyLevel
    input_summary: str
    input_type: InputType


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "1.0.0"
    services: dict = {}


class TTSRequest(BaseModel):
    """Text-to-Speech request."""
    text: str
    language: str = "en-US"
    voice_type: str = "standard"  # standard, neural
