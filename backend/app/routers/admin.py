import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import require_roles
from ..models import AuditRecord, Incident, Notification, User, utcnow
from ..schemas import StatusPatch
from .incidents import serialize
router = APIRouter(prefix="/api/admin", tags=["admin"])
ALLOWED_STATUS = {"unverified", "under_review", "verified", "rejected", "flagged"}
@router.get("/reports")
def admin_reports(
    q: str | None = None,
    status: str | None = None,
    category: str | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("ADMIN", "MODERATOR")),
):
    query = db.query(Incident)
    if status:
        query = query.filter(Incident.verification_status == status)
    if category:
        query = query.filter(Incident.category == category)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (Incident.description.ilike(like))
            | (Incident.location_label.ilike(like))
            | (Incident.id.ilike(like))
        )
    rows = query.order_by(Incident.submitted_at.desc()).all()
    prioritized = sorted(
        rows,
        key=lambda i: (
            0 if i.verification_status == "unverified" else 1,
            0 if (i.ai_risk_category or "") in {"Higher", "Elevated"} else 1,
        ),
    )
    return {"items": [serialize(i) for i in prioritized], "total": len(rows)}
@router.patch("/reports/{report_id}/status")
def patch_status(
    report_id: str,
    body: StatusPatch,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("ADMIN", "MODERATOR")),
):
    inc = db.get(Incident, report_id)
    if not inc:
        raise HTTPException(404, "Report not found.")
    if body.verification_status not in ALLOWED_STATUS:
        raise HTTPException(400, "Invalid status.")
    prev = {"status": inc.verification_status, "category": inc.category, "notes": inc.reviewer_notes}
    inc.verification_status = body.verification_status
    if body.reviewer_notes is not None:
        inc.reviewer_notes = body.reviewer_notes
    if body.category:
        inc.category = body.category
    inc.reviewed_by = user.id
    inc.updated_at = utcnow()
    db.add(
        AuditRecord(
            action="status_change",
            entity="incident",
            entity_id=inc.id,
            actor_id=user.id,
            previous_state=json.dumps(prev),
            new_state=json.dumps(
                {"status": inc.verification_status, "category": inc.category, "notes": inc.reviewer_notes}
            ),
        )
    )
    db.add(
        Notification(
            kind="status",
            title="Report status changed",
            body=f"Report {inc.id[:8]} is now {inc.verification_status}. This is an information notice, not an official alert.",
            is_official=False,
        )
    )
    db.commit()
    db.refresh(inc)
    return serialize(inc)