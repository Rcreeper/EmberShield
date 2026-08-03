"""
EmberShield Backend Server

FastAPI server for:

• Feature A
    POST /analyze

• Feature B
    POST /analyze-multi

• Download Excel
    GET /export

• Live AI reasoning
    WS /ws/updates
"""

import os
from uuid import uuid4

from fastapi import (
    FastAPI,
    Form,
    HTTPException,
    WebSocket,
    WebSocketDisconnect
)

from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from websocket_manager import manager

from agents.sentinel_agent import detect_fire
from agents.multi_hotspot_agent import analyze_multi_hotspots, MultiHotspotAnalysisError
from agents.risk_analyst_agent import analyze_risk
from agents.commander_agent import commander_analysis
from agents.scout_agent import (
    find_location_image,
    find_multi_location_images,
    HotspotSearchError,
    NoHotspotFoundError,
)

from utils.excel_logger import logger
from config import MULTI_HOTSPOT_POINT_COUNT

# ----------------------------------------------------------
# FastAPI App
# ----------------------------------------------------------

app = FastAPI(
    title="EmberShield",
    version="1.0.0"
)

# ----------------------------------------------------------
# CORS
# ----------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------------------
# Upload Folder
# ----------------------------------------------------------

UPLOAD_FOLDER = "uploads"

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

# ----------------------------------------------------------
# Root
# ----------------------------------------------------------

@app.get("/")
async def root():

    return {
        "message": "EmberShield Backend Running"
    }

# ----------------------------------------------------------
# WebSocket
# ----------------------------------------------------------

@app.websocket("/ws/updates")
async def websocket_endpoint(
    websocket: WebSocket
):

    await manager.connect(websocket)

    try:

        while True:

            await websocket.receive_text()

    except WebSocketDisconnect:

        manager.disconnect(websocket)

# ----------------------------------------------------------
# Feature A - Single Location Analysis
# ----------------------------------------------------------

@app.post("/analyze")
async def analyze(
    latitude: float = Form(...),
    longitude: float = Form(...)
):
    """
    Search for a real wildfire report near the given coordinates
    (via Gemini + Google Search grounding) and analyze the photo
    found.

    Pipeline

    Scout Agent (Gemini search)
        ↓
    Sentinel Agent
        ↓
    Risk Analyst
        ↓
    Commander
        ↓
    Excel Logger
    """

    filename = f"{uuid4()}.jpg"

    filepath = os.path.join(
        UPLOAD_FOLDER,
        filename
    )

    try:

        # --------------------------------------------------
        # Scout Agent
        # --------------------------------------------------

        await manager.send_message(
            "Searching for a photo of this location...",
            "Scout Agent"
        )

        try:

            scout_result = find_location_image(
                latitude,
                longitude,
                filepath
            )

        except NoHotspotFoundError as exc:

            await manager.send_message(
                str(exc),
                "Scout Agent"
            )

            raise HTTPException(
                status_code=404,
                detail=str(exc)
            )

        except HotspotSearchError as exc:

            await manager.send_message(
                f"Search failed: {exc}",
                "Scout Agent"
            )

            raise HTTPException(
                status_code=502,
                detail=str(exc)
            )

        await manager.send_message(
            f"Found: {scout_result['source_url']}",
            "Scout Agent"
        )

        # --------------------------------------------------
        # Sentinel Agent
        # --------------------------------------------------

        await manager.send_message(
            "Analyzing image...",
            "Sentinel Agent"
        )

        sentinel_result = detect_fire(
            filepath
        )

        await manager.send_message(
            f"Fire Detected: {sentinel_result['fire_detected']}",
            "Sentinel Agent"
        )

        await manager.send_message(
            f"Confidence: {sentinel_result['confidence']}%",
            "Sentinel Agent"
        )

        # --------------------------------------------------
        # Risk Analyst
        # --------------------------------------------------

        await manager.send_message(
            "Fetching live weather...",
            "Risk Analyst"
        )

        risk_result = analyze_risk(
            latitude,
            longitude
        )

        await manager.send_message(
            "Weather downloaded.",
            "Risk Analyst"
        )

        await manager.send_message(
            f"Spread Speed: {risk_result['spread']['speed_kmh']} km/h",
            "Risk Analyst"
        )

        await manager.send_message(
            f"Spread Direction: {risk_result['spread']['direction']}°",
            "Risk Analyst"
        )

        settlement = risk_result.get(
            "nearest_settlement"
        )

        if settlement:

            await manager.send_message(

                f"Nearest Settlement: {settlement['name']} ({settlement['distance_km']} km)",

                "Risk Analyst"
            )

        else:

            await manager.send_message(

                "No settlements found in spread direction.",

                "Risk Analyst"
            )

        # --------------------------------------------------
        # Commander
        # --------------------------------------------------

        await manager.send_message(
            "Generating emergency response...",
            "Commander"
        )

        commander_result = commander_analysis(
            sentinel_result,
            risk_result
        )

        await manager.send_message(

            f"Severity: {commander_result['severity'].upper()}",

            "Commander"
        )

        # --------------------------------------------------
        # Excel Log
        # --------------------------------------------------

        logger.log_incident(
            latitude,
            longitude,
            sentinel_result,
            risk_result,
            commander_result
        )

        await manager.send_message(
            "Incident stored successfully.",
            "System"
        )

        # --------------------------------------------------
        # Return JSON
        # --------------------------------------------------

        return {

            "source": {
                "url": scout_result["source_url"],
                "summary": scout_result["summary"]
            },

            "sentinel": sentinel_result,

            "risk": risk_result,

            "commander": commander_result
        }

    finally:

        if os.path.exists(filepath):

            os.remove(filepath)

