"""
EmberShield - Scout Agent

Replaces manual image upload (and the old Google Maps Static
satellite fetch, utils/satellite_service.py, removed) with a live
web search. Uses Gemini's built-in Google Search grounding tool to
find a real, recent photo of a location, so the Sentinel / Multi-
Hotspot agents always have a real image to assess for wildfire risk
-- not just locations with an already-confirmed active fire. This
app predicts wildfire probability, so it needs to work for any
location the user picks, not only ones already on fire.

Two entry points:

    find_location_image(lat, lon, filepath)
        Single-location search, used by POST /analyze.

    find_multi_location_images(north, south, east, west)
        Samples up to MULTI_HOTSPOT_POINT_COUNT points across a
        bounding box (center + 4 quadrants by default) and searches
        each one independently, used by POST /analyze-multi. Points
        where nothing usable is found are skipped rather than
        failing the whole request.

Pipeline (per point)
---------------------
1. Ask Gemini (with the google_search tool enabled) to search for a
   real, recent photo of that location -- prioritizing wildfire/
   fire/smoke reports if any exist, falling back to any real aerial
   or ground-level photo of the area otherwise.
2. Read the grounding citations Gemini used to ground its answer.
3. Follow each citation and look for a real photo on that page
   (the og:image meta tag, falling back to the page's first <img>).
4. Download the first image that resolves successfully.

VERIFICATION NOTE
------------------
This was written against Google's published google-genai SDK docs
(Tool(google_search=GoogleSearch()) and
response.candidates[0].grounding_metadata.grounding_chunks with
chunk.web.uri / chunk.web.title) but has not been run against a
live API key in this environment. If Google has changed that shape,
_get_grounding_urls() below will raise AttributeError internally,
which is caught and treated as "no sources found" rather than
crashing -- if that happens on your first real run, paste the
output of print(response) here and I'll fix the field access.

There is also a more literal "Google Images" option worth knowing
about: the Google Custom Search JSON API supports searchType=image,
which returns direct image URLs instead of scraping og:image tags
off linked pages. That needs a separate Programmable Search Engine
ID + API key (distinct from GEMINI_API_KEY). The scraping approach
below needs no extra credentials and reuses the key you already
have, but if you already have a Custom Search Engine set up, that
API is more direct/reliable than this og:image scraping -- say the
word and I'll wire that in instead/as well.

COMPLIANCE NOTE
----------------
Google's terms for Grounding with Google Search require displaying
search results appropriately in production (typically the
search_entry_point.rendered_content "Search Suggestions" widget).
This backend only extracts a photo for internal analysis -- if you
surface Gemini's summary or search results directly to end users in
the frontend, make sure that UI shows the required attribution/
suggestions widget. See https://ai.google.dev/gemini-api/docs/google-search
"""

import os
import re

from typing import Dict, List, Optional
from urllib.parse import urljoin
from uuid import uuid4

import requests

from dotenv import load_dotenv
from google import genai
from google.genai import types

from config import (
    GEMINI_MODEL,
    HOTSPOT_SEARCH_RADIUS_KM,
    MULTI_HOTSPOT_POINT_COUNT,
)

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; EmberShieldBot/1.0)"
}


class HotspotSearchError(Exception):
    """Raised when the Gemini search itself fails (missing/bad key, request error)."""
    pass


class NoHotspotFoundError(HotspotSearchError):
    """Raised when the search succeeded but found no usable photo nearby."""
    pass


# ==========================================================
# Gemini Search
# ==========================================================

def _search_location(
    latitude: float,
    longitude: float,
    radius_km: float
):
    """
    Ask Gemini (grounded with Google Search) for a real, recent
    photo of the given coordinates -- prioritizing wildfire/fire/
    smoke reports if any exist near there right now, but falling
    back to any real aerial or ground-level photo of the area so
    wildfire *risk* can still be assessed even with no active fire.

    Returns the raw Gemini response so the caller can read both the
    summary text and the grounding citations.
    """

    if not GEMINI_API_KEY:
        raise HotspotSearchError(
            "GEMINI_API_KEY is missing from your .env file. "
            "Get one at https://aistudio.google.com/apikey"
        )

    client = genai.Client(api_key=GEMINI_API_KEY)

    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )

    generate_config = types.GenerateContentConfig(
        tools=[grounding_tool]
    )

    prompt = f"""
Search for a real, recent photo of the location at latitude
{latitude}, longitude {longitude}, within {radius_km} km.

Prioritize any real, current reports of active wildfire, brush fire,
or significant smoke near this location if they exist.

If nothing fire-related is currently being reported there, instead
find any real, recent aerial or ground-level photo of this location
(news, government, tourism, or mapping sources) so its terrain and
vegetation can be assessed for wildfire risk. Do not fabricate a
source -- only report something you can find a real source for.
"""

    try:

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=generate_config
        )

    except Exception as exc:

        raise HotspotSearchError(
            f"Gemini search request failed: {exc}"
        )

    return response


def _get_grounding_urls(response) -> list:
    """
    Pull the list of source URLs Gemini cited while grounding its
    answer. Returns an empty list if there's no grounding metadata
    (e.g. Gemini answered without needing to search) or if the
    response shape doesn't match what's expected here.
    """

    urls = []

    try:

        candidates = response.candidates

        if not candidates:
            return urls

        grounding_metadata = candidates[0].grounding_metadata

        if not grounding_metadata or not grounding_metadata.grounding_chunks:
            return urls

        for chunk in grounding_metadata.grounding_chunks:

            web = getattr(chunk, "web", None)

            if web and getattr(web, "uri", None):
                urls.append(web.uri)

    except AttributeError:

        # Grounding metadata shape differs from what's expected --
        # surface as "no sources found" rather than crashing the
        # request. See VERIFICATION NOTE at the top of this file.
        pass

    return urls


