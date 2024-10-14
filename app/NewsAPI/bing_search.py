import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz
from collections import defaultdict
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get your Bing Search API key from environment variable
subscription_key = os.getenv("BING_SEARCH_V7_SUBSCRIPTION_KEY")
if not subscription_key:
    raise ValueError("BING_SEARCH_V7_SUBSCRIPTION_KEY not found in environment variables")

# Bing News Search endpoint
search_url = "https://api.bing.microsoft.com/v7.0/news/search"

async def fetch_article_content(session, url):
    try:
        async with session.get(url, timeout=10) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                article_text = ' '.join([p.get_text() for p in soup.find_all('p')])
                return article_text[:500]  # Return first 500 characters
    except Exception as e:
        logger.error(f"Error fetching article content: {e}")
    return None

async def get_trending_news(query, count=100):
    headers = {"Ocp-Apim-Subscription-Key": subscription_key}
    
    one_week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat() + 'Z'
    
    params = {
        "q": query,
        "count": count,
        "mkt": "en-US",
        "safeSearch": "Moderate",
        "sortBy": "Date",
        "freshness": "Week",
        "since": one_week_ago
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(search_url, headers=headers, params=params) as response:
                response.raise_for_status()
                search_results = await response.json()
                
                articles = []
                tasks = []
                for article in search_results.get("value", []):
                    date_published = datetime.fromisoformat(article["datePublished"].rstrip('Z')).replace(tzinfo=pytz.utc)
                    formatted_date = date_published.strftime("%Y-%m-%d %H:%M:%S %Z")
                    
                    article_data = {
                        "name": article["name"],
                        "url": article["url"],
                        "description": article["description"],
                        "datePublished": formatted_date,
                        "category": article.get("category", "N/A"),
                        "image": None,
                        "provider": article["provider"][0]["name"] if article.get("provider") else "Unknown"
                    }
                    
                    if "image" in article and "thumbnail" in article["image"]:
                        article_data["image"] = article["image"]["thumbnail"]["contentUrl"]
                    
                    articles.append(article_data)
                    tasks.append(fetch_article_content(session, article_data["url"]))
                
                contents = await asyncio.gather(*tasks)
                for article, content in zip(articles, contents):
                    article["content"] = content
                
                return articles
    except aiohttp.ClientError as e:
        logger.error(f"Request Error: {e}")
        return []
    except Exception as ex:
        logger.error(f"Error: {str(ex)}")
        return []

def deduplicate_and_rank(articles):
    grouped_articles = defaultdict(list)
    for article in articles:
        grouped_articles[article['description']].append(article)
    
    unique_articles = [sorted(group, key=lambda x: x['datePublished'], reverse=True)[0] 
                       for group in grouped_articles.values()]
    
    ai_keywords = ['ai', 'artificial intelligence', 'machine learning', 'deep learning', 
                   'generative ai', 'genai', 'large language model', 'llm']
    
    def score_article(article):
        score = 0
        title_lower = article['name'].lower()
        desc_lower = article['description'].lower()
        
        for keyword in ai_keywords:
            if keyword in title_lower:
                score += 2
            if keyword in desc_lower:
                score += 1
        
        return score

    ranked_articles = sorted(unique_articles, 
                             key=lambda x: (score_article(x), x['datePublished']), 
                             reverse=True)
    
    return ranked_articles[:10]

def generate_html(articles):
    article_blocks = ""
    for article in articles:
        image_tag = f'<img src="{article["image"]}" alt="{article["name"]}" class="article-image">' if article["image"] else ''
        content = article['content'] if article['content'] else article['description']
        article_block = f"""
        <div class="article">
            {image_tag}
            <span class="article-category">{article['category']}</span>
            <h3>{article['name']}</h3>
            <p>{content}</p>
            <p class="highlight-category">Published: {article['datePublished']} by {article['provider']}</p>
            <a href="{article['url']}" class="read-more" target="_blank">Read more</a>
        </div>
        """
        article_blocks += article_block

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Top 10 AI News - CurioDaily</title>
        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&family=Montserrat:wght@500;700&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
        <style>
            body {{
                font-family: 'Roboto', sans-serif;
                line-height: 1.6;
                color: #333;
                margin: 0;
                padding: 0;
                background-color: #f4f4f4;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 0 20px;
            }}
            .main-header {{
                background-color: #2c3e50;
                color: #ecf0f1;
                padding: 1rem 0;
            }}
            .logo-title {{
                display: flex;
                align-items: center;
                gap: 1rem;
            }}
            .logo {{
                width: 50px;
                height: 50px;
                border-radius: 50%;
            }}
            h1, h2 {{
                font-family: 'Montserrat', sans-serif;
            }}
            .article-header {{
                background-color: #3498db;
                color: #fff;
                padding: 2rem 0;
                margin-bottom: 2rem;
            }}
            .date {{
                font-style: italic;
            }}
            .article-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 2rem;
            }}
            .article {{
                background-color: #fff;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                overflow: hidden;
                transition: transform 0.3s ease;
            }}
            .article:hover {{
                transform: translateY(-5px);
            }}
            .article-image {{
                width: 100%;
                height: 200px;
                object-fit: cover;
            }}
            .article-category {{
                display: inline-block;
                background-color: #e74c3c;
                color: #fff;
                padding: 0.2rem 0.5rem;
                border-radius: 4px;
                font-size: 0.8rem;
                margin: 1rem;
            }}
            .article h3 {{
                margin: 1rem;
                font-size: 1.2rem;
            }}
            .article p {{
                margin: 1rem;
                font-size: 0.9rem;
            }}
            .highlight-category {{
                font-weight: bold;
                color: #7f8c8d;
            }}
            .read-more {{
                display: inline-block;
                background-color: #2980b9;
                color: #fff;
                padding: 0.5rem 1rem;
                text-decoration: none;
                border-radius: 4px;
                margin: 1rem;
                transition: background-color 0.3s ease;
            }}
            .read-more:hover {{
                background-color: #3498db;
            }}
        </style>
    </head>
    <body>
        <header class="main-header">
            <div class="container">
                <div class="logo-title">
                    <img src="https://storage.googleapis.com/curiodaily_image/logo.jpeg" alt="CurioDaily Logo" class="logo">
                    <h1>CurioDaily: Your Weekly Top AI News</h1>
                </div>
            </div>
        </header>

        <div class="article-header">
            <div class="container">
                <h2>Top 10 AI News of the Week</h2>
                <p class="date">{datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}</p>
            </div>
        </div>

        <main class="container">
            <section id="articles" class="content-section">
                <h2>Top Articles</h2>
                <div class="article-grid">
                    {article_blocks}
                </div>
            </section>
        </main>
    </body>
    </html>
    """

    with open("weekly_ai_news.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    logger.info("HTML file generated: weekly_ai_news.html")

async def main():
    query = 'Artificial Intelligence'
    
    logger.info("Fetching weekly top 10 AI news...")
    all_articles = await get_trending_news(query, count=100)
    
    if not all_articles:
        logger.warning("No articles found")
    else:
        top_articles = deduplicate_and_rank(all_articles)
        
        logger.info("\nTop 10 AI Articles of the Week:")
        for i, article in enumerate(top_articles, 1):
            logger.info(f"\n{i}. {article['name']}")
            logger.info(f"   URL: {article['url']}")
            logger.info(f"   Published: {article['datePublished']}")
            logger.info(f"   Category: {article['category']}")
            logger.info(f"   Provider: {article['provider']}")
        
        # Generate HTML file with top articles
        generate_html(top_articles)

if __name__ == "__main__":
    asyncio.run(main())