import math


def predict_fire_spread(weather_data, risk_data):
    wind_speed = weather_data.get("wind_speed", 0)
    wind_direction = weather_data.get("wind_direction", 0)
    risk_score = risk_data.get("risk_score", 0)


    # Estimate fire movement speed
    if wind_speed < 10:
        spread_speed = 0.5
    elif wind_speed < 25:
        spread_speed = 1.2
    else:
        spread_speed = 2.0


    # Increase with risk
    spread_speed += (risk_score / 100) * 0.5


    # Convert wind direction into compass direction
    directions = [
        "North",
        "North-East",
        "East",
        "South-East",
        "South",
        "South-West",
        "West",
        "North-West"
    ]

    index = round(wind_direction / 45) % 8
    spread_direction = directions[index]


    # Predict affected radius after 6 hours
    hours = 6
    radius = spread_speed * hours


    return {
        "spread_direction": spread_direction,
        "spread_speed_kmh": round(spread_speed, 2),
        "prediction_time_hours": hours,
        "danger_radius_km": round(radius, 2),
        "wind_influence": f"{wind_speed} km/h wind pushing fire {spread_direction}"
    }