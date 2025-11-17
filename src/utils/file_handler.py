import os
import uuid
from fastapi import UploadFile, HTTPException, status
from typing import Union
import uuid
from src.core.config import settings


def validate_file(file: UploadFile) -> None:
    """Validate file extension and size"""
    # Check file extension
    file_extension = file.filename.split(".")[-1].lower()  # type: ignore
    if file_extension not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )


def generate_unique_filename(original_filename: str) -> str:
    """Generate unique filename using UUID"""
    file_extension = original_filename.split(".")[-1].lower()
    unique_id = uuid.uuid4().hex
    return f"{unique_id}.{file_extension}"


async def save_upload_file(file: UploadFile, user_id: Union[uuid.UUID, str]) -> tuple:
    """Save uploaded file and return file info"""
    validate_file(file)

    # Create user-specific directory
    user_dir = os.path.join(settings.UPLOAD_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)

    # Generate unique filename
    unique_filename = generate_unique_filename(file.filename)  # type: ignore
    file_path = os.path.join(user_dir, unique_filename)

    # Save file
    file_size = 0
    with open(file_path, "wb") as buffer:
        content = await file.read()
        file_size = len(content)

        # Check file size
        if file_size > settings.MAX_UPLOAD_SIZE:
            os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE / (1024*1024)}MB"
            )

        buffer.write(content)

    return unique_filename, file_path, file_size


def delete_file(file_path: str) -> None:
    """Delete file from storage"""
    if os.path.exists(file_path):
        os.remove(file_path)
