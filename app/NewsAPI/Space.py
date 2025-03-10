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
from jinja2 import Environment, FileSystemLoader

current_dir = os.path.dirname(os.path.abspath(__file__))
web_template_path = os.path.join(current_dir, 'newsletter_template.html')
email_template_path = os.path.join(current_dir, 'email_template.html')


# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class SpaceNewsFetcher:
    def __init__(self):
        self.openai_model= os.getenv('OPENAI_MODEL')
        self.news_api_key = os.getenv('NEWS_API_KEY_1')
        if not self.news_api_key:
            raise ValueError("NEWS_API_KEY not found in environment variables")
        self.base_url = "https://newsapi.org/v2/everything"
        self.db_url = os.getenv('DATABASE_URL')
        if not self.db_url:
            raise ValueError("DATABASE_URL not found in environment variables")

        self.trusted_sources = [
            'nasa.gov', 'esa.int', 'space.com', 'spaceflightnow.com',
            'universetoday.com', 'planetary.org', 'spacenews.com',
            'astronomy.com', 'skyandtelescope.org', 'nasaspaceflight.com',
            'blueorigin.com', 'spacex.com', 'rocketlabusa.com',
            'arstechnica.com/science', 'sciencemag.org/space',
            'nature.com/subjects/astronomy-and-astrophysics'
        ]

        self.space_companies = [
            'NASA', 'ESA', 'SpaceX', 'Blue Origin', 'Rocket Lab', 'Virgin Galactic',
            'Boeing', 'Lockheed Martin', 'Northrop Grumman', 'ULA', 'Arianespace',
            'ISRO', 'JAXA', 'Roscosmos', 'CNSA', 'Maxar', 'Planet Labs', 'Firefly Aerospace',
            'Relativity Space', 'Axiom Space', 'Sierra Nevada Corporation'
        ]

        self.priority_topics = [
            'Mars exploration', 'Moon missions', 'Exoplanets', 'Space telescope',
            'Asteroid mining', 'Space tourism', 'Satellite constellation',
            'Space station', 'Rocket launch', 'Space debris', 'Solar system exploration',
            'Black hole', 'Cosmic microwave background', 'Dark matter', 'Dark energy'
        ]
        
        self.space_topics = [
            'Astronomy', 'Astrophysics', 'Cosmology', 'Planetary science',
            'Space exploration', 'Space technology', 'Astrobiology', 'Space policy',
            'Space weather', 'Space medicine', 'Space manufacturing',
            'Space communications', 'Space debris mitigation', 'Space law',
            'Satellite technology', 'Propulsion systems', 'Space habitats',
            'Space resources', 'Extraterrestrial life', 'Space archaeology'
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
    s.is_active = true and st.topic_id = 20
                    """)
                    cur.execute(query)
                    subscriptions = cur.fetchall()
                    return [{"id": str(sub[0]), "email": sub[1]} for sub in subscriptions]
        except Exception as e:
            logger.error(f"Error fetching active subscriptions: {e}")
            return []

    def fetch_news(self, date, language='en', sort_by='relevancy'):
        all_articles = []
        
        queries = [
            'Space exploration OR space discovery',
            'Mars mission OR Moon landing',
            'Exoplanet OR space telescope',
            'Rocket launch OR spacecraft',
            'Space station OR space habitat',
            'Asteroid OR comet OR solar system',
            'Space technology OR space innovation',
            'NASA OR ESA OR SpaceX OR Blue Origin'
        ]

        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_query = {executor.submit(self._fetch_news, query, date, language, sort_by): query for query in queries}
            for future in as_completed(future_to_query):
                query = future_to_query[future]
                try:
                    articles = future.result()
                    all_articles.extend(articles)
                except Exception as exc:
                    logger.error(f'{query} generated an exception: {exc}')

        # Filter out articles without content or images
        filtered_articles = [
            article for article in all_articles
            if article.get('title') and article.get('description') and article.get('urlToImage')
        ]

        # Sort and limit to top 10 articles
        sorted_articles = self.filter_and_sort_articles(filtered_articles)
        return sorted_articles[:10]

    def _fetch_news(self, query, date, language, sort_by):
        params = {
            'q': query,
            'from': date.isoformat(),
            'to': (date + timedelta(days=1)).isoformat(),
            'language': language,
            'sortBy': sort_by,
            'pageSize': 20,
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
            company_score = sum(content.count(company.lower()) for company in self.space_companies)
            
            return priority_score * 2 + company_score

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
            description = article.get('description', '')
            prompt = f"""
            Based on the following space-related article title and description:

            Title: {title}
            Description: {description}

            1. Rephrase the article into a concise highlight between 20 and 70 characters.
            2. Suggest an appropriate icon name that represents this highlight. The icon should be simple and widely available (e.g., from Font Awesome).
            3. Suggest a vibrant color for the icon (use hexadecimal color code).
            4. Categorize this highlight into one of these categories: Exploration, Technology, Discovery, Policy, or Innovation.

            Respond in the following format:
            Highlight: [Your rephrased highlight]
            Icon: [Your suggested icon name]
            Color: [Hexadecimal color code]
            Category: [Your category choice]
            """

            try:
                response = client.chat.completions.create(
                    model=self.openai_model,
                    messages=[
                        {"role": "system", "content": "You are an AI assistant that creates concise space news highlights and suggests relevant icons and colors."},
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
                category = result[3].split(': ')[1]

                if len(rephrased_highlight) < 20:
                    rephrased_highlight = rephrased_highlight.ljust(20)
                elif len(rephrased_highlight) > 70:
                    rephrased_highlight = rephrased_highlight[:67] + "..."
                
                highlights.append((rephrased_highlight, icon, color, category))
            except Exception as e:
                logger.error(f"Error generating highlight with OpenAI: {e}")
                short_title = title[:67] + "..." if len(title) > 70 else title.ljust(20)
                highlights.append((short_title, "rocket", "#0B3D91", "Exploration"))

        return highlights

    def generate_dynamic_title(self, highlights):
        prompt = f"""
        Based on the following space news highlights, generate a catchy and informative title 
        that summarizes the main themes or most significant developments. The title should 
        be engaging and specific to space advancements mentioned in the highlights.

        Highlights:
        {', '.join(highlights)}

        Generate a title in the format: "Space [Theme]: [Specific Detail]"
        For example: "Space Discovery: New Exoplanet With Earth-like Atmosphere Found"
        """

        try:
            response = client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "You are an AI assistant that creates engaging titles for space news summaries."},
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
            return "Today's Space Highlights"

    def generate_summary(self, highlights):
        highlight_texts = [highlight[0] for highlight in highlights]
        
        prompt = f"""
        Based on the following space news highlights, create a 4-line overview in a human tone:

        {', '.join(highlight_texts)}

        The overview should be engaging and summarize the main themes or developments in space exploration and astronomy.
        """

        try:
            response = client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "You are an AI assistant that creates engaging summaries of space news."},
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

    def store_newsletter(self, title, web_content, email_content, topic_id, subscription_ids):
        try:
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor() as cur:
                    insert_query = sql.SQL("""
                        INSERT INTO newsletters (title, content, email_content, topic_id, subscription_ids)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                    """)
                    subscription_ids_str = ','.join(subscription_ids)
                    cur.execute(insert_query, (title, web_content, email_content, topic_id, subscription_ids_str))
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
            
            content = soup.find('article') or soup.find('main') or soup.find('body')
            
            if content:
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
            'Space Exploration': ['exploration', 'mission', 'spacecraft', 'probe', 'rover'],
            'Astronomy': ['star', 'galaxy', 'planet', 'comet', 'asteroid', 'telescope'],
            'Space Technology': ['rocket', 'satellite', 'propulsion', 'spacecraft', 'space station'],
            'Space Policy': ['policy', 'regulation', 'treaty', 'space law', 'commercialization'],
            'Space Science': ['research', 'study', 'discovery', 'experiment', 'observation'],
            'Space Industry': ['company', 'startup', 'investment', 'commercial', 'launch provider']
        }
        
        article_categories = []
        for category, keywords in categories.items():
            if any(keyword in full_text.lower() for keyword in keywords):
                article_categories.append(category)
        
        return article_categories if article_categories else ['General Space News']

def generate_html_content(fetcher, dynamic_title, summary, highlights, articles, subscription_ids, is_email=False):
    base_url = os.getenv('BASE_URL', 'https://www.thecuriodaily.com')
    current_date = datetime.now().strftime("%B %d, %Y")
    
    summary_html = f"<p>{summary}</p>"
    
    highlights_html = "".join([
        f"""
        <div class="highlight-item">
            <span class="highlight-icon" style="background-color: {color};">
                <i class="fas fa-{icon.lower().replace(' ', '-')}" aria-hidden="true"></i>
            </span>
            <div class="highlight-content">
                <p>{highlight}</p>
            </div>
        </div>
        """
        for highlight, icon, color, category in highlights
    ])
    
    articles_html = "".join([
        f"""
        <article class="article">
            <span class="article-category">{', '.join(fetcher.categorize_article(article))}</span>
            <h3>{article.get('title', 'Untitled Article')}</h3>
            <img src="{article.get('urlToImage', '/api/placeholder/400/300')}" alt="Article image" class="article-image">
            <p>{article.get('description', 'No description available.')}</p>
            <a href="{article.get('url', '#')}" class="read-more" target="_blank">Read More</a>
        </article>
        """
        for article in articles
        if article.get('title') and article.get('description') and article.get('url')
    ])

    template_path = email_template_path if is_email else web_template_path
    
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
    
    # Replace placeholders in the template
    template = template.replace('{{dynamic_title}}', dynamic_title)
    template = template.replace('{{current_date}}', current_date)
    template = template.replace('{{summary}}', summary_html)
    template = template.replace('{{highlights}}', highlights_html)
    template = template.replace('{{articles}}', articles_html)
    template = template.replace('{{base_url}}', base_url)
    
    # Create a placeholder for the unsubscribe link
    template = template.replace('{{unsubscribe_link}}', '{{unsubscribe_link_placeholder}}')
    
    return template


def main():
    fetcher = SpaceNewsFetcher()
    base_url = os.getenv('BASE_URL', 'https://www.thecuriodaily.com')

    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    logger.info(f"Fetching top 10 AI-related news articles for {yesterday}...")
    articles = fetcher.fetch_news(yesterday)

    if articles:
        highlights = fetcher.generate_highlights(articles)
        logger.info(f"Highlights: {highlights}")
        
        summary = fetcher.generate_summary(highlights)
        logger.info(f"Summary: {summary}")
        
        highlight_texts = [highlight[0] for highlight in highlights]
        dynamic_title = fetcher.generate_dynamic_title(highlight_texts)
        logger.info(f"Dynamic Title: {dynamic_title}")
        
        # Fetch all active subscriptions
        subscriptions = fetcher.get_active_subscriptions()
        subscription_ids = [sub['id'] for sub in subscriptions]
        
        # Generate web content
        web_content = generate_html_content(
            fetcher, 
            dynamic_title, 
            summary, 
            highlights, 
            articles,
            subscription_ids,
            is_email=False
        )
        # Generate email content
        email_content = generate_html_content(
            fetcher, 
            dynamic_title, 
            summary, 
            highlights, 
            articles,
            subscription_ids,
            is_email=True
        )
        
        if web_content and email_content:
            logger.info("Storing newsletter for all active subscriptions...")
            inserted_id = fetcher.store_newsletter(dynamic_title, web_content, email_content, 20, subscription_ids)  # Assuming topic_id 1 for AI
            if inserted_id:
                logger.info(f"Newsletter stored successfully with ID: {inserted_id}")
            else:
                logger.error("Failed to store newsletter")
        else:
            logger.error("Failed to generate HTML content")

        logger.info(f"Found {len(articles)} unique articles from trusted sources for {yesterday}.")
    else:
        logger.info(f"No articles found from trusted sources for {yesterday}.")

    logger.info("AI news fetching, summarization, and newsletter generation complete.")

if __name__ == "__main__":
    main()
