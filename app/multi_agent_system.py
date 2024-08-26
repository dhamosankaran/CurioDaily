import os
import time
import logging
from crewai import Agent, Task, Crew, Process
from langchain_openai import OpenAI
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.agents import Tool
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.evaluation import load_evaluator
from langchain.evaluation.criteria import CriteriaEvalChain

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize OpenAI LLM
llm = OpenAI(temperature=0.7, api_key=os.getenv("OPENAI_API_KEY"))

# Initialize tools
search_tool = DuckDuckGoSearchRun()


class MemoryManager:
    def __init__(self):
        self.researcher_memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self.analyzer_memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self.creator_memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    def get_memory(self, agent_type):
        if agent_type == 'researcher':
            return self.researcher_memory
        elif agent_type == 'analyzer':
            return self.analyzer_memory
        elif agent_type == 'creator':
            return self.creator_memory
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

class EvaluationManager:
    def __init__(self):
        self.evaluator = load_evaluator("criteria", criteria="relevance")
        self.criteria_eval_chain = CriteriaEvalChain.from_llm(
            llm=llm,
            criteria={
                "relevance": "Is the content relevant to the given topic?",
                "coherence": "Is the content coherent and well-structured?",
                "engagement": "Is the content engaging and interesting to read?"
            }
        )

    def evaluate_newsletter(self, newsletter, topic):
        relevance_eval = self.evaluator.evaluate_strings(
            prediction=newsletter,
            input=f"A newsletter about {topic}"
        )

        criteria_eval = self.criteria_eval_chain.evaluate_strings(
            prediction=newsletter,
            input=f"A newsletter about {topic}"
        )

        return {
            "relevance": relevance_eval,
            "criteria": criteria_eval
        }

class PerformanceMonitor:
    def __init__(self):
        self.start_time = None
        self.end_time = None

    def start(self):
        self.start_time = time.time()

    def stop(self):
        self.end_time = time.time()

    def get_execution_time(self):
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        else:
            return None

class MultiAgentSystem:
    def __init__(self):
        logger.info("Initializing MultiAgentSystem")
        self.memory_manager = MemoryManager()
        self.evaluation_manager = EvaluationManager()
        self.performance_monitor = PerformanceMonitor()

        # Create LLMChains for each agent
        researcher_chain = LLMChain(
            llm=llm,
            prompt=PromptTemplate(
                input_variables=["input", "chat_history"],
                template="You are a news researcher. Given the following chat history and the new input, find relevant news articles.\n\nChat History: {chat_history}\n\nNew Input: {input}\n\nYour response:"
            ),
            memory=self.memory_manager.get_memory('researcher')
        )

        analyzer_chain = LLMChain(
            llm=llm,
            prompt=PromptTemplate(
                input_variables=["input", "chat_history"],
                template="You are a content analyzer. Given the following chat history and the new input, analyze and summarize the content.\n\nChat History: {chat_history}\n\nNew Input: {input}\n\nYour response:"
            ),
            memory=self.memory_manager.get_memory('analyzer')
        )

        creator_chain = LLMChain(
            llm=llm,
            prompt=PromptTemplate(
                input_variables=["input", "chat_history"],
                template="You are a newsletter creator. Given the following chat history and the new input, create an engaging newsletter.\n\nChat History: {chat_history}\n\nNew Input: {input}\n\nYour response:"
            ),
            memory=self.memory_manager.get_memory('creator')
        )

        self.news_researcher = Agent(
            role='News Researcher',
            goal='Find the latest and most relevant news articles',
            backstory='You are an expert news researcher with a keen eye for trending topics.',
            verbose=True,
            allow_delegation=True,
            tools=[Tool(name="Search", func=search_tool.run, description="Useful for searching the internet")],
            llm_chain=researcher_chain
        )

        self.content_analyzer = Agent(
            role='Content Analyzer',
            goal='Analyze and summarize news articles',
            backstory='You are an expert in content analysis and summarization.',
            verbose=True,
            allow_delegation=True,
            llm_chain=analyzer_chain
        )

        self.newsletter_creator = Agent(
            role='Newsletter Creator',
            goal='Create engaging newsletters from analyzed content',
            backstory='You are a creative writer specialized in crafting compelling newsletters.',
            verbose=True,
            allow_delegation=True,
            llm_chain=creator_chain
        )

    def run(self, topic):
        logger.info(f"Running MultiAgentSystem for topic: {topic}")
        self.performance_monitor.start()

        research_task = Task(
            description=f"Research the latest news about {topic}",
            agent=self.news_researcher,
            expected_output="A list of relevant news articles about the given topic"
        )

        analyze_task = Task(
            description="Analyze and summarize the found news articles",
            agent=self.content_analyzer,
            expected_output="A summary of the key points from the analyzed news articles"
        )

        create_newsletter_task = Task(
            description="Create an engaging newsletter from the analyzed content",
            agent=self.newsletter_creator,
            expected_output="An engaging newsletter based on the analyzed content"
        )

        crew = Crew(
            agents=[self.news_researcher, self.content_analyzer, self.newsletter_creator],
            tasks=[research_task, analyze_task, create_newsletter_task],
            verbose=True,
            process=Process.sequential
        )

        result = crew.kickoff()

        self.performance_monitor.stop()
        execution_time = self.performance_monitor.get_execution_time()

        evaluation = self.evaluation_manager.evaluate_newsletter(result, topic)

        logger.info(f"MultiAgentSystem run completed for topic: {topic}")
        return {
            "newsletter": result,
            "evaluation": evaluation,
            "execution_time": execution_time
        }
# Example usage
if __name__ == "__main__":
    logger.info("Running multi_agent_system.py directly")
    mas = MultiAgentSystem()
    result = mas.run("artificial intelligence")
    logger.info(f"Newsletter: {result['newsletter']}")
    logger.info(f"Evaluation: {result['evaluation']}")
    logger.info(f"Execution Time: {result['execution_time']} seconds")