import sys
import os
from dotenv import load_dotenv  # Add this import

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from jinja2 import Template


# Load environment variables
load_dotenv()

# Import settings after loading environment variables
from app.core.config import settings

# Create a database engine
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_subscriptions():
    with SessionLocal() as db:
        result = db.execute(text("SELECT id, email FROM subscriptions"))
        return result.fetchall()

def get_topic_ids(subscription_id):
    with SessionLocal() as db:
        result = db.execute(text("SELECT topic_id FROM subscription_topic WHERE subscription_id = :sub_id"),
                            {"sub_id": subscription_id})
        topic_ids = [row[0] for row in result.fetchall()]
        return topic_ids

def get_newsletter_content(topic_id):
    with SessionLocal() as db:
        result = db.execute(text("SELECT title, content FROM newsletters WHERE topic_id = :topic_id ORDER BY created_at DESC LIMIT 1"),
                            {"topic_id": topic_id})
        row = result.fetchone()
        if row:
            print(f"Newsletter content fetched for topic_id {topic_id}: {row[0][:50]}...")
            return row
        else:
            print(f"No newsletter content found for topic_id {topic_id}")
            return None

def create_html_content(newsletters):
    """
    Create HTML content for the email using a Jinja2 template.
    """
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
                max-width: 800 px;
                margin: 0 auto;
                padding: 20px;
            }
            .header {
                background-color: #ffffff;
                color: white;
                padding: 20px;
                text-align: center;
            }

            .content {
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                padding: 20px;
                margin-top: 20px;
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
        <div class="header">
            <h1>{{ subject }}</h1>
        </div>
        <div class="content">
            {% for newsletter in newsletters %}
                <h2>{{ newsletter.title }}</h2>
                {{ newsletter.content | safe }}
                <hr>
            {% endfor %}
        </div>
        <div class="footer">
            <p>You received this email because you're subscribed to CurioDaily. <a href="#">Unsubscribe</a></p>
        </div>
    </body>
    </html>
    """)
    
    return template.render(subject="CurioDaily: Your Daily Dose of Interesting", newsletters=newsletters)


def send_email(recipient, subject, newsletters):
    try:
        msg = MIMEMultipart()
        msg['From'] = settings.SENDER_EMAIL
        msg['To'] = recipient
        msg['Subject'] = subject

        # Create HTML content
        html_content = create_html_content(newsletters)
        msg.attach(MIMEText(html_content, 'html'))

        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SENDER_EMAIL, settings.SENDER_PASSWORD)
            server.send_message(msg)

        print(f"Email sent successfully to {recipient}")
    except Exception as e:
        print(f"Error sending email to {recipient}: {e}")

def main():
    subscriptions = get_subscriptions()
    print(f"Fetched {len(subscriptions)} subscriptions")

    for sub_id, email in subscriptions:
        print(f"\nProcessing subscription for {email} (ID: {sub_id}")

        topic_ids = get_topic_ids(sub_id)
        print(f"  Topic IDs for this subscription: {topic_ids}")

        newsletters = []

        for topic_id in topic_ids:
            print(f"  Fetching newsletter content for topic_id: {topic_id}")

            newsletter = get_newsletter_content(topic_id)

            if newsletter:
                title, content = newsletter
                print(f"    Newsletter found: {title[:50]}...")
                #newsletters.append({"title": title, "content": content})
                newsletters.append({"content": content})
            else:
                print(f"    No newsletter found for topic_id: {topic_id}")

        if newsletters:
            subject = "CurioDaily: Your Daily Dose of Interesting"
            print(f"  Sending email to {email}")
            send_email(email, subject, newsletters)
        else:
            print(f"  No content found for subscriber {email}")

if __name__ == "__main__":
    main()