# ----------------------------------------------------------
# Feature B - Multi Hotspot Analysis
# ----------------------------------------------------------

@app.post("/analyze-multi")
async def analyze_multi(
    north: float = Form(...),
    south: float = Form(...),
    east: float = Form(...),
    west: float = Form(...)
):
    """
    Sample up to MULTI_HOTSPOT_POINT_COUNT points across the bounding
    box (center + 4 quadrants by default), search for a real photo
    at each one (via Gemini + Google Search grounding), then analyze
    all found photos together in a single combined Gemini vision
    call before running the full weather + severity pipeline per
    resulting hotspot.

    Points where no usable photo was found are skipped rather than
    failing the whole request -- this only 404s if NOTHING was found
    anywhere in the box.
    """

    candidates = []

    try:

        # --------------------------------------------------
        # Scout Agent
        # --------------------------------------------------

        await manager.send_message(
            "Searching for locations across this area...",
            "Scout Agent"
        )

        try:

            candidates = find_multi_location_images(
                north,
                south,
                east,
                west,
                count=MULTI_HOTSPOT_POINT_COUNT,
                upload_folder=UPLOAD_FOLDER
            )

        except HotspotSearchError as exc:

            await manager.send_message(
                f"Search failed: {exc}",
                "Scout Agent"
            )

            raise HTTPException(
                status_code=502,
                detail=str(exc)
            )

        if not candidates:

            message = "No usable photos found anywhere in this area."

            await manager.send_message(
                message,
                "Scout Agent"
            )

            raise HTTPException(
                status_code=404,
                detail=message
            )

        await manager.send_message(
            f"Found {len(candidates)} location photo(s).",
            "Scout Agent"
        )

        # --------------------------------------------------
        # Multi-Hotspot Agent (Gemini, combined call)
        # --------------------------------------------------

        await manager.send_message(
            "Analyzing photos for wildfire risk...",
            "Multi-Hotspot Sentinel"
        )

        try:

            hotspots = analyze_multi_hotspots(
                candidates
            )

        except MultiHotspotAnalysisError as exc:

            await manager.send_message(
                f"Analysis failed: {exc}",
                "Multi-Hotspot Sentinel"
            )

            raise HTTPException(
                status_code=502,
                detail=str(exc)
            )

        await manager.send_message(
            f"{len(hotspots)} location(s) analyzed.",
            "Multi-Hotspot Sentinel"
        )

        # --------------------------------------------------
        # Risk + Commander (per hotspot)
        # --------------------------------------------------

        results = []

        total = len(hotspots)

        for index, hotspot in enumerate(hotspots, start=1):

            await manager.send_progress(
                index,
                total,
                f"Analyzing hotspot {index} of {total}",
                "Risk Analyst"
            )

            risk = analyze_risk(
                hotspot["latitude"],
                hotspot["longitude"]
            )

            sentinel = {
                "fire_detected": hotspot["fire_detected"],
                "confidence": hotspot["confidence"],
                "description": hotspot["description"]
            }

            commander = commander_analysis(
                sentinel,
                risk
            )

            logger.log_incident(
                hotspot["latitude"],
                hotspot["longitude"],
                sentinel,
                risk,
                commander
            )

            results.append({
                "location": hotspot,
                "risk": risk,
                "commander": commander
            })

            await manager.send_message(
                f"Hotspot {index} complete.",
                "Commander"
            )

        await manager.send_message(
            "Multi-hotspot analysis finished.",
            "System"
        )

        return {
            "hotspots": results
        }

    finally:

        for candidate in candidates:

            candidate_path = candidate.get("filepath")

            if candidate_path and os.path.exists(candidate_path):
                os.remove(candidate_path)


# ----------------------------------------------------------
# Export Excel Log
# ----------------------------------------------------------

@app.get("/export")
async def export_excel():
    """
    Download the Excel incident log.
    """

    return FileResponse(
        logger.get_excel_path(),
        filename="EmberShield_Incident_Log.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# ----------------------------------------------------------
# Health Check
# ----------------------------------------------------------

@app.get("/health")
async def health():
    """
    Simple endpoint to verify the backend is running.
    """

    return {
        "status": "online",
        "service": "EmberShield",
        "version": "1.0.0"
    }