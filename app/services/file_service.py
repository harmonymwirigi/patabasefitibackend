# File: backend/app/services/file_service.py
# Status: COMPLETE
# Dependencies: fastapi, fastapi.uploadfile, app.core.config

import os
import shutil
from typing import List
from fastapi import UploadFile, HTTPException
from app.core.config import settings
import uuid

def validate_image(file: UploadFile) -> bool:
    """
    Validate if the file is an allowed image type.
    """
    return file.content_type in settings.ALLOWED_IMAGE_TYPES

def save_upload(file: UploadFile, folder: str = "general") -> str:
    """
    Save uploaded file to disk and return the file path.
    """
    if not validate_image(file):
        raise HTTPException(
            status_code=400, 
            detail="File type not allowed. Allowed types: " + ", ".join(settings.ALLOWED_IMAGE_TYPES)
        )
    
    # Create folder if it doesn't exist
    folder_path = os.path.join(settings.UPLOAD_DIRECTORY, folder)
    os.makedirs(folder_path, exist_ok=True)
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # Save file
    file_path = os.path.join(folder_path, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Return relative path for database storage
    relative_path = os.path.join("uploads", folder, unique_filename)
    return relative_path

def save_multiple_uploads(files: List[UploadFile], folder: str = "general") -> List[str]:
    """
    Save multiple uploaded files and return their paths.
    """
    paths = []
    for file in files:
        path = save_upload(file, folder)
        paths.append(path)
    return paths

def delete_file(file_path: str) -> bool:
    """
    Delete a file from disk.
    """
    # Remove 'uploads/' prefix if present
    if file_path.startswith("uploads/"):
        file_path = file_path[8:]
    
    full_path = os.path.join(settings.UPLOAD_DIRECTORY, file_path)
    
    try:
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False
    except:
        return False