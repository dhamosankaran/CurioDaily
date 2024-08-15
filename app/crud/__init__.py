# app/crud/__init__.py

from .crud_topic import create_topic, get_topics, get_topic, list_all_topics
from .crud_subscription import create_subscription, get_subscription_by_email
from .crud_newsletter import create_newsletter, get_recent_newsletters, get_newsletters_by_topic