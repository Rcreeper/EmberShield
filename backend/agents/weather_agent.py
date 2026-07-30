import requests


def get_weather(latitude, longitude):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}"
        f"&longitude={longitude}"
        "&current="
        "temperature_2m,"
        "relative_humidity_2m,"
        "precipitation,"
        "wind_speed_10m,"
        "wind_direction_10m"
    )

    response = requests.get(url)

    if response.status_code != 200:
        return {
            "error": "Weather data unavailable"
        }

    data = response.json()

    weather = data["current"]

    return {
        "temperature": weather["temperature_2m"],
        "humidity": weather["relative_humidity_2m"],
        "precipitation": weather["precipitation"],
        "wind_speed": weather["wind_speed_10m"],
        "wind_direction": weather["wind_direction_10m"]
    }

  