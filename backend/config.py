"""
EmberShield Configuration
-------------------------

This file stores all configurable values used throughout the project.

Instead of hardcoding values across multiple files, everything is
defined here so it can be changed from one place.
"""

# ==========================================================
# MAP CONFIGURATION
# ==========================================================

# Radius (in meters) used for Feature A.
# A visible circle of this size will be drawn around the
# selected point on the Leaflet map.
ANALYSIS_RADIUS_METERS = 1000

# ==========================================================
# FIRE SPREAD SETTINGS
# ==========================================================

# Maximum distance (km) to search for settlements.
SETTLEMENT_SEARCH_RADIUS_KM = 20

# Fire only threatens settlements roughly in front of it.
# This creates a ±45° cone in the spread direction.
SPREAD_DIRECTION_CONE_DEGREES = 45

# Minimum possible fire spread speed.
MIN_SPREAD_SPEED_KMH = 0.3

# Base crawl speed used in the simplified spread model.
BASE_FIRE_SPEED_KMH = 0.5

# ==========================================================
# IMAGE SETTINGS
# ==========================================================

# Maximum upload size (MB)
MAX_IMAGE_SIZE_MB = 10

# Images larger than this width should be resized before
# sending to Claude Vision to reduce latency and cost.
MAX_IMAGE_WIDTH = 1600

# ==========================================================
# API ENDPOINTS
# ==========================================================

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# ==========================================================
# HOTSPOT SEARCH (Scout Agent)
# ==========================================================

# How far around a clicked point (or bounding-box center) to search
# for real, current wildfire/fire/smoke reports via Gemini +
# Google Search grounding. See agents/scout_agent.py.
HOTSPOT_SEARCH_RADIUS_KM = 25

# Number of sub-locations to sample across a bounding box for the
# multi-hotspot feature (center + 4 quadrants by default).
MULTI_HOTSPOT_POINT_COUNT = 5

# ==========================================================
# AI MODEL
# ==========================================================

# NOTE: claude-sonnet-4-20250514 was retired on June 15, 2026 and
# now returns 404. claude-sonnet-4-6 is the current drop-in
# replacement in the same tier. For max capability instead, use
# claude-opus-4-8 (that tier no longer accepts temperature/top_p/
# top_k or manual thinking-budget params).
CLAUDE_MODEL = "claude-sonnet-4-6"

# Model used by agents/scout_agent.py for Google Search grounding.
# Google ships new Gemini versions frequently -- verify this is
# still current at https://ai.google.dev/gemini-api/docs/models
# before relying on it long-term.
GEMINI_MODEL = "gemini-3.6-flash"

# ==========================================================
# LOGGING
# ==========================================================

EXCEL_LOG_FILE = "logs/incidents.xlsx"

# ==========================================================
# WEBSOCKET
# ==========================================================

MAX_TRACE_MESSAGES = 1000