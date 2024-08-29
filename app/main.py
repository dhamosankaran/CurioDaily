import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from app.api.api import api_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine


from app.db.session import SessionLocal
from app.crud.crud_topic import seed_initial_topics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)
logger.info("Database tables created")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"/api/openapi.json"
)

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.on_event("startup")
def startup_event():
    logger.info("Running startup event")
    db = SessionLocal()
    try:
        seed_initial_topics(db)
    finally:
        db.close()

app.include_router(api_router, prefix="/api")

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info(f"CORS middleware added with origins: {settings.BACKEND_CORS_ORIGINS}")

# Mount the static directory
app.mount("/static", StaticFiles(directory="static"), name="static")
logger.info("Static files mounted")

@app.get("/")
async def read_root():
    logger.info("Serving index.html")
    return FileResponse("static/index.html")

@app.get("/favicon.ico")
async def favicon():
    logger.info("Serving favicon.ico")
    return FileResponse("static/favicon.ico")

# Include the API router
app.include_router(api_router)
logger.info("API router included")

@app.exception_handler(404)
async def custom_404_handler(request: Request, exc: Exception):
    if request.url.path == "/favicon.ico":
        logger.info("Favicon not found, returning 204")
        return JSONResponse(status_code=204)  # No Content
    logger.warning(f"404 error for path: {request.url.path}")
    return JSONResponse({"detail": "Not found"}, status_code=404)

# Add middleware to log all requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # Default to 8080 if PORT env var is not set
    logger.info(f"Starting the application on port {port}")
    
    try:
        uvicorn.run(app, host="0.0.0.0", reload=True, log_level="info")
    except Exception as e:
        logger.error(f"Failed to start the application: {e}")
        