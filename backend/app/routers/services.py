from __future__ import annotations

import json
from collections import Counter
from datetime import timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..geo import find_place, haversine_km, point_near_line
from ..ml_service import analyze_risk, cluster_incidents
from ..models import ExternalObservation, Incident, ModelOutput, Notification, utcnow
from ..routing import build_route, geocode, list_places
from ..schemas import RiskIn, RouteIn
from ..weather import fetch_weather
from .incidents import PUBLIC_STATUSES, serialize

router = APIRouter(prefix="/api", tags=["services"])


@router.get("/places")
def places():
    return {"items": list_places()}


@router.get("/search")
async def search(q: str, db: Session = Depends(get_db)):
    place = find_place(q) or await geocode(q)
    if not place:
        return {"found": False, "place": None, "nearby": []}

    lat, lng = float(place["lat"]), float(place["lng"])
    rows = db.query(Incident).filter(Incident.verification_status.in_(PUBLIC_STATUSES)).all()
    nearby = [serialize(i) for i in rows if haversine_km(lat, lng, i.latitude, i.longitude) <= 20]
    weather = await fetch_weather(lat, lng)
    values = weather.get("values") or {}
    risk = analyze_risk(lat, lng, rows, values.get("rainfall_mm") if weather.get("available") else None)
    return {"found": True, "place": place, "nearby": nearby, "weather": weather, "risk": risk}


@router.get("/weather")
async def weather(lat: float, lng: float):
    return await fetch_weather(lat, lng)


@router.post("/ai/risk")
async def ai_risk(body: RiskIn, db: Session = Depends(get_db)):
    rows = db.query(Incident).filter(Incident.verification_status.in_(PUBLIC_STATUSES)).all()
    rainfall = body.rainfall_mm
    if rainfall is None:
        weather = await fetch_weather(body.latitude, body.longitude)
        if weather.get("available"):
            rainfall = (weather.get("values") or {}).get("rainfall_mm")

    out = analyze_risk(body.latitude, body.longitude, rows, rainfall)
    db.add(
        ModelOutput(
            latitude=body.latitude,
            longitude=body.longitude,
            target="area_risk",
            category=out["risk_category"],
            model_version=out["model_version"],
            input_coverage=out["data_coverage"],
            uncertainty=out["uncertainty"],
            explanation_json=json.dumps(out["factors"]),
            is_demo=True,
        )
    )
    db.commit()
    return out


@router.post("/ai/image-analysis")
async def image_analysis():
    return {
        "message": "Upload an image with POST /api/incidents. Standalone analysis uses the demonstration triage service.",
        "mode": "demonstration",
    }


@router.get("/clusters")
def clusters(db: Session = Depends(get_db)):
    return {"items": cluster_incidents(db.query(Incident).all())}


@router.get("/analytics")
def analytics(db: Session = Depends(get_db)):
    rows = db.query(Incident).filter(Incident.verification_status != "rejected").all()
    by_type = Counter(i.category for i in rows)
    by_status = Counter(i.verification_status for i in rows)
    cutoff = utcnow() - timedelta(hours=24)
    last24 = [
        i
        for i in rows
        if i.submitted_at
        and i.submitted_at.replace(tzinfo=i.submitted_at.tzinfo or timezone.utc) >= cutoff
    ]
    cluster_count = len(cluster_incidents(db.query(Incident).all()))
    days = {}
    for i in rows:
        key = i.submitted_at.date().isoformat()
        days[key] = days.get(key, 0) + 1
    weather_n = db.query(ExternalObservation).count()
    return {
        "kpis": {
            "total": len(rows),
            "verified": by_status.get("verified", 0),
            "unverified": by_status.get("unverified", 0),
            "under_review": by_status.get("under_review", 0),
            "last_24h": len(last24),
            "clusters": cluster_count,
            "ai_risk_areas": len({i.ai_risk_category for i in rows if i.ai_risk_category in {"Elevated", "Higher"}}),
            "weather_observations": weather_n or 1,
        },
        "by_type": dict(by_type),
        "by_status": dict(by_status),
        "over_time": [{"date": k, "count": days[k]} for k in sorted(days)],
        "density": [{"lat": i.latitude, "lng": i.longitude, "category": i.category} for i in rows],
    }