# ==========================================================
# Image Extraction
# ==========================================================

def _extract_image_url(page_url: str) -> Optional[str]:
    """
    Fetch a web page (following Google's grounding redirect if
    present) and pull out a usable photo URL -- the og:image meta
    tag if present, otherwise the page's first <img> tag.
    """

    try:

        response = requests.get(
            page_url,
            headers=_HEADERS,
            timeout=15,
            allow_redirects=True
        )

        response.raise_for_status()

    except requests.RequestException:

        return None

    html = response.text
    final_url = response.url

    og_match = re.search(
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        html,
        re.IGNORECASE
    )

    if not og_match:

        # og:image / content attribute order can be reversed
        og_match = re.search(
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
            html,
            re.IGNORECASE
        )

    if og_match:
        return urljoin(final_url, og_match.group(1))

    img_match = re.search(
        r'<img[^>]+src=["\']([^"\']+)["\']',
        html,
        re.IGNORECASE
    )

    if img_match:
        return urljoin(final_url, img_match.group(1))

    return None


def _download_image(image_url: str, filepath: str) -> bool:
    """
    Download image_url to filepath. Returns True on success, False
    if the URL didn't actually resolve to an image.
    """

    try:

        response = requests.get(
            image_url,
            headers=_HEADERS,
            timeout=20,
            stream=True
        )

        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")

        if not content_type.startswith("image/"):
            return False

        with open(filepath, "wb") as f:

            for chunk in response.iter_content(8192):
                f.write(chunk)

        return True

    except requests.RequestException:

        return False


# ==========================================================
# Single-Location Pipeline (POST /analyze)
# ==========================================================

def find_location_image(
    latitude: float,
    longitude: float,
    filepath: str,
    radius_km: float = HOTSPOT_SEARCH_RADIUS_KM
) -> Dict:
    """
    Search for a real, recent photo of (latitude, longitude),
    download it to filepath, and return what was found.

    Returns:
        {
            "filepath": str,
            "latitude": float,
            "longitude": float,
            "source_url": str,
            "summary": str    # Gemini's grounded text summary
        }

    Raises:
        HotspotSearchError    -- missing key / request failure
        NoHotspotFoundError   -- search succeeded but nothing usable found
    """

    response = _search_location(
        latitude,
        longitude,
        radius_km
    )

    summary = getattr(response, "text", "") or ""

    source_urls = _get_grounding_urls(response)

    if not source_urls:

        raise NoHotspotFoundError(
            "Gemini found no usable photo sources for this location."
        )

    for source_url in source_urls:

        image_url = _extract_image_url(source_url)

        if not image_url:
            continue

        if _download_image(image_url, filepath):

            return {
                "filepath": filepath,
                "latitude": latitude,
                "longitude": longitude,
                "source_url": source_url,
                "summary": summary
            }

    raise NoHotspotFoundError(
        "Found sources for this location, but couldn't retrieve a "
        "usable photo from any of them."
    )


# ==========================================================
# Multi-Location Pipeline (POST /analyze-multi)
# ==========================================================

def generate_grid_points(
    north: float,
    south: float,
    east: float,
    west: float,
    count: int = MULTI_HOTSPOT_POINT_COUNT
) -> List[Dict]:
    """
    Generate sample GPS points spread across a bounding box.

    Default (count=5): center + the four quadrant centers, giving
    even geographic coverage of the whole box so each search looks
    at a different part of the selected area.
    """

    mid_lat = (north + south) / 2
    mid_lon = (east + west) / 2

    quarter_lat = (north - south) / 4
    quarter_lon = (east - west) / 4

    points = [
        {"latitude": mid_lat, "longitude": mid_lon, "label": "Center"},
        {"latitude": mid_lat + quarter_lat, "longitude": mid_lon - quarter_lon, "label": "Northwest"},
        {"latitude": mid_lat + quarter_lat, "longitude": mid_lon + quarter_lon, "label": "Northeast"},
        {"latitude": mid_lat - quarter_lat, "longitude": mid_lon - quarter_lon, "label": "Southwest"},
        {"latitude": mid_lat - quarter_lat, "longitude": mid_lon + quarter_lon, "label": "Southeast"},
    ]

    return points[:count]


def find_multi_location_images(
    north: float,
    south: float,
    east: float,
    west: float,
    count: int = MULTI_HOTSPOT_POINT_COUNT,
    upload_folder: str = "uploads"
) -> List[Dict]:
    """
    Sample up to `count` points across the bounding box and search
    each one independently for a real photo. Points where nothing
    usable is found are skipped rather than failing the whole
    request -- callers should treat an empty result list as "found
    nothing anywhere in this area".

    Returns a list of dicts (same shape as find_location_image(),
    plus "label"), one per point that succeeded -- so it may have
    fewer than `count` entries.
    """

    points = generate_grid_points(north, south, east, west, count)

    results = []

    for point in points:

        filepath = os.path.join(upload_folder, f"{uuid4()}.jpg")

        try:

            found = find_location_image(
                point["latitude"],
                point["longitude"],
                filepath
            )

        except HotspotSearchError:

            # Best-effort across points -- one bad/empty point
            # shouldn't sink the other four.
            continue

        found["label"] = point["label"]

        results.append(found)

    return results


# ==========================================================
# Standalone Test
# ==========================================================

if __name__ == "__main__":

    # Example coordinates: Los Angeles, California
    result = find_location_image(
        latitude=34.0522,
        longitude=-118.2437,
        filepath="../uploads/test_scout.jpg"
    )

    from pprint import pprint

    pprint(result)
