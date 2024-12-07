import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging
from openai import OpenAI
import psycopg2
from psycopg2 import sql
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

current_dir = os.path.dirname(os.path.abspath(__file__))
web_template_path = os.path.join(current_dir, 'newsletter_template.html')
email_template_path = os.path.join(current_dir, 'newsletter_template.html')  # Using same template

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class AINewsFetcher:
    def __init__(self):
        self.openai_model = os.getenv('OPENAI_MODEL')
        logger.info(f"openai model {self.openai_model}")
        self.news_api_key = os.getenv('NEWS_API_KEY')
        if not self.news_api_key:
            raise ValueError("NEWS_API_KEY not found in environment variables")
        self.base_url = "https://newsapi.org/v2/everything"
        self.db_url = os.getenv('DATABASE_URL')
        if not self.db_url:
            raise ValueError("DATABASE_URL not found in environment variables")

        # Enhanced categorization of AI topics
        self.ai_categories = {
            'GenAI': [
                'generative AI', 'GenAI', 'text-to-image', 'text-to-video',
                'AI generation', 'AI creation', 'AI art', 'AI content',
                'GPT-4', 'GPT-5', 'Claude', 'Gemini', 'DALL-E', 'Midjourney',
                'Stable Diffusion', 'Anthropic', 'foundation models'
            ],
            'Humanoid': [
                'humanoid robot', 'AI robot', 'Figure AI', 'Tesla Bot', 'Optimus',
                'Atlas robot', 'Boston Dynamics', 'Agility Robotics', 'robot navigation',
                'human-like robot', 'android', 'robotic movement', 'robot learning'
            ],
            'BigTech': [
                'OpenAI', 'Microsoft AI', 'Google AI', 'Meta AI', 'Amazon AI',
                'Apple AI', 'Tesla AI', 'NVIDIA AI', 'IBM AI', 'Anthropic',
                'DeepMind', 'X AI', 'Inflection AI', 'AI acquisition',
                'AI partnership', 'AI investment', 'AI startup'
            ],
            'AI Development': [
                'large language model', 'LLM', 'transformer model', 'AI model',
                'neural network', 'deep learning', 'machine learning', 'AI training',
                'AI infrastructure', 'AI chip', 'TPU', 'GPU', 'AI hardware',
                'AI breakthrough', 'AI research', 'AI paper', 'AI conference'
            ],
            'AI Ethics': [
                'AI safety', 'AI alignment', 'AI regulation', 'AI policy',
                'AI governance', 'AI ethics', 'responsible AI', 'AI bias',
                'AI transparency', 'AI explainability', 'AI rights',
                'AI accountability', 'AI supervision'
            ],
            'AI Applications': [
                'AI in healthcare', 'AI in finance', 'AI in education',
                'AI in business', 'enterprise AI', 'AI automation',
                'AI assistant', 'AI agent', 'autonomous system',
                'computer vision', 'natural language processing', 'NLP'
            ]
        }

        # Enhanced company tracking
        self.major_ai_companies = {
            'Tech Giants': [
                'OpenAI', 'Microsoft', 'Google', 'Meta', 'Amazon', 'Apple',
                'Tesla', 'NVIDIA', 'IBM', 'Baidu', 'Anthropic', 'DeepMind'
            ],
            'AI Startups': [
                'Anthropic', 'Inflection AI', 'Cohere', 'AI21 Labs',
                'Stability AI', 'Midjourney', 'Figure AI', 'Character AI',
                'Mistral AI', 'Hugging Face', 'Scale AI', 'Databricks'
            ],
            'Robotics': [
                'Boston Dynamics', 'Figure AI', 'Agility Robotics',
                'Sanctuary AI', 'Tesla Robotics', 'Honda Robotics',
                'ABB Robotics', 'FANUC', 'Fetch Robotics'
            ]
        }

    def get_active_subscriptions(self):
        try:
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor() as cur:
                    query = sql.SQL("""
                        SELECT 
                            s.id, 
                            s.email, 
                            st.topic_id
                        FROM 
                            public.subscriptions s
                        JOIN 
                            public.subscription_topic st ON s.id = st.subscription_id 
                        WHERE 
                            s.is_active = true and st.topic_id = 1
                    """)
                    cur.execute(query)
                    subscriptions = cur.fetchall()
                    return [{"id": str(sub[0]), "email": sub[1]} for sub in subscriptions]
        except Exception as e:
            logger.error(f"Error fetching active subscriptions: {e}")
            return []

    def fetch_news(self, date, language='en', sort_by='relevancy'):
        all_articles = []
        
        # Enhanced query structure for better coverage
        query_categories = {
            'GenAI': [
                'GenAI OR "generative AI" OR "foundation model"',
                'GPT-4 OR GPT-5 OR Claude OR Gemini OR DALL-E',
                'text-to-image OR text-to-video OR AI generation'
            ],
            'Humanoid': [
                'humanoid robot OR Tesla Bot OR Figure AI robot',
                'Boston Dynamics OR Atlas robot OR Optimus robot',
                'AI robot development OR human-like robot'
            ],
            'BigTech': [
                'OpenAI OR Microsoft AI OR Google AI OR Meta AI',
                'Anthropic OR DeepMind OR Tesla AI OR NVIDIA AI',
                'AI acquisition OR AI investment OR AI startup'
            ],
            'Development': [
                'LLM OR "large language model" OR "AI model"',
                'AI chip OR AI hardware OR AI infrastructure',
                'AI breakthrough OR AI research OR AI conference'
            ],
            'Ethics': [
                'AI safety OR AI alignment OR AI regulation',
                'AI ethics OR responsible AI OR AI governance',
                'AI bias OR AI transparency OR AI rights'
            ]
        }

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for category, queries in query_categories.items():
                for query in queries:
                    futures.append(
                        executor.submit(
                            self._fetch_news,
                            query,
                            date,
                            language,
                            sort_by,
                            category
                        )
                    )
            
            for future in as_completed(futures):
                try:
                    category_articles = future.result()
                    all_articles.extend(category_articles)
                except Exception as exc:
                    logger.error(f'Error fetching news: {exc}')

        processed_articles = self.process_articles_with_ai(all_articles)
        return processed_articles

