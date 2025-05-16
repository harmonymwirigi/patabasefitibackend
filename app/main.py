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

@app.get("/", tags=["status"])
async def root():
    return {"message": "Welcome to PataBaseFiti API. Go to /docs for documentation."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", port=8001, reload=True)