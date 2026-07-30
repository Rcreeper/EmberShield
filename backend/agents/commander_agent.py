def generate_response_plan(risk_data, spread_data, weather_data):

    risk_level = risk_data.get("risk_level", "LOW")
    reasons = risk_data.get("reasons", [])

    direction = spread_data.get("spread_direction", "Unknown")
    radius = spread_data.get("danger_radius_km", 0)
    speed = spread_data.get("spread_speed_kmh", 0)


    actions = []


    if risk_level == "HIGH":
        actions.extend([
            "Deploy wildfire response teams immediately",
            "Increase drone and satellite monitoring frequency",
            "Issue evacuation warnings for nearby settlements",
            "Create fire containment barriers"
        ])

    elif risk_level == "MEDIUM":
        actions.extend([
            "Place emergency teams on standby",
            "Monitor weather changes continuously",
            "Increase forest patrol frequency"
        ])

    else:
        actions.extend([
            "Continue normal monitoring",
            "Maintain wildfire prevention measures"
        ])


    return {
        "priority": risk_level,
        "fire_direction": direction,
        "estimated_spread_speed": f"{speed} km/h",
        "danger_radius": f"{radius} km",
        "critical_factors": reasons,
        "recommended_actions": actions
    }