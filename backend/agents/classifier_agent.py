"""
JeevanSetu.AI — Agent 1: ClassifierAgent
Uses Google ADK LlmAgent to classify input type, domain, and urgency.

Inputs (via ADK session state):
  - state["input_text"]: combined text from all modalities
  - state["has_image"]: bool
  - state["has_audio"]: bool

Outputs (written to ADK session state):
  - state["classification"]: dict with input_type, domain, urgency, confidence, summary
"""

import json
import logging
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext

logger = logging.getLogger(__name__)

CLASSIFIER_INSTRUCTION = """You are JeevanSetu.AI — Agent 1: Input Classifier.
Your ONLY job is to analyze the input and classify it precisely.

You MUST return a single JSON object with EXACTLY these fields:
{
    "input_type": "text" | "voice" | "image" | "document" | "multimodal",
    "domain": "medical" | "disaster" | "traffic" | "safety" | "general",
    "urgency": "critical" | "high" | "medium" | "low" | "info",
    "confidence": <float 0.0 to 1.0>,
    "summary": "<1-2 sentence summary of the input situation>"
}

Classification rules:
- "medical": any health, injury, medication, symptom, hospital content
- "disaster": floods, earthquakes, fires, cyclones, natural emergencies
- "traffic": accidents, congestion, road issues, vehicle emergencies
- "safety": crime, violence, threats, personal safety concerns
- "general": anything that doesn't fit the above

Urgency rules:
- "critical": life-threatening, active emergency, call 112 NOW
- "high": serious, needs action within the hour
- "medium": important but not immediately dangerous
- "low": informational, planning, or non-urgent
- "info": purely informational, no action needed

IMPORTANT: Return ONLY the JSON object. No markdown, no explanation, no extra text."""


def create_classifier_agent(model_name: str = "gemini-2.5-flash") -> LlmAgent:
    """
    Create the ClassifierAgent — Stage 1 of the JeevanSetu pipeline.

    Uses ADK's LlmAgent with a targeted classification instruction.
    Reads `input_text`, `has_image`, `has_audio` from session state.
    Writes `classification` dict back to session state via after_agent_callback.
    """

    def after_classifier_callback(callback_context: CallbackContext) -> None:
        """Extract classification JSON from agent response and store in state."""
        agent_output = callback_context.state.get("_classifier_raw", "")

        # Try to parse JSON from the agent's last message
        try:
            import re
            # Strip markdown fences if any
            text = str(agent_output).strip()
            text = re.sub(r'^```(?:json)?\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            text = text.strip()

            # Find outermost JSON object
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                result = json.loads(text[start:end])
            else:
                result = json.loads(text)

            # Validate and normalize
            callback_context.state["classification"] = {
                "input_type": result.get("input_type", "text"),
                "domain": result.get("domain", "general"),
                "urgency": result.get("urgency", "medium"),
                "confidence": float(result.get("confidence", 0.7)),
                "summary": result.get("summary", "")
            }
            logger.info(f"✅ ClassifierAgent: domain={result.get('domain')}, urgency={result.get('urgency')}")
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning(f"⚠️ ClassifierAgent JSON parse failed: {e}. Using defaults.")
            callback_context.state["classification"] = {
                "input_type": "text",
                "domain": "general",
                "urgency": "medium",
                "confidence": 0.5,
                "summary": "Unable to classify input."
            }

    agent = LlmAgent(
        name="ClassifierAgent",
        model=model_name,
        instruction=CLASSIFIER_INSTRUCTION,
        description=(
            "Stage 1 of JeevanSetu pipeline. Classifies the input modality (text/voice/image/document), "
            "emergency domain (medical/disaster/traffic/safety/general), and urgency level "
            "(critical/high/medium/low/info) with a confidence score."
        ),
        after_agent_callback=after_classifier_callback,
        output_key="_classifier_raw",
    )

    return agent
