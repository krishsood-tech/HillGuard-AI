from __future__ import annotations

import json
from datetime import datetime, timezone

import httpx

from .config import get_settings
from .geo import freshness_payload, nearest_place

WMO = {
    0: "Clear",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    51: "Drizzle",
    61: "Rain",
    63: "Rain",
    65: "Heavy rain",
    71: "Snow",
    80: "Rain showers",
    95: "Thunderstorm",
}


async def fetch_weather(lat: float, lng: float) -> dict:
    settings = get_settings()
    retrieved = datetime.now(timezone.utc)
    location = nearest_place(lat, lng)
    try:
        if settings.weather_api_key and settings.weather_provider == "openweather":
            url = "https://api.openweathermap.org/data/2.5/weather"
            async with httpx.AsyncClient(timeout=8) as client:
                r = await client.get(
                    url,
                    params={"lat": lat, "lon": lng, "appid": settings.weather_api_key, "units": "metric"},
                )
                r.raise_for_status()
                data = r.json()
            observed = datetime.fromtimestamp(data.get("dt", retrieved.timestamp()), tz=timezone.utc)
            payload = {
                "temperature_c": data["main"]["temp"],
                "humidity": data["main"]["humidity"],
                "wind_kmh": round(data["wind"].get("speed", 0) * 3.6, 1),
                "rainfall_mm": data.get("rain", {}).get("1h", 0),
                "condition": data["weather"][0]["description"].title() if data.get("weather") else "Unknown",
            }
            source = "OpenWeatherMap"
            is_demo = False
            source_url = "https://openweathermap.org/"
        else:
            url = "https://api.open-meteo.com/v1/forecast"
            async with httpx.AsyncClient(timeout=8) as client:
                r = await client.get(
                    url,
                    params={
                        "latitude": lat,
                        "longitude": lng,
                        "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m",
                    },
                )
                r.raise_for_status()
                data = r.json()
            cur = data.get("current", {})
            observed = datetime.fromisoformat(cur["time"].replace("Z", "+00:00")) if cur.get("time") else retrieved
            code = int(cur.get("weather_code", 0))
            payload = {
                "temperature_c": cur.get("temperature_2m"),
                "humidity": cur.get("relative_humidity_2m"),
                "wind_kmh": cur.get("wind_speed_10m"),
                "rainfall_mm": cur.get("precipitation"),
                "condition": WMO.get(code, "Unknown"),
            }
            source = "Open-Meteo"
            is_demo = False
            source_url = "https://open-meteo.com/"
        fresh = freshness_payload(observed, retrieved)
        return {
            "available": True,
            "is_demo": is_demo,
            "source": source,
            "source_url": source_url,
            "license": "See provider terms",
            "location": location,
            "latitude": lat,
            "longitude": lng,
            "values": payload,
            "freshness": fresh,
            "label": "Live observation" if not is_demo else "Demo Data",
        }
    except Exception:
        if not settings.demo_mode:
            return {
                "available": False,
                "is_demo": False,
                "error": "Weather service temporarily unavailable.",
                "location": location,
            }
        observed = retrieved
        fresh = freshness_payload(observed, retrieved)
        fresh["notice"] = "Demo Data — not a live weather observation."
        return {
            "available": True,
            "is_demo": True,
            "source": "Demo weather fallback",
            "source_url": None,
            "license": "Academic demo sample",
            "location": location,
            "latitude": lat,
            "longitude": lng,
            "values": {
                "temperature_c": 15.0,
                "humidity": 70,
                "wind_kmh": 8,
                "rainfall_mm": 1.2,
                "condition": "Cloudy (demo)",
            },
            "freshness": fresh,
            "label": "Demo Data",
        }
