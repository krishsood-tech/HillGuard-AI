from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import get_current_user
from ..models import User
from ..schemas import LoginIn, RegisterIn, TokenOut
from ..security import create_access_token, hash_password, verify_password
router = APIRouter(prefix="/api/auth", tags=["auth"])
@router.post("/register", response_model=TokenOut)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email.lower()).first():
        raise HTTPException(400, "An account with this email already exists.")
    user = User(
        email=body.email.lower(),
        password_hash=hash_password(body.password),
        role="USER",
        display_name=body.display_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenOut(
        access_token=create_access_token(user.id, user.role),
        role=user.role,
        email=user.email,
        display_name=user.display_name,
    )
@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.lower()).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password.")
    return TokenOut(
        access_token=create_access_token(user.id, user.role),
        role=user.role,
        email=user.email,
        display_name=user.display_name,
    )
@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "role": user.role, "display_name": user.display_name}