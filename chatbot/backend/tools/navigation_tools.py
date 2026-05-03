import requests
from langchain.tools import tool

@tool
def get_shortest_paths(start: str, destinations: list[str]):
    """
    Get shortest paths from a starting location to multiple destinations.
    """

    url = "http://localhost:3001/shortest-path"

    payload = {
        "start": start,
        "destinations": destinations
    }

    try:
        response = requests.post(url, json=payload, timeout=2)

        if response.status_code == 200:
            return response.json()

    except Exception:
        pass  # fallback to mock

    # =========================
    # MOCK DATA (fallback)
    # =========================
    mock_response = {
        "distances": [
            {
                "restaurant_id": dest,
                "total_minutes": (i + 1) * 3,
                "path": [start, f"PATH_{i}", dest]
            }
            for i, dest in enumerate(destinations)
        ]
    }

    return mock_response