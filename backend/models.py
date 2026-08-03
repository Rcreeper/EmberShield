"""
EmberShield Data Models

These Pydantic models define the structure of requests and responses
used throughout the FastAPI backend.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# ==========================================================
# Feature A - Single Location Analysis
# ==========================================================

class AnalyzeRequest(BaseModel):
    latitude: float = Field(..., description="Latitude of selected point")
    longitude: float = Field(..., description="Longitude of selected point")


# ==========================================================
# Feature B - Bounding Box
# ==========================================================

class BoundingBox(BaseModel):
    north: float
    south: float
    east: float
    west: float


class AnalyzeMultiRequest(BaseModel):
    bounding_box: BoundingBox


# ==========================================================
# Weather Data
# ==========================================================

class WeatherData(BaseModel):
    temperature: float
    humidity: float
    wind_speed: float
    wind_direction: float


# ==========================================================
# Settlement Information
# ==========================================================

class SettlementInfo(BaseModel):
    name: str
    latitude: float
    longitude: float
    distance_km: float
    eta_hours: float


# ==========================================================
# Risk Analysis
# ==========================================================

class SpreadInfo(BaseModel):
    speed_kmh: float
    direction: float


class AnalysisLocation(BaseModel):
    latitude: float
    longitude: float


class RiskAnalysis(BaseModel):
    # NOTE: analyze_risk() returns a nested {"spread": {"speed_kmh":
    # ..., "direction": ...}, ...} dict (see main.py / excel_logger.py
    # usage of risk_result["spread"]["speed_kmh"]). The previous flat
    # spread_speed_kmh / spread_direction fields didn't match that
    # shape, so this model would have failed validation the moment it
    # was actually used as a response_model.
    weather: WeatherData
    spread: SpreadInfo
    settlements_found: int
    nearest_settlement: Optional[SettlementInfo] = None
    analysis_location: AnalysisLocation


# ==========================================================
# Commander Output
# ==========================================================

class CommanderResult(BaseModel):
    severity: str
    recommended_action: str
    alert_message: str


# ==========================================================
# Hotspot Detection
# ==========================================================

class Hotspot(BaseModel):
    # Matches what agents/multi_hotspot_agent.py's
    # analyze_multi_hotspots() returns per candidate photo.
    latitude: float
    longitude: float
    fire_detected: bool
    confidence: float
    description: str
    source_url: Optional[str] = None


class HotspotList(BaseModel):
    hotspots: List[Hotspot]


# ==========================================================
# Final Analysis Result
# ==========================================================

class SentinelResult(BaseModel):
    fire_detected: bool
    confidence: float
    description: Optional[str] = None


class SourceInfo(BaseModel):
    # Matches the citation agents/scout_agent.py's
    # find_location_image() returns, included in the /analyze
    # response (each hotspot in /analyze-multi carries its own
    # source_url instead -- see Hotspot above).
    url: str
    summary: str


class AnalysisResult(BaseModel):
    # Matches the actual shape returned by POST /analyze:
    # {"source": {...}, "sentinel": {...}, "risk": {...}, "commander": {...}}
    source: SourceInfo
    sentinel: SentinelResult
    risk: RiskAnalysis
    commander: CommanderResult


class MultiHotspotResultItem(BaseModel):
    location: Hotspot
    risk: RiskAnalysis
    commander: CommanderResult


class MultiAnalysisResult(BaseModel):
    # Matches the actual shape returned by POST /analyze-multi:
    # {"hotspots": [{"location": {...}, "risk": {...}, "commander": {...}}, ...]}
    hotspots: List[MultiHotspotResultItem]