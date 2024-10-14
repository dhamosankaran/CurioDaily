# app/utils/sitemap_generator.py

from sqlalchemy.orm import Session
from app import crud
from app.core.config import settings
from datetime import datetime

def generate_sitemap(db: Session) -> str:
    """
    Generate a sitemap XML for the website.
    
    Args:
        db (Session): The database session.
    
    Returns:
        str: The sitemap XML content.
    """
    base_url = settings.BASE_URL
    current_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+00:00")

    # Start the sitemap XML
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

    # Add the homepage
    sitemap += f'  <url>\n    <loc>{base_url}/</loc>\n    <lastmod>{current_time}</lastmod>\n    <changefreq>daily</changefreq>\n    <priority>1.0</priority>\n  </url>\n'

    # Add topic pages
    topics = crud.get_topics(db)
    for topic in topics:
        sitemap += f'  <url>\n    <loc>{base_url}/topic/{topic.id}</loc>\n    <lastmod>{current_time}</lastmod>\n    <changefreq>weekly</changefreq>\n    <priority>0.8</priority>\n  </url>\n'

    # Add recent newsletters
    newsletters = crud.get_recent_newsletters(db, days=30)
    for newsletter in newsletters:
        sitemap += f'  <url>\n    <loc>{base_url}/newsletter/{newsletter.id}</loc>\n    <lastmod>{newsletter.created_at.strftime("%Y-%m-%dT%H:%M:%S+00:00")}</lastmod>\n    <changefreq>monthly</changefreq>\n    <priority>0.6</priority>\n  </url>\n'

    # Close the sitemap XML
    sitemap += '</urlset>'

    return sitemap