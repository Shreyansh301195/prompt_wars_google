"""
JeevanSetu.AI — API Routes
REST API endpoints for the processing pipeline.
"""

import uuid
import logging
import base64
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from backend.core.security import (
    sanitize_text_input, validate_file_type,
    ALLOWED_IMAGE_TYPES, ALLOWED_AUDIO_TYPES, ALLOWED_DOCUMENT_TYPES,
    MAX_FILE_SIZE
)
from backend.models.schemas import (
    ProcessingResponse, HealthResponse, TTSRequest,
    InputType, Domain, UrgencyLevel, ActionPriority,
    ActionItem, EntityInfo, StructuredData, LocationData,
    ProcessingHistoryItem
)
from backend.services.gemini_service import get_gemini_service
from backend.services.speech_service import get_speech_service
from backend.services.tts_service import get_tts_service
from backend.services.nlp_service import get_nlp_service
from backend.services.vision_service import get_vision_service
from backend.services.maps_service import get_maps_service

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory history (would use a database in production)
processing_history: list[dict] = []


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with Google services status."""
    gemini = get_gemini_service()
    speech = get_speech_service()
    tts = get_tts_service()
    nlp = get_nlp_service()
    vision = get_vision_service()
    maps = get_maps_service()

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        services={
            "gemini": {
                "available": not gemini.using_ollama,
                "engine": gemini.engine_name,
                "model": gemini.model_name
            },
            "ollama": {
                "available": gemini.using_ollama,
                "model": gemini.model_name if gemini.using_ollama else "N/A"
            },
            "speech_to_text": {"available": speech.available},
            "text_to_speech": {"available": tts.available},
            "natural_language": {"available": nlp.available},
            "vision": {"available": vision.available},
            "maps": {"available": maps.available}
        }
    )


@router.post("/process")
async def process_input(
    text: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None),
    document: Optional[UploadFile] = File(None),
):
    """
    Main processing endpoint.
    Accepts multimodal input (text, image, audio, document) and returns
    structured, verified action plans.
    """
    request_id = str(uuid.uuid4())[:8]
    logger.info(f"[{request_id}] Processing new request")

    try:
        # Sanitize text input
        clean_text = sanitize_text_input(text) if text else ""

        # Process image
        image_data = None
        image_mime = None
        ocr_text = ""

        if image:
            if not validate_file_type(image.filename or "", ALLOWED_IMAGE_TYPES):
                raise HTTPException(400, "Unsupported image type")

            image_data = await image.read()
            if len(image_data) > MAX_FILE_SIZE:
                raise HTTPException(400, "Image too large (max 10MB)")

            image_mime = image.content_type or "image/jpeg"
            logger.info(f"[{request_id}] Image received: {image.filename}")

            # Try OCR with Vision API
            vision_service = get_vision_service()
            if vision_service.available:
                ocr_result = await vision_service.detect_text(image_data)
                ocr_text = ocr_result.get("text", "")
                logger.info(f"[{request_id}] OCR extracted {len(ocr_text)} chars")

        # Process audio
        audio_transcription = ""
        if audio:
            if not validate_file_type(audio.filename or "", ALLOWED_AUDIO_TYPES):
                raise HTTPException(400, "Unsupported audio type")

            audio_data = await audio.read()
            if len(audio_data) > MAX_FILE_SIZE:
                raise HTTPException(400, "Audio too large (max 10MB)")

            logger.info(f"[{request_id}] Audio received: {audio.filename}")

            speech_service = get_speech_service()
            if speech_service.available:
                transcription = await speech_service.transcribe_audio(audio_data)
                audio_transcription = transcription.get("text", "")
                logger.info(f"[{request_id}] Transcribed: {audio_transcription[:100]}")

        # Process document
        if document:
            if not validate_file_type(document.filename or "", ALLOWED_DOCUMENT_TYPES):
                raise HTTPException(400, "Unsupported document type")

            doc_data = await document.read()
            if len(doc_data) > MAX_FILE_SIZE:
                raise HTTPException(400, "Document too large (max 10MB)")

            # For PDFs, try Vision OCR; for text files, read directly
            ext = (document.filename or "").rsplit(".", 1)[-1].lower()
            if ext == "txt":
                clean_text += f"\n\n[Document content]: {doc_data.decode('utf-8', errors='replace')}"
            elif ext == "pdf":
                # Use Vision API for PDF OCR
                vision_service = get_vision_service()
                if vision_service.available:
                    ocr_result = await vision_service.detect_text(doc_data)
                    ocr_text += "\n" + ocr_result.get("text", "")

        if not clean_text and not image_data and not audio_transcription and not ocr_text:
            raise HTTPException(400, "No input provided. Please provide text, image, audio, or document.")

        # Run the full Gemini pipeline
        gemini = get_gemini_service()
        pipeline_result = await gemini.process_full_pipeline(
            text=clean_text,
            image_data=image_data,
            image_mime=image_mime,
            audio_transcription=audio_transcription,
            ocr_text=ocr_text
        )

        # Enhance with NLP entities if available
        nlp_service = get_nlp_service()
        nlp_entities = []
        combined_text = f"{clean_text} {audio_transcription} {ocr_text}".strip()
        if nlp_service.available and combined_text:
            nlp_result = await nlp_service.analyze_entities(combined_text)
            nlp_entities = nlp_result.get("entities", [])

        # Build structured response
        classification = pipeline_result.get("classification", {})
        extracted = pipeline_result.get("extracted_data", {})
        actions_raw = pipeline_result.get("actions", [])

        # Parse entities
        entities = []
        for e in extracted.get("entities", []):
            entities.append(EntityInfo(
                name=e.get("name", ""),
                type=e.get("type", "other"),
                value=e.get("value", e.get("name", "")),
                confidence=float(e.get("confidence", 0.7))
            ))

        # Add NLP entities
        for e in nlp_entities:
            entities.append(EntityInfo(
                name=e.get("name", ""),
                type=e.get("type", "other"),
                value=e.get("name", ""),
                confidence=float(e.get("salience", 0.5))
            ))

        # Parse actions
        actions = []
        for i, a in enumerate(actions_raw):
            actions.append(ActionItem(
                id=a.get("id", i + 1),
                title=a.get("title", "Action"),
                description=a.get("description", ""),
                priority=ActionPriority(a.get("priority", "medium")),
                category=a.get("category", "general"),
                is_verified=a.get("is_verified", False),
                verification_notes=a.get("verification_notes"),
                contact_info=a.get("contact_info"),
                location=None
            ))

        # Get locations if maps is available
        locations = []
        maps_service = get_maps_service()
        location_mentions = extracted.get("locations_mentioned", [])

        if maps_service.available and location_mentions:
            for loc in location_mentions[:3]:  # Limit geocoding calls
                geo = await maps_service.geocode(loc.get("address", loc.get("name", "")))
                if geo.get("lat", 0) != 0:
                    locations.append(LocationData(
                        name=loc.get("name", "Location"),
                        lat=geo["lat"],
                        lng=geo["lng"],
                        type=loc.get("type", "location"),
                        address=geo.get("formatted_address")
                    ))

                    # Find nearby relevant places
                    domain = classification.get("domain", "general")
                    place_types = {
                        "medical": "hospital",
                        "disaster": "fire_station",
                        "traffic": "police",
                        "safety": "police"
                    }
                    if domain in place_types:
                        nearby = await maps_service.find_nearby(
                            geo["lat"], geo["lng"],
                            place_type=place_types[domain]
                        )
                        for place in nearby[:3]:
                            locations.append(LocationData(
                                name=place["name"],
                                lat=place["lat"],
                                lng=place["lng"],
                                type=place["type"],
                                address=place.get("address")
                            ))

        # Build final response
        response = ProcessingResponse(
            request_id=request_id,
            input_type=InputType(classification.get("input_type", "text")),
            domain=Domain(classification.get("domain", "general")),
            urgency=UrgencyLevel(classification.get("urgency", "medium")),
            confidence=classification.get("confidence", 0.7),
            structured_data=StructuredData(
                entities=entities,
                key_facts=extracted.get("key_facts", []),
                relationships=extracted.get("relationships", []),
                summary=extracted.get("summary", ""),
                raw_text=combined_text[:500] if combined_text else None
            ),
            action_plan=actions,
            locations=locations,
            ai_engine_used=pipeline_result.get("ai_engine", "gemini"),
            processing_stages=pipeline_result.get("stages", []),
            audio_available=get_tts_service().available,
            input_summary=classification.get("summary", clean_text[:200])
        )

        # Save to history
        processing_history.insert(0, {
            "request_id": request_id,
            "timestamp": response.timestamp,
            "domain": response.domain.value,
            "urgency": response.urgency.value,
            "input_summary": response.input_summary[:100],
            "input_type": response.input_type.value
        })

        # Keep only last 50 entries
        if len(processing_history) > 50:
            processing_history.pop()

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Processing error: {e}", exc_info=True)
        raise HTTPException(500, f"Processing failed: {str(e)}")


@router.post("/voice")
async def process_voice(audio: UploadFile = File(...)):
    """
    Voice-specific endpoint.
    Accepts audio file and returns transcription along with processing.
    """
    if not validate_file_type(audio.filename or "", ALLOWED_AUDIO_TYPES):
        raise HTTPException(400, "Unsupported audio format")

    audio_data = await audio.read()
    if len(audio_data) > MAX_FILE_SIZE:
        raise HTTPException(400, "Audio too large (max 10MB)")

    speech_service = get_speech_service()

    if speech_service.available:
        result = await speech_service.transcribe_audio(audio_data)
        transcription = result.get("text", "")

        if transcription:
            # Process the transcription through the main pipeline
            gemini = get_gemini_service()
            pipeline_result = await gemini.process_full_pipeline(
                text=transcription,
                audio_transcription=transcription
            )
            return {
                "transcription": result,
                "pipeline_result": pipeline_result
            }

        return {"transcription": result, "pipeline_result": None}

    return {
        "transcription": {"text": "", "error": "Speech service not available"},
        "pipeline_result": None,
        "hint": "Use browser Web Speech API for transcription and send text to /api/process"
    }


@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    """
    Text-to-Speech endpoint for accessibility.
    Converts action plan text to audio.
    """
    if not request.text:
        raise HTTPException(400, "No text provided")

    tts_service = get_tts_service()
    result = await tts_service.synthesize(
        text=request.text,
        language=request.language,
        voice_type=request.voice_type
    )

    return result


@router.get("/history")
async def get_history():
    """Get processing history."""
    return {
        "history": processing_history,
        "total": len(processing_history)
    }


@router.get("/services-status")
async def services_status():
    """Get detailed status of all Google services."""
    return {
        "gemini": {
            "name": "Gemini 2.5 Flash",
            "available": not get_gemini_service().using_ollama,
            "description": "Core AI engine for multimodal understanding"
        },
        "ollama": {
            "name": f"Ollama ({get_gemini_service().model_name})",
            "available": get_gemini_service().using_ollama,
            "description": "Open-source AI fallback engine"
        },
        "speech_to_text": {
            "name": "Cloud Speech-to-Text",
            "available": get_speech_service().available,
            "description": "Voice input transcription"
        },
        "text_to_speech": {
            "name": "Cloud Text-to-Speech",
            "available": get_tts_service().available,
            "description": "Accessible audio output"
        },
        "natural_language": {
            "name": "Cloud Natural Language",
            "available": get_nlp_service().available,
            "description": "Entity & sentiment analysis"
        },
        "vision": {
            "name": "Cloud Vision API",
            "available": get_vision_service().available,
            "description": "OCR & image analysis"
        },
        "maps": {
            "name": "Google Maps Platform",
            "available": get_maps_service().available,
            "description": "Location & navigation services"
        }
    }
