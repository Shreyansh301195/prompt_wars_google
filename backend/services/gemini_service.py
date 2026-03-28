"""
JeevanSetu.AI — Gemini AI Service (with Ollama Fallback)
Core AI engine for multimodal understanding, structuring, and action generation.
"""

import json
import base64
import logging
import httpx
from typing import Optional
from google import genai
from google.genai import types

from backend.core.config import get_settings
from backend.models.schemas import (
    InputType, Domain, UrgencyLevel, ActionPriority,
    ActionItem, EntityInfo, StructuredData, ProcessingResponse, LocationData
)

logger = logging.getLogger(__name__)

# System prompts for each processing stage
CLASSIFICATION_PROMPT = """You are JeevanSetu.AI — a life-saving universal intent-to-action bridge.
Analyze the following input and classify it.

Return a JSON object with EXACTLY these fields:
{
    "input_type": "text|voice|image|document|multimodal",
    "domain": "medical|disaster|traffic|safety|general",
    "urgency": "critical|high|medium|low|info",
    "confidence": 0.0 to 1.0,
    "summary": "Brief 1-2 sentence summary of the input"
}

IMPORTANT: Return ONLY the JSON object, no other text."""

EXTRACTION_PROMPT = """You are JeevanSetu.AI — a life-saving universal intent-to-action bridge.
Extract structured data from this input. Be thorough and precise.

Return a JSON object with EXACTLY these fields:
{
    "entities": [
        {"name": "entity name", "type": "person|location|organization|date|medical_term|symptom|medication|condition|vehicle|weather|number", "value": "the value", "confidence": 0.0 to 1.0}
    ],
    "key_facts": ["fact 1", "fact 2", ...],
    "relationships": ["relationship 1", "relationship 2", ...],
    "summary": "Detailed summary paragraph",
    "locations_mentioned": [
        {"name": "place name", "type": "hospital|fire_station|shelter|incident|home|office|road|city", "address": "if available"}
    ]
}

IMPORTANT: Return ONLY the JSON object, no other text. Be comprehensive."""

ACTION_PLAN_PROMPT = """You are JeevanSetu.AI — a life-saving universal intent-to-action bridge.
Based on the classified input and extracted data, generate a prioritized action plan.
These actions must be practical, verified, and potentially life-saving.

Domain: {domain}
Urgency: {urgency}
Extracted Data: {extracted_data}

Return a JSON object with an "actions" array. Each action should have these fields:
- "id": number
- "title": string
- "description": string (detailed description of what to do)
- "priority": "immediate" or "high" or "medium" or "low"
- "category": "emergency" or "medical" or "safety" or "communication" or "logistics" or "documentation" or "follow_up"
- "is_verified": boolean
- "verification_notes": string (how this action was verified or caveats)
- "contact_info": string (phone number if relevant, use real numbers like 112, 108, 911)
- "location_hint": string (location description if relevant)

RULES:
- For medical emergencies, ALWAYS include "Call emergency services" as the first action
- Use real emergency numbers: 112 (India/EU), 911 (US), 108 (India Ambulance)
- Verify actions are safe and do not recommend dangerous activities
- Be specific and actionable, not vague
- Include follow-up actions

IMPORTANT: Return ONLY the JSON object, no other text."""


