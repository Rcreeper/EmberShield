def analyze_fire_risk(weather_data, satellite_data):

    temperature = weather_data.get("temperature", 0)
    humidity = weather_data.get("humidity", 100)
    precipitation = weather_data.get("precipitation", 0)
    wind_speed = weather_data.get("wind_speed", 0)

    satellite_analysis = satellite_data.get("analysis", {})

    forest_density = satellite_analysis.get(
        "forest_density",
        "Unknown"
    )

    dryness = satellite_analysis.get(
        "dry vegetation risk",
        "Low"
    )


    risk_score = 0
    reasons = []


    # Weather factors

    if temperature > 35:
        risk_score += 25
        reasons.append(
            "Extreme temperature increases ignition probability"
        )

    elif temperature > 30:
        risk_score += 15
        reasons.append(
            "High temperature detected"
        )


    if humidity < 20:
        risk_score += 30
        reasons.append(
            "Very low humidity creates dry conditions"
        )

    elif humidity < 40:
        risk_score += 15
        reasons.append(
            "Low humidity detected"
        )


    if precipitation == 0:
        risk_score += 10
        reasons.append(
            "No recent rainfall detected"
        )


    if wind_speed > 25:
        risk_score += 25
        reasons.append(
            "Strong winds may accelerate fire spread"
        )

    elif wind_speed > 15:
        risk_score += 10
        reasons.append(
            "Moderate wind conditions"
        )


    # Satellite factors

    if forest_density == "High":
        risk_score += 15
        reasons.append(
            "Dense vegetation provides fuel for wildfire"
        )


    if dryness == "High":
        risk_score += 20
        reasons.append(
            "Dry vegetation increases ignition risk"
        )

    elif dryness == "Moderate":
        risk_score += 10
        reasons.append(
            "Moderate vegetation dryness detected"
        )


    risk_score = min(risk_score, 100)


    if risk_score >= 75:
        level = "HIGH"

    elif risk_score >= 45:
        level = "MEDIUM"

    else:
        level = "LOW"


    return {
        "risk_score": risk_score,
        "risk_level": level,
        "reasons": reasons
    }