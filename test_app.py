# File: backend/test_app.py
# A minimal test FastAPI app to verify basic functionality

from fastapi import FastAPI, Depends, HTTPException, status, Form
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_app")

# Create test app
app = FastAPI(title="Test App")

# CORS configuration
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Test endpoints
@app.get("/")
def read_root():
    logger.info("Root endpoint called")
    return {"message": "Test app is running"}

@app.post("/login")
def login(username: str = Form(), password: str = Form()):
    logger.info(f"Login attempt for user: {username}")
    return {"access_token": "test_token", "token_type": "bearer"}

@app.post("/register")
def register(username: str = Form(), password: str = Form()):
    logger.info(f"Registration attempt for user: {username}")
    return {"id": 1, "username": username}

@app.get("/health")
def health():
    logger.info("Health check called")
    return {"status": "healthy"}

if __name__ == "__main__":
    logger.info("Starting test FastAPI app...")
    uvicorn.run("test_app:app", host="0.0.0.0", port=8001, reload=True)