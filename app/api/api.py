# app/api/api.py

import logging
from fastapi import APIRouter
from app.api.endpoints import topics, newsletters, subscriptions

# Set up logging
logger = logging.getLogger(__name__)

api_router = APIRouter()

# Include router for topics
try:
    api_router.include_router(topics.router, prefix="/topics", tags=["topics"])
    logger.info("Topics router included successfully")
except Exception as e:
    logger.error(f"Failed to include topics router: {str(e)}", exc_info=True)

# Include router for newsletters
try:
    api_router.include_router(newsletters.router, prefix="/newsletters", tags=["newsletters"])
    logger.info("Newsletters router included successfully")
except Exception as e:
    logger.error(f"Failed to include newsletters router: {str(e)}", exc_info=True)

# Include router for subscriptions
try:
    api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])
    logger.info("Subscriptions router included successfully")
except Exception as e:
    logger.error(f"Failed to include subscriptions router: {str(e)}", exc_info=True)

logger.info("All routers have been included in the API router")