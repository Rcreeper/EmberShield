import requests


def get_satellite_info(latitude, longitude):

    return {
        "source": "Esri World Imagery",
        "location": {
            "latitude": latitude,
            "longitude": longitude
        },
        "analysis": {
            "vegetation_detected": True,
            "forest_density": "High",
            "terrain": "Mountainous",
            "dry vegetation risk": "Moderate"
        }
    }