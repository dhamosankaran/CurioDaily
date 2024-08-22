import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


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
        topic_ids = [row[0] for row in result.fetchall()]  # Convert the result to a list
        #print(f"topic_ids: {topic_ids}")  # Print the list of topic IDs
        return topic_ids

def get_newsletter_content(topic_id):
    with SessionLocal() as db:
        result = db.execute(text("SELECT title, content FROM newsletters WHERE topic_id = :topic_id ORDER BY created_at DESC LIMIT 1"),
                            {"topic_id": topic_id})
        row = result.fetchone()
        if row:
            print(f"Newsletter content fetched for topic_id {topic_id}: {row}")
            return row
        else:
            print(f"No newsletter content found for topic_id {topic_id}")
            return None

def send_email(recipient, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = settings.SENDER_EMAIL
        msg['To'] = recipient
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
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
        print(f"\nProcessing subscription for {email} (ID: {sub_id})")
        
        topic_ids = get_topic_ids(sub_id)
        print(f"  Topic IDs for this subscription: {topic_ids}")
        
        email_content = ""
        
        for topic_id in topic_ids:
            print(f"  Fetching newsletter content for topic_id: {topic_id}")
            
            newsletter = get_newsletter_content(topic_id)
            
            if newsletter:
                title, content = newsletter
                print(f"    Newsletter found: {title[:50]}...")
                email_content += f"{content}\n\n"
            else:
                print(f"    No newsletter found for topic_id: {topic_id}")
        
        if email_content:
            subject = "CurioDaily Newsletter: Your Daily Dose of Interesting"
            print(f"  Sending email to {email}")
            send_email(email, subject, email_content)
        else:
            print(f"  No content found for subscriber {email}")

if __name__ == "__main__":
    main()