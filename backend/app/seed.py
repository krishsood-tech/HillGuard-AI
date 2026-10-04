from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from .config import get_settings
from .geo import nearest_place
from .models import ExternalObservation, Incident, ModelOutput, Notification, User, utcnow, uuid_str
from .security import hash_password

CATEGORIES = [
    "landslide",
    "flood",
    "heavy_rain",
    "falling_rocks",
    "road_blockage",
    "damaged_road",
    "waterlogging",
    "other",
]


def seed_if_empty(db: Session) -> None:
    if db.query(User).count() > 0:
        return
    now = utcnow()
    admin = User(
        email="admin@hillguard.local",
        password_hash=hash_password("HillGuardAdmin123!"),
        role="ADMIN",
        display_name="HillGuard Admin",
    )
    mod = User(
        email="moderator@hillguard.local",
        password_hash=hash_password("HillGuardMod123!"),
        role="MODERATOR",
        display_name="HillGuard Moderator",
    )
    user = User(
        email="user@hillguard.local",
        password_hash=hash_password("HillGuardUser123!"),
        role="USER",
        display_name="Community Reporter",
    )
    db.add_all([admin, mod, user])
    db.flush()

    samples = [
        ("landslide", 31.72, 76.94, "Debris movement reported above NH near Mandi.", "verified", "community", 2),
        ("road_blockage", 31.71, 76.95, "Traffic delayed due to fallen trees after rainfall.", "unverified", "community", 4),
        ("heavy_rain", 31.1048, 77.1734, "Intense rainfall observed in central Shimla.", "verified", "community", 1),
        ("falling_rocks", 31.12, 77.16, "Loose rocks noted on hillside stretch.", "under_review", "community", 6),
        ("flood", 32.22, 76.32, "Surface water accumulation near Dharamshala access road.", "verified", "community", 8),
        ("waterlogging", 32.10, 76.27, "Low-lying stretch waterlogged after overnight rain.", "unverified", "community", 3),
        ("damaged_road", 32.24, 77.19, "Pavement cracks and edge failure reported near Manali.", "verified", "community", 10),
        ("road_blockage", 32.25, 77.18, "Temporary obstruction from construction debris.", "flagged", "community", 5),
        ("landslide", 31.96, 77.11, "Slope material on carriageway, Kullu belt.", "verified", "community", 12),
        ("falling_rocks", 31.95, 77.12, "Small rockfall traces on inner verge.", "unverified", "community", 7),
        ("heavy_rain", 30.90, 77.10, "Continuous rainfall reported in Solan.", "verified", "community", 2),
        ("other", 30.91, 77.08, "Visibility reduced; conditions not visually confirmed.", "rejected", "community", 20),
        ("landslide", 32.55, 76.13, "Hill cut showing fresh erosion, Chamba.", "under_review", "community", 9),
        ("flood", 32.54, 75.97, "Stream overflow concern near Dalhousie approach.", "unverified", "community", 14),
        ("damaged_road", 32.53, 75.98, "Potholes and shoulder collapse after rain.", "verified", "community", 18),
        ("road_blockage", 31.34, 76.76, "Parked machinery narrowing roadway, Bilaspur area.", "unverified", "community", 11),
        ("heavy_rain", 31.686, 76.521, "Heavy showers in Hamirpur district.", "verified", "community", 3),
        ("waterlogging", 31.47, 76.27, "Standing water on Una-side link road.", "verified", "community", 16),
        ("falling_rocks", 31.70, 76.93, "Loose stones along cut slope, Mandi south.", "verified", "community", 1),
        ("landslide", 31.73, 76.91, "Second report of debris near same Mandi corridor.", "unverified", "community", 2),
        ("other", 32.21, 76.32, "Unconfirmed slope noise reported by travellers.", "unverified", "community", 22),
        ("flood", 31.11, 77.18, "Nallah running high below Shimla ridge.", "under_review", "community", 5),
    ]

    incidents = []
    for cat, lat, lng, desc, status, source, hours in samples:
        inc = Incident(
            category=cat,
            description=desc,
            latitude=lat,
            longitude=lng,
            location_label=nearest_place(lat, lng) + ", Himachal Pradesh",
            observed_at=now - timedelta(hours=hours),
            submitted_at=now - timedelta(hours=hours - 0.2 if hours > 1 else 0),
            source=source,
            verification_status=status,
            submitter_id=user.id,
            ai_risk_category=_demo_risk(cat, hours),
        )
        incidents.append(inc)
        db.add(inc)

    db.flush()

    db.add(
        ModelOutput(
            latitude=31.7084,
            longitude=76.9320,
            target="area_risk",
            time_window="6h",
            category="Elevated",
            uncertainty="high",
            model_version="Risk Model v1.0-demo",
            input_coverage="Limited",
            explanation_json=json.dumps(
                {
                    "factors": ["Recent rainfall proxy", "Nearby historical incidents"],
                    "notice": "This is an experimental decision-support indicator and is not an official warning.",
                }
            ),
            is_demo=True,
        )
    )

    db.add(
        ExternalObservation(
            source="Demo weather (labeled)",
            observation_type="weather",
            location_label="Mandi, Himachal Pradesh",
            latitude=31.7084,
            longitude=76.9320,
            observed_at=now - timedelta(minutes=25),
            retrieved_at=now,
            value_json=json.dumps({"temperature_c": 16.2, "humidity": 78, "wind_kmh": 12, "condition": "Rain"}),
            units="mixed",
            source_url=None,
            license="Demo sample for academic use",
            quality_flag="demo",
            is_demo=True,
        )
    )

    db.add_all(
        [
            Notification(
                kind="info",
                title="Demo data loaded",
                body="HillGuard AI is running with clearly labeled demonstration incidents for Himachal Pradesh.",
                is_official=False,
            ),
            Notification(
                kind="stale",
                title="Data freshness reminder",
                body="Always check observation times. Absence of reports does not mean conditions are safe.",
                is_official=False,
            ),
            Notification(
                kind="status",
                title="Not an official warning system",
                body="Follow IMD, NDMA and Himachal SDMA for official instructions. HillGuard AI is an academic prototype.",
                is_official=False,
            ),
        ]
    )
    db.commit()

    settings = get_settings()
    note = Path(__file__).resolve().parents[2] / "seed" / "README.md"
    note.parent.mkdir(parents=True, exist_ok=True)
    if not note.exists():
        note.write_text(
            "Seed incidents are inserted on first backend start when the database is empty.\n"
            f"DEMO_MODE={settings.demo_mode}\n",
            encoding="utf-8",
        )


def _demo_risk(category: str, hours: int) -> str:
    if category in {"landslide", "flood"} and hours <= 6:
        return "Elevated"
    if category in {"road_blockage", "falling_rocks", "heavy_rain"}:
        return "Moderate"
    return "Lower"
