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
            SELECT DISTINCT ON (topic_id) id, title, content, topic_id, subscription_ids
            FROM newsletters 
            WHERE subscription_ids IS NOT NULL 
            AND subscription_ids != ''
            ORDER BY topic_id, created_at DESC
        """))
        return result.fetchall()

def get_subscriptions(subscription_ids):
    """
    Fetch active subscriptions for given subscription IDs.
    """
    with SessionLocal() as db:
        result = db.execute(text("""
            SELECT id, email 
            FROM subscriptions 
            WHERE id = ANY(:sub_ids) AND is_active = TRUE
        """), {"sub_ids": subscription_ids})
        return result.fetchall()

def create_html_content(newsletter, sub_id):
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
            {{ newsletter.content | safe }}
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
        newsletter=newsletter,
        unsubscribe_url=unsubscribe_url)

def send_email(recipient, subject, newsletter, sub_id):
    """
    Send an email to a recipient.
    """
    try:
        msg = MIMEMultipart()
        msg['From'] = settings.SENDER_EMAIL
        msg['To'] = recipient
        msg['Subject'] = subject

        logger.info(f"Sending email to {recipient} (ID: {sub_id})")
        html_content = create_html_content(newsletter, sub_id)
        msg.attach(MIMEText(html_content, 'html'))

        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SENDER_EMAIL, settings.SENDER_PASSWORD)
            server.send_message(msg)

        logger.info(f"Email sent successfully to {recipient}")
    except Exception as e:
        logger.error(f"Error sending email to {recipient}: {e}")

def main():
    """
    Main function to distribute newsletters.
    """
    latest_newsletters = get_latest_newsletters()
    
    if not latest_newsletters:
        logger.info("No newsletters found with non-empty subscription_ids.")
        return

    for newsletter in latest_newsletters:
        newsletter_id, title, content, topic_id, subscription_ids = newsletter
        
        logger.info(f"Processing newsletter: {title} (ID: {newsletter_id}, Topic ID: {topic_id})")

        try:
            subscription_ids = [int(id.strip()) for id in subscription_ids.split(',') if id.strip()]
        except ValueError:
            logger.error(f"Error parsing subscription_ids for newsletter {newsletter_id}: {subscription_ids}")
            continue

        if not subscription_ids:
            logger.info(f"No valid subscription IDs found for newsletter {newsletter_id}")
            continue

        subscriptions = get_subscriptions(subscription_ids)
        logger.info(f"Fetched {len(subscriptions)} active subscriptions for newsletter {newsletter_id}")

        newsletter_content = {
            "title": title,
            "content": content
        }

        for sub_id, email in subscriptions:
            subject = f"CurioDaily: {title}"
            send_email(email, subject, newsletter_content, sub_id)

    logger.info("Newsletter distribution complete.")

if __name__ == "__main__":
    main()