@router.post("/routes/analyze")
async def routes_analyze(body: RouteIn, db: Session = Depends(get_db)):
    route = await build_route(body.start, body.destination)
    if not route.get("ok"):
        return {"error": route.get("error", "Route service unavailable.")}
    coords = route["geometry"]["coordinates"]
    rows = db.query(Incident).filter(Incident.verification_status.in_(PUBLIC_STATUSES)).all()
    nearby = [serialize(i) for i in rows if point_near_line(i.latitude, i.longitude, coords, 8)]
    verified = sum(1 for i in nearby if i["verification_status"] == "verified")
    unverified = sum(1 for i in nearby if i["verification_status"] == "unverified")
    mid = coords[len(coords) // 2]
    weather = await fetch_weather(mid[1], mid[0])
    rain = (weather.get("values") or {}).get("rainfall_mm") if weather.get("available") else None
    risk = analyze_risk(mid[1], mid[0], rows, rain)
    summary_line = (
        "Reported hazards detected near this route."
        if nearby
        else "No relevant reports found in the available data."
    )
    return {
        "route": route,
        "summary": {
            "start": route["start"]["name"] if isinstance(route["start"], dict) else body.start,
            "destination": route["end"]["name"] if isinstance(route["end"], dict) else body.destination,
            "reported_nearby": len(nearby),
            "unverified": unverified,
            "verified": verified,
            "weather_observations": "Available" if weather.get("available") else "Unavailable",
            "ai_indicator": risk["risk_category"],
            "last_checked": utcnow().isoformat(),
            "headline": summary_line,
            "disclaimer": "Absence of reported incidents does not guarantee safe conditions.",
        },
        "incidents": nearby,
        "weather": weather,
        "risk": risk,
    }


@router.get("/routes")
def routes():
    return {
        "message": "POST /api/routes/analyze with start and destination.",
        "examples": [{"start": "Shimla", "destination": "Manali"}],
    }


@router.get("/notifications")
def notifications(db: Session = Depends(get_db)):
    rows = db.query(Notification).order_by(Notification.created_at.desc()).limit(30).all()
    return {
        "items": [
            {
                "id": n.id,
                "kind": n.kind,
                "title": n.title,
                "body": n.body,
                "is_official": n.is_official,
                "official_label": "OFFICIAL" if n.is_official else "INFORMATIONAL",
                "created_at": n.created_at.isoformat(),
            }
            for n in rows
        ]
    }


@router.get("/sources")
def sources():
    return {
        "items": [
            {
                "name": "OpenStreetMap",
                "data_type": "Map information",
                "status": "Available",
                "update_frequency": "Community / tile provider",
                "license": "ODbL — © OpenStreetMap contributors",
                "kind": "AUTHORIZED_BASEMAP",
            },
            {
                "name": "Open-Meteo / optional OpenWeather",
                "data_type": "Weather observations",
                "status": "Available with fallback",
                "update_frequency": "Hourly typical",
                "license": "Provider terms",
                "kind": "EXTERNAL_OBSERVATION",
            },
            {
                "name": "OSRM public server",
                "data_type": "Routing geometry",
                "status": "Best-effort with demo fallback",
                "update_frequency": "On request",
                "license": "OSRM / OSM",
                "kind": "EXTERNAL_SERVICE",
            },
            {
                "name": "Community reports",
                "data_type": "Hazard incident reports",
                "status": "User submitted",
                "update_frequency": "As submitted",
                "license": "Platform academic use",
                "kind": "COMMUNITY_REPORT",
            },
            {
                "name": "HillGuard AI models",
                "data_type": "Risk indicator and image triage",
                "status": "Experimental / demonstration",
                "update_frequency": "On request",
                "license": "Academic prototype",
                "kind": "AI_GENERATED_ESTIMATE",
            },
        ],
        "kinds": {
            "OFFICIAL / AUTHORIZED SOURCE": "Government or licensed basemap/weather providers. HillGuard does not speak for them.",
            "COMMUNITY REPORT": "User-submitted observations. Unverified until a moderator reviews them.",
            "AI-GENERATED ESTIMATE": "Experimental indicators. May be incomplete or incorrect. Not official warnings.",
        },
    }
