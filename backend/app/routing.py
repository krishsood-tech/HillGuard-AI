from __future__ import annotations

from datetime import datetime, timezone

import httpx

from .config import get_settings
from .geo import PLACES, find_place, haversine_km


async def geocode(query: str) -> dict | None:
    local = find_place(query)
    if local:
        return {**local, "source": "HillGuard place index"}
    try:
        async with httpx.AsyncClient(timeout=8, headers={"User-Agent": "HillGuardAI/1.0 academic"}) as client:
            r = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": f"{query}, Himachal Pradesh, India", "format": "json", "limit": 1},
            )
            r.raise_for_status()
            items = r.json()
        if not items:
            return None
        return {
            "name": items[0].get("display_name", query),
            "lat": float(items[0]["lat"]),
            "lng": float(items[0]["lon"]),
            "source": "OpenStreetMap Nominatim",
        }
    except Exception:
        return local


def interpolate_line(a: dict, b: dict, n: int = 24) -> list[list[float]]:
    coords = []
    for i in range(n + 1):
        t = i / n
        lat = a["lat"] + (b["lat"] - a["lat"]) * t
        lng = a["lng"] + (b["lng"] - a["lng"]) * t
        coords.append([lng, lat])
    return coords


async def build_route(start_q: str, end_q: str) -> dict:
    start = await geocode(start_q)
    end = await geocode(end_q)
    if not start or not end:
        return {"ok": False, "error": "Could not resolve start or destination."}

    settings = get_settings()
    retrieved = datetime.now(timezone.utc)
    try:
        url = (
            f"{settings.osrm_url}/route/v1/driving/"
            f"{start['lng']},{start['lat']};{end['lng']},{end['lat']}"
        )
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url, params={"overview": "full", "geometries": "geojson"})
            r.raise_for_status()
            data = r.json()
        route = data["routes"][0]
        coords = route["geometry"]["coordinates"]
        return {
            "ok": True,
            "is_demo": False,
            "source": "OSRM",
            "start": start,
            "end": end,
            "distance_km": round(route["distance"] / 1000, 1),
            "duration_min": round(route["duration"] / 60),
            "geometry": {"type": "LineString", "coordinates": coords},
            "retrieved_at": retrieved.isoformat(),
            "notice": "Route geometry is from a routing provider and is not a safety rating.",
        }
    except Exception:
        coords = interpolate_line(start, end)
        dist = haversine_km(start["lat"], start["lng"], end["lat"], end["lng"])
        return {
            "ok": True,
            "is_demo": True,
            "source": "Demo route fallback (straight-line approximation)",
            "start": start,
            "end": end,
            "distance_km": round(dist, 1),
            "duration_min": int(dist / 35 * 60) if dist else 0,
            "geometry": {"type": "LineString", "coordinates": coords},
            "retrieved_at": retrieved.isoformat(),
            "notice": "Demo Data: routing service unavailable. This is not a driving-quality path.",
        }


def list_places() -> list[dict]:
    return PLACES
