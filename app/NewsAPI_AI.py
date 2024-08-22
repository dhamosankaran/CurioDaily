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


class AINewsFetcher:
    def __init__(self):
        self.news_api_key = os.getenv('NEWS_API_KEY')
        if not self.news_api_key:
            raise ValueError("NEWS_API_KEY not found in environment variables")
        self.base_url = "https://newsapi.org/v2/everything"
        self.preferred_entities = [
            'OpenAI', 'DeepMind', 'Microsoft', 'MIT', 'Mistral', 
            'Anthropic', 'Meta', 'IBM', 'NVIDIA', 'Intel', 'Apple', 
            'Amazon', 'Boston Dynamics', 'Tesla', 'Google'
        ]
        self.db_url = os.getenv('DATABASE_URL')
        if not self.db_url:
            raise ValueError("DATABASE_URL not found in environment variables")

                # List of trusted sources
        self.trusted_sources = [
            # Major Tech News Sites
            'techcrunch.com', 'wired.com', 'technologyreview.com', 'theverge.com',
            'arstechnica.com', 'venturebeat.com', 'zdnet.com', 'engadget.com',
            'cnet.com', 'techmeme.com', 'thenextweb.com', 'protocol.com',
            
            # Scientific Publications
            'nature.com', 'sciencemag.org', 'ieee.org', 'sciencedaily.com',
            'newscientist.com', 'scientificamerican.com', 'phys.org',
            
            # Business and General News
            'forbes.com', 'bloomberg.com', 'reuters.com', 'nytimes.com',
            'wsj.com', 'washingtonpost.com', 'bbc.com', 'theguardian.com',
            'economist.com', 'ft.com',
            
            # AI-Focused News Sites
            'artificialintelligence-news.com', 'ai.stanford.edu', 'aitrends.com',
            'deeplearning.ai', 'lexology.com/ai', 'bdtechtalks.com',
            
            # AI Company Official Blogs and Websites
            'openai.com', 'blog.google', 'ai.googleblog.com', 'deepmind.com',
            'blog.bing.com', 'blogs.microsoft.com', 'research.ibm.com',
            'ai.facebook.com', 'blog.twitter.com', 'amazon.science',
            'blogs.nvidia.com', 'intel.com/content/www/us/en/artificial-intelligence',
            'anthropic.com', 'mistral.ai', 'x.ai', 'stability.ai',
            
            # AI Research Institutions
            'ai.mit.edu', 'humancompatible.ai', 'cset.georgetown.edu',
            'futureoflife.org', 'cser.ac.uk', 'fhi.ox.ac.uk',
            
            # Tech Giants' AI Pages
            'ai.google', 'azure.microsoft.com/en-us/solutions/ai',
            'aws.amazon.com/machine-learning', 'www.ibm.com/watson',
            
            # AI Ethics and Policy
            'aiethicslab.com', 'ainowinstitute.org', 'partnershiponai.org',
            'caidp.org', 'hai.stanford.edu',
            
            # AI in Specific Domains
            'healthitanalytics.com', 'aiin.healthcare', 'emerj.com'
        ]
        self.focus_companies = [
            # Major AI Research Companies
            'OpenAI', 'DeepMind', 'Anthropic', 'X.AI', 'Google AI', 'Microsoft Research',
            'IBM Watson', 'Facebook AI Research', 'Amazon AI', 'Apple Machine Learning',
            
            # AI Chip Companies
            'NVIDIA', 'Intel AI', 'AMD AI', 'Graphcore',
            
            # AI in Cloud Services
            'Google Cloud AI', 'AWS AI', 'Azure AI', 'IBM Cloud AI',
            
            # Specialized AI Companies
            'Databricks', 'Palantir', 'C3.ai', 'DataRobot', 'H2O.ai',
            
            # AI in Robotics
            'Boston Dynamics', 'iRobot', 'ABB Robotics',
            
            # AI Ethics and Safety Organizations
            'AI Safety Center', 'Center for AI Safety', 'Machine Intelligence Research Institute',
            'Future of Humanity Institute', 'AI Alignment', 'Center for Human-Compatible AI',
            
            # AI Governance and Policy
            'Partnership on AI', 'AI Now Institute', 'OpenAI Policy Team', 'DeepMind Ethics & Society',
            
            # Emerging AI Startups
            'Cohere', 'Hugging Face', 'Stability AI', 'Midjourney', 'Inflection AI',
            
            # AI in Healthcare
            'DeepMind Health', 'IBM Watson Health', 'Google Health AI',
            
            # AI in Finance
            'Two Sigma', 'Citadel AI', 'JPMorgan AI Research',
            
            # AI in Autonomous Vehicles
            'Waymo', 'Tesla AI', 'Cruise Automation', 'Argo AI',
            
            # AI Research Institutes
            'Allen Institute for AI', 'MIT AI Lab', 'Stanford AI Lab', 'Berkeley AI Research'
        ]

    def fetch_news(self, keywords, date, language='en', sort_by='relevancy'):

        all_keywords = keywords
        #logger.info (f"all keywords: {all_keywords}")
        query = ' OR '.join(f'"{keyword}"' for keyword in all_keywords[:20])  # Increased limit to include more focus companies
        logger.info (f"query:........ {query}")

        params = {
            'q': query,
            'from': date.isoformat(),
            'to': (date + timedelta(days=1)).isoformat(),  # End of the day
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
        #trusted_articles = [article for article in unique_articles if self.is_trusted_source(article)]
        #sorted_articles = self.sort_articles_by_preference(trusted_articles)
        return unique_articles[:10]  # Return top 6 articles for 3x2 grid

    def is_trusted_source(self, article):
        source_url = article.get('url', '')
        return any(trusted_domain in source_url for trusted_domain in self.trusted_sources)

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

            company_score = sum(content.count(company.lower()) for company in self.focus_companies) * 5


            entity_score = sum(content.count(entity.lower()) for entity in self.preferred_entities)

            ai_keywords = ['artificial intelligence', 'machine learning', 'deep learning', 'neural network']
            genai_keywords = ['generative ai', 'gpt', 'llm', 'large language model']
            robot_keywords = ['robot', 'humanoid', 'android', 'automaton']
            
            ai_score = sum(content.count(keyword) for keyword in ai_keywords)
            genai_score = sum(content.count(keyword) for keyword in genai_keywords)
            robot_score = sum(content.count(keyword) for keyword in robot_keywords)

            total_score = company_score + (entity_score * 2) + (ai_score * 1.5) + (genai_score * 2) + (robot_score * 2.5)

            return total_score

        return sorted(articles, key=preference_score, reverse=True)


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

    def generate_summary(self, article):
        title = article.get('title', 'No title available')
        description = article.get('description', 'No description available')
        url = article.get('url', 'No URL available')

        prompt = f"""
        Summarize the following article in this format:

        🔥 **[CATCHY TITLE]: [Subtitle]**

        🚀 **Innovation Spotlight:**
        [1-2 sentences highlighting the key innovation, development, or news]

        💡 **Key Takeaways:**
        • [First key point]
        • [Second key point]

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
                    border-bottom: 1px solid #e0e0e0;
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
                .key-takeaways {{
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
                    background-color: #f8f9fa;
                    border: 1px solid #e9ecef;
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
                    color: #6c757d;
                }}
                .embed-container {{
                    margin-top: 15px;
                }}
                .embed-container iframe {{
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
                    <h2>Key AI Highlights <span class="date">{today_date}</span></h2>
                    {self.format_highlights(highlights)}
                </section>
                
                <section class="article-grid">
                    {''.join(self.generate_article_html(article) for article in articles)}
                </section>
            </main>

            <script>
            function toggleEmbed(embedId, url) {{
                var container = document.getElementById(embedId);
                if (container.style.display === "none") {{
                    container.style.display = "block";
                    container.querySelector('iframe').src = url;
                }} else {{
                    container.style.display = "none";
                    container.querySelector('iframe').src = "about:blank";
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
        
        title = "Untitled Article"
        innovation_spotlight = ""
        key_takeaways = []
        deep_dive = article.get('url', '#')  # Default to '#' if no URL is available

        for section in sections:
            if section.startswith('🔥'):
                title = section.strip('🔥 *')
            elif section.startswith('🚀'):
                innovation_spotlight = section.replace('🚀 **Innovation Spotlight:**', '').strip()
            elif section.startswith('💡'):
                key_takeaways = section.replace('💡 **Key Takeaways:**', '').strip().split('\n')
            elif section.startswith('🔗'):
                deep_dive = section.replace('🔗 **Deep Dive:**', '').strip() or deep_dive

        # Limit title to 50 characters
        title = title[:47] + '...' if len(title) > 50 else title

        key_takeaways_html = ""
        if key_takeaways:
            key_takeaways_html = f"""
            <h4>Key Takeaways</h4>
            <ul class="key-takeaways">
                {''.join(f'<li>{takeaway.strip("• ")}</li>' for takeaway in key_takeaways)}
            </ul>
            """

        # Generate a unique ID for this article's embedded content
        embed_id = f"embed-{hash(title)}"

        return f"""
        <article class="article">
            <h3>{title}</h3>
            <p>{innovation_spotlight}</p>
            {key_takeaways_html}
            <div class="embedded-content">
                <img src="{article.get('urlToImage', '/api/placeholder/400/300')}" alt="Article image" class="article-image">
                <div class="embedded-text">
                    <a href="#" onclick="toggleEmbed('{embed_id}', '{deep_dive}'); return false;" class="read-more">Read Full Article</a>
                    <p class="article-source">{article.get('source', {}).get('name', 'Unknown Source')}</p>
                </div>
            </div>
            <div id="{embed_id}" class="embed-container" style="display: none;">
                <iframe src="about:blank" width="100%" height="600" frameborder="0"></iframe>
            </div>
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
        'artificial intelligence', 'generative AI', 'large language models', 'AI humanoids',
        'GPT-4', 'ChatGPT', 'AI breakthroughs', 'AI ethics', 'AI governance', 'AI safety',
        'AI regulation', 'conversational AI', 'AI assistants', 'multimodal AI', 'AI in robotics',
        'AI-human interaction', 'neural networks', 'AI policy', 'AGI development', 'AI startups'
    ]

    logger.info(f"Fetching top AI-related news articles for {yesterday}...")
    articles = fetcher.fetch_news(keywords, yesterday, sort_by='relevancy')

    logger.info(f"Fetching top AI-related news articles for {yesterday}...")
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

    logger.info("AI news fetching, summarization, HTML generation, and database storage complete.")

if __name__ == "__main__":
    main()