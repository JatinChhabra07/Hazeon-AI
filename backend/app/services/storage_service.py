"""
File Storage Service — handles file uploads to local storage.
In production, swap to AWS S3 / Cloudflare R2.
"""
import os
import uuid
import shutil
from datetime import datetime
from fastapi import UploadFile

from app.config import settings


def save_upload(file: UploadFile, subfolder: str = "submissions") -> str:
    """
    Save an uploaded file to the uploads directory.
    Returns the relative file path.
    """
    # Create date-based subdirectory
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    upload_dir = os.path.join(settings.UPLOAD_DIR, subfolder, date_str)
    os.makedirs(upload_dir, exist_ok=True)

    # Generate unique filename
    ext = os.path.splitext(file.filename)[1] if file.filename else ".pdf"
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(upload_dir, unique_name)

    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return file_path


def get_file_type(filename: str) -> str:
    """Determine file type from filename."""
    ext = os.path.splitext(filename)[1].lower()
    type_map = {
        ".pdf": "pdf",
        ".jpg": "jpg",
        ".jpeg": "jpg",
        ".png": "png",
        ".bmp": "bmp",
        ".tiff": "tiff",
    }
    return type_map.get(ext, "unknown")


def delete_file(file_path: str) -> bool:
    """Delete a file from storage."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception:
        pass
    return False
