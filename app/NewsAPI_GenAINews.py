import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging
from textwrap import wrap
from openai import OpenAI
import psycopg2
from psycopg2 import sql
import re
from collections import Counter

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
        self.db_url = os.getenv('DATABASE_URL')
        if not self.db_url:
            raise ValueError("DATABASE_URL not found in environment variables")

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
        return sorted_articles[:6]

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


    def generate_highlights(self, articles):
        highlights = ""
        for index, article in enumerate(articles, start=1):
            title = article.get('title', 'Untitled Article')
            highlights += f"{index}. {title[:77]}{'...' if len(title) > 80 else ''}\n"
        return highlights.strip()

    def generate_dynamic_title(self, highlights):
        prompt = f"""
        Based on the following AI news highlights, generate a catchy and informative title 
        that summarizes the main themes or most significant developments. The title should 
        be engaging and specific to AI advancements mentioned in the highlights.

        Highlights:
        {highlights}

        Generate a title in the format: "AI [Theme]: [Specific Detail]"
        For example: AI Breakthroughs: Language Models Achieve Human-Level Understanding
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
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

    def rephrase_highlights(self, highlights):
        prompt = f"""
        Rephrase the following AI and tech news highlights to make them more impactful and engaging. 
        Maintain the numbering and overall structure, but make each highlight more compelling:

        {highlights}

        Focus on the most groundbreaking or significant aspects of each highlight. Use powerful language 
        and emphasize the potential impact or innovation of each item.
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an AI assistant that rephrases news highlights to make them more impactful and engaging."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                n=1,
                stop=None,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error rephrasing highlights with OpenAI: {e}")
            return highlights  # Return original highlights if there's an error


    def generate_summary(self, article):
        title = article.get('title', 'No title available')
        description = article.get('description', 'No description available')
        url = article.get('url', 'No URL available')

        prompt = f"""
        Summarize the following article in this format:

        🔥 **[CATCHY TITLE]: [Subtitle]**

        🚀 **Innovation Spotlight:**
        [2-3 sentences highlighting the key innovation, development, or news]

        💡 **Key Takeaways:**
        • [First key point]
        • [Second key point]
        • [Third key point]

        🌍 **Impact & Significance:**
        [2-3 sentences on why this matters and its potential impact]

        🔮 **Future Implications:**
        [1-2 sentences on potential future developments or applications]

        🔗 **Deep Dive:** {url}

        Use the article's content to fill in the brackets. Be concise, informative, and engaging. Use relevant emojis where appropriate.

        Article Title: {title}
        Article Description: {description}
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a tech-savvy AI assistant that creates engaging summaries of AI and technology news for social media and newsletters."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                n=1,
                stop=None,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating summary with OpenAI: {e}")
            return "Error generating summary."
            logger.error(f"Error generating summary with OpenAI: {e}")
            return "Error generating summary."

    def format_article_with_summary(self, article, index):
        formatted_article = self.format_article(article, index)
        summary = self.generate_summary(article)
        return f"{formatted_article}\n\nSummarized Content for LinkedIn/Newsletter:\n{summary}\n"


    def generate_html_page(self, highlights, articles):
        dynamic_title = self.generate_dynamic_title(highlights)
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
                    --primary-color: #1a237e;
                    --secondary-color: #3f51b5;
                    --background-color: #f5f5f5;
                    --text-color: #212121;
                    --accent-color: #ff4081;
                    --highlight-box-color: #e8eaf6;
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
                    max-width: 1000px;
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
                    border-bottom: 1px solid #e0e0e0;
                }}
                .highlights li:last-child {{
                    border-bottom: none;
                }}
                .article {{
                    background-color: #fff;
                    border-radius: 10px;
                    padding: 15px;
                    margin-top: 20px;
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
                .key-takeaways {{
                    padding-left: 20px;
                }}
                .read-more {{
                    display: inline-block;
                    margin-top: 10px;
                    color: var(--secondary-color);
                    text-decoration: none;
                    font-weight: bold;
                }}
                .modal {{
                    display: none;
                    position: fixed;
                    z-index: 1;
                    left: 0;
                    top: 0;
                    width: 100%;
                    height: 100%;
                    overflow: auto;
                    background-color: rgba(0,0,0,0.4);
                }}
                .modal-content {{
                    background-color: #fefefe;
                    margin: 15% auto;
                    padding: 20px;
                    border: 1px solid #888;
                    width: 80%;
                    max-width: 800px;
                }}
                .close {{
                    color: #aaa;
                    float: right;
                    font-size: 28px;
                    font-weight: bold;
                    cursor: pointer;
                }}
                .close:hover,
                .close:focus {{
                    color: #000;
                    text-decoration: none;
                    cursor: pointer;
                }}
                #embedded-content {{
                    width: 100%;
                    height: 600px;
                    border: none;
                }}
            </style>
        </head>
        <body>
            <header class="header">
                <h1>{dynamic_title}</h1>
            </header>
            
            <main class="container">
                <section class="highlights">
                    <h2>Key AI Highlights</h2>
                    {self.format_highlights(highlights)}
                </section>
                
                <section class="featured-articles">
                    {''.join(self.generate_article_html(article) for article in articles)}
                </section>
            </main>

            <div id="modal" class="modal">
                <div class="modal-content">
                    <span class="close">&times;</span>
                    <iframe id="embedded-content"></iframe>
                </div>
            </div>

            <script>
                var modal = document.getElementById('modal');
                var embeddedContent = document.getElementById('embedded-content');
                var span = document.getElementsByClassName('close')[0];

                function openModal(url) {{
                    embeddedContent.src = url;
                    modal.style.display = 'block';
                }}

                span.onclick = function() {{
                    modal.style.display = 'none';
                    embeddedContent.src = '';
                }}

                window.onclick = function(event) {{
                    if (event.target == modal) {{
                        modal.style.display = 'none';
                        embeddedContent.src = '';
                    }}
                }}
            </script>
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
        title = sections[0].strip('🔥 *')
        innovation_spotlight = sections[1].replace('🚀 **Innovation Spotlight:**', '').strip()
        key_takeaways = sections[2].replace('💡 **Key Takeaways:**', '').strip().split('\n')
        impact_significance = sections[3].replace('🌍 **Impact & Significance:**', '').strip()
        future_implications = sections[4].replace('🔮 **Future Implications:**', '').strip()
        deep_dive = sections[5].replace('🔗 **Deep Dive:**', '').strip()

        return f"""
        <article class="article">
            <h3>{title}</h3>
            <p>{innovation_spotlight}</p>
            <h4>Key Takeaways</h4>
            <ul class="key-takeaways">
                {''.join(f'<li>{takeaway.strip("• ")}</li>' for takeaway in key_takeaways)}
            </ul>
            <h4>Impact & Significance</h4>
            <p>{impact_significance}</p>
            <h4>Future Implications</h4>
            <p>{future_implications}</p>
            <a href="javascript:void(0);" onclick="openModal('{deep_dive}')" class="read-more">Read Full Article</a>
        </article>
        """

 

    def save_html_page(self, html_content, filename="ai_news_highlights.html"):
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
                    cur.execute(insert_query, (title, content, 1))
                    inserted_id = cur.fetchone()[0]
                    conn.commit()
                    logger.info(f"Newsletter stored in database with ID: {inserted_id}")
                    return inserted_id
        except Exception as e:
            logger.error(f"Error storing newsletter in database: {e}")
            return None


def main():
    fetcher = AINewsFetcher()
    
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    keywords = [
        'artificial intelligence', 'machine learning', 'deep learning',
        'GPT', 'LLM', 'generative AI', 'robot', 'humanoid', 'AI ethics',
        'AI breakthrough', 'robotic breakthrough', 'humanoid development'
    ]

    # Initialize articles lists
    popular_articles = []
    relevant_articles = []

    # Fetch popular articles
    logger.info(f"Fetching top 10 popular AI-related news articles from {yesterday} to {today}...")
    popular_articles = fetcher.fetch_news(keywords, yesterday, today, sort_by='popularity')

    # Fetch relevant articles
    #logger.info(f"Fetching top 10 relevant AI-related news articles from {yesterday} to {today}...")
    #relevant_articles = fetcher.fetch_news(keywords, yesterday, today, sort_by='relevancy')

    # Combine and deduplicate articles
    all_articles = list({article['url']: article for article in popular_articles + relevant_articles}.values())
    all_articles = list({article['url']: article for article in popular_articles}.values())


    if all_articles:
        # Generate highlights
        highlights = fetcher.generate_highlights(all_articles)
        
        # Generate image based on highlights
        #logger.info("Generating image based on highlights...")
        #image_prompt = f"Create an abstract image representing AI news highlights: {highlights}"
        #image_url = fetcher.generate_image(image_prompt)

        # Generate HTML page with dynamic title
        logger.info("Generating HTML page...")
        html_content = fetcher.generate_html_page(highlights, all_articles[:6])  # Use top 5 articles
        
        # Extract dynamic title for database storage
        dynamic_title = fetcher.generate_dynamic_title(highlights)
        
        # Store newsletter in database
        logger.info("Storing newsletter in database...")
        inserted_id = fetcher.store_newsletter(dynamic_title, html_content)
        if inserted_id:
            logger.info(f"Newsletter stored successfully with ID: {inserted_id}")
        else:
            logger.error("Failed to store newsletter in database")

        fetcher.save_html_page(html_content)

        logger.info(f"Found {len(all_articles)} unique articles. HTML page generated with top 5 articles and stored in database.")
    else:
        logger.info("No articles found for the given criteria.")

    logger.info("AI news fetching, summarization, HTML generation, and database storage complete.")



if __name__ == "__main__":
    main()