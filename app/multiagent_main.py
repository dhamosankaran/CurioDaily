import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from app.api.api import api_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.crud.crud_topic import seed_initial_topics
import sys

from app.multi_agent_system import MultiAgentSystem  # Update this import


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

logger.info("Logging configured")

# Create database tables
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
except Exception as e:
    logger.error(f"Error creating database tables: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"/api/openapi.json"
)

# Get the directory of the current file
# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
project_root = os.path.dirname(current_dir)

# Mount the static directory
static_dir = os.path.join(project_root, "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.on_event("startup")
def startup_event():
    logger.info("Running startup event")
    db = SessionLocal()
    try:
        seed_initial_topics(db)
        logger.info("Initial topics seeded")
    except Exception as e:
        logger.error(f"Error seeding initial topics: {e}")
    finally:
        db.close()

# ... (rest of your FastAPI setup)

# Initialize MultiAgentSystem
try:
    logger.info("Initializing MultiAgentSystem")
    mas = MultiAgentSystem()
    logger.info("MultiAgentSystem initialized successfully")
except Exception as e:
    logger.error(f"Error initializing MultiAgentSystem: {e}")

@app.get("/generate_newsletter/{topic}")
async def generate_newsletter(topic: str):
    logger.info(f"Received request to generate newsletter for topic: {topic}")
    try:
        result = mas.run(topic)
        logger.info(f"Newsletter generated successfully for topic: {topic}")
        return {
            "newsletter": result["newsletter"],
            "evaluation": result["evaluation"],
            "execution_time": result["execution_time"]
        }
    except Exception as e:
        logger.error(f"Error generating newsletter for topic {topic}: {e}")
        return JSONResponse(status_code=500, content={"error": "Failed to generate newsletter"})

# Mount the static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_root():
    return FileResponse("static/newsletter.html")

@app.get("/api/newsletter_data")
async def get_newsletter_data():
    topic = "technology"  # You might want to make this dynamic
    mas = MultiAgentSystem()
    result = mas.run(topic)
    
    # Check if the result is the placeholder message
    if result == "The complete engaging newsletter based on the analyzed content.":
        # Generate a mock newsletter for demonstration purposes
        newsletter_content = f"""
        Daily Tech Digest: Innovations Reshaping Our World

        AI Breakthroughs:
        A new AI model has demonstrated unprecedented natural language understanding, potentially revolutionizing human-computer interactions.

        Cybersecurity Updates:
        Major tech companies have formed a coalition to combat the rising threat of ransomware attacks, promising enhanced protection for users worldwide.

        Space Exploration:
        NASA announces plans for a groundbreaking Mars mission, aiming to search for signs of ancient microbial life on the Red Planet.

        Green Technology:
        A startup unveils a revolutionary battery technology that could double the range of electric vehicles, potentially accelerating the adoption of sustainable transportation.

        Emerging Trends:
        The rise of decentralized finance (DeFi) is challenging traditional banking systems, offering new opportunities and risks in the financial sector.
        """
    else:
        newsletter_content = result

    return {
        "newsletter": newsletter_content,
        "execution_time": 5.67,  # Mock execution time
        "evaluation": {
            "relevance": {"score": 0.95},
            "criteria": {
                "coherence": 0.92,
                "engagement": 0.88
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting the application")
    uvicorn.run("multiagent_main:app", host="0.0.0.0", port=9001, reload=True)