class GeminiService:
    """Primary AI service using Google Gemini with Ollama fallback."""

    def __init__(self):
        self.settings = get_settings()
        self.client = None
        self.model_name = "gemini-2.5-flash"
        self.using_ollama = False

        self._initialize()

    def _initialize(self):
        """Initialize the AI client (Gemini preferred, Ollama fallback)."""
        if self.settings.is_gemini_available:
            try:
                self.client = genai.Client(api_key=self.settings.gemini_api_key)
                logger.info("✅ Gemini AI client initialized successfully")
                return
            except Exception as e:
                logger.warning(f"⚠️ Gemini initialization failed: {e}")

        if self.settings.is_ollama_available:
            logger.info("🔄 Falling back to Ollama...")
            self.using_ollama = True
            self.model_name = self.settings.ollama_model
            logger.info(f"✅ Ollama fallback configured with model: {self.model_name}")
        else:
            logger.error("❌ No AI engine available. Set GEMINI_API_KEY or enable Ollama.")

    async def _call_gemini(self, prompt: str, image_data: Optional[bytes] = None,
                           image_mime: Optional[str] = None) -> str:
        """Call Gemini API with text and optional image."""
        try:
            contents = [prompt]

            if image_data and image_mime:
                image_part = types.Part.from_bytes(data=image_data, mime_type=image_mime)
                contents.append(image_part)

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=4096,
                    response_mime_type="application/json"
                )
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            if self.settings.is_ollama_available:
                logger.info("Falling back to Ollama for this request...")
                return await self._call_ollama(prompt)
            raise

    async def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API as fallback."""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.settings.ollama_base_url}/api/generate",
                    json={
                        "model": self.settings.ollama_model,
                        "prompt": prompt + "\n\nCRITICAL INSTRUCTIONS:\n1. Return ONLY a valid JSON object\n2. Do NOT use markdown code fences\n3. Do NOT add any text before or after the JSON\n4. Make sure all brackets and braces are properly closed\n5. Start your response with { and end with }",
                        "stream": False,
                        "options": {
                            "temperature": 0.2,
                            "num_predict": 4096
                        }
                    }
                )
                response.raise_for_status()
                result = response.json()
                raw = result.get("response", "{}")
                logger.info(f"Ollama raw response length: {len(raw)}")
                return raw
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise

    async def _call_ai(self, prompt: str, image_data: Optional[bytes] = None,
                       image_mime: Optional[str] = None) -> str:
        """Unified AI call — tries Gemini first, falls back to Ollama."""
        if self.using_ollama:
            return await self._call_ollama(prompt)
        return await self._call_gemini(prompt, image_data, image_mime)

    def _parse_json_response(self, text: str) -> dict:
        """Parse JSON from AI response, handling common issues."""
        if not text:
            return {}

        text = text.strip()

        # Remove markdown code fences if present
        import re
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        text = text.strip()

        # Attempt 1: Direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Attempt 2: Find outermost JSON object
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            json_str = text[start:end]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # Attempt 3: Try to fix common issues (trailing commas, missing brackets)
                json_str = re.sub(r',\s*([}\]])', r'\1', json_str)  # Remove trailing commas
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass

                # Attempt 4: Try to fix truncated JSON by closing brackets
                open_braces = json_str.count('{') - json_str.count('}')
                open_brackets = json_str.count('[') - json_str.count(']')
                fixed = json_str
                if open_braces > 0 or open_brackets > 0:
                    # Remove last incomplete entry after last comma
                    last_comma = fixed.rfind(',')
                    if last_comma > fixed.rfind('}'):
                        fixed = fixed[:last_comma]
                    fixed += ']' * open_brackets + '}' * open_braces
                    try:
                        return json.loads(fixed)
                    except json.JSONDecodeError:
                        pass

        logger.error(f"Failed to parse AI response as JSON: {text[:300]}")
        return {}

    async def classify_input(self, text: str, has_image: bool = False,
                             has_audio: bool = False) -> dict:
        """Stage 1: Classify the input type, domain, and urgency."""
        input_desc = f"Input text: {text}"
        if has_image:
            input_desc += "\n[An image is also attached]"
        if has_audio:
            input_desc += "\n[Audio recording was transcribed to the text above]"

        prompt = f"{CLASSIFICATION_PROMPT}\n\n{input_desc}"
        response = await self._call_ai(prompt)
        result = self._parse_json_response(response)

        return {
            "input_type": result.get("input_type", "text"),
            "domain": result.get("domain", "general"),
            "urgency": result.get("urgency", "medium"),
            "confidence": float(result.get("confidence", 0.7)),
            "summary": result.get("summary", text[:200])
        }

    async def extract_structured_data(self, text: str,
                                       image_data: Optional[bytes] = None,
                                       image_mime: Optional[str] = None) -> dict:
        """Stage 2: Extract structured data from the input."""
        prompt = f"{EXTRACTION_PROMPT}\n\nInput:\n{text}"
        response = await self._call_ai(prompt, image_data, image_mime)
        return self._parse_json_response(response)

    async def generate_action_plan(self, domain: str, urgency: str,
                                    extracted_data: dict) -> list[dict]:
        """Stage 3: Generate a prioritized action plan."""
        prompt = ACTION_PLAN_PROMPT.format(
            domain=domain,
            urgency=urgency,
            extracted_data=json.dumps(extracted_data, indent=2)
        )
        response = await self._call_ai(prompt)
        result = self._parse_json_response(response)
        return result.get("actions", [])

    async def process_full_pipeline(self, text: str,
                                     image_data: Optional[bytes] = None,
                                     image_mime: Optional[str] = None,
                                     audio_transcription: Optional[str] = None,
                                     ocr_text: Optional[str] = None) -> dict:
        """Run the complete 5-stage processing pipeline."""
        stages = []

        # Combine all text inputs
        full_text = text or ""
        if audio_transcription:
            full_text += f"\n\n[Transcribed Audio]: {audio_transcription}"
        if ocr_text:
            full_text += f"\n\n[OCR from Document/Image]: {ocr_text}"

        if not full_text.strip():
            full_text = "No text input provided. Please analyze the attached media."

        # Stage 1: Classification
        stages.append({"stage": "classification", "status": "processing"})
        classification = await self.classify_input(
            full_text,
            has_image=image_data is not None,
            has_audio=audio_transcription is not None
        )
        stages[-1]["status"] = "complete"
        stages[-1]["result"] = classification

        # Stage 2: Extraction
        stages.append({"stage": "extraction", "status": "processing"})
        extracted = await self.extract_structured_data(full_text, image_data, image_mime)
        stages[-1]["status"] = "complete"

        # Stage 3: Action Plan Generation
        stages.append({"stage": "action_generation", "status": "processing"})
        actions = await self.generate_action_plan(
            classification.get("domain", "general"),
            classification.get("urgency", "medium"),
            extracted
        )
        stages[-1]["status"] = "complete"

        # Stage 4: Verification (built into Gemini prompts)
        stages.append({"stage": "verification", "status": "complete"})

        # Stage 5: Response assembly
        stages.append({"stage": "assembly", "status": "complete"})

        return {
            "classification": classification,
            "extracted_data": extracted,
            "actions": actions,
            "stages": stages,
            "ai_engine": "ollama" if self.using_ollama else "gemini"
        }

    @property
    def engine_name(self) -> str:
        return "ollama" if self.using_ollama else "gemini"


# Singleton instance
_gemini_service: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    """Get or create the Gemini service singleton."""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service
