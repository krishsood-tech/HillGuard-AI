from __future__ import annotations

import os
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image

from .config import get_settings

ALLOWED = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

if os.getenv("VERCEL") == "1":
    # Vercel Functions have a read-only app bundle; /tmp is writable but
    # temporary, so persistent uploads should use object storage.
    UPLOAD_DIR = Path("/tmp/hillguard-uploads")
else:
    UPLOAD_DIR = Path(__file__).resolve().parents[1] / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def save_image(file: UploadFile | None) -> str | None:
    if file is None or not file.filename:
        return None
    settings = get_settings()
    raw = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(raw) > max_bytes:
        raise HTTPException(400, f"Image exceeds {settings.max_upload_mb} MB.")
    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED:
        raise HTTPException(400, "Only JPG, JPEG, PNG and WEBP images are allowed.")
    ext = ALLOWED[content_type]
    name = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOAD_DIR / name
    dest.write_bytes(raw)
    try:
        with Image.open(dest) as img:
            img.verify()
    except Exception:
        dest.unlink(missing_ok=True)
        raise HTTPException(400, "Uploaded file is not a valid image.")
    return f"/uploads/{name}"
