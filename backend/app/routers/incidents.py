from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import get_current_user_optional
from ..geo import freshness_payload, haversine_km, nearest_place
from ..ml_service import analyze_risk, triage_image
from ..models import Incident, Notification, User, utcnow
from ..schemas import IncidentOut
from ..uploads import UPLOAD_DIR, save_image
router = APIRouter(prefix="/api/incidents", tags=["incidents"])
PUBLIC_STATUSES = {"unverified", "under_review", "verified", "flagged"}
def serialize(inc: Incident) -> dict:
    fresh = freshness_payload(inc.observed_at, inc.updated_at)
    return {
        "id": inc.id,
        "category": inc.category,
        "description": inc.description,
        "latitude": inc.latitude,
        "longitude": inc.longitude,
        "location_label": inc.location_label,
        "observed_at": inc.observed_at.isoformat() if inc.observed_at else None,
        "submitted_at": inc.submitted_at.isoformat() if inc.submitted_at else None,
        "source": inc.source,
        "source_kind": "COMMUNITY REPORT" if inc.source == "community" else inc.source.upper(),
        "verification_status": inc.verification_status,
        "image_url": inc.image_url,
        "reviewer_notes": inc.reviewer_notes,
        "ai_image_label": inc.ai_image_label,
        "ai_image_confidence": inc.ai_image_confidence,
        "ai_risk_category": inc.ai_risk_category,
        "last_updated": inc.updated_at.isoformat() if inc.updated_at else None,
        "freshness": fresh,
        "limitations": "Community reports may be incomplete, delayed, or incorrect until verified.",
    }
@router.get("")
def list_incidents(
    category: str | None = None,
    status: str | None = None,
    source: str | None = None,
    risk: str | None = None,
    location: str | None = None,
    hours: int | None = Query(default=None, ge=1, le=24 * 30),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(Incident).filter(Incident.verification_status.in_(PUBLIC_STATUSES))
    if category:
        q = q.filter(Incident.category == category)
    if status:
        q = q.filter(Incident.verification_status == status)
    if source:
        q = q.filter(Incident.source == source)
    if risk:
        q = q.filter(Incident.ai_risk_category == risk)
    if location:
        q = q.filter(Incident.location_label.ilike(f"%{location}%"))
    if hours:
        cutoff = utcnow() - timedelta(hours=hours)
        q = q.filter(Incident.observed_at >= cutoff)
    total = q.count()
    rows = (
        q.order_by(Incident.observed_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {"total": total, "page": page, "items": [serialize(i) for i in rows]}
@router.get("/nearby")
def nearby(
    lat: float,
    lng: float,
    km: float = 15,
    db: Session = Depends(get_db),
):
    rows = db.query(Incident).filter(Incident.verification_status.in_(PUBLIC_STATUSES)).all()
    items = [serialize(i) for i in rows if haversine_km(lat, lng, i.latitude, i.longitude) <= km]
    items.sort(key=lambda x: haversine_km(lat, lng, x["latitude"], x["longitude"]))
    return {"count": len(items), "items": items, "center": {"lat": lat, "lng": lng}, "radius_km": km}
@router.get("/{incident_id}")
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    inc = db.get(Incident, incident_id)
    if not inc or inc.verification_status == "rejected":
        raise HTTPException(404, "Incident not found.")
    return serialize(inc)
@router.post("")
async def create_incident(
    category: str = Form(...),
    description: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    observed_at: str = Form(...),
    location_label: str | None = Form(None),
    contact_ref: str | None = Form(None),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
):
    allowed_cats = {
        "landslide",
        "flood",
        "heavy_rain",
        "falling_rocks",
        "road_blockage",
        "damaged_road",
        "waterlogging",
        "other",
    }
    if category not in allowed_cats:
        raise HTTPException(400, "Invalid hazard type.")
    try:
        observed = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(400, "Invalid observed_at datetime.")
    image_url = await save_image(image)
    ai_img = None
    if image_url:
        local = UPLOAD_DIR / image_url.split("/")[-1]
        ai_img = triage_image(local)
    others = db.query(Incident).all()
    risk = analyze_risk(latitude, longitude, others, None)
    inc = Incident(
        category=category,
        description=description.strip(),
        latitude=latitude,
        longitude=longitude,
        location_label=location_label or f"{nearest_place(latitude, longitude)}, Himachal Pradesh",
        observed_at=observed,
        source="community",
        verification_status="unverified",
        image_url=image_url,
        contact_ref=contact_ref,
        submitter_id=user.id if user else None,
        ai_image_label=ai_img["classification"] if ai_img else None,
        ai_image_confidence=ai_img["confidence"] if ai_img else None,
        ai_risk_category=risk["risk_category"],
    )
    db.add(inc)
    db.add(
        Notification(
            kind="report",
            title="New community report submitted",
            body=f"{category.replace('_', ' ').title()} report is unverified and awaiting review.",
            is_official=False,
        )
    )
    db.commit()
    db.refresh(inc)
    return {
        "message": "Report submitted successfully.",
        "report_id": inc.id,
        "submitted_at": inc.submitted_at.isoformat(),
        "status": inc.verification_status,
        "ai_image": ai_img,
        "ai_risk": risk,
        "incident": serialize(inc),
    }