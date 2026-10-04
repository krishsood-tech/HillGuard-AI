from __future__ import annotations

import math
from datetime import datetime, timezone

HP_BOUNDS = {"min_lat": 30.3, "max_lat": 33.3, "min_lon": 75.5, "max_lon": 79.1}
HP_CENTER = {"lat": 31.8, "lng": 77.2, "zoom": 8}

PLACES = [
    {"name": "Shimla", "lat": 31.1048, "lng": 77.1734},
    {"name": "Manali", "lat": 32.2396, "lng": 77.1887},
    {"name": "Mandi", "lat": 31.7084, "lng": 76.9320},
    {"name": "Kangra", "lat": 32.0998, "lng": 76.2691},
    {"name": "Dharamshala", "lat": 32.2190, "lng": 76.3234},
    {"name": "Solan", "lat": 30.9045, "lng": 77.0967},
    {"name": "Chamba", "lat": 32.5534, "lng": 76.1258},
    {"name": "Kullu", "lat": 31.9578, "lng": 77.1095},
    {"name": "Dalhousie", "lat": 32.5385, "lng": 75.9708},
    {"name": "Bilaspur", "lat": 31.3400, "lng": 76.7600},
    {"name": "Hamirpur", "lat": 31.6860, "lng": 76.5210},
    {"name": "Una", "lat": 31.4680, "lng": 76.2700},
]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def nearest_place(lat: float, lng: float) -> str:
    best = min(PLACES, key=lambda p: haversine_km(lat, lng, p["lat"], p["lng"]))
    return best["name"]


def find_place(query: str) -> dict | None:
    q = query.strip().lower()
    for p in PLACES:
        if p["name"].lower() == q or q in p["name"].lower():
            return p
    return None


def freshness_payload(observed_at: datetime | None, retrieved_at: datetime | None = None) -> dict:
    now = datetime.now(timezone.utc)
    retrieved = retrieved_at or now
    if observed_at is None:
        return {
            "status": "unavailable",
            "status_label": "Unavailable",
            "freshness_text": "No observation time",
            "age_minutes": None,
            "observed_at": None,
            "retrieved_at": retrieved.isoformat(),
            "stale": True,
            "notice": "Data may be outdated.",
        }
    obs = observed_at if observed_at.tzinfo else observed_at.replace(tzinfo=timezone.utc)
    age = (now - obs).total_seconds() / 60
    if age <= 60:
        status, label = "recent", "Recent"
        notice = None
    elif age <= 360:
        status, label = "aging", "Aging"
        notice = "Data may be outdated."
    else:
        status, label = "stale", "Stale"
        notice = "Data may be outdated."
    return {
        "status": status,
        "status_label": label,
        "freshness_text": f"{int(age)} minutes old" if age >= 1 else "just now",
        "age_minutes": round(age, 1),
        "observed_at": obs.isoformat(),
        "retrieved_at": retrieved.isoformat(),
        "stale": status != "recent",
        "notice": notice,
    }


def point_near_line(lat: float, lon: float, coords: list[list[float]], buffer_km: float = 8.0) -> bool:
    """coords are [lng, lat] GeoJSON positions."""
    for lng, lat2 in coords:
        if haversine_km(lat, lon, lat2, lng) <= buffer_km:
            return True
    return False
