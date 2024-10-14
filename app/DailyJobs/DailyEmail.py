import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from jinja2 import Template
import logging
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import settings
from app.core.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create a database engine
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def configure_api_client():
    """Configure the Brevo API client with the API key from settings."""
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = settings.EMAIL_API
    return sib_api_v3_sdk.ApiClient(configuration)

def get_latest_newsletters():
    """Fetch the latest newsletter for each topic from the database."""
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
    """Fetch active subscriptions for given subscription IDs."""
    with SessionLocal() as db:
        result = db.execute(text("""
            SELECT id, email 
            FROM subscriptions 
            WHERE id = ANY(:sub_ids) AND is_active = TRUE
        """), {"sub_ids": subscription_ids})
        return result.fetchall()

def create_html_content(newsletter, sub_id):
    """Create HTML content for the email using a template."""
    unsubscribe_url = f"{settings.BASE_URL}/api/subscriptions/{sub_id}/unsubscribe"
    
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

def send_email(api_instance, recipient, subject, newsletter, sub_id):
    """Send an email to a recipient using Brevo API."""
    try:
        html_content = create_html_content(newsletter, sub_id)
        
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": recipient}],
            subject=subject,
            html_content=html_content,
            sender={"name": "Curio Daily Newsletter", "email": settings.SENDER_EMAIL}
        )
        
        api_response = api_instance.send_transac_email(send_smtp_email)
        logger.info(f"Email sent successfully to {recipient} (ID: {sub_id})")
        return api_response
    except ApiException as e:
        logger.error(f"Error sending email to {recipient}: {e}")

def main():
    """Main function to distribute newsletters."""
    # Configure API client
    api_client = configure_api_client()
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(api_client)
    
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
            send_email(api_instance, email, subject, newsletter_content, sub_id)

    logger.info("Newsletter distribution complete.")

if __name__ == "__main__":
    main()