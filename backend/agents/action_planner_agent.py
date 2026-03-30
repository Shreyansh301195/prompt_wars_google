"""
JeevanSetu.AI — Agent 3: ActionPlannerAgent
Uses Google ADK LlmAgent to generate a verified, prioritized action plan
based on the classified input and extracted structured data.

Inputs (via ADK session state):
  - state["classification"]:   output from ClassifierAgent
  - state["extracted_data"]:   output from ExtractorAgent
  - state["input_text"]:       original combined text

Outputs (written to ADK session state):
  - state["actions"]: list of action dicts
"""

import json
import logging
import re
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext

logger = logging.getLogger(__name__)

ACTION_PLANNER_INSTRUCTION = """You are JeevanSetu.AI — Agent 3: Action Planner.
Your ONLY job is to create a VERIFIED, PRIORITIZED action plan that could save lives.

You will receive:
- Classification: domain, urgency level
- Extracted Data: entities, facts, locations, relationships
- Original input text

You MUST return a single JSON object with an "actions" array:
{
    "actions": [
        {
            "id": <integer starting at 1>,
            "title": "<short action title>",
            "description": "<detailed, specific description of exactly what to do>",
            "priority": "immediate" | "high" | "medium" | "low",
            "category": "emergency" | "medical" | "safety" | "communication" | "logistics" | "documentation" | "follow_up",
            "is_verified": <true | false>,
            "verification_notes": "<how this was verified, or caveats / disclaimers>",
            "contact_info": "<phone number or contact details if relevant, else empty string>",
            "location_hint": "<relevant location description, else empty string>"
        }
    ]
}

CRITICAL RULES — Follow these without exception:
1. For ALL medical emergencies → First action MUST be "Call emergency services" (112 in India/EU, 911 in US, 108 for India Ambulance)
2. For disasters → Include evacuation routes and shelter locations if known
3. For traffic accidents → Include police (100 in India), ambulance (108), and NHAI helpline
4. For safety threats → Include police contact and safe zone guidance
5. Use REAL emergency numbers — never make up contacts
6. Mark life-safety actions as priority "immediate"
7. Include at least one "follow_up" action (e.g., document incident, contact insurance, follow-up with doctor)
8. Minimum 3 actions, maximum 10 actions
9. is_verified = true ONLY if the action is universally safe and validated guidance
10. Be SPECIFIC — never write vague platitudes like "seek help" — say WHO, WHERE, HOW

Emergency contacts reference:
- India: Emergency 112, Ambulance 108, Police 100, Fire 101, Women Helpline 1091
- US: Emergency 911
- EU: Emergency 112
- NHAI (Road): 1033
- Disaster Management India: 1070
- National Poison Control: 1800-116-117

IMPORTANT: Return ONLY the JSON object. No markdown, no explanation."""


def create_action_planner_agent(model_name: str = "gemini-2.5-flash") -> LlmAgent:
    """
    Create the ActionPlannerAgent — Stage 3 (final) of the JeevanSetu pipeline.

    Reads `classification` + `extracted_data` + `input_text` from session state.
    Writes `actions` list to session state via after_agent_callback.
    """

    def after_action_planner_callback(callback_context: CallbackContext) -> None:
        """Extract action plan JSON from agent response and store in state."""
        agent_output = callback_context.state.get("_action_planner_raw", "")

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

                # Try parsing; if fails, attempt to fix truncated JSON
                try:
                    result = json.loads(json_str)
                except json.JSONDecodeError:
                    open_braces = json_str.count('{') - json_str.count('}')
                    open_brackets = json_str.count('[') - json_str.count(']')
                    fixed = json_str
                    if open_braces > 0 or open_brackets > 0:
                        last_comma = fixed.rfind(',')
                        if last_comma > fixed.rfind('}'):
                            fixed = fixed[:last_comma]
                        fixed += ']' * max(0, open_brackets) + '}' * max(0, open_braces)
                        result = json.loads(fixed)
                    else:
                        raise
            else:
                result = {"actions": []}

            actions = result.get("actions", [])
            callback_context.state["actions"] = actions
            logger.info(f"✅ ActionPlannerAgent: {len(actions)} actions generated")
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning(f"⚠️ ActionPlannerAgent JSON parse failed: {e}. Providing default action.")
            callback_context.state["actions"] = [
                {
                    "id": 1,
                    "title": "Contact Emergency Services",
                    "description": "If this is an emergency, call 112 immediately (India/EU) or 911 (US).",
                    "priority": "immediate",
                    "category": "emergency",
                    "is_verified": True,
                    "verification_notes": "Universal emergency number, always valid.",
                    "contact_info": "112",
                    "location_hint": ""
                }
            ]

    agent = LlmAgent(
        name="ActionPlannerAgent",
        model=model_name,
        instruction=ACTION_PLANNER_INSTRUCTION,
        description=(
            "Stage 3 of JeevanSetu pipeline. Generates a verified, prioritized action plan "
            "with specific steps, real emergency contact numbers, and safety guidelines. "
            "All actions are categorized by urgency (immediate/high/medium/low) and type "
            "(emergency, medical, safety, communication, logistics, documentation, follow_up)."
        ),
        after_agent_callback=after_action_planner_callback,
        output_key="_action_planner_raw",
    )

    return agent