# Fix the _fetch_news method to handle None values
    def _fetch_news(self, query, date, language, sort_by, category):
        if not query:  # Handle None query
            return []

        params = {
            'q': str(query),  # Ensure query is string
            'from': date.isoformat(),
            'to': (date + timedelta(days=1)).isoformat(),
            'language': language,
            'sortBy': sort_by,
            'pageSize': 10,
            'apiKey': self.news_api_key
        }

        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            articles = data.get('articles', [])
            
            # Process each article safely
            processed_articles = []
            for article in articles:
                if article:  # Only process valid articles
                    try:
                        # Safely get text content
                        title = article.get('title', '')
                        description = article.get('description', '')
                        content_text = f"{title} {description}".strip()
                        
                        # Add category and keywords only if we have content
                        if content_text:
                            article['category'] = category
                            article['keywords'] = self._extract_keywords(content_text)
                            processed_articles.append(article)
                    except Exception as e:
                        logger.error(f"Error processing article: {e}")
                        continue
            
            return processed_articles

        except requests.RequestException as e:
            logger.error(f"Error fetching news: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.content}")
            return []

    # Fix the _extract_keywords method to handle None values
    def _extract_keywords(self, text):
        if not text:  # Handle None or empty text
            return []
            
        keywords = []
        text_lower = str(text).lower()  # Convert to string to handle any type
        
        # Check for category keywords
        for category, terms in self.ai_categories.items():
            if any(term.lower() in text_lower for term in terms):
                keywords.append(category)
        
        # Check for company mentions
        for company_type, companies in self.major_ai_companies.items():
            for company in companies:
                if company.lower() in text_lower:
                    keywords.append(company)
        
        return list(set(keywords))

 # Add safety checks to process_articles_with_ai method
    def process_articles_with_ai(self, articles):
        if not articles:
            return {
                'filtered_articles': [],
                'highlights': [],
                'title': "Today's AI Highlights",
                'summary': "No articles available today."
            }

        # Safely prepare articles text
        articles_text = "\n\n".join([
            f"Title: {article.get('title', 'No Title')}\n"
            f"Description: {article.get('description', 'No Description')}\n"
            f"Category: {article.get('category', 'General')}\n"
            f"Keywords: {', '.join(article.get('keywords', []))}\n"
            f"Source: {article.get('source', {}).get('name', 'Unknown Source')}"
            for article in articles
            if article and article.get('title') and article.get('description')  # Only include articles with content
        ])

        if not articles_text:
            return {
                'filtered_articles': [],
                'highlights': [],
                'title': "Today's AI Highlights",
                'summary': "No valid articles available today."
            }

        try:
            response = client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": """You are an AI news curator specializing in AI technology news. 
                    Focus on significant developments in:
                    1. Generative AI and foundation models
                    2. Humanoid robotics and autonomous systems
                    3. Big tech AI initiatives and investments
                    4. AI ethics and regulation
                    5. Breakthrough AI research and applications
                    
                    Output format must be valid JSON:
                    {
                        "filtered_indices": [array of indices],
                        "highlights": [
                            {
                                "text": "highlight text max 120 chars",
                                "category": "category name"
                            }
                        ],
                        "title": "AI [Theme]: [Specific Detail]",
                        "summary": "4-line summary focusing on major developments"
                    }"""},
                    {"role": "user", "content": f"""Analyze these AI news articles:
                    {articles_text}
                    
                    Prioritize:
                    1. Major AI company announcements and developments
                    2. Breakthrough technologies and research
                    3. Significant AI product launches
                    4. Important AI policy and regulation news
                    5. Novel AI applications and use cases"""}
                ],
                temperature=0.7,
                max_tokens=1000,
                response_format={ "type": "json_object" }
            )

            result = json.loads(response.choices[0].message.content)
            logger.info("Successfully parsed AI response")

            if not all(field in result for field in ['filtered_indices', 'highlights', 'title', 'summary']):
                raise ValueError("Missing required fields in AI response")

            # Safely get filtered articles
            filtered_articles = []
            for idx in result['filtered_indices']:
                if isinstance(idx, int) and 0 <= idx < len(articles):
                    article = articles[idx]
                    if article and article.get('title') and article.get('description'):
                        filtered_articles.append(article)
            filtered_articles = filtered_articles[:10]  # Limit to top 10

            # Safely get highlights
            highlights = []
            for h in result.get('highlights', [])[:5]:
                if isinstance(h, dict):
                    text = str(h.get('text', ''))[:120]  # Ensure string and limit length
                    category = str(h.get('category', 'General'))
                    if text and category:
                        highlights.append((text, category))

            return {
                'filtered_articles': filtered_articles,
                'highlights': highlights,
                'title': str(result.get('title', "Today's AI Highlights")),
                'summary': str(result.get('summary', "Latest developments in AI technology."))
            }

        except Exception as e:
            logger.error(f"Error in AI processing: {e}")
            return self._fallback_processing(articles)

    def _fallback_processing(self, articles):
        basic_filtered = [
            article for article in articles
            if article.get('title') and article.get('description') and article.get('urlToImage')
            and article.get('keywords')  # Ensure articles have keywords
        ][:10]
        
        return {
            'filtered_articles': basic_filtered,
            'highlights': [
                (article.get('title', '')[:117] + "...", article.get('category', 'General')) 
                for article in basic_filtered[:5]
            ],
            'title': "Today's AI Technology Updates",
            'summary': "Compilation of latest developments in AI technology and research."
        }

    def store_newsletter(self, title, content, email_content, topic_id, subscription_ids):
        try:
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor() as cur:
                    insert_query = sql.SQL("""
                        INSERT INTO newsletters (title, content, email_content, topic_id, subscription_ids)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                    """)
                    subscription_ids_str = ','.join(subscription_ids)
                    cur.execute(insert_query, (title, content, email_content, topic_id, subscription_ids_str))
                    inserted_id = cur.fetchone()[0]
                    conn.commit()
                    logger.info(f"Newsletter stored in database with ID: {inserted_id}")
                    return inserted_id
        except Exception as e:
            logger.error(f"Error storing newsletter in database: {e}")
            return None

def generate_html_content(dynamic_title, summary, highlights, articles):
    base_url = os.getenv('BASE_URL', 'https://www.thecuriodaily.com')
    current_date = datetime.now().strftime("%B %d, %Y")
    
    # Generate highlights HTML
    highlights_html = "<ul class='highlights-list'>\n" + "".join([
        f"""    <li class="highlight-item">
        <span class="highlight-text">{text}</span>
    </li>
