
# Update app/models/__init__.py
from app.models.topic import Topic
from app.models.subscription import Subscription, subscription_topic
from app.models.newsletter import Newsletter
from app.models.user import User
from app.models.blog_post import BlogPost, BlogPostLike
from app.models.weekly_newsletter import WeeklyNewsletter
from app.models.weekly_newsletter_topic import WeeklyNewsletterTopic

__all__ = [
    "Topic",
    "Subscription",
    "subscription_topic",
    "Newsletter",
    "User",
    "BlogPost",
    "BlogPostLike",
    "WeeklyNewsletter",
    "WeeklyNewsletterTopic"
]