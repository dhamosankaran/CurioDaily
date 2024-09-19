import sys
import os
import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi import Path
import uvicorn
from sqlalchemy.orm import Session
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import RedirectResponse



# Adjust the path to ensure imports work correctly
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)  # This should now point to the project root
sys.path.insert(0, project_root)

from app.api.api import api_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.api import deps
from app.crud.crud_topic import seed_initial_topics
from app import crud

logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# SSL configuration
ssl_dir = os.path.join(project_root, "ssl")
ssl_keyfile = os.path.join(ssl_dir, "key.pem")
ssl_certfile = os.path.join(ssl_dir, "cert.pem")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application is starting up")
    if not os.path.exists(ssl_keyfile) or not os.path.exists(ssl_certfile):
        logger.info(f"SSL certificate files not found. Running without SSL. Project root: {project_root}")
    db = SessionLocal()
    try:
        seed_initial_topics(db)
        logger.info("Initial topics seeded successfully")
    except Exception as e:
        logger.error(f"Error seeding initial topics: {str(e)}")
    finally:
        db.close()
    yield
    logger.info("Application is shutting down")

# Create database tables
Base.metadata.create_all(bind=engine)
logger.info("Database tables created")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"/api/openapi.json",
    lifespan=lifespan
)

app.include_router(api_router, prefix="/api")
logger.info("API router included")

# CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    try:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                "https://autonomous-newsletter-457954888435.us-central1.run.app",
                "http://autonomous-newsletter-457954888435.us-central1.run.app",
                "http://localhost:8080",
                "https://localhost:8080",
                "http://127.0.0.1:8080",
                "https://127.0.0.1:8080"
            ],
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE"],
            allow_headers=["*"],
        )


        logger.info(f"CORS middleware added with origins: {settings.BACKEND_CORS_ORIGINS}")
    except Exception as e:
        logger.error(f"Failed to add CORS middleware: {str(e)}")
else:
    logger.warning("No CORS origins specified. CORS middleware not added.")


# Static files setup
static_dir = os.path.join(current_dir, "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
    logger.info(f"Created static directory at {static_dir}")
#app.mount("/static", StaticFiles(directory=static_dir), name="static")
app.mount("/static", StaticFiles(directory=static_dir, html=True), name="static")

@app.get("/unsubscribe-confirmation")
async def unsubscribe_confirmation(id: int):
    return {"message": f"You have been unsubscribed. Subscription ID: {id}"}

from fastapi import Path

@app.api_route("/api/subscriptions/{subscription_id}/unsubscribe", methods=["GET", "PUT"])
async def unsubscribe(
    request: Request,
    subscription_id: int = Path(...),
    db: Session = Depends(deps.get_db)
):
    try:
        db_subscription = crud.update_subscription_status(db, subscription_id=subscription_id, is_active=False)
        if db_subscription is None:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        if request.method == "GET":
            return RedirectResponse(url=f"{settings.BASE_URL}/?unsubscribe=success")
        
        return {"message": "Successfully unsubscribed"}
    except Exception as e:
        logger.error(f"Error unsubscribing: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while unsubscribing")

@app.get("/health")
async def health_check(db: Session = Depends(deps.get_db)):
    try:
        db.execute("SELECT 1")
        logger.info("Health check passed")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "unhealthy", "database": "disconnected"}
        )

@app.get("/")
async def read_root():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        logger.error(f"index.html not found at {index_path}")
        raise HTTPException(status_code=404, detail="index.html not found")

@app.get("/favicon.ico")
async def favicon():
    favicon_path = os.path.join(static_dir, "favicon.ico")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    else:
        logger.warning(f"Favicon not found at {favicon_path}")
        raise HTTPException(status_code=404, detail="Favicon not found")

@app.get("/debug/cors")
async def debug_cors():
    return {"CORS_ORIGINS": settings.BACKEND_CORS_ORIGINS}

@app.get("/debug/settings")
async def debug_settings():
    return {
        "BACKEND_CORS_ORIGINS": settings.BACKEND_CORS_ORIGINS,
        "ENVIRONMENT": settings.ENVIRONMENT,
        "DATABASE_URL": settings.DATABASE_URL,
        # Add other non-sensitive settings here
    }





@app.exception_handler(404)
async def custom_404_handler(request: Request, exc: Exception):
    logger.warning(f"404 error for path: {request.url.path}")
    return JSONResponse({"detail": "Not found"}, status_code=404)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred."}
    )

if settings.ENVIRONMENT != "development":
    #app.add_middleware(HTTPSRedirectMiddleware)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["autonomous-newsletter-457954888435.us-central1.run.app"])


@app.middleware("http")
async def add_request_id_header(request: Request, call_next):
    request_id = str(uuid.uuid4())
    logger.info(f"Request {request_id}: {request.method} {request.url}")
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    logger.info(f"Response {request_id}: Status {response.status_code}")
    return response

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = "upgrade-insecure-requests"
    return response

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Received request: {request.method} {request.url}")
    #logger.info(f"Headers: {request.headers}")
    response = await call_next(request)
    #logger.info(f"Response status: {response.status_code}")
    #logger.info(f"Response headers: {response.headers}")
    return response

def run_server():
    environment = os.getenv("ENVIRONMENT", "development")
    logger.info(f"Running server in {environment} environment")
    
    if environment == "development":
        if not os.path.exists(ssl_keyfile) or not os.path.exists(ssl_certfile):
            logger.warning("SSL certificate files not found. Running without SSL.")
            uvicorn.run(app, host="0.0.0.0", port=8080, reload=True)
        else:
            logger.info("Running with local HTTPS")
            uvicorn.run(
                app,
                host="0.0.0.0",
                port=8443,
                ssl_keyfile=ssl_keyfile,
                ssl_certfile=ssl_certfile,
                reload=True
            )
    elif environment == "docker":
        uvicorn.run(app, host="0.0.0.0", port=8080)
    else:  # GCP or any other environment
        port = int(os.getenv("PORT", 8080))
        uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    run_server()