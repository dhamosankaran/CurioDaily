import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging
from textwrap import wrap
from openai import OpenAI

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class AINewsFetcher:
    def __init__(self):
        self.news_api_key = os.getenv('NEWS_API_KEY')
        #self.openai_api_key = os.getenv('OPENAI_API_KEY')
        # Initialize the client with your API key
        
        
        if not self.news_api_key:
            raise ValueError("NEWS_API_KEY not found in environment variables")
        #if not client:
            #raise ValueError("OPENAI_API_KEY not found in environment variables")
        self.base_url = "https://newsapi.org/v2/everything"
        self.preferred_entities = [
            'OpenAI', 'DeepMind', 'Microsoft', 'MIT', 'Mistral', 
            'Anthropic', 'Meta', 'IBM', 'NVIDIA', 'Intel', 'Apple', 
            'Amazon', 'Boston Dynamics', 'Tesla', 'Google'
        ]
        #openai.api_key = self.openai_api_key

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
            'apiKey': self.news_api_key
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
        return sorted_articles[:2]

    def remove_duplicates(self, articles):
        unique_articles = []
        seen_content = set()

        for article in articles:
            title = article.get('title', '') or ''
            description = article.get('description', '') or ''
            content = (title + ' ' + description).lower()
            content_hash = hash(content)

            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_articles.append(article)

        return unique_articles

    def sort_articles_by_preference(self, articles):
        def preference_score(article):
            title = article.get('title', '') or ''
            description = article.get('description', '') or ''
            content = (title + ' ' + description).lower()

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
        title = article.get('title', 'No title available')
        description = article.get('description', 'No description available.')
        source = article['source'].get('name', 'Unknown source')
        url = article.get('url', 'No URL available')
        published_at = article.get('publishedAt', 'Unknown publication date')
        if published_at != 'Unknown publication date':
            published_at = datetime.fromisoformat(published_at.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S UTC')

        formatted_article = f"""
{'-'*100}
{index}. {title}

Description:
{os.linesep.join(wrap(description, width=200))}

Source: {source}
URL: {url}
Published at: {published_at}
{'-'*100}
"""
        return formatted_article

    def generate_summary(self, article):
        title = article.get('title', 'No title available')
        description = article.get('description', 'No description available')
        url = article.get('url', 'No URL available')

        prompt = f"""
        Summarize the following article in this format:
        **[Topic Title]**: Key Highlights
        🚀 **Update Overview**: [Brief introduction to the update. Mention the key development, release, or innovation in GenAI/LLM.]
        💡 **Key Highlights**:
        1. **[Highlight 1]**: [Brief description of the first key point or feature.]
        2. **[Highlight 2]**: [Brief description of the second key point or feature.]
        3. **[Highlight 3]**: [Brief description of the third key point or feature.]
        🔍 **Why It Matters**: [Explain the significance of this update. How does it impact users, industries, or the broader AI community?]
        🎯 **Practical Applications**: [Discuss potential use cases or applications of the update in real-world scenarios.]
        📚 **Further Reading**: {url}

        Article Title: {title}
        Article Description: {description}
        """

        try:
            #response = openai.ChatCompletion.create(
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant that summarizes news articles about artificial intelligence and technology."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                n=1,
                stop=None,
                temperature=0.7,
            )
            #return response.choices[0].message['content'].strip()
            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error generating summary with OpenAI: {e}")
            return "Error generating summary."

    def format_article_with_summary(self, article, index):
        formatted_article = self.format_article(article, index)
        summary = self.generate_summary(article)
        return f"{formatted_article}\nSummary:\n{summary}\n"

def main():
    fetcher = AINewsFetcher()
    
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    keywords = [
        'artificial intelligence', 'machine learning', 'deep learning',
        'GPT', 'LLM', 'generative AI', 'robot', 'humanoid', 'AI ethics',
        'AI breakthrough', 'robotic breakthrough', 'humanoid development'
    ]

    # Fetch popular articles
    #logger.info(f"Fetching top 10 popular AI-related news articles from {yesterday} to {today}...")
    #popular_articles = fetcher.fetch_news(keywords, yesterday, today, sort_by='popularity')

    #if popular_articles:
        #logger.info(f"Found {len(popular_articles)} popular articles:")
        #for index, article in enumerate(popular_articles, start=1):
            #print(fetcher.format_article_with_summary(article, index))
    #else:
        #logger.info("No popular articles found for the given criteria.")

    # Fetch relevant articles
    logger.info(f"Fetching top 10 relevant AI-related news articles from {yesterday} to {today}...")
    relevant_articles = fetcher.fetch_news(keywords, yesterday, today, sort_by='relevancy')

    if relevant_articles:
        logger.info(f"Found {len(relevant_articles)} relevant articles:")
        for index, article in enumerate(relevant_articles, start=1):
            print(fetcher.format_article_with_summary(article, index))
    else:
        logger.info("No relevant articles found for the given criteria.")

    logger.info("News fetching and summarization complete.")

if __name__ == "__main__":
    main()