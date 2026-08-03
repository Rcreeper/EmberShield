"""
EmberShield - Sentinel Agent

Supports two modes:

1. DEMO MODE
   No Anthropic API key required.
   Returns realistic AI results for hackathon demos.

2. LIVE MODE
   Automatically uses Claude Vision when
   ANTHROPIC_API_KEY is present.
"""

import os
import io
import json
import base64
import random

from PIL import Image
from dotenv import load_dotenv

from config import CLAUDE_MODEL, MAX_IMAGE_WIDTH

load_dotenv()

API_KEY = os.getenv("ANTHROPIC_API_KEY")

USE_CLAUDE = API_KEY not in (None, "", "YOUR_API_KEY")


# ==========================================================
# Optional Claude Import
# ==========================================================

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
    those before parsing so a fenced reply doesn't get treated
    as a parse failure.
    """

    cleaned = text.strip()

    if cleaned.startswith("```"):

        cleaned = cleaned.strip("`")

        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]

        cleaned = cleaned.strip()

    return json.loads(cleaned)


# ==========================================================
# Image Preparation
# ==========================================================

def prepare_image(image_path: str):

    image = Image.open(image_path)

    if image.width > MAX_IMAGE_WIDTH:

        ratio = MAX_IMAGE_WIDTH / image.width

        image = image.resize(

            (
                MAX_IMAGE_WIDTH,
                int(image.height * ratio)
            )

        )

    buffer = io.BytesIO()

    image.save(buffer, format="JPEG", quality=90)

    return base64.b64encode(
        buffer.getvalue()
    ).decode()


# ==========================================================
# Demo Mode
# ==========================================================

def demo_detection():

    fire = random.choice([True, True, True, False])

    if fire:

        return {

            "fire_detected": True,

            "confidence": random.randint(84, 98),

            "description":
                random.choice([
                    "Visible flames detected with dense smoke.",
                    "Large smoke plume indicates an active wildfire.",
                    "Fire detected near dense vegetation.",
                    "Smoke and flames visible in the image."
                ])

        }

    return {

        "fire_detected": False,

        "confidence": random.randint(75, 92),

        "description":
            "No obvious fire detected."

    }


# ==========================================================
# Main Detection
# ==========================================================

def detect_fire(image_path: str):

    if not USE_CLAUDE:

        print("\n===== DEMO MODE =====")
        print("Claude API key not found.")
        print("Returning simulated AI response.\n")

        return demo_detection()

    image_data = prepare_image(image_path)

    prompt = """
You are an expert wildfire detection AI.

Return ONLY JSON.

{
 "fire_detected": true,
 "confidence": 97,
 "description":"..."
}
"""

    response = client.messages.create(

        model=CLAUDE_MODEL,

        max_tokens=300,

        messages=[

            {

                "role": "user",

                "content": [

                    {

                        "type": "image",

                        "source": {

                            "type": "base64",

                            "media_type": "image/jpeg",

                            "data": image_data

                        }

                    },

                    {

                        "type": "text",

                        "text": prompt

                    }

                ]

            }

        ]

    )

    text = response.content[0].text

    try:

        return _extract_json(text)

    except Exception:

        return {

            "fire_detected": False,

            "confidence": 0,

            "description": text

        }


# ==========================================================
# Test
# ==========================================================

if __name__ == "__main__":

    print(

        detect_fire(
            "../uploads/test.jpg"
        )

    )