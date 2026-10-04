from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    email: str
    display_name: str | None = None


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str | None = None


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class IncidentOut(BaseModel):
    id: str
    category: str
    description: str
    latitude: float
    longitude: float
    location_label: str | None
    observed_at: datetime
    submitted_at: datetime
    source: str
    verification_status: str
    image_url: str | None
    reviewer_notes: str | None = None
    ai_image_label: str | None = None
    ai_image_confidence: float | None = None
    ai_risk_category: str | None = None
    last_updated: datetime | None = None

    class Config:
        from_attributes = True


class StatusPatch(BaseModel):
    verification_status: str
    reviewer_notes: str | None = None
    category: str | None = None


class RiskIn(BaseModel):
    latitude: float
    longitude: float
    rainfall_mm: float | None = None


class RouteIn(BaseModel):
    start: str
    destination: str
