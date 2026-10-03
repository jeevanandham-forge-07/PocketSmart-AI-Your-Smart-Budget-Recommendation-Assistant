import os
import uuid
from pathlib import Path
from typing import Tuple, Optional
from fastapi import UploadFile, HTTPException
from PIL import Image
from app.config import settings


class ImageService:
    @staticmethod
    def validate_and_save_upload(upload_file: UploadFile) -> Tuple[str, Path]:
        """
        Validates an uploaded image and saves it safely.
        Returns:
            Tuple[str, Path]: (relative_url_path, absolute_file_path)
        """
        if not upload_file or not upload_file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        # 1. Check file extension
        ext = Path(upload_file.filename).suffix.lower()
        if ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
            allowed = ", ".join(settings.ALLOWED_IMAGE_EXTENSIONS)
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image format '{ext}'. Allowed formats: {allowed}"
            )

        # 2. Check MIME type
        content_type = upload_file.content_type or ""
        if not content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail=f"Uploaded file MIME type '{content_type}' is not a valid image."
            )

        # 3. Read content & check size
        try:
            content = upload_file.file.read()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read uploaded file: {str(e)}")

        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"Image size exceeds the maximum limit of {settings.MAX_UPLOAD_SIZE_MB}MB."
            )

        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        # 4. Verify image content with Pillow
        try:
            import io
            img = Image.open(io.BytesIO(content))
            img.verify()
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid or corrupted image data: {str(e)}"
            )

        # 5. Save with secure UUID filename
        filename = f"outfit_{uuid.uuid4().hex[:12]}{ext}"
        save_path = settings.UPLOAD_DIR / filename

        with open(save_path, "wb") as f:
            f.write(content)

        relative_url = f"/static/uploads/{filename}"
        return relative_url, save_path


image_service = ImageService()
