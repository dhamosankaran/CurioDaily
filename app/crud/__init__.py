# app/crud/__init__.py

from .crud_topic import create_topic, get_topics, get_topic, list_all_topics
from .crud_subscription import create_subscription, get_subscription_by_email, update_subscription_status

# Import other CRUD functions as needed

from .crud_newsletter import (
    create_newsletter,
    get_newsletter,
    get_recent_newsletters,
    get_newsletters_by_topic,
    update_newsletter,
    delete_newsletter
)

# If you want to expose all functions directly, you can use:
# from .crud_newsletter import *

# Optionally, you can create an alias for the crud_newsletter module
from . import crud_newsletter