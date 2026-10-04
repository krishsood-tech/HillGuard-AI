from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image
from sklearn.cluster import DBSCAN

from .geo import haversine_km, nearest_place
from .models import Incident, utcnow

DISCLAIMER = (
    "This is an experimental decision-support indicator and is not an official warning. "
    "AI results are supporting indicators and may be incomplete or incorrect."
)

LABELS = [
    "Possible Landslide",
    "Possible Flood/Waterlogging",
    "Possible Road Obstruction",
    "Possible Road Damage",
    "Possible Falling Rocks",
    "Other/Uncertain",
]


def analyze_risk(lat: float, lng: float, incidents: list[Incident], rainfall_mm: float | None) -> dict:
    nearby = [i for i in incidents if haversine_km(lat, lng, i.latitude, i.longitude) <= 12]
    recent = [i for i in nearby if (utcnow() - _aware(i.observed_at)).total_seconds() <= 24 * 3600]
    rain = rainfall_mm if rainfall_mm is not None else 0.0
    score = 0.0
    factors = []
    if rain >= 20:
        score += 2
        factors.append("Recent rainfall observation")
    elif rain >= 5:
        score += 1
        factors.append("Light-to-moderate rainfall observation")
    if len(recent) >= 3:
        score += 2
        factors.append("Multiple nearby reports in last 24 hours")
    elif len(recent) >= 1:
        score += 1
        factors.append("Nearby historical/community incidents")
    severe = sum(1 for i in recent if i.category in {"landslide", "flood", "falling_rocks"})
    if severe:
        score += 1
        factors.append("Severe-category reports nearby")
    if not factors:
        factors.append("Limited local reports in available data")

    if score >= 4:
        category = "Higher"
    elif score >= 3:
        category = "Elevated"
    elif score >= 1.5:
        category = "Moderate"
    else:
        category = "Lower"

    coverage = "Limited" if rainfall_mm is None or len(nearby) < 2 else "Moderate"
    return {
        "risk_category": category,
        "analysis_timestamp": utcnow().isoformat(),
        "model_version": "Risk Model v1.0-demo",
        "input_information": {
            "nearby_incidents": len(nearby),
            "recent_incidents_24h": len(recent),
            "rainfall_mm": rainfall_mm,
            "area": nearest_place(lat, lng),
        },
        "factors": factors,
        "data_coverage": coverage,
        "uncertainty": "high",
        "notice": DISCLAIMER,
        "is_demo": True,
        "probability": None,
        "why": (
            "Relative indicator from available rainfall (if any) and nearby community reports. "
            "It is not calibrated and must not be treated as a disaster forecast."
        ),
    }


def cluster_incidents(incidents: list[Incident], hours: int = 24) -> list[dict]:
    recent = [
        i
        for i in incidents
        if i.verification_status != "rejected" and (utcnow() - _aware(i.observed_at)).total_seconds() <= hours * 3600
    ]
    if len(recent) < 2:
        return []
    coords = np.radians(np.array([[i.latitude, i.longitude] for i in recent]))
    kms_per_radian = 6371.0088
    eps = 8 / kms_per_radian
    labels = DBSCAN(eps=eps, min_samples=2, metric="haversine").fit_predict(coords)
    clusters = []
    for lab in sorted(set(labels)):
        if lab < 0:
            continue
        members = [i for i, l in zip(recent, labels) if l == lab]
        cats = {}
        for m in members:
            cats[m.category] = cats.get(m.category, 0) + 1
        primary = max(cats, key=cats.get)
        lats = [m.latitude for m in members]
        lngs = [m.longitude for m in members]
        statuses = {m.verification_status for m in members}
        times = [_aware(m.observed_at) for m in members]
        clusters.append(
            {
                "id": f"cluster-{lab}",
                "count": len(members),
                "primary_type": primary,
                "area": nearest_place(sum(lats) / len(lats), sum(lngs) / len(lngs)) + " region",
                "center": {"lat": sum(lats) / len(lats), "lng": sum(lngs) / len(lngs)},
                "time_window": f"Last {hours} hours",
                "time_range": {
                    "from": min(times).isoformat(),
                    "to": max(times).isoformat(),
                },
                "verification_status": "mixed" if len(statuses) > 1 else next(iter(statuses)),
                "status_note": "Requires review",
                "incident_ids": [m.id for m in members],
                "explanation": (
                    "A cluster groups nearby reports in space and time. "
                    "It does not prove that a disaster occurred."
                ),
            }
        )
    return clusters


def triage_image(path: Path) -> dict:
    """Demonstration image triage — not a validated hazard detector."""
    try:
        img = Image.open(path).convert("RGB")
        arr = np.array(img.resize((64, 64))) / 255.0
        mean = arr.mean(axis=(0, 1))
        r, g, b = mean.tolist()
        brown = r > 0.35 and g > 0.25 and b < 0.35
        blue = b > r and b > g
        gray = abs(r - g) < 0.08 and abs(g - b) < 0.08
        if brown:
            label, conf = LABELS[0], 0.62
        elif blue:
            label, conf = LABELS[1], 0.58
        elif gray and mean.mean() < 0.45:
            label, conf = LABELS[2], 0.55
        else:
            label, conf = LABELS[5], 0.41
    except Exception:
        label, conf = LABELS[5], 0.3
    return {
        "mode": "demonstration",
        "title": "AI-assisted image triage",
        "classification": label,
        "confidence": round(conf * 100),
        "confidence_note": "Demonstration score only — not a calibrated probability.",
        "status": "Requires Human Review",
        "notice": "Possible hazard identified; human verification required. Not a confirmed hazard.",
        "model_version": "ImageTriage-demo-v0",
        "generated_at": utcnow().isoformat(),
    }


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt
