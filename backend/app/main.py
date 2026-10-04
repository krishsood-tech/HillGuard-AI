from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .config import get_settings
from .database import Base, SessionLocal, engine
from .routers import admin_router, auth_router, incidents_router, services_router
from .seed import seed_if_empty
from .uploads import UPLOAD_DIR

BACKEND = Path(__file__).resolve().parents[1]
(BACKEND / "data").mkdir(parents=True, exist_ok=True)
(BACKEND / "uploads").mkdir(parents=True, exist_ok=True)

settings = get_settings()
Base.metadata.create_all(bind=engine)
with SessionLocal() as db:
    seed_if_empty(db)

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="HillGuard AI API",
    description="Academic mountain hazard awareness prototype. Not an official warning system.",
    version="1.0.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(incidents_router)
app.include_router(admin_router)
app.include_router(services_router)

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "demo_mode": settings.demo_mode,
        "map_tile_url": settings.map_tile_url,
        "emergency": {
            "imd": settings.emergency_imd_url,
            "ndma": settings.emergency_ndma_url,
            "hpsdma": settings.emergency_hpsdma_url,
        },
        "disclaimer": (
            "HillGuard AI does not replace government warnings, emergency services, "
            "disaster-management authorities, official weather advisories, or local authorities."
        ),
    }
