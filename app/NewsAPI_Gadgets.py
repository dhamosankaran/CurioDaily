import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging
from textwrap import wrap
from openai import OpenAI
import psycopg2
from psycopg2 import sql

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class GadgetNewsFetcher:
    def __init__(self):
        self.news_api_key = os.getenv('NEWS_API_KEY')
        if not self.news_api_key:
            raise ValueError("NEWS_API_KEY not found in environment variables")
        self.base_url = "https://newsapi.org/v2/everything"
        self.preferred_entities = [
            'Apple', 'Samsung', 'Google', 'Sony', 'Microsoft', 'Amazon', 'Tesla',
            'LG', 'Huawei', 'OnePlus', 'Xiaomi', 'DJI', 'GoPro', 'Fitbit', 'Garmin',
            'Bose', 'Sonos', 'Oculus', 'Nintendo', 'Dyson', 'Roku', 'Nest'
        ]
        self.db_url = os.getenv('DATABASE_URL')
        if not self.db_url:
            raise ValueError("DATABASE_URL not found in environment variables")

        # List of trusted gadget news sources
        self.trusted_sources = [
            'theverge.com', 'techcrunch.com', 'engadget.com', 'gizmodo.com',
            'wired.com', 'cnet.com', 'arstechnica.com', 'techradar.com',
            'zdnet.com', 'digitaltrends.com', 'tomsguide.com', 'pcmag.com',
            'androidcentral.com', 'macrumors.com', '9to5mac.com', '9to5google.com',
            'appleinsider.com', 'slashgear.com', 'venturebeat.com', 'gadgetreview.com'
        ]

        self.focus_areas = [
            # Gadget Categories
            'Smartphones', 'Tablets', 'Laptops', 'Smartwatches', 'Fitness Trackers',
            'Wireless Earbuds', 'Smart Speakers', 'Smart Home Devices', 'Gaming Consoles',
            'VR Headsets', 'Drones', 'Action Cameras', 'E-readers',

            # Technology Trends
            '5G', 'AI in Gadgets', 'Foldable Devices', 'Augmented Reality', 'Internet of Things',
            'Wireless Charging', 'Biometric Security', 'Edge Computing', 'Quantum Computing',

            # Consumer Electronics
            'TVs', 'Home Theater Systems', 'Digital Cameras', 'Projectors', 'Portable Chargers',
            'Noise-Cancelling Headphones', 'Bluetooth Speakers', 'Smart Displays',

            # Emerging Technologies
            'Wearable Tech', 'Smart Glasses', 'Brain-Computer Interfaces', 'Haptic Feedback',
            'Flexible Displays', 'Self-Driving Cars', 'Robot Assistants', 'Smart Fabrics',

            # Gadget Software and Ecosystems
            'iOS', 'Android', 'Windows', 'macOS', 'App Ecosystems', 'Voice Assistants',
            'Smart Home Platforms', 'Cloud Gaming',

            # Industry Events and Releases
            'CES', 'IFA', 'MWC', 'Apple Events', 'Google I/O', 'Samsung Unpacked'
        ]

    def fetch_news(self, keywords, date, language='en', sort_by='relevancy'):
        all_keywords = keywords + self.focus_areas
        query = ' OR '.join(f'"{keyword}"' for keyword in all_keywords[:20])
        logger.info(f"Query: {query}")

        params = {
            'q': query,
            'from': date.isoformat(),
            'to': (date + timedelta(days=1)).isoformat(),
            'language': language,
            'sortBy': sort_by,
            'pageSize': 100,
            'apiKey': self.news_api_key,
            'domains': ','.join(self.trusted_sources)
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
        return unique_articles[:10]

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
        highlights = ""
        for index, article in enumerate(articles, start=1):
            title = article.get('title', 'Untitled Article')
            highlights += f"{index}. {title[:77]}{'...' if len(title) > 80 else ''}\n"
        return highlights.strip()

    def generate_dynamic_title(self, highlights):
        prompt = f"""
        Based on the following gadget news highlights, generate a catchy and informative title 
        that summarizes the main themes or most significant developments. The title should 
        be engaging and specific to gadget advancements mentioned in the highlights.

        Highlights:
        {highlights}

        Generate a title in the format: "Tech [Theme]: [Specific Detail]"
        For example: "Tech Revolution: Foldable Screens Redefine Smartphones"
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an AI assistant that creates engaging titles for gadget news summaries."},
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
            return "Today's Gadget Highlights"

    def generate_summary(self, article):
        title = article.get('title', 'No title available')
        description = article.get('description', 'No description available')
        url = article.get('url', 'No URL available')

        prompt = f"""
        Summarize the following gadget article in this format:

        🔧 **[CATCHY TITLE]: [Subtitle]**

        🚀 **Tech Breakthrough:**
        [1-2 sentences highlighting the key gadget-related information or development]

        💡 **Key Features:**
        • [First key feature]
        • [Second key feature]

        🔗 **Learn More:** {url}

        Use the article's content to fill in the brackets. Be concise, informative, and engaging. Use relevant emojis where appropriate.

        Article Title: {title}
        Article Description: {description}
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a tech-savvy AI assistant that creates engaging summaries of gadget news for social media and newsletters."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                n=1,
                stop=None,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating summary with OpenAI: {e}")
            return "Error generating summary."

    def generate_html_page(self, highlights, articles):
        dynamic_title = self.generate_dynamic_title(highlights)
        today_date = datetime.now().strftime("%b %d, %Y") 
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{dynamic_title}</title>
            <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap" rel="stylesheet">
            <style>
                :root {{
                    --primary-color: #1565c0;
                    --secondary-color: #0d47a1;
                    --background-color: #e3f2fd;
                    --text-color: #263238;
                    --accent-color: #ffd54f;
                    --highlight-box-color: #bbdefb;
                }}
                body {{
                    font-family: 'Roboto', sans-serif;
                    line-height: 1.4;
                    color: var(--text-color);
                    background-color: var(--background-color);
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: var(--primary-color);
                    color: #fff;
                    padding: 10px 0;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 1.8em;
                    font-weight: 700;
                }}
                .highlights {{
                    background-color: var(--highlight-box-color);
                    border-radius: 10px;
                    padding: 15px;
                    margin-top: 20px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                .highlights h2 {{
                    color: var(--secondary-color);
                    font-size: 1.4em;
                    margin: 0 0 10px 0;
                    text-align: center;
                }}
                .highlights ul {{
                    list-style-type: none;
                    padding: 0;
                    margin: 0;
                }}
                .highlights li {{
                    padding: 8px 10px;
                    background-color: #fff;
                    border-bottom: 1px solid #90caf9;
                }}
                .highlights li:last-child {{
                    border-bottom: none;
                }}
                .article-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                    margin-top: 20px;
                }}
                .article {{
                    background-color: #fff;
                    border-radius: 10px;
                    padding: 15px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                .article h3 {{
                    color: var(--secondary-color);
                    font-size: 1.3em;
                    margin: 0 0 10px 0;
                }}
                .article h4 {{
                    color: var(--accent-color);
                    font-size: 1.1em;
                    margin: 15px 0 5px 0;
                }}
                .key-features {{
                    padding-left: 20px;
                }}
                .read-more {{
                    display: inline-block;
                    margin-top: 10px;
                    color: var(--secondary-color);
                    text-decoration: none;
                    font-weight: bold;
                    transition: color 0.3s ease;
                }}
                .read-more:hover {{
                    color: var(--accent-color);
                }}
                .date {{
                    font-size: 0.8em;
                    color: var(--text-color);
                    font-weight: normal;
                    margin-left: 10px;
                }}
                .embedded-content {{
                    display: flex;
                    align-items: center;
                    margin-top: 15px;
                    background-color: #e3f2fd;
                    border: 1px solid #90caf9;
                    border-radius: 8px;
                    overflow: hidden;
                }}
                .article-image {{
                    width: 100px;
                    height: 100px;
                    object-fit: cover;
                }}
                .embedded-text {{
                    padding: 10px;
                    flex-grow: 1;
                }}
                .article-source {{
                    font-size: 0.8em;
                    color: #1565c0;
                }}
            </style>
        </head>
        <body>
            <header class="header">
                <h1>{dynamic_title}</h1>
            </header>
            
            <main class="container">
                <section class="highlights">
                    <h2>Key Gadget Highlights <span class="date">{today_date}</span></h2>
                    {self.format_highlights(highlights)}
                </section>
                
                <section class="article-grid">
                    {''.join(self.generate_article_html(article) for article in articles)}
                </section>
            </main>
        </body>
        </html>
        """
        return html_content

    def format_highlights(self, highlights):
        highlight_points = highlights.split('\n')
        formatted_highlights = "<ul>\n"
        for point in highlight_points:
            formatted_highlights += f"    <li>{point}</li>\n"
        formatted_highlights += "</ul>"
        return formatted_highlights

    def generate_article_html(self, article):
        summary = self.generate_summary(article)
        
        sections = summary.split('\n\n')
        
        title = "Untitled Article"
        tech_breakthrough = ""
        key_features = []
        learn_more = article.get('url', '#')

        for section in sections:
            if section.startswith('🔧'):
                title = section.strip('🔧 *')
            elif section.startswith('🚀'):
                tech_breakthrough = section.replace('🚀 **Tech Breakthrough:**', '').strip()
            elif section.startswith('💡'):
                key_features = section.replace('💡 **Key Features:**', '').strip().split('\n')
            elif section.startswith('🔗'):
                learn_more = section.replace('🔗 **Learn More:**', '').strip() or learn_more

        title = title[:55] + '...' if len(title) > 60 else title

        key_features_html = ""
        if key_features:
            key_features_html = f"""
            <h4>Key Features</h4>
            <ul class="key-features">
                {''.join(f'<li>{feature.strip("• ")}</li>' for feature in key_features)}
            </ul>
            """

        return f"""
        <article class="article">
            <h3>{title}</h3>
            <p>{tech_breakthrough}</p>
            {key_features_html}
            <div class="embedded-content">
                <img src="{article.get('urlToImage', '/api/placeholder/400/300')}" alt="Article image" class="article-image">
                <div class="embedded-text">
                    <a href="{learn_more}" target="_blank" rel="noopener noreferrer" class="read-more">Read Full Article</a>
                    <p class="article-source">{article.get('source', {}).get('name', 'Unknown Source')}</p>
                </div>
            </div>
        </article>
        """

    def save_html_page(self, html_content, filename="gadget_news_highlights.html"):
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_content)
        logger.info(f"HTML page saved as {filename}")

    def store_newsletter(self, title, content):
        """
        Store the newsletter information in the database.
        
        Args:
        title (str): The title of the newsletter.
        content (str): The HTML content of the newsletter.
        
        Returns:
        int: The ID of the inserted row, or None if the insertion failed.
        """
        try:
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor() as cur:
                    insert_query = sql.SQL("""
                        INSERT INTO newsletters (title, content, topic_id)
                        VALUES (%s, %s, %s)
                        RETURNING id
                    """)
                    cur.execute(insert_query, (title, content, 13))  # Assuming 4 is the topic_id for Gadgets
                    inserted_id = cur.fetchone()[0]
                    conn.commit()
                    logger.info(f"Newsletter stored in database with ID: {inserted_id}")
                    return inserted_id
        except Exception as e:
            logger.error(f"Error storing newsletter in database: {e}")
            return None

def main():
    fetcher = GadgetNewsFetcher()
    
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    keywords = [
        'new gadget', 'tech innovation', 'smart device', 'wearable tech',
        'consumer electronics', 'mobile technology', 'smart home', 'AI gadgets',
        'IoT devices', 'wireless technology', 'virtual reality', 'augmented reality',
        'smartphone features', 'laptop innovation', 'gaming hardware', 'audio technology',
        'camera tech', 'fitness gadgets', 'electric vehicles', 'robotics'
    ]

    logger.info(f"Fetching top gadget-related news articles for {yesterday}...")
    articles = fetcher.fetch_news(keywords, yesterday, sort_by='relevancy')

    if articles:
        highlights = fetcher.generate_highlights(articles)
        logger.info("Generating HTML page...")
        html_content = fetcher.generate_html_page(highlights, articles)
        
        dynamic_title = fetcher.generate_dynamic_title(highlights)
        
        logger.info("Storing newsletter in database...")
        inserted_id = fetcher.store_newsletter(dynamic_title, html_content)
        if inserted_id:
            logger.info(f"Newsletter stored successfully with ID: {inserted_id}")
        else:
            logger.error("Failed to store newsletter in database")

        fetcher.save_html_page(html_content)

        logger.info(f"Found {len(articles)} unique articles from trusted sources for {yesterday}. HTML page generated and stored in database.")
    else:
        logger.info(f"No articles found from trusted sources for {yesterday}.")

    logger.info("Gadget news fetching, summarization, HTML generation, and database storage complete.")

if __name__ == "__main__":
    main()