"""
        for text, category in highlights
    ]) + "</ul>"
    
    
    # Generate articles HTML
    articles_html = "<div class='article-grid'>\n" + "".join([
        f"""    <article class="article">
        <span class="article-category">{article.get('category', 'General')}</span>
        <h3>{article.get('title', 'Untitled')}</h3>
        <img src="{article.get('urlToImage', '/api/placeholder/400/300')}" 
             alt="Article image" class="article-image">
        <p>{article.get('description', 'No description available.')}</p>
        <a href="{article.get('url', '#')}" class="read-more" target="_blank">Read More</a>
    </article>
"""
        for article in articles
    ]) + "</div>"

    # Read and fill template
    with open(web_template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    # Replace placeholders in template
    template = template.replace('{{dynamic_title}}', dynamic_title)
    template = template.replace('{{current_date}}', current_date)
    template = template.replace('{{summary}}', f"<p>{summary}</p>")
    template = template.replace('{{highlights}}', highlights_html)
    template = template.replace('{{articles}}', articles_html)
    template = template.replace('{{base_url}}', base_url)
    template = template.replace('{{unsubscribe_link}}', '{{unsubscribe_link_placeholder}}')

    return template

def store_html_content(html_content, filename):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"HTML content successfully stored in {filename}")
        return True
    except Exception as e:
        logger.error(f"Error storing HTML content: {e}")
        return False

def main():
    fetcher = AINewsFetcher()
    
    # Get current date
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    logger.info(f"Starting AI news collection for {yesterday}")
    
    try:
        # Fetch and process articles
        logger.info("Fetching news articles...")
        processed_content = fetcher.fetch_news(yesterday)
        
        if processed_content['filtered_articles']:
            # Extract processed content
            filtered_articles = processed_content['filtered_articles']
            highlights = processed_content['highlights']
            title = processed_content['title']
            summary = processed_content['summary']
            
            logger.info(f"Found {len(filtered_articles)} relevant articles")
            
            # Generate HTML content
            logger.info("Generating newsletter content...")
            html_content = generate_html_content(
                title,
                summary,
                highlights,
                filtered_articles
            )
            
            if html_content:
                # Store HTML file
                filename = f"AI_Roundup_{today.strftime('%Y%m%d')}.html"
                if store_html_content(html_content, filename):
                    logger.info(f"Newsletter saved as {filename}")
                
                # Get active subscriptions
                logger.info("Fetching active subscriptions...")
                subscriptions = fetcher.get_active_subscriptions()
                subscription_ids = [sub['id'] for sub in subscriptions]
                
                if subscription_ids:
                    # Store in database
                    logger.info("Storing newsletter in database...")
                    inserted_id = fetcher.store_newsletter(
                        title,
                        html_content,
                        html_content,  # Using same content for both web and email
                        1,  # topic_id for AI
                        subscription_ids
                    )
                    
                    if inserted_id:
                        logger.info(f"Newsletter stored successfully with ID: {inserted_id}")
                    else:
                        logger.error("Failed to store newsletter in database")
                else:
                    logger.warning("No active subscriptions found")
            else:
                logger.error("Failed to generate HTML content")
        else:
            logger.warning(f"No relevant articles found for {yesterday}")
    
    except Exception as e:
        logger.error(f"Error in main process: {e}")
    
    logger.info("Newsletter generation process complete")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Critical error in main execution: {e}")