# File: backend/app/main.py
# Fixed with correct middleware order and enhanced error handling
import os
import logging
import json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
# Add SQLAlchemy event listener for JSON serialization
from sqlalchemy import event
from sqlalchemy.engine import Engine
from app.api.api_v1.router import api_router
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add JSON serialization for SQLite
@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    # Serialize JSON data in parameters
    if parameters is not None:
        # Handle single parameter sets
        if not executemany:
            if isinstance(parameters, (list, tuple)):
                parameters = list(parameters)
                for i, param in enumerate(parameters):
                    if isinstance(param, (dict, list)):
                        parameters[i] = json.dumps(param)
            elif isinstance(parameters, dict):
                for key, value in list(parameters.items()):
                    if isinstance(value, (dict, list)):
                        parameters[key] = json.dumps(value)

app = FastAPI(
    title="PataBaseFiti API",
    description="Property marketplace for the Kenyan market",
    version="0.1.0",
    # Enable standard docs URL
    docs_url="/docs",
    redoc_url="/redoc",
)

# Set up CORS
if settings.BACKEND_CORS_ORIGINS:
    logger.info(f"Setting up CORS with origins: {settings.BACKEND_CORS_ORIGINS}")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Create uploads directory if it doesn't exist
os.makedirs(settings.UPLOAD_DIRECTORY, exist_ok=True)
properties_dir = os.path.join(settings.UPLOAD_DIRECTORY, "properties")
os.makedirs(properties_dir, exist_ok=True)
# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIRECTORY), name="uploads")

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Custom docs URL
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html(request: Request):
    return get_swagger_ui_html(
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=f"{settings.API_V1_STR}/oauth2-redirect",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )
# Add this middleware to backend/app/main.py
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Log the request path
    logger.info(f"Request: {request.method} {request.url.path}")
    
    # Process the request
    response = await call_next(request)
    
    # Log the response status
    logger.info(f"Response status: {response.status_code}")
    
    return response

@app.get("/api/check-image/{folder}/{filename}")
async def check_image(folder: str, filename: str):
    """Endpoint to check if an image exists on the server"""
    file_path = os.path.join(settings.UPLOAD_DIRECTORY, folder, filename)
    if os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
        return {
            "exists": True,
            "path": file_path,
            "size": file_size,
            "url": f"/uploads/{folder}/{filename}"
        }
    else:
        return {
            "exists": False,
            "path": file_path
        }
@app.on_event("startup")
def on_startup():
    logger.info("Application startup...")
    # Import here to avoid circular imports
    from app.db.database import engine, Base
    # Check if tables exist, create them if not
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        if not table_names:
            logger.info("Creating database tables...")
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created.")
    except Exception as e:
        logger.error(f"Error checking/creating database tables: {str(e)}")

@app.get("/api/debug/image-url/{path:path}")
async def debug_image_url(path: str):
    """
    Debug endpoint to check if an image exists and is accessible
    """
    # Construct the full path to the image
    full_path = os.path.join(settings.UPLOAD_DIRECTORY, path)
    
    # Check if the file exists
    exists = os.path.exists(full_path)
    
    # Get file info if it exists
    file_info = {}
    if exists:
        try:
            file_info = {
                "size": os.path.getsize(full_path),
                "created": os.path.getctime(full_path),
                "modified": os.path.getmtime(full_path),
                "is_file": os.path.isfile(full_path),
                "is_readable": os.access(full_path, os.R_OK),
            }
        except Exception as e:
            file_info = {"error": str(e)}
    
    # Return the debug info
    return {
        "requested_path": path,
        "full_path": full_path,
        "exists": exists,
        "access_url": f"/uploads/{path}",
        "file_info": file_info if exists else None,
    }


@app.get("/api/debug/check-static-files")
async def check_static_files():
    """
    Check static file serving configuration
    """
    upload_dir = settings.UPLOAD_DIRECTORY
    if not os.path.exists(upload_dir):
        logger.error(f"Upload directory does not exist: {upload_dir}")
        return {"error": f"Upload directory does not exist: {upload_dir}"}
        
    # Check permissions
    readable = os.access(upload_dir, os.R_OK)
    writable = os.access(upload_dir, os.W_OK)
    
    # Get all subdirectories
    subdirs = []
    try:
        subdirs = [d for d in os.listdir(upload_dir) if os.path.isdir(os.path.join(upload_dir, d))]
    except Exception as e:
        logger.error(f"Error listing upload directory: {str(e)}")
    
    # Count files in each subdirectory
    file_counts = {}
    for subdir in subdirs:
        subdir_path = os.path.join(upload_dir, subdir)
        try:
            files = [f for f in os.listdir(subdir_path) if os.path.isfile(os.path.join(subdir_path, f))]
            file_counts[subdir] = len(files)
        except Exception as e:
            logger.error(f"Error listing subdirectory {subdir}: {str(e)}")
            file_counts[subdir] = f"Error: {str(e)}"
    
    return {
        "upload_directory": upload_dir,
        "exists": os.path.exists(upload_dir),
        "readable": readable,
        "writable": writable,
        "subdirectories": subdirs,
        "file_counts": file_counts
    }

@app.get("/api/debug/list-property-images/{property_id}")
async def list_property_images(property_id: int):
    """
    List images for a specific property
    """
    property_dir = os.path.join(settings.UPLOAD_DIRECTORY, f"properties/{property_id}")
    
    if not os.path.exists(property_dir):
        return {
            "exists": False,
            "property_dir": property_dir,
            "message": "Property directory does not exist"
        }
        
    try:
        files = [f for f in os.listdir(property_dir) if os.path.isfile(os.path.join(property_dir, f))]
        file_details = []
        
        for f in files:
            file_path = os.path.join(property_dir, f)
            file_details.append({
                "filename": f,
                "size": os.path.getsize(file_path),
                "last_modified": os.path.getmtime(file_path),
                "url": f"/uploads/properties/{property_id}/{f}"
            })
            
        return {
            "exists": True,
            "property_dir": property_dir,
            "file_count": len(files),
            "files": file_details
        }
    except Exception as e:
        logger.error(f"Error listing property images: {str(e)}")
        return {
            "exists": True,
            "property_dir": property_dir,
            "error": str(e)
        }
    
@app.get("/api/placeholder-image", include_in_schema=False)
async def get_placeholder_image():
    """
    Returns a placeholder image URL for testing
    """
    # Check if placeholder image exists in public directory
    placeholder_path = os.path.join(settings.UPLOAD_DIRECTORY, "placeholder.jpg")
    if not os.path.exists(placeholder_path):
        # Create a placeholder image if it doesn't exist
        try:
            import requests
            from PIL import Image
            from io import BytesIO
            
            # Download a placeholder from a public service
            response = requests.get("https://via.placeholder.com/640x480.jpg?text=PataBasefiti+Property")
            img = Image.open(BytesIO(response.content))
            img.save(placeholder_path)
            logger.info(f"Created placeholder image at {placeholder_path}")
        except Exception as e:
            logger.error(f"Failed to create placeholder image: {e}")
            return {"error": "Failed to create placeholder", "url": None}
    
    return {"url": "/uploads/placeholder.jpg"}
@app.get("/", tags=["status"])
async def root():
    return {"message": "Welcome to PataBaseFiti API. Go to /docs for documentation."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", port=8000, reload=True)