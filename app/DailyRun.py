import os
import glob
import importlib.util
import concurrent.futures
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from openai import OpenAI
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

def get_llm_task_distribution(scripts):
    prompt = f"""
    Given the following list of news aggregation scripts:
    {', '.join(scripts)}

    Suggest an efficient distribution of tasks for parallel processing. Consider:
    1. Balancing the workload
    2. Grouping similar topics if beneficial
    3. Optimal number of parallel processes
    4. Ensuring each topic is only processed once

    Respond with a JSON structure of task groups. For example:
    {{
        "group1": ["NewsAPI_AI.py"],
        "group2": ["NewsAPI_Tech.py", "NewsAPI_Gadgets.py"],
        ...
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4-0125-preview",
            messages=[
                {"role": "system", "content": "You are an AI assistant that optimizes task distribution for parallel processing."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            n=1,
            stop=None,
            temperature=0.5,
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"Error getting LLM task distribution: {str(e)}")
        return {f"group{i}": [script] for i, script in enumerate(scripts)}

def validate_task_distribution(task_groups, all_scripts):
    # Check if all scripts are accounted for
    distributed_scripts = [script for group in task_groups.values() for script in group]
    missing_scripts = set(all_scripts) - set(distributed_scripts)
    extra_scripts = set(distributed_scripts) - set(all_scripts)

    if missing_scripts:
        logger.warning(f"Missing scripts in distribution: {missing_scripts}")
    if extra_scripts:
        logger.warning(f"Extra scripts in distribution: {extra_scripts}")

    # Check for duplicates
    seen_scripts = set()
    duplicates = set()
    for group in task_groups.values():
        for script in group:
            if script in seen_scripts:
                duplicates.add(script)
            seen_scripts.add(script)

    if duplicates:
        logger.warning(f"Duplicate scripts found: {duplicates}")

    return len(missing_scripts) == 0 and len(extra_scripts) == 0 and len(duplicates) == 0

def main():
    # Get all NewsAPI*.py scripts in the current directory
    scripts = glob.glob("NewsAPI_*.py")
    
    if not scripts:
        logger.warning("No NewsAPI scripts found in the current directory.")
        return

    # Get task distribution from LLM
    task_groups = get_llm_task_distribution(scripts)

    # Validate the task distribution
    if not validate_task_distribution(task_groups, scripts):
        logger.error("Invalid task distribution. Falling back to default distribution.")
        task_groups = {f"group{i}": [script] for i, script in enumerate(scripts)}

    # Execute scripts in parallel using the suggested distribution
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for group, group_scripts in task_groups.items():
            for script in group_scripts:
                if script in scripts:  # Additional check to ensure the script exists
                    futures.append(executor.submit(execute_script, script))
                else:
                    logger.warning(f"Script {script} not found in the directory. Skipping.")
        
        # Wait for all tasks to complete
        concurrent.futures.wait(futures)

    logger.info("All scripts executed successfully.")

if __name__ == "__main__":
    main()