import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging
from openai import OpenAI
import psycopg2
from psycopg2 import sql

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

current_dir = os.path.dirname(os.path.abspath(__file__))
template_path = os.path.join(current_dir, 'weekly_newsletter_template.html')

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class BusinessFinanceWeeklyFetcher:
    def __init__(self):
        self.news_api_key = os.getenv('NEWS_API_KEY_Weekly')
        if not self.news_api_key:
            raise ValueError("NEWS_API_KEY not found in environment variables")
        self.base_url = "https://newsapi.org/v2/everything"
        self.db_url = os.getenv('DATABASE_URL')
        if not self.db_url:
            raise ValueError("DATABASE_URL not found in environment variables")

    def fetch_news(self, start_date, end_date, language='en', sort_by='relevancy'):
        # Comprehensive query for Business & Finance-related news and insights
        query = ("(business OR finance OR economy OR stock market OR investment OR "
                 "entrepreneurship OR corporate OR financial markets OR banking OR "
                 "economic policy OR mergers and acquisitions OR startups OR "
                 "venture capital OR IPO OR earnings report OR financial technology OR "
                 "market trends OR business strategy OR economic indicators OR "
                 "financial regulation OR global trade OR business innovation OR "
                 "financial planning OR business leadership OR economic growth OR "
                 "financial services OR business analytics)")

        articles = self._fetch_news(query, start_date, end_date, language, sort_by)
        
        filtered_articles = [
            article for article in articles
            if article.get('title') and article.get('description') and article.get('urlToImage')
        ]

        sorted_articles = self.filter_and_sort_articles(filtered_articles)
        return sorted_articles[:10]  # Return only top 10 articles

    def _fetch_news(self, query, start_date, end_date, language, sort_by):
        params = {
            'q': query,
            'from': start_date.isoformat(),
            'to': end_date.isoformat(),
            'language': language,
            'sortBy': sort_by,
            'pageSize': 10,  # Fetch only 10 articles
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
            
            priority_topics = [
                'business', 'finance', 'economy', 'stock market', 'investment',
                'entrepreneurship', 'corporate', 'financial markets', 'banking',
                'economic policy', 'mergers and acquisitions', 'startups',
                'venture capital', 'IPO', 'earnings report', 'financial technology',
                'market trends', 'business strategy', 'economic indicators',
                'financial regulation', 'global trade', 'business innovation',
                'financial planning', 'business leadership', 'economic growth',
                'financial services', 'business analytics', 'CEO', 'profit',
                'revenue', 'market share', 'business expansion', 'economic forecast'
            ]
            
            priority_score = sum(content.count(topic.lower()) for topic in priority_topics)
            return priority_score

        sorted_articles = sorted(articles, key=relevance_score, reverse=True)
        return sorted_articles

    def generate_highlights(self, articles):
        highlights = []

        for article in articles:
            title = article.get('title', 'Untitled Article')
            prompt = f"""
            Based on the following Business & Finance-related news article title:

            Title: {title}

            1. Create a concise highlight of maximum 130 characters that captures the essence of the Business & Finance-related news or insight.
            2. Suggest an appropriate icon name that represents this highlight, focusing on business and finance themes. The icon should be simple and widely available (e.g., from Font Awesome).
            3. Suggest a vibrant color for the icon (use hexadecimal color code) that fits the business and finance theme.

            Respond in the following format:
            Highlight: [Your rephrased highlight]
            Icon: [Your suggested icon name]
            Color: [Hexadecimal color code]
            """

            try:
                response = client.chat.completions.create(
                    model="gpt-4-1106-preview",
                    messages=[
                        {"role": "system", "content": "You are an AI assistant that creates concise Business & Finance-related news highlights and suggests relevant icons and colors."},
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

                if len(rephrased_highlight) > 130:
                    rephrased_highlight = rephrased_highlight[:127] + "..."
                
                highlights.append((rephrased_highlight, icon, color))
            except Exception as e:
                logger.error(f"Error generating highlight with OpenAI: {e}")
                short_title = title[:127] + "..." if len(title) > 130 else title
                highlights.append((short_title, "chart-line", "#0056b3"))  # Using a chart-line icon and a professional blue color

        return highlights

    def generate_dynamic_overview(self, highlights):
        highlight_texts = [highlight[0] for highlight in highlights[:7]]
        prompt = f"""
        Based on the following Business & Finance-related news highlights, generate a catchy and informative overview
        that summarizes the main themes or most significant developments. The overview should
        be engaging and specific to Business & Finance developments mentioned in the highlights.

        Highlights:
        {', '.join(highlight_texts)}

        Generate an overview in the format: "Business & Finance Weekly: [Theme]: [Specific Detail]"
        For example: "Business & Finance Weekly: Tech Boom: Major IPO Shakes Up Stock Market"

        The overview should be 2-3 sentences long, capturing the essence of the week's Business & Finance developments based on the highlights.
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[
                    {"role": "system", "content": "You are an AI assistant that creates engaging overviews for Business & Finance-related news summaries."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                n=1,
                stop=None,
                temperature=0.5,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating overview with OpenAI: {e}")
            return "Business & Finance Weekly: Significant developments reshape the global business and financial landscape."

    def store_weekly_newsletter(self, title, content, key_highlight, topic_id):
        try:
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor() as cur:
                    insert_query = sql.SQL("""
                        INSERT INTO public.weekly_newsletter 
                        (title, content, weeklynewsletter_topic_id, key_highlight)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id
                    """)
                    cur.execute(insert_query, (title, content, topic_id, key_highlight))
                    inserted_id = cur.fetchone()[0]
                    conn.commit()
                    logger.info(f"Weekly newsletter stored in database with ID: {inserted_id}")
                    return inserted_id
        except Exception as e:
            logger.error(f"Error storing weekly newsletter in database: {e}")
            return None

    def generate_html_content(self, dynamic_overview, highlights, articles):
        base_url = os.getenv('BASE_URL', 'https://www.curiodaily.com')
        
        highlights_html = "".join([
            f"<li>{highlight}</li>"
            for highlight, _, _ in highlights[:7]
        ])
        
        articles_html = "".join([
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
            for article in articles
            if article.get('title') and article.get('description') and article.get('url')
        ])

        current_date = datetime.now()
        formatted_date = current_date.strftime("%b %d, %Y")

        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()
        
        template = template.replace('{{dynamic_overview}}', dynamic_overview)
        template = template.replace('{{highlights}}', highlights_html)
        template = template.replace('{{articles}}', articles_html)
        template = template.replace('{{base_url}}', base_url)
        template = template.replace('{{topic}}', "Business & Finance Weekly")
        template = template.replace('{{date}}', formatted_date)
            
        return template

def store_html_content(html_content, filename):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"HTML content successfully stored in {filename}")
    except Exception as e:
        logger.error(f"Error storing HTML content in file: {e}")

def main():
    fetcher = BusinessFinanceWeeklyFetcher()
    today = datetime.now().date()
    last_week = today - timedelta(days=7)
    
    logger.info(f"Fetching top 10 Business & Finance Weekly news articles for the week {last_week} to {today}...")
    articles = fetcher.fetch_news(last_week, today)

    if articles:
        highlights = fetcher.generate_highlights(articles)
        logger.info(f"Highlights: {highlights}")

        dynamic_overview = fetcher.generate_dynamic_overview(highlights)
        logger.info(f"Dynamic Overview: {dynamic_overview}")

        html_content = fetcher.generate_html_content(dynamic_overview, highlights, articles)

        if html_content:
            filename = f"weekly_Business_Finance_{today.strftime('%Y%m%d')}.html"
            store_html_content(html_content, filename)
            logger.info(f"Newsletter generated and saved as {filename}")

            key_highlight = highlights[0][0] if highlights else ""
            inserted_id = fetcher.store_weekly_newsletter(
                title=dynamic_overview,
                content=html_content,
                key_highlight=", ".join([h[0] for h in highlights[:3]]),  # Store top 3 highlights as key highlights
                topic_id=2  # Topic ID for Business & Finance Weekly newsletters
            )

            if inserted_id:
                logger.info(f"Newsletter stored in database with ID: {inserted_id}")
            else:
                logger.error("Failed to store newsletter in database")

        else:
            logger.error("Failed to generate HTML content")

        logger.info(f"Found {len(articles)} unique articles for the week {last_week} to {today}.")
    else:
        logger.info(f"No articles found for the week {last_week} to {today}.")

    logger.info("Weekly Business & Finance news fetching, summarization, and newsletter generation complete.")

if __name__ == "__main__":
    main()