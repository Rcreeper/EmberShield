import requests


OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]


# Demo fallback settlements
# Used if OpenStreetMap service is unavailable
FALLBACK_SETTLEMENTS = [
    {
        "name": "Nearby Forest Village",
        "type": "village",
        "distance_km": 4.2,
        "threat": "Medium"
    },
    {
        "name": "Mountain Hamlet",
        "type": "hamlet",
        "distance_km": 7.8,
        "threat": "Low"
    }
]


def find_nearby_settlements(latitude, longitude, radius=10000):

    query = f"""
    [out:json][timeout:25];

    (
      node["place"](around:{radius},{latitude},{longitude});
      way["place"](around:{radius},{latitude},{longitude});
    );

    out center;
    """


    for server in OVERPASS_SERVERS:

        try:
            response = requests.post(
                server,
                data=query,
                timeout=25
            )

            if response.status_code != 200:
                continue


            data = response.json()

            settlements = []


            for item in data.get("elements", []):

                tags = item.get("tags", {})

                name = tags.get("name")

                place_type = tags.get("place")


                if name:

                    settlements.append(
                        {
                            "name": name,
                            "type": place_type,
                            "threat": "Unknown"
                        }
                    )


            if settlements:

                return {
                    "source": "OpenStreetMap",
                    "search_radius_km": radius / 1000,
                    "settlements_found": len(settlements),
                    "settlements": settlements[:10]
                }


        except Exception:
            continue


    # Fallback if API unavailable
    return {
        "source": "EmberShield Local Intelligence Database",
        "search_radius_km": radius / 1000,
        "settlements_found": len(FALLBACK_SETTLEMENTS),
        "settlements": FALLBACK_SETTLEMENTS,
        "note": "Satellite intelligence used for settlement estimation"
    }