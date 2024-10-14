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
import random
import urllib.parse

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

current_dir = os.path.dirname(os.path.abspath(__file__))
template_path = os.path.join(current_dir, 'weekly_newsletter_template.html')

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class EnhancedAINewsFetcher:
    def __init__(self):
        self.news_api_key = os.getenv('NEWS_API_KEY')
        if not self.news_api_key:
            raise ValueError("NEWS_API_KEY not found in environment variables")
        self.base_url = "https://newsapi.org/v2/everything"
        self.db_url = os.getenv('DATABASE_URL')
        if not self.db_url:
            raise ValueError("DATABASE_URL not found in environment variables")

        self.trusted_sources = [
            'techcrunch.com', 'wired.com', 'technologyreview.com', 'theverge.com',
            'venturebeat.com', 'zdnet.com', 'arstechnica.com', 'forbes.com',
            'cio.com', 'computerworld.com', 'infoworld.com', 'networkworld.com',
            'csoonline.com', 'cnet.com', 'engadget.com', 'gizmodo.com',
            'mashable.com', 'thenextweb.com', 'slashdot.org', 'techmeme.com',
            'technologyreview.com', 'techradar.com', 'theinformation.com',
            'fivethirtyeight.com', 'hbr.org', 'nature.com', 'scientificamerican.com',
            'sciencemag.org', 'newscientist.com', 'popsci.com', 'pnas.org',
            'ieee.org', 'acm.org', 'aaas.org', 'phys.org', 'sciencedaily.com',
            'eurekalert.org', 'medicalxpress.com', 'healthdata.org', 'nih.gov',
            'who.int', 'cdc.gov', 'fda.gov', 'europa.eu', 'un.org', 'worldbank.org',
            'imf.org', 'weforum.org', 'mckinsey.com', 'bcg.com', 'bain.com',
            'deloitte.com', 'pwc.com', 'ey.com', 'kpmg.com', 'accenture.com',
            'gartner.com', 'forrester.com', 'idc.com', 'statista.com', 'economist.com'
        ]

        self.ai_companies = [
            'OpenAI', 'Anthropic', 'DeepMind', 'Google AI', 'Microsoft AI',
            'Meta AI', 'NVIDIA AI', 'IBM AI', 'Hugging Face', 'AI21 Labs',
            'Cohere', 'Stability AI', 'Midjourney', 'Inflection AI',
            'Amazon', 'Apple', 'Baidu', 'Tesla', 'Intel', 'SenseTime', 'Grok',
            'Databricks', 'DataRobot', 'C3.ai', 'Scale AI', 'Runway',
            'Palantir', 'Snowflake', 'Cloudera', 'Salesforce', 'Oracle',
            'SAP', 'Adobe', 'Autodesk', 'Siemens', 'General Electric',
            'Bosch', 'ABB', 'Honeywell', 'Johnson & Johnson', 'Pfizer',
            'Roche', 'Novartis', 'GSK', 'AstraZeneca', 'Medtronic'
        ]

        self.priority_topics = [
            'LLM', 'Large Language Model', 'GPT', 'Generative AI', 'GenAI',
            'OpenAI', 'Anthropic', 'DeepMind', 'Google AI', 'Microsoft AI',
            'AI Research', 'AI Ethics', 'AI Alignment', 'AI Safety',
            'Transformer Model', 'Foundation Model', 'Multimodal AI',
            'Few-shot Learning', 'Zero-shot Learning', 'Prompt Engineering'
        ]

        self.ai_topics = [
            'Artificial Intelligence', 'Machine Learning', 'Deep Learning', 'Neural Networks',
            'Natural Language Processing', 'Computer Vision', 'Robotics', 'Generative AI',
            'Large Language Models', 'Reinforcement Learning', 'AI Ethics', 'AI Research',
            'AI Applications', 'AI in Healthcare', 'AI in Finance', 'AI in Education',
            'Transformer Models', 'Few-shot Learning', 'Transfer Learning', 'Federated Learning',
            'Explainable AI', 'AI Alignment', 'Quantum Machine Learning', 'Edge AI',
            'AI Chips', 'AI Governance', 'AI Safety', 'AI Bias', 'AI Regulation',
            'Multimodal AI', 'AI Agents', 'AI Assistants', 'Autonomous Systems',
            'AI in Manufacturing', 'AI in Agriculture', 'AI in Energy', 'AI in Retail',
            'AI in Transportation', 'AI in Space Exploration', 'AI in Environmental Science',
            'AI in Drug Discovery', 'AI in Materials Science', 'AI in Cybersecurity',
            'AI in Gaming', 'AI in Art and Creativity', 'AI in Law', 'AI in Human Resources'
        ]

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

    def fetch_news(self, start_date, end_date, language='en', sort_by='relevancy'):
        all_articles = []
        
        industries = [
            'Technology', 'Healthcare', 'Finance', 'Manufacturing', 'Energy',
            'Retail', 'Transportation', 'Agriculture', 'Education', 'Entertainment'
        ]
        
        queries = [
            f"AI OR artificial intelligence OR machine learning AND {industry}" 
            for industry in industries
        ]
        queries.extend([
            'AI breakthrough OR AI advancement',
            'LLM OR large language model OR GPT',
            'AI ethics OR AI alignment OR AI safety',
            'AI research OR AI conference',
            'AI application OR AI use case',
            'AI robotics OR autonomous systems OR computer vision'
        ])

        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_query = {executor.submit(self._fetch_news, query, start_date, end_date, language, sort_by): query for query in queries}
            for future in as_completed(future_to_query):
                query = future_to_query[future]
                try:
                    articles = future.result()
                    all_articles.extend(articles)
                except Exception as exc:
                    logger.error(f'{query} generated an exception: {exc}')

        filtered_articles = [
            article for article in all_articles
            if article.get('title') and article.get('description') and article.get('urlToImage')
        ]

        sorted_articles = self.filter_and_sort_articles(filtered_articles)
        return sorted_articles[:20]  # Increased to top 20 articles


    def _fetch_news(self, query, start_date, end_date, language, sort_by):
        params = {
            'q': query,
            'from': start_date.isoformat(),
            'to': end_date.isoformat(),
            'language': language,
            'sortBy': sort_by,
            'pageSize': 20,  # Increased to get more articles for the week
            'apiKey': self.news_api_key
        }

        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('articles', [])
        except requests.RequestException as e:
            logger.error(f"Error fetching news: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.content}")
            return []

    def filter_and_sort_articles(self, articles):
        def relevance_score(article):
            title = article.get('title', '').lower()
            description = article.get('description', '').lower()
            content = (title + ' ' + description)
            
            priority_score = sum(content.count(topic.lower()) for topic in self.priority_topics)
            company_score = sum(content.count(company.lower()) for company in self.ai_companies)
            topic_score = sum(content.count(topic.lower()) for topic in self.ai_topics)
            
            return priority_score * 3 + company_score * 2 + topic_score

        unique_articles = self.remove_duplicates(articles)
        sorted_articles = sorted(unique_articles, key=relevance_score, reverse=True)
        return sorted_articles

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

    def generate_highlights(self, articles):
        highlights = []

        for article in articles[:5]:  # Top 5 articles for highlights
            title = article.get('title', 'Untitled Article')
            prompt = f"""
            Based on the following article title:

            Title: {title}

            1. Create a concise highlight of maximum 120 characters.
            2. Suggest an appropriate icon name that represents this highlight. The icon should be simple and widely available (e.g., from Font Awesome).
            3. Suggest a vibrant color for the icon (use hexadecimal color code).

            Respond in the following format:
            Highlight: [Your rephrased highlight]
            Icon: [Your suggested icon name]
            Color: [Hexadecimal color code]
            """

            try:
                response = client.chat.completions.create(
                    model="gpt-4-1106-preview",
                    messages=[
                        {"role": "system", "content": "You are an AI assistant that creates concise news highlights and suggests relevant icons and colors."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=150,
                    n=1,
                    stop=None,
                    temperature=0.7,
                )
                result = response.choices[0].message.content.strip().split('\n')
                rephrased_highlight = result[0].split(': ')[1]
                icon = result[1].split(': ')[1]
                color = result[2].split(': ')[1]

                if len(rephrased_highlight) > 120:
                    rephrased_highlight = rephrased_highlight[:117] + "..."
                
                highlights.append((rephrased_highlight, icon, color))
            except Exception as e:
                logger.error(f"Error generating highlight with OpenAI: {e}")
                short_title = title[:117] + "..." if len(title) > 120 else title
                highlights.append((short_title, "newspaper", "#333333"))

        return highlights


    def generate_dynamic_title(self, highlights):
        prompt = f"""
        Based on the following AI news highlights, generate a catchy and informative title 
        that summarizes the main themes or most significant developments. The title should 
        be engaging and specific to AI advancements mentioned in the highlights.

        Highlights:
        {', '.join(highlights)}

        Generate a title in the format: "AI [Theme]: [Specific Detail]"
        For example: "AI Breakthrough: New Language Model Surpasses Human Performance"
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[
                    {"role": "system", "content": "You are an AI assistant that creates engaging titles for AI news summaries."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                n=1,
                stop=None,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating title with OpenAI: {e}")
            return "Today's AI Highlights"

    def generate_summary(self, highlights):
        # Extract only the highlight text from the list of tuples
        highlight_texts = [highlight[0] for highlight in highlights]
        
        prompt = f"""
        Based on the following AI news highlights, create a 4-line overview in a human tone:

        {', '.join(highlight_texts)}

        The overview should be engaging and summarize the main themes or developments in AI.
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[
                    {"role": "system", "content": "You are an AI assistant that creates engaging summaries of AI news."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                n=1,
                stop=None,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating summary with OpenAI: {e}")
            return "Error generating summary."

    def store_newsletter(self, title, content, topic_id, subscription_ids):
        try:
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor() as cur:
                    insert_query = sql.SQL("""
                        INSERT INTO newsletters (title, content, topic_id, subscription_ids)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id
                    """)
                    subscription_ids_str = ','.join(subscription_ids)
                    cur.execute(insert_query, (title, content, topic_id, subscription_ids_str))
                    inserted_id = cur.fetchone()[0]
                    conn.commit()
                    logger.info(f"Newsletter stored in database with ID: {inserted_id}")
                    return inserted_id
        except Exception as e:
            logger.error(f"Error storing newsletter in database: {e}")
            return None

    def fetch_full_content(self, url):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract the main content (this is a simple example, might need adjustment for specific sites)
            content = soup.find('article') or soup.find('main') or soup.find('body')
            
            if content:
                # Remove scripts, styles, and comments
                for element in content(['script', 'style', 'comments']):
                    element.decompose()
                return content.get_text(strip=True)
            else:
                return None
        except Exception as e:
            logger.error(f"Error fetching full content from {url}: {e}")
            return None

    def categorize_article(self, article):
        title = article.get('title', '')
        description = article.get('description', '')
        content = article.get('content', '')
        
        full_text = f"{title} {description} {content}"
        
        categories = {
            'Technology': ['AI', 'machine learning', 'robotics', 'software', 'hardware', '5G', 'IoT'],
            'Healthcare': ['medical', 'health', 'pharma', 'biotech', 'drug discovery', 'telemedicine'],
            'Finance': ['banking', 'fintech', 'cryptocurrency', 'blockchain', 'investment'],
            'Manufacturing': ['industry 4.0', 'smart factory', '3D printing', 'automation'],
            'Energy': ['renewable', 'solar', 'wind', 'energy storage', 'smart grid'],
            'Retail': ['e-commerce', 'supply chain', 'inventory management', 'customer experience'],
            'Transportation': ['autonomous vehicles', 'electric vehicles', 'logistics', 'smart cities'],
            'Agriculture': ['precision agriculture', 'vertical farming', 'crop monitoring', 'agtech'],
            'Education': ['edtech', 'online learning', 'personalized learning', 'STEM'],
            'Entertainment': ['streaming', 'gaming', 'virtual reality', 'augmented reality']
        }
        
        article_categories = []
        for category, keywords in categories.items():
            if any(keyword.lower() in full_text.lower() for keyword in keywords):
                article_categories.append(category)
        
        return article_categories if article_categories else ['General AI & Tech']

    def edu_research_fetch(self, start_date, end_date, language='en', sort_by='relevancy'):
            edu_research_articles = []
            
            queries = [
                'AI course OR machine learning course',
                'AI research paper OR LLM research',
                'GenAI tutorial OR generative AI workshop',
                'Robotics seminar OR robotics research',
                'AI education OR machine learning education'
            ]

            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_query = {executor.submit(self._fetch_news, query, start_date, end_date, language, sort_by): query for query in queries}
                for future in as_completed(future_to_query):
                    query = future_to_query[future]
                    try:
                        articles = future.result()
                        edu_research_articles.extend(articles)
                    except Exception as exc:
                        logger.error(f'{query} generated an exception: {exc}')

            # Filter and sort articles
            filtered_articles = [
                article for article in edu_research_articles
                if article.get('title') and article.get('description')
            ]
            sorted_articles = sorted(filtered_articles, key=lambda x: x['publishedAt'], reverse=True)
            
            return sorted_articles[:5]  # Return top 5 articles

    def generate_html_content(self, dynamic_title, summary, highlights, articles):
        base_url = os.getenv('BASE_URL', 'https://www.thecuriodaily.com')
        current_date = datetime.now().strftime("%B %d, %Y")
        
        summary_html = f"<p>{summary}</p>"
        
        highlights_html = "<ul>" + "".join([
            f"""
            <li class="highlight-item">
                <span class="highlight-icon" style="background-color: {color};">
                    <i class="fas fa-{icon.lower().replace(' ', '-')}" aria-hidden="true"></i>
                </span>
                <span class="highlight-content">{highlight}</span>
            </li>
            """
            for highlight, icon, color in highlights
        ]) + "</ul>"
        
        articles_html = '<div class="article-grid">' + "".join([
            f"""
            <article class="article-card">
                <img src="{article.get('urlToImage', '/api/placeholder/400/300')}" alt="{article.get('title', 'Article image')}" class="article-image">
                <div class="article-content">
                    <h3>{article.get('title', 'Untitled Article')}</h3>
                    <p>{article.get('description', 'No description available.')[:100]}...</p>
                    <a href="{article.get('url', '#')}" class="read-more-btn" target="_blank">Read More</a>
                </div>
            </article>
            """
            for article in articles[:15]  # Limit to top 15 articles
            if article.get('title') and article.get('description') and article.get('url')
        ]) + '</div>'

        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()
        
        # Replace placeholders in the template
        template = template.replace('{{dynamic_title}}', dynamic_title)
        template = template.replace('{{current_date}}', current_date)
        template = template.replace('{{summary}}', summary_html)
        template = template.replace('{{highlights}}', highlights_html)
        template = template.replace('{{articles}}', articles_html)
        template = template.replace('{{base_url}}', base_url)
        
        return template

def store_html_content(html_content, filename):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"HTML content successfully stored in {filename}")
    except Exception as e:
        logger.error(f"Error storing HTML content in file: {e}")

def main():
    fetcher = EnhancedAINewsFetcher()
    
    today = datetime.now().date()
    last_week = today - timedelta(days=7)
    
    logger.info(f"Fetching top AI-related news articles across industries for the week {last_week} to {today}...")
    articles = fetcher.fetch_news(last_week, today)

    if articles:
        highlights = fetcher.generate_highlights(articles)
        logger.info(f"Highlights: {highlights}")
        
        summary = fetcher.generate_summary(highlights)
        logger.info(f"Summary: {summary}")
        
        highlight_texts = [highlight[0] for highlight in highlights]
        dynamic_title = fetcher.generate_dynamic_title(highlight_texts)
        logger.info(f"Dynamic Title: {dynamic_title}")
        
        # Generate HTML content
        html_content = fetcher.generate_html_content(dynamic_title, summary, highlights, articles)
        
        if html_content:
            # Store HTML content in a file
            filename = f"weekly_ai_tech_newsletter_{today.strftime('%Y%m%d')}.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"Newsletter generated and saved as {filename}")
        else:
            logger.error("Failed to generate HTML content")

        logger.info(f"Found {len(articles)} unique articles from trusted sources for the week {last_week} to {today}.")
    else:
        logger.info(f"No articles found from trusted sources for the week {last_week} to {today}.")

    logger.info("Weekly AI & Tech news fetching, summarization, and newsletter generation complete.")

if __name__ == "__main__":
    main()