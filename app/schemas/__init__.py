#app/schemas/__init__.py

from .topic import Topic, TopicCreate
from .newsletter import Newsletter, NewsletterCreate, NewsletterUpdate
from .subscription import Subscription, SubscriptionCreate
from .weekly_newsletter import WeeklyNewsletter, WeeklyNewsletterCreate, WeeklyNewsletterUpdate
from .blog_post import BlogPost, BlogPostCreate, BlogPostUpdate



from .weekly_newsletter_topic import WeeklyNewsletterTopic, WeeklyNewsletterTopicCreate, WeeklyNewsletterTopicUpdate

# Add any other schema imports here

__all__ = [
    "Topic", "TopicCreate",
    "Newsletter", "NewsletterCreate", "NewsletterUpdate",
    "Subscription", "SubscriptionCreate",
    "WeeklyNewsletter", "WeeklyNewsletterCreate", "WeeklyNewsletterUpdate",
    "WeeklyNewsletterTopic", "WeeklyNewsletterTopicCreate", "WeeklyNewsletterTopicUpdate",
    "BlogPost", "BlogPostCreate", "BlogPostUpdate",
    "BlogPostLike", "BlogPostLikeCreate", "BlogPostLikeDetail"
]