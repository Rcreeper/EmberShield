"""
EmberShield - Risk Analyst Agent

This agent is responsible for:
1. Fetching live weather from Open-Meteo.
2. Calculating fire spread speed and direction.
3. Searching for nearby settlements using Overpass API.
4. Filtering settlements in the predicted spread direction.
5. Estimating the time for the fire to reach a settlement.
"""

import math
import requests
from typing import Dict, List, Optional

from config import (
    OPEN_METEO_URL,
    OVERPASS_URL,
    SETTLEMENT_SEARCH_RADIUS_KM,
    SPREAD_DIRECTION_CONE_DEGREES,
    MIN_SPREAD_SPEED_KMH,
    BASE_FIRE_SPEED_KMH,
)

# Radius of Earth (km)
EARTH_RADIUS = 6371.0


# ==========================================================
# Distance Calculation (Haversine Formula)
# ==========================================================

def haversine_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
) -> float:
    """
    Calculate the great-circle distance between two GPS coordinates.

    Returns:
        Distance in kilometres.
    """

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)

    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS * c


# ==========================================================
# Bearing Calculation
# ==========================================================

def calculate_bearing(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
) -> float:
    """
    Calculate the compass bearing from one point to another.

    Returns:
        Bearing in degrees (0–360).
    """

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    dlon = math.radians(lon2 - lon1)

    y = math.sin(dlon) * math.cos(lat2)

    x = (
        math.cos(lat1) * math.sin(lat2)
        - math.sin(lat1)
        * math.cos(lat2)
        * math.cos(dlon)
    )

    bearing = math.degrees(math.atan2(y, x))

    return (bearing + 360) % 360


# ==========================================================
# Spread Direction
# ==========================================================

def calculate_spread_direction(
    wind_direction_from: float
) -> float:
    """
    Weather APIs report where wind COMES FROM.

    Fire spreads where wind GOES TO.

    Formula:
        (direction + 180) % 360
    """

    return (wind_direction_from + 180) % 360


# ==========================================================
# Spread Speed
# ==========================================================

def calculate_spread_speed(
    humidity: float,
    wind_speed_kmh: float
) -> float:
    """
    Simplified wildfire spread model.

    dryness = (100 - humidity) / 100

    spread_speed =
        max(
            0.3,
            0.5
            + wind_speed/10
            + dryness*2
        )
    """

    dryness = max(0.0, (100 - humidity) / 100)

    speed = (
        BASE_FIRE_SPEED_KMH
        + (wind_speed_kmh / 10)
        + (dryness * 2)
    )

    return max(MIN_SPREAD_SPEED_KMH, speed)

# ==========================================================
# Weather Lookup
# ==========================================================

def get_weather(
    latitude: float,
    longitude: float
) -> Dict:
    """
    Fetch live weather information from Open-Meteo.

    Returns:
        {
            "temperature": float,
            "humidity": float,
            "wind_speed": float,
            "wind_direction": float
        }
    """

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "wind_speed_10m",
            "wind_direction_10m"
        ]
    }

    response = requests.get(
        OPEN_METEO_URL,
        params=params,
        timeout=20
    )

    response.raise_for_status()

    data = response.json()

    current = data["current"]

    return {
        "temperature": current["temperature_2m"],
        "humidity": current["relative_humidity_2m"],
        "wind_speed": current["wind_speed_10m"],
        "wind_direction": current["wind_direction_10m"]
    }


# ==========================================================
# Fire Spread Calculation
# ==========================================================

def calculate_fire_spread(weather: Dict) -> Dict:
    """
    Calculate spread direction and speed using
    the simplified wildfire model.
    """

    spread_direction = calculate_spread_direction(
        weather["wind_direction"]
    )

    spread_speed = calculate_spread_speed(
        weather["humidity"],
        weather["wind_speed"]
    )

    return {
        "spread_direction": spread_direction,
        "spread_speed": spread_speed
    }

# ==========================================================
# Settlement Search (OpenStreetMap Overpass API)
# ==========================================================

