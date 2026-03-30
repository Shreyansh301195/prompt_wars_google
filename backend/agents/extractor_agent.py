"""
JeevanSetu.AI — Agent 2: ExtractorAgent
Uses Google ADK LlmAgent to extract structured entities, locations, key facts,
and relationships from the classified input.

Inputs (via ADK session state):
  - state["input_text"]:    combined text
  - state["classification"]: output from ClassifierAgent

Outputs (written to ADK session state):
  - state["extracted_data"]: dict with entities, key_facts, relationships,
                              summary, locations_mentioned
"""

import json
import logging
import re
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext

logger = logging.getLogger(__name__)

EXTRACTOR_INSTRUCTION = """You are JeevanSetu.AI — Agent 2: Data Extractor.
Your ONLY job is to extract every piece of structured information from the input.

You will receive:
- The raw input text
- Classification context (domain, urgency) from Agent 1

You MUST return a single JSON object with EXACTLY these fields:
{
    "entities": [
        {
            "name": "<entity name>",
            "type": "person" | "location" | "organization" | "date" | "medical_term" | "symptom" | "medication" | "condition" | "vehicle" | "weather" | "number" | "other",
            "value": "<the extracted value>",
            "confidence": <float 0.0 to 1.0>
        }
    ],
    "key_facts": ["<fact 1>", "<fact 2>", ...],
    "relationships": ["<relationship description>", ...],
    "summary": "<detailed paragraph summarizing all extracted information>",
    "locations_mentioned": [
        {
            "name": "<place name>",
            "type": "hospital" | "fire_station" | "shelter" | "incident" | "home" | "office" | "road" | "city" | "other",
            "address": "<full address if available, else empty string>"
        }
    ]
}

Extraction rules:
- Be EXHAUSTIVE — extract every entity, name, number, date, location you can find
- For medical domain: extract ALL symptoms, medications, dosages, conditions, allergies
- For disaster domain: extract ALL locations, affected areas, infrastructure damage
- For traffic domain: extract vehicle details, road names, incident locations, severity
- key_facts should be self-contained, actionable sentences
- relationships describe how entities relate to each other
- locations_mentioned is CRITICAL — extract every place that could be geocoded

IMPORTANT: Return ONLY the JSON object. No markdown, no explanation."""


def create_extractor_agent(model_name: str = "gemini-2.5-flash") -> LlmAgent:
    """
    Create the ExtractorAgent — Stage 2 of the JeevanSetu pipeline.

    Reads `input_text` + `classification` from session state.
    Writes `extracted_data` dict to session state via after_agent_callback.
    """

    def after_extractor_callback(callback_context: CallbackContext) -> None:
        """Extract structured data JSON from agent response and store in state."""
        agent_output = callback_context.state.get("_extractor_raw", "")

        try:
            text = str(agent_output).strip()
            text = re.sub(r'^```(?:json)?\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            text = text.strip()

            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                json_str = text[start:end]
                # Fix trailing commas
                json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
                result = json.loads(json_str)
            else:
                result = {}

            callback_context.state["extracted_data"] = {
                "entities": result.get("entities", []),
                "key_facts": result.get("key_facts", []),
                "relationships": result.get("relationships", []),
                "summary": result.get("summary", ""),
                "locations_mentioned": result.get("locations_mentioned", [])
            }
            entity_count = len(result.get("entities", []))
            logger.info(f"✅ ExtractorAgent: {entity_count} entities, "
                        f"{len(result.get('locations_mentioned', []))} locations")
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning(f"⚠️ ExtractorAgent JSON parse failed: {e}. Using empty defaults.")
            callback_context.state["extracted_data"] = {
                "entities": [],
                "key_facts": [],
                "relationships": [],
                "summary": "Extraction failed. Please see raw input.",
                "locations_mentioned": []
            }

    agent = LlmAgent(
        name="ExtractorAgent",
        model=model_name,
        instruction=EXTRACTOR_INSTRUCTION,
        description=(
            "Stage 2 of JeevanSetu pipeline. Extracts structured information from unstructured input: "
            "named entities (people, places, organizations, medical terms), key facts, relationships "
            "between entities, and geographic locations for map display."
        ),
        after_agent_callback=after_extractor_callback,
        output_key="_extractor_raw",
    )

    return agent
