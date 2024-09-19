import os
import sys
import glob
import importlib.util
import concurrent.futures
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Now we can import from app
from app.core.config import settings

# Create a database engine
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

current_dir = os.path.dirname(os.path.abspath(__file__))
newsapi_dir = os.path.join(os.path.dirname(current_dir), "NewsAPI")

def load_module(file_path):
    spec = importlib.util.spec_from_file_location("module.name", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def execute_script(script_path):
    try:
        module = load_module(script_path)
        if hasattr(module, 'main'):
            module.main()
        logger.info(f"Successfully executed {script_path}")
    except Exception as e:
        logger.error(f"Error executing {script_path}: {str(e)}")

def get_active_topics():
    with SessionLocal() as db:
        result = db.execute(text("""
            SELECT name 
            FROM topics 
            WHERE is_active = 'Y'
        """))
        return [row[0].lower() for row in result.fetchall()]

def main():
    # Get active topics from the database
    active_topics = get_active_topics()
    logger.info(f"Active topics: {active_topics}")

    # Get all NewsAPI scripts
    all_scripts = glob.glob(os.path.join(newsapi_dir, "*.py"))
    
    if not all_scripts:
        logger.warning(f"No NewsAPI scripts found in the directory: {newsapi_dir}")
        return

    # Filter scripts based on active topics
    scripts_to_run = []
    for script in all_scripts:
        script_name = os.path.basename(script)
        # Remove ".py" suffix and convert to lowercase
        topic_name = os.path.splitext(script_name)[0].lower()
        if topic_name in active_topics:
            scripts_to_run.append(script)
            logger.info(f"Matched script: {script_name} with topic: {topic_name}")
        else:
            logger.info(f"No match for script: {script_name}")

    logger.info(f"Scripts to run: {scripts_to_run}")

    # Execute scripts in parallel
    # Uncomment the following lines if you want to execute the scripts
    with concurrent.futures.ThreadPoolExecutor() as executor:
         futures = [executor.submit(execute_script, script) for script in scripts_to_run]
         concurrent.futures.wait(futures)

    logger.info("All scripts executed successfully.")

if __name__ == "__main__":
    main()