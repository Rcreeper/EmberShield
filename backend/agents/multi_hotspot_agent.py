"""
EmberShield - Multi Hotspot Agent

Takes the batch of location photos found by
agents/scout_agent.py's find_multi_location_images() -- each already
tied to a known GPS point from the bounding-box grid sample -- and
asks Gemini, in a single combined multimodal call, to assess every
photo for wildfire risk.

This intentionally uses Gemini rather than Claude for this step (per
project direction), so multi-hotspot scoring doesn't touch the
Anthropic API at all. Sentinel/Commander (single-location flow)
still use Claude -- only this combined multi-image step is Gemini.

Because each photo already comes from a known lat/lon (the grid
point scout_agent searched from), there's no need for the old
percentage-position-to-GPS conversion the previous version of this
file did -- Gemini just needs to rate each photo, and the caller
zips the ratings back to the coordinates it already has.
"""

import io
import json
import os

from typing import Dict, List

from dotenv import load_dotenv
from PIL import Image
from google import genai
from google.genai import types

from config import GEMINI_MODEL, MAX_IMAGE_WIDTH

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# NOTE: this file intentionally uses Gemini, not Claude, for the
# combined multi-image analysis below (per project direction).
# Sentinel/Commander (single-location flow) still use Claude --
# only this multi-image step runs on Gemini.


class MultiHotspotAnalysisError(Exception):
    """Raised when the combined Gemini vision call fails or returns something unusable."""
    pass


# ==========================================================
# JSON Parsing Helper
# ==========================================================

def _extract_json(text: str):
    """
    Gemini sometimes wraps JSON replies in markdown code fences
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
# Image Preparation
# ==========================================================

def _prepare_image_bytes(image_path: str) -> bytes:
    """
    Resize the image if necessary (photos scraped from arbitrary
    web pages can be much larger than what we need) and return JPEG
    bytes ready to hand to Gemini.
    """

    image = Image.open(image_path)

    if image.mode != "RGB":
        image = image.convert("RGB")

    if image.width > MAX_IMAGE_WIDTH:

        ratio = MAX_IMAGE_WIDTH / image.width

        new_height = int(image.height * ratio)

        image = image.resize(
            (MAX_IMAGE_WIDTH, new_height)
        )

    buffer = io.BytesIO()

    image.save(
        buffer,
        format="JPEG",
        quality=90
    )

    return buffer.getvalue()


# ==========================================================
# Combined Multi-Image Analysis
# ==========================================================

def analyze_multi_hotspots(candidates: List[Dict]) -> List[Dict]:
    """
    candidates: list of dicts as produced by
    scout_agent.find_multi_location_images(), each with at least
    "filepath", "latitude", "longitude", "source_url".

    Sends all candidate photos to Gemini in a single call and asks
    it to rate each one for wildfire risk.

    Returns a list of hotspot dicts, one per candidate:
        {
            "latitude": float,
            "longitude": float,
            "fire_detected": bool,
            "confidence": float,
            "description": str,
            "source_url": str
        }
    """

    if not candidates:
        return []

    if not GEMINI_API_KEY:

        raise MultiHotspotAnalysisError(
            "GEMINI_API_KEY is missing from your .env file. "
            "Get one at https://aistudio.google.com/apikey"
        )

    client = genai.Client(api_key=GEMINI_API_KEY)

    image_parts = []

    for candidate in candidates:

        image_bytes = _prepare_image_bytes(candidate["filepath"])

        image_parts.append(
            types.Part.from_bytes(
                data=image_bytes,
                mime_type="image/jpeg"
            )
        )

    prompt = f"""
You are an expert wildfire detection AI reviewing {len(candidates)}
photos of different locations, indexed 0 to {len(candidates) - 1} in
the exact order given.

For EACH image, determine whether it shows visible fire or smoke, or
otherwise indicates elevated wildfire risk (dry or browning
vegetation, drought stress, existing burn scars, dense dry brush).

Return ONLY valid JSON in this exact format, with exactly one entry
per image:

{{
    "results": [
        {{"index": 0, "fire_detected": true, "confidence": 92, "description": "..."}},
        {{"index": 1, "fire_detected": false, "confidence": 35, "description": "..."}}
    ]
}}
"""

    contents = [prompt] + image_parts

    try:

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents
        )

    except Exception as exc:

        raise MultiHotspotAnalysisError(
            f"Gemini multi-image analysis request failed: {exc}"
        )

    try:

        data = _extract_json(response.text)

        raw_results = data["results"]

    except Exception:

        raise MultiHotspotAnalysisError(
            "Gemini didn't return valid JSON for the multi-hotspot analysis."
        )

    hotspots = []

    for item in raw_results:

        index = item.get("index")

        if index is None or not (0 <= index < len(candidates)):
            # Skip anything Gemini couldn't tie back to a real photo
            # rather than guessing which candidate it meant.
            continue

        candidate = candidates[index]

        hotspots.append({
            "latitude": candidate["latitude"],
            "longitude": candidate["longitude"],
            "fire_detected": item.get("fire_detected", False),
            "confidence": item.get("confidence", 0),
            "description": item.get("description", ""),
            "source_url": candidate.get("source_url")
        })

    return hotspots


# ==========================================================
# Standalone Test
# ==========================================================

if __name__ == "__main__":

    # Requires real files at these paths to actually run.
    test_candidates = [
        {
            "filepath": "../uploads/test_1.jpg",
            "latitude": 34.10,
            "longitude": -118.30,
            "source_url": "https://example.com/story-1"
        },
        {
            "filepath": "../uploads/test_2.jpg",
            "latitude": 34.05,
            "longitude": -118.25,
            "source_url": "https://example.com/story-2"
        },
    ]

    from pprint import pprint

    pprint(analyze_multi_hotspots(test_candidates))
