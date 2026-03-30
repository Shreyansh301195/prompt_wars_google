"""
JeevanSetu.AI — ADK Pipeline Orchestrator
Wires ClassifierAgent → ExtractorAgent → ActionPlannerAgent into a
SequentialAgent pipeline using Google ADK.

Usage:
    from backend.agents.pipeline_agent import run_pipeline

    result = await run_pipeline(
        input_text="Patient is having chest pain...",
        has_image=False,
        has_audio=False
    )
    # result = {"classification": {...}, "extracted_data": {...}, "actions": [...], ...}
"""

import logging
import asyncio
from typing import Optional

from google.adk.agents import SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

from backend.agents.classifier_agent import create_classifier_agent
from backend.agents.extractor_agent import create_extractor_agent
from backend.agents.action_planner_agent import create_action_planner_agent

logger = logging.getLogger(__name__)

# ADK App name for session tracking
APP_NAME = "jeevansetu_ai"


def _build_pipeline_prompt(
    input_text: str,
    classification: Optional[dict] = None,
    extracted_data: Optional[dict] = None
) -> str:
    """Build the message sent to each agent in the pipeline."""
    parts = [f"INPUT TEXT:\n{input_text}"]

    if classification:
        import json
        parts.append(f"\nCLASSIFICATION CONTEXT (from Agent 1):\n{json.dumps(classification, indent=2)}")

    if extracted_data:
        import json
        parts.append(f"\nEXTRACTED DATA CONTEXT (from Agent 2):\n{json.dumps(extracted_data, indent=2)}")

    return "\n\n".join(parts)


def get_pipeline_agent(model_name: str = "gemini-2.5-flash") -> SequentialAgent:
    """
    Build the JeevanSetuPipeline as a Google ADK SequentialAgent.

    The pipeline runs three LlmAgents in sequence:
      1. ClassifierAgent  → classifies input type, domain, urgency
      2. ExtractorAgent   → extracts entities, facts, locations
      3. ActionPlannerAgent → generates verified action plan

    Each agent reads from and writes to ADK session state.
    """
    classifier = create_classifier_agent(model_name)
    extractor = create_extractor_agent(model_name)
    action_planner = create_action_planner_agent(model_name)

    pipeline = SequentialAgent(
        name="JeevanSetuPipeline",
        sub_agents=[classifier, extractor, action_planner],
        description=(
            "JeevanSetu.AI multi-agent pipeline. Processes multimodal emergency input through "
            "three specialized stages: (1) ClassifierAgent classifies the input domain and urgency, "
            "(2) ExtractorAgent extracts structured entities and locations, "
            "(3) ActionPlannerAgent generates a verified, prioritized life-saving action plan."
        ),
    )

    return pipeline


async def run_pipeline(
    input_text: str,
    has_image: bool = False,
    has_audio: bool = False,
    model_name: str = "gemini-2.5-flash"
) -> dict:
    """
    Run the full JeevanSetu ADK pipeline for a single request.

    Args:
        input_text:  Combined text from all input modalities
        has_image:   Whether an image was attached
        has_audio:   Whether audio was attached/transcribed
        model_name:  Gemini model to use (default: gemini-2.5-flash)

    Returns:
        dict with keys: classification, extracted_data, actions, stages, ai_engine
    """
    import uuid

    session_id = str(uuid.uuid4())
    user_id = "jeevansetu_user"

    # ADK session service (in-memory, stateless per request)
    session_service = InMemorySessionService()

    # Enrich input text with modality context
    enriched_text = input_text
    if has_image:
        enriched_text += "\n[An image has also been provided with this request]"
    if has_audio:
        enriched_text += "\n[This text was transcribed from an audio recording]"

    # Create session with initial state
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id,
        state={
            "input_text": enriched_text,
            "has_image": has_image,
            "has_audio": has_audio,
            "classification": None,
            "extracted_data": None,
            "actions": None,
            "_classifier_raw": "",
            "_extractor_raw": "",
            "_action_planner_raw": "",
        }
    )

    # Build and run the pipeline
    pipeline = get_pipeline_agent(model_name)

    runner = Runner(
        agent=pipeline,
        app_name=APP_NAME,
        session_service=session_service,
    )

    stages = [
        {"stage": "classification", "status": "processing", "label": "Classifying Input"},
        {"stage": "extraction", "status": "pending", "label": "Extracting Structured Data"},
        {"stage": "action_generation", "status": "pending", "label": "Generating Action Plan"},
        {"stage": "verification", "status": "pending", "label": "Verifying Safety"},
        {"stage": "assembly", "status": "pending", "label": "Assembling Response"},
    ]

    try:
        logger.info(f"🚀 Starting JeevanSetu ADK pipeline | session={session_id}")

        # Send the enriched text to the pipeline
        message = genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=enriched_text)]
        )

        # Run the SequentialAgent pipeline
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=message
        ):
            # Log agent turn completions
            if hasattr(event, 'author') and event.author:
                agent_name = event.author
                if agent_name == "ClassifierAgent":
                    stages[0]["status"] = "complete"
                    stages[1]["status"] = "processing"
                    logger.info("✅ Stage 1/3: ClassifierAgent complete")
                elif agent_name == "ExtractorAgent":
                    stages[1]["status"] = "complete"
                    stages[2]["status"] = "processing"
                    logger.info("✅ Stage 2/3: ExtractorAgent complete")
                elif agent_name == "ActionPlannerAgent":
                    stages[2]["status"] = "complete"
                    stages[3]["status"] = "complete"
                    stages[4]["status"] = "complete"
                    logger.info("✅ Stage 3/3: ActionPlannerAgent complete")

        # Retrieve final state from session
        final_session = await session_service.get_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id
        )
        final_state = final_session.state if final_session else {}

        classification = final_state.get("classification") or {
            "input_type": "text",
            "domain": "general",
            "urgency": "medium",
            "confidence": 0.5,
            "summary": input_text[:200]
        }

        extracted_data = final_state.get("extracted_data") or {
            "entities": [],
            "key_facts": [],
            "relationships": [],
            "summary": "",
            "locations_mentioned": []
        }

        actions = final_state.get("actions") or []

        # Mark all stages complete
        for stage in stages:
            stage["status"] = "complete"

        logger.info(
            f"🎉 Pipeline complete | domain={classification.get('domain')} "
            f"| urgency={classification.get('urgency')} "
            f"| {len(actions)} actions"
        )

        return {
            "classification": classification,
            "extracted_data": extracted_data,
            "actions": actions,
            "stages": stages,
            "ai_engine": "gemini-adk",
        }

    except Exception as e:
        logger.error(f"❌ ADK Pipeline error: {e}", exc_info=True)
        # Mark failed stages
        for stage in stages:
            if stage["status"] in ("processing", "pending"):
                stage["status"] = "failed"
        raise


# Singleton pipeline instance (lazy-initialized per request for statelessness)
_pipeline_instance: Optional[SequentialAgent] = None


def _get_or_create_pipeline(model_name: str = "gemini-2.5-flash") -> SequentialAgent:
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = get_pipeline_agent(model_name)
        logger.info("✅ JeevanSetu ADK Pipeline initialized (ClassifierAgent → ExtractorAgent → ActionPlannerAgent)")
    return _pipeline_instance
