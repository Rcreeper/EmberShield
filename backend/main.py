from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agents.weather_agent import get_weather
from agents.risk_agent import analyze_fire_risk
from agents.spread_agent import predict_fire_spread
from agents.commander_agent import generate_response_plan
from agents.satellite_agent import get_satellite_info
from agents.settlement_agent import find_nearby_settlements


app = FastAPI(
    title="EmberShield AI",
    description="AI Agent Wildfire Prediction and Emergency Response System",
    version="1.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "status": "online",
        "message": "EmberShield Command Center is running"
    }


@app.get("/health")
def health():
    return {
        "healthy": True,
        "system": "EmberShield Backend"
    }


@app.post("/analyze")
def analyze_fire(location: dict):

    latitude = location.get("latitude")
    longitude = location.get("longitude")

    # NEW
    fire_start_time = location.get("fire_start_time")
    radius_km = location.get("radius_km", 1)

    # 1. Satellite Intelligence
    satellite = get_satellite_info(
        latitude,
        longitude
    )

    # 2. Weather Intelligence
    weather = get_weather(
        latitude,
        longitude
    )

    # 3. Fire Risk Analysis
    risk = analyze_fire_risk(
        weather,
        satellite
    )

    # 4. Fire Spread Simulation
    spread = predict_fire_spread(
        weather,
        risk
    )

    # 5. Settlement Detection
    settlements = find_nearby_settlements(
        latitude,
        longitude
    )

    # 6. Emergency Commander
    response = generate_response_plan(
        risk,
        spread,
        weather
    )

    return {

        "incident": {
            "fire_start_time": fire_start_time,
            "analysis_radius_km": radius_km
        },

        "location": {
            "latitude": latitude,
            "longitude": longitude
        },

        "satellite_analysis": satellite,

        "weather": weather,

        "risk_analysis": risk,

        "spread_prediction": spread,

        "nearby_settlements": settlements,

        "commander_response": response

    }
}