# app/api/api.py

import logging
from fastapi import Request  # Add at the top of the file
from fastapi import APIRouter
from app.api.endpoints import (
    topics,
    newsletters,
    subscriptions,
    analytics,
    weekly_newsletter,
    weekly_newsletter_topics,
    blog_posts,
)



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


# Include router for weekly_newsletter
try:
    api_router.include_router(weekly_newsletter.router, prefix="/weekly-newsletter", tags=["weekly newsletter"])
    logger.info("weekly_newsletter router included successfully")
except Exception as e:
    logger.error(f"Failed to include weekly_newsletter router: {str(e)}", exc_info=True)

try:
    api_router.include_router(
        blog_posts.router,
        prefix="/blog",
        tags=["blog"]
    )
    logger.info("Blog posts router included successfully")
except Exception as e:
    logger.error(f"Failed to include blog posts router: {str(e)}", exc_info=True)




# Include router for weekly_newsletter_topics
try:
    api_router.include_router(weekly_newsletter_topics.router, prefix="/weekly-newsletter-topics", tags=["weekly newsletter topics"])
    logger.info("weekly_newsletter_topics router included successfully")
except Exception as e:
    logger.error(f"Failed to include weekly_newsletter_topics router: {str(e)}", exc_info=True)



# Include router for analytics
try:
    #api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
    api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
    logger.info("Analytics router included successfully")
except Exception as e:
    logger.error(f"Failed to include analytics router: {str(e)}", exc_info=True)

logger.info(f"API routes configured: {[route.path for route in api_router.routes]}")

logger.info("All routers have been included in the API router")

