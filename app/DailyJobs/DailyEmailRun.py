import sys
import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from jinja2 import Template
import logging
from collections import defaultdict

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Load environment variables
load_dotenv()

# Import settings after loading environment variables
from app.core.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create a database engine
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

baseUrl = settings.BASE_URL

def get_latest_newsletters():
    """
    Fetch the latest newsletter for each topic from the database.
    """
    with SessionLocal() as db:
        result = db.execute(text("""
            SELECT DISTINCT ON (topic_id) id, title, email_content, topic_id, subscription_ids
            FROM newsletters 
            WHERE subscription_ids IS NOT NULL 
            AND subscription_ids != ''
            ORDER BY topic_id, created_at DESC
        """))
        return result.fetchall()

def get_subscriptions():
    """
    Fetch all active subscriptions with their associated topics.
    """
    with SessionLocal() as db:
        result = db.execute(text("""
            SELECT s.id, s.email, array_agg(st.topic_id) as topic_ids
            FROM subscriptions s
            JOIN subscription_topic st ON s.id = st.subscription_id
            WHERE s.is_active = TRUE
            GROUP BY s.id, s.email
        """))
        return result.fetchall()

def create_html_content(newsletters, sub_id):
    """
    Create HTML content for the email using a template.
    """
    unsubscribe_url = f"{baseUrl}/api/subscriptions/{sub_id}/unsubscribe"
    
    template = Template("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                margin: 0;
                padding: 0;
                background-color: #f4f4f4;
            }
            .content {
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                padding: 20px;
                margin-top: 20px;
                width: 70%;
                margin-left: auto;
                margin-right: auto;
            }
            .footer {
                text-align: center;
                margin-top: 20px;
                font-size: 0.8em;
                color: #666;
            }
        </style>
    </head>
    <body>
        <div class="content">
            {% for newsletter in newsletters %}
                <h2>{{ newsletter.title }}</h2>
                {{ newsletter.content | safe }}
                <hr>
            {% endfor %}
        </div>
        <div class="footer">
            <p>You received this email because you're subscribed to CurioDaily. © 2024 CurioDaily. All rights reserved.
            <a href="{{ unsubscribe_url }}">Unsubscribe</a>
            </p>
        </div>
    </body>
    </html>
    """)
    
    return template.render(
        newsletters=newsletters,
        unsubscribe_url=unsubscribe_url)

def send_email(recipient, subject, newsletters, sub_id):
    """
    Send an email to a recipient.
    """
    try:
        msg = MIMEMultipart()
        msg['From'] = settings.SENDER_EMAIL
        msg['To'] = recipient
        msg['Subject'] = subject

        logger.info(f"Sending consolidated email to {recipient} (ID: {sub_id})")
        html_content = create_html_content(newsletters, sub_id)
        msg.attach(MIMEText(html_content, 'html'))

        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SENDER_EMAIL, settings.SENDER_PASSWORD)
            server.send_message(msg)

        logger.info(f"Consolidated email sent successfully to {recipient}")
    except Exception as e:
        logger.error(f"Error sending consolidated email to {recipient}: {e}")

def main():
    """
    Main function to distribute consolidated newsletters.
    """
    latest_newsletters = get_latest_newsletters()
    
    if not latest_newsletters:
        logger.info("No newsletters found.")
        return

    # Create a dictionary of newsletters by topic_id
    newsletters_by_topic = {newsletter[3]: {"id": newsletter[0], "title": newsletter[1], "content": newsletter[2]} for newsletter in latest_newsletters}

    # Get all active subscriptions
    subscriptions = get_subscriptions()

    # Create a dictionary to store newsletters for each subscriber
    subscriber_newsletters = defaultdict(list)

    for sub_id, email, topic_ids in subscriptions:
        for topic_id in topic_ids:
            if topic_id in newsletters_by_topic:
                subscriber_newsletters[email].append((sub_id, newsletters_by_topic[topic_id]))

    # Send consolidated emails
    for email, newsletters_with_sub_id in subscriber_newsletters.items():
        if newsletters_with_sub_id:
            sub_id = newsletters_with_sub_id[0][0]  # Use the first sub_id (should be the same for all)
            newsletters = [n[1] for n in newsletters_with_sub_id]  # Extract just the newsletter data
            subject = f"CurioDaily: Your Personalized Newsletter"
            send_email(email, subject, newsletters, sub_id)

    logger.info("Consolidated newsletter distribution complete.")

if __name__ == "__main__":
    main()