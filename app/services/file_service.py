# File: backend/app/services/file_service.py
import os
import uuid
import logging
from typing import List
from fastapi import UploadFile
from app.core.config import settings

logger = logging.getLogger(__name__)

def save_upload(upload_file: UploadFile, folder: str = "properties") -> str:
    """
    Save a single uploaded file to disk
    
    Args:
        upload_file: Uploaded file
        folder: Subfolder within uploads directory
        
    Returns:
        Relative path to saved file
    """
    # Make sure directory exists
    directory = os.path.join(settings.UPLOAD_DIRECTORY, folder)
    os.makedirs(directory, exist_ok=True)
    
    # Generate unique filename
    ext = os.path.splitext(upload_file.filename)[1].lower() if upload_file.filename else ".jpg"
    filename = f"{uuid.uuid4()}{ext}"
    
    # Full path to save the file
    file_path = os.path.join(directory, filename)
    
    logger.info(f"Saving file to: {file_path}")
    logger.info(f"Upload directory from settings: {settings.UPLOAD_DIRECTORY}")
    logger.info(f"Upload file content type: {upload_file.content_type}")
    
    # Save file
    try:
        contents = upload_file.file.read()
        logger.info(f"Read {len(contents)} bytes from uploaded file")
        
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Reset the file pointer for potential reuse
        upload_file.file.seek(0)
        
        # Return the relative path that will be accessible via URL
        relative_path = f"{folder}/{filename}"
        logger.info(f"File saved successfully as: {relative_path}")
        
        # Verify file existence after save
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            logger.info(f"Verified file exists at {file_path} with size {file_size} bytes")
        else:
            logger.error(f"File not found at {file_path} after save operation!")
            
        return relative_path
    except Exception as e:
        logger.error(f"Error saving file {upload_file.filename}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

def save_multiple_uploads(uploads: List[UploadFile], folder: str = "properties") -> List[str]:
    """
    Save multiple uploaded files to disk
    
    Args:
        uploads: List of uploaded files
        folder: Subfolder within uploads directory
        
    Returns:
        List of relative paths to saved files
    """
    logger.info(f"Saving {len(uploads)} files to folder: {folder}")
    
    saved_paths = []
    for i, upload in enumerate(uploads):
        try:
            logger.info(f"Processing file {i+1}/{len(uploads)}: {upload.filename}")
            path = save_upload(upload, folder)
            saved_paths.append(path)
        except Exception as e:
            logger.error(f"Error saving file in batch: {str(e)}")
            # Continue with other files even if one fails
    
    logger.info(f"Successfully saved {len(saved_paths)} files in {folder}")
    return saved_paths