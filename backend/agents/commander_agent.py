"""
EmberShield - Commander Agent

The Commander Agent is the final decision-making layer.

It receives structured outputs from:
    • Sentinel Agent
    • Risk Analyst Agent

and asks Claude to produce an emergency response.

Output:
{
    severity,
    recommended_action,
    alert_message
}
"""

import os
import json

from dotenv import load_dotenv

from config import CLAUDE_MODEL

load_dotenv()

API_KEY = os.getenv("ANTHROPIC_API_KEY")

# NOTE: previously `client = Anthropic(api_key=...)` ran
# unconditionally at import time, which crashes the whole app on
# startup if the key is missing/empty (main.py imports this module
# eagerly). Guarding it the same way sentinel_agent.py does, with a
# heuristic demo mode as the fallback.
USE_CLAUDE = API_KEY not in (None, "", "YOUR_API_KEY")

if USE_CLAUDE:
    from anthropic import Anthropic

    client = Anthropic(api_key=API_KEY)


# ==========================================================
# JSON Parsing Helper
# ==========================================================

def _extract_json(text: str):
    """
    Claude sometimes wraps JSON replies in markdown code fences
    (```json ... ```) even when told to return only JSON. Strip
    those before parsing.
    """

    cleaned = text.strip()

    if cleaned.startswith("```"):

        cleaned = cleaned.strip("`")

        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]

        cleaned = cleaned.strip()

    return json.loads(cleaned)


# ==========================================================
# Demo Mode
# ==========================================================

def demo_commander_analysis(
    sentinel_result: dict,
    risk_result: dict
) -> dict:
    """
    Rule-based emergency response used when no Anthropic API key is
    configured, so the app still functions end-to-end for demos.
    """

    confidence = sentinel_result.get("confidence", 0)
    spread = risk_result.get("spread", {}) or {}
    spread_speed = spread.get("speed_kmh", 0)
    settlement = risk_result.get("nearest_settlement")

    if not sentinel_result.get("fire_detected"):
        severity = "low"
    elif settlement and settlement.get("distance_km", 999) < 5:
        severity = "critical"
    elif spread_speed > 3 or confidence > 90:
        severity = "high"
    elif spread_speed > 1.5:
        severity = "medium"
    else:
        severity = "low"

    actions = {
        "critical": "Deploy fire engines immediately and begin evacuating the nearest settlement.",
        "high": "Dispatch fire crews now and place nearby settlements on evacuation standby.",
        "medium": "Monitor the fire closely and alert local authorities.",
        "low": "Continue routine monitoring; no immediate action required."
    }

    if settlement:
        alert = (
            f"Wildfire detected. {settlement['name']} is "
            f"{settlement['distance_km']} km away in the projected "
            f"spread path — residents should stay alert."
        )
    else:
        alert = "Wildfire activity detected. No settlements currently in the projected spread path."

    return {
        "severity": severity,
        "recommended_action": actions[severity],
        "alert_message": alert
    }


# ==========================================================
# Prompt Builder
# ==========================================================

def build_prompt(
    sentinel_result: dict,
    risk_result: dict
) -> str:
    """
    Creates a structured prompt for Claude.
    """

    return f"""
You are EmberShield Commander AI.

Your job is to assess wildfire severity and generate
an emergency response.

Sentinel Output

{json.dumps(sentinel_result, indent=2)}

Risk Analysis

{json.dumps(risk_result, indent=2)}

----------------------------

Determine:

1. severity
Choose ONLY ONE:

low
medium
high
critical

2. recommended_action

Explain the immediate action emergency responders
should take.

3. alert_message

Write a concise public warning message.

Return ONLY JSON.

Example

{{
    "severity":"high",
    "recommended_action":"Deploy two fire engines and alert nearby authorities.",
    "alert_message":"Wildfire detected. Residents within the projected spread path should prepare to evacuate."
}}
"""


# ==========================================================
# Commander Analysis
# ==========================================================

def commander_analysis(
    sentinel_result: dict,
    risk_result: dict
):
    """
    Generate emergency response recommendations.
    """

    if not USE_CLAUDE:

        print("\n===== DEMO MODE (Commander) =====")
        print("Claude API key not found.")
        print("Returning rule-based emergency response.\n")

        return demo_commander_analysis(
            sentinel_result,
            risk_result
        )

    prompt = build_prompt(
        sentinel_result,
        risk_result
    )

    response = client.messages.create(

        model=CLAUDE_MODEL,

        max_tokens=500,

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    text = response.content[0].text

    try:

        return _extract_json(text)

    except Exception:

        return {

            "severity": "unknown",

            "recommended_action":
                "Unable to determine action.",

            "alert_message": text
        }


# ==========================================================
# Standalone Test
# ==========================================================

if __name__ == "__main__":

    sentinel = {

        "fire_detected": True,

        "confidence": 96,

        "description":
            "Visible flames with dense smoke."
    }

    risk = {

        "weather": {

            "temperature": 31,

            "humidity": 28,

            "wind_speed": 18,

            "wind_direction": 270
        },

        "spread": {

            "direction": 90,

            "speed_kmh": 4.1
        },

        "nearest_settlement": {

            "name": "Example Village",

            "distance_km": 5.3,

            "eta_hours": 1.29
        }
    }

    result = commander_analysis(
        sentinel,
        risk
    )

    from pprint import pprint

    pprint(result)