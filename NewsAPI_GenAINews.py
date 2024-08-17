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


    def generate_highlights(self, articles):
        highlights = "🌟 **Today's AI & Tech Highlights** 🌟\n\n"
        for index, article in enumerate(articles, start=1):
            title = article.get('title', 'Untitled Article')
            highlights += f"{index}. {title}\n"
        highlights += "\n" + "=" * 50 + "\n"
        return highlights

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
                model="gpt-3.5-turbo",
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

    def generate_image(self, prompt, size="1024x1024", quality="standard"):
        try:
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality=quality,
                n=1,
            )
            image_url = response.data[0].url
            return image_url
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return f"An error occurred: {e}"

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

        #AI #TechNews #Innovation

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

    def format_article_with_summary(self, article, index):
        formatted_article = self.format_article(article, index)
        summary = self.generate_summary(article)
        return f"{formatted_article}\n\nSummarized Content for LinkedIn/Newsletter:\n{summary}\n"

    def generate_html_page(self, image_url, highlights, articles):
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AI News Highlights</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 20px;
                }}
                .header img {{
                    max-width: 100%;
                    height: auto;
                }}
                .highlights {{
                    border: 2px solid #4CAF50;
                    border-radius: 5px;
                    padding: 20px;
                    margin-bottom: 30px;
                    background-color: #f0f8f0;
                }}
                .highlights h2 {{
                    color: #4CAF50;
                    margin-top: 0;
                }}
                .highlights ul {{
                    list-style-type: none;
                    padding-left: 0;
                }}
                .highlights li {{
                    margin-bottom: 10px;
                    padding-left: 20px;
                    position: relative;
                }}
                .highlights li:before {{
                    content: "🔹";
                    position: absolute;
                    left: 0;
                }}
                .featured-articles {{
                    border: 2px solid #2196F3;
                    border-radius: 5px;
                    padding: 20px;
                    background-color: #f0f8ff;
                }}
                .featured-articles h2 {{
                    color: #2196F3;
                    margin-top: 0;
                }}
                .article {{
                    background-color: #ffffff;
                    border-radius: 5px;
                    padding: 20px;
                    margin-bottom: 20px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }}
                .article h3 {{
                    color: #2196F3;
                    margin-top: 0;
                }}
                .summary-section {{
                    margin-bottom: 15px;
                }}
                .summary-section h4 {{
                    color: #e74c3c;
                    margin-bottom: 5px;
                }}
                .key-takeaways {{
                    list-style-type: none;
                    padding-left: 0;
                }}
                .key-takeaways li:before {{
                    content: "• ";
                    color: #3498db;
                }}
                .deep-dive {{
                    font-style: italic;
                }}
                .tags {{
                    color: #7f8c8d;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <img src="{image_url}" alt="AI News Highlights">
                <h1>Today's AI & Tech Highlights</h1>
            </div>
            
            <div class="highlights">
                <h2>🌟 Key Highlights</h2>
                {self.format_highlights(highlights)}
            </div>
            
            <div class="featured-articles">
                <h2>📰 Featured Articles</h2>
                {''.join(self.generate_article_html(article) for article in articles)}
            </div>
        </body>
        </html>
        """
        return html_content

    def format_highlights(self, highlights):
        # Split the highlights into individual points
        highlight_points = highlights.split('\n')
        # Remove any empty strings and the separator line
        highlight_points = [point.strip() for point in highlight_points if point.strip() and not point.startswith('=')]
        
        # Format the highlights as an unordered list
        formatted_highlights = "<ul>\n"
        for point in highlight_points:
            if point.startswith('🌟'):  # Skip the title if it's there
                continue
            formatted_highlights += f"    <li>{point}</li>\n"
        formatted_highlights += "</ul>"
        
        return formatted_highlights

    def generate_article_html(self, article):
        summary = self.generate_summary(article)
        
        # Parse the summary into sections
        sections = summary.split('\n\n')
        title = sections[0].strip('🔥 *')
        innovation_spotlight = sections[1].replace('🚀 **Innovation Spotlight:**', '').strip()
        key_takeaways = sections[2].replace('💡 **Key Takeaways:**', '').strip().split('\n')
        impact_significance = sections[3].replace('🌍 **Impact & Significance:**', '').strip()
        future_implications = sections[4].replace('🔮 **Future Implications:**', '').strip()
        deep_dive = sections[5].replace('🔗 **Deep Dive:**', '').strip()
        tags = sections[6].strip()

        return f"""
        <div class="article">
            <h3>{article['title']}</h3>
            
            <div class="summary-section">
                <h4>🔥 {title}</h4>
            </div>
            
            <div class="summary-section">
                <h4>🚀 Innovation Spotlight:</h4>
                <p>{innovation_spotlight}</p>
            </div>
            
            <div class="summary-section">
                <h4>💡 Key Takeaways:</h4>
                <ul class="key-takeaways">
                    {''.join(f'<li>{takeaway.strip("• ")}</li>' for takeaway in key_takeaways)}
                </ul>
            </div>
            
            <div class="summary-section">
                <h4>🌍 Impact & Significance:</h4>
                <p>{impact_significance}</p>
            </div>
            
            <div class="summary-section">
                <h4>🔮 Future Implications:</h4>
                <p>{future_implications}</p>
            </div>
            
            <p class="deep-dive">🔗 Deep Dive: {deep_dive}</p>
            
            <p class="tags">{tags}</p>
        </div>
        """

    def save_html_page(self, html_content, filename="ai_news_highlights.html"):
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_content)
        logger.info(f"HTML page saved as {filename}")


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
    logger.info(f"Fetching top 10 relevant AI-related news articles from {yesterday} to {today}...")
    relevant_articles = fetcher.fetch_news(keywords, yesterday, today, sort_by='relevancy')

    # Combine and deduplicate articles
    all_articles = list({article['url']: article for article in popular_articles + relevant_articles}.values())

    if all_articles:
        # Generate highlights
        highlights = fetcher.generate_highlights(all_articles)
        
        # Rephrase highlights
        logger.info("Rephrasing highlights...")
        rephrased_highlights = fetcher.rephrase_highlights(highlights)

        # Generate image based on rephrased highlights
        logger.info("Generating image based on highlights...")
        image_prompt = f"Create an image that represents the following AI and tech news highlights:\n\n{rephrased_highlights}"
        image_url = fetcher.generate_image(image_prompt)

        # Generate HTML page
        logger.info("Generating HTML page...")
        html_content = fetcher.generate_html_page(image_url, rephrased_highlights, all_articles[:5])  # Use top 5 articles
        fetcher.save_html_page(html_content)

        logger.info(f"Found {len(all_articles)} unique articles. HTML page generated with top 5 articles.")
    else:
        logger.info("No articles found for the given criteria.")

    logger.info("News fetching, summarization, and HTML generation complete.")

if __name__ == "__main__":
    main()