def get_nearby_settlements(
    latitude: float,
    longitude: float,
    radius_km: float = SETTLEMENT_SEARCH_RADIUS_KM
) -> List[Dict]:
    """
    Search for nearby cities, towns and villages using
    the OpenStreetMap Overpass API.

    Returns a list of settlements with coordinates.
    """

    radius_m = int(radius_km * 1000)

    overpass_query = f"""
    [out:json];
    (
      node["place"="city"](around:{radius_m},{latitude},{longitude});
      node["place"="town"](around:{radius_m},{latitude},{longitude});
      node["place"="village"](around:{radius_m},{latitude},{longitude});
      node["place"="hamlet"](around:{radius_m},{latitude},{longitude});
    );
    out body;
    """

    response = requests.post(
        OVERPASS_URL,
        data=overpass_query,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    settlements = []

    for element in data.get("elements", []):

        name = element.get("tags", {}).get("name")

        if not name:
            continue

        settlements.append(
            {
                "name": name,
                "latitude": element["lat"],
                "longitude": element["lon"]
            }
        )

    return settlements


# ==========================================================
# Direction Filtering
# ==========================================================

def is_within_spread_cone(
    fire_lat: float,
    fire_lon: float,
    target_lat: float,
    target_lon: float,
    spread_direction: float
) -> bool:
    """
    Determines whether a settlement lies within the
    predicted fire spread cone (±45°).
    """

    bearing = calculate_bearing(
        fire_lat,
        fire_lon,
        target_lat,
        target_lon
    )

    difference = abs(bearing - spread_direction)

    if difference > 180:
        difference = 360 - difference

    return difference <= SPREAD_DIRECTION_CONE_DEGREES


# ==========================================================
# Find Nearest Settlement At Risk
# ==========================================================

def find_nearest_settlement(
    fire_lat: float,
    fire_lon: float,
    settlements: List[Dict],
    spread_direction: float,
    spread_speed: float
) -> Optional[Dict]:
    """
    Returns the closest settlement that lies within the
    predicted spread direction.
    """

    nearest = None

    for settlement in settlements:

        if not is_within_spread_cone(
            fire_lat,
            fire_lon,
            settlement["latitude"],
            settlement["longitude"],
            spread_direction
        ):
            continue

        distance = haversine_distance(
            fire_lat,
            fire_lon,
            settlement["latitude"],
            settlement["longitude"]
        )

        eta = distance / spread_speed

        if nearest is None or distance < nearest["distance_km"]:

            nearest = {
                "name": settlement["name"],
                "latitude": settlement["latitude"],
                "longitude": settlement["longitude"],
                "distance_km": round(distance, 2),
                "eta_hours": round(eta, 2)
            }

    return nearest

# ==========================================================
# Main Risk Analysis Function
# ==========================================================

def analyze_risk(
    latitude: float,
    longitude: float
) -> Dict:
    """
    Main entry point for the Risk Analyst Agent.

    Workflow:
        1. Fetch live weather
        2. Calculate fire spread
        3. Search nearby settlements
        4. Determine which settlement is most at risk
        5. Estimate fire arrival time
        6. Return a structured report
    """

    print("STEP 1 - Getting weather...")
    weather = get_weather(latitude, longitude)
    print("✓ Weather:", weather)

    print("STEP 2 - Calculating spread...")
    spread = calculate_fire_spread(weather)
    print("✓ Spread:", spread)

    print("STEP 3 - Searching settlements...")
    settlements = get_nearby_settlements(latitude, longitude)
    print(f"✓ Found {len(settlements)} settlements")

    print("STEP 4 - Finding nearest...")
    nearest = find_nearest_settlement(
        fire_lat=latitude,
        fire_lon=longitude,
        settlements=settlements,
        spread_direction=spread["spread_direction"],
        spread_speed=spread["spread_speed"]
    )

    print("✓ Risk analysis complete")

    return {
        "weather": weather,
        "spread": {
            "direction": round(spread["spread_direction"], 2),
            "speed_kmh": round(spread["spread_speed"], 2)
        },
        "settlements_found": len(settlements),
        "nearest_settlement": nearest,
        "analysis_location": {
            "latitude": latitude,
            "longitude": longitude
        }
    }

# ==========================================================
# Standalone Test
# ==========================================================

if __name__ == "__main__":

    # Example Coordinates:
    # Delhi, India

    result = analyze_risk(
        latitude=28.6139,
        longitude=77.2090
    )

    from pprint import pprint

    pprint(result)