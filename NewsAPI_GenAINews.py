import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging
from textwrap import wrap

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class AINewsFetcher:
    def __init__(self):
        self.api_key = os.getenv('NEWS_API_KEY')
        if not self.api_key:
            raise ValueError("NEWS_API_KEY not found in environment variables")
        self.base_url = "https://newsapi.org/v2/everything"
        self.preferred_entities = [
            'OpenAI', 'DeepMind', 'Microsoft', 'MIT', 'Mistral', 
            'Anthropic', 'Meta', 'IBM', 'NVIDIA', 'Intel', 'Apple', 
            'Amazon', 'Boston Dynamics', 'Tesla', 'Google'
        ]
        self.popular_keywords = [
            'artificial intelligence', 'machine learning', 'deep learning',
            'GPT', 'LLM', 'generative AI', 'robot', 'humanoid', 'AI ethics',
            'AI breakthrough', 'robotic breakthrough', 'humanoid development'
        ]
        self.relevant_keywords = self.popular_keywords + [
            'neural network', 'computer vision', 'natural language processing',
            'reinforcement learning', 'AI research', 'AI application'
        ]

    def fetch_news(self, keywords, from_date, to_date, language='en', sort_by='relevancy'):
        all_keywords = keywords + self.preferred_entities
        query = ' OR '.join(f'"{keyword}"' for keyword in all_keywords[:20])  # Limit to 20 keywords

        params = {
            'q': query,
            'from': from_date.isoformat(),
            'to': to_date.isoformat(),
            'language': language,
            'sortBy': sort_by,
            'pageSize': 100,
            'apiKey': self.api_key
        }

        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            articles = data.get('articles', [])
            return self.filter_and_sort_articles(articles)
        except requests.RequestException as e:
            logger.error(f"Error fetching news: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.content}")
            return []

    def filter_and_sort_articles(self, articles):
        unique_articles = self.remove_duplicates(articles)
        sorted_articles = self.sort_articles_by_preference(unique_articles)
        return sorted_articles[:10]

    def remove_duplicates(self, articles):
        unique_articles = []
        seen_content = set()

        for article in articles:
            content = (article.get('title', '') + ' ' + article.get('description', '')).lower()
            content_hash = hash(content)

            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_articles.append(article)

        return unique_articles

    def sort_articles_by_preference(self, articles):
        def preference_score(article):
            title = article.get('title', '').lower()
            description = article.get('description', '').lower()
            content = title + ' ' + description

            entity_score = sum(content.count(entity.lower()) for entity in self.preferred_entities)

            ai_keywords = ['artificial intelligence', 'machine learning', 'deep learning', 'neural network']
            genai_keywords = ['generative ai', 'gpt', 'llm', 'large language model']
            robot_keywords = ['robot', 'humanoid', 'android', 'automaton']
            
            ai_score = sum(content.count(keyword) for keyword in ai_keywords)
            genai_score = sum(content.count(keyword) for keyword in genai_keywords)
            robot_score = sum(content.count(keyword) for keyword in robot_keywords)

            total_score = (entity_score * 2) + (ai_score * 1.5) + (genai_score * 2) + (robot_score * 2.5)

            return total_score

        return sorted(articles, key=preference_score, reverse=True)

    @staticmethod
    def format_article(article, index):
        title = article['title']
        description = article.get('description', 'No description available.')
        source = article['source']['name']
        url = article['url']
        published_at = datetime.fromisoformat(article['publishedAt'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S UTC')

        formatted_article = f"""
{'-'*80}
{index}. {title}

Description:
{os.linesep.join(wrap(description, width=80))}

Source: {source}
URL: {url}
Published at: {published_at}
{'-'*80}
"""
        return formatted_article

    def remove_duplicate_articles(self, articles1, articles2):
        seen_urls = set()
        unique_articles1 = []
        unique_articles2 = []

        for article in articles1:
            url = article['url']
            if url not in seen_urls:
                seen_urls.add(url)
                unique_articles1.append(article)

        for article in articles2:
            url = article['url']
            if url not in seen_urls:
                seen_urls.add(url)
                unique_articles2.append(article)

        return unique_articles1, unique_articles2

def main():
    fetcher = AINewsFetcher()
    
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    # Fetch popular articles with restricted keywords
    logger.info(f"Fetching top 10 popular AI-related news articles from {yesterday} to {today}...")
    popular_articles = fetcher.fetch_news(fetcher.popular_keywords, yesterday, today, sort_by='popularity')

    # Fetch relevant articles with a broader set of keywords
    logger.info(f"Fetching top 10 relevant AI-related news articles from {yesterday} to {today}...")
    relevant_articles = fetcher.fetch_news(fetcher.relevant_keywords, yesterday, today, sort_by='relevancy')

    # Remove duplicates across both lists
    popular_articles, relevant_articles = fetcher.remove_duplicate_articles(popular_articles, relevant_articles)

    # Display popular articles
    if popular_articles:
        logger.info(f"Found {len(popular_articles)} unique popular articles:")
        for index, article in enumerate(popular_articles, start=1):
            print(fetcher.format_article(article, index))
    else:
        logger.info("No unique popular articles found for the given criteria.")

    # Display relevant articles
    if relevant_articles:
        logger.info(f"Found {len(relevant_articles)} unique relevant articles:")
        for index, article in enumerate(relevant_articles, start=1):
            print(fetcher.format_article(article, index))
    else:
        logger.info("No unique relevant articles found for the given criteria.")

    logger.info("News fetching complete.")

if __name__ == "__main__":
    main()