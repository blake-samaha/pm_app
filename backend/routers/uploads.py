"""File uploads router."""
import os
import structlog
from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, HTTPException, UploadFile, File, status

from dependencies import CogniterUser

logger = structlog.get_logger()

router = APIRouter(
    prefix="/uploads",
    tags=["uploads"],
)

# Configuration
UPLOAD_DIR = Path("uploads")
LOGO_DIR = UPLOAD_DIR / "logos"
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB


def ensure_upload_dirs():
    """Ensure upload directories exist."""
    LOGO_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/logo")
async def upload_logo(
    current_user: CogniterUser,
    file: UploadFile = File(...),
) -> dict:
    """
    Upload a project logo image.
    
    - Only Cogniters can upload logos
    - Accepts: JPEG, PNG, GIF, WebP
    - Max size: 2MB
    - Returns the URL path to access the uploaded file
    """
    ensure_upload_dirs()
    
    # Validate file type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_IMAGE_TYPES)}"
        )
    
    # Read file content
    content = await file.read()
    
    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024 * 1024)}MB"
        )
    
    # Generate unique filename
    original_extension = Path(file.filename).suffix.lower() if file.filename else ".png"
    # Ensure extension is valid
    if original_extension not in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
        original_extension = ".png"
    
    filename = f"{uuid4()}{original_extension}"
    filepath = LOGO_DIR / filename
    
    # Save file
    try:
        with open(filepath, "wb") as f:
            f.write(content)
        
        logger.info(
            "Logo uploaded successfully",
            filename=filename,
            size=len(content),
            content_type=file.content_type,
            user_id=str(current_user.id)
        )
        
        # Return the URL path (relative to static mount)
        return {"url": f"/uploads/logos/{filename}"}
    
    except Exception as e:
        logger.error("Failed to save uploaded file", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded file"
        )


@router.delete("/logo/{filename}")
async def delete_logo(
    filename: str,
    current_user: CogniterUser,
) -> dict:
    """
    Delete a previously uploaded logo.
    
    Only Cogniters can delete logos.
    """
    # Sanitize filename to prevent directory traversal
    safe_filename = Path(filename).name
    filepath = LOGO_DIR / safe_filename
    
    if not filepath.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    try:
        os.remove(filepath)
        logger.info(
            "Logo deleted",
            filename=safe_filename,
            user_id=str(current_user.id)
        )
        return {"message": "File deleted successfully"}
    except Exception as e:
        logger.error("Failed to delete file", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file"
        )

