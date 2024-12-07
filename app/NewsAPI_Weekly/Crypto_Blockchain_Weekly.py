import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging
from openai import OpenAI
import psycopg2
from psycopg2 import sql
from typing import List, Dict, Any, Optional
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class CryptoBlockchainWeeklyFetcher:
    def __init__(self):
        self.news_api_key = os.getenv('NEWS_API_KEY_Weekly')
        if not self.news_api_key:
            raise ValueError("NEWS_API_KEY not found in environment variables")
        self.base_url = "https://newsapi.org/v2/everything"
        self.db_url = os.getenv('DATABASE_URL')
        if not self.db_url:
            raise ValueError("DATABASE_URL not found in environment variables")

        self.trusted_sources = [
            'coindesk.com', 'cointelegraph.com', 'decrypt.co', 'bitcoin.com',
            'theblock.co', 'cryptoslate.com', 'bitcoinmagazine.com',
            'cryptobriefing.com', 'blockchain.news', 'newsbtc.com',
            'ambcrypto.com', 'crypto.news', 'cryptopotato.com',
            'beincrypto.com', 'bitcoinist.com'
        ]

        self.crypto_entities = [
            'Bitcoin', 'Ethereum', 'Binance', 'Coinbase', 'Ripple',
            'Solana', 'Cardano', 'Polygon', 'Chainlink', 'Uniswap',
            'Aave', 'MetaMask', 'OpenSea', 'FTX', 'Kraken',
            'Gemini', 'Avalanche', 'Layer Zero', 'Base', 'Arbitrum'
        ]

        self.priority_topics = [
            'DeFi', 'NFTs', 'Web3', 'Layer 2', 'Smart Contracts',
            'Crypto Regulation', 'Mining', 'Staking', 'DEX', 'CEX',
            'Blockchain Technology', 'Tokenization', 'Digital Assets',
            'Crypto Security', 'Crypto Innovation', 'Market Analysis'
        ]

    async def fetch_news(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        all_articles = []
        
        queries = [
            'cryptocurrency OR blockchain',
            'Bitcoin OR Ethereum OR Web3',
            'DeFi OR NFT OR smart contracts',
            'crypto regulation OR blockchain policy',
            'crypto market OR crypto trading',
            'blockchain technology OR crypto innovation',
            'Layer 2 OR blockchain scaling'
        ]

        async with aiohttp.ClientSession() as session:
            tasks = [
                self._fetch_news_batch(session, query, start_date, end_date)
                for query in queries
            ]
            results = await asyncio.gather(*tasks)
            
        seen_titles = set()
        unique_articles = []
        
        for articles in results:
            for article in articles:
                title = article.get('title', '').lower()
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    unique_articles.append(article)
        
        return unique_articles

    async def _fetch_news_batch(self, session: aiohttp.ClientSession, query: str, 
                              start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        params = {
            'q': query,
            'from': start_date.isoformat(),
            'to': end_date.isoformat(),
            'language': 'en',
            'sortBy': 'relevancy',
            'pageSize': 10,
            'apiKey': self.news_api_key
        }

        try:
            async with session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('articles', [])
                return []
        except Exception as e:
            logger.error(f"Error fetching news batch: {e}")
            return []

    def _prepare_articles_for_ai(self, articles: List[Dict[str, Any]]) -> str:
        """Prepare articles in a compressed format."""
        return "\n".join([
            f"[{i}] {a['title']} | {a['description']}"
            for i, a in enumerate(articles)
        ])

    def _prefilter_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Pre-filter articles to reduce input tokens."""
        filtered = []
        seen_titles = set()
        
        for article in articles:
            if not article or not article.get('title') or not article.get('description'):
                continue
                
            title = article['title'].lower()
            if title in seen_titles:
                continue
                
            seen_titles.add(title)
            filtered.append(article)
            
            if len(filtered) >= 15:
                break
                
        return filtered

    async def process_articles_with_ai(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not articles:
            return self._get_empty_response()

        filtered_articles = self._prefilter_articles(articles)
        if not filtered_articles:
            return self._get_empty_response()

        articles_text = self._prepare_articles_for_ai(filtered_articles)

        try:
            messages = [
                {"role": "system", "content": """Crypto & Blockchain news curator. Output JSON:
{
  "filtered_indices": [0-based indices],
  "highlights": [{"text": "max 170 chars", "category": "cat", "icon": "bitcoin", "color": "#hex"}],
  "title": "Crypto Weekly: [Theme]",
  "summary": "2-line cryptocurrency and blockchain summary"
}"""},
                {"role": "user", "content": f"Select top crypto and blockchain news:\n{articles_text}"}
            ]

            response = await asyncio.to_thread(
                client.chat.completions.create,
                model="gpt-4-1106-preview",
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )

            return self._process_ai_response(response, filtered_articles)
        except Exception as e:
            logger.error(f"Error in AI processing: {e}")
            return self._fallback_processing(filtered_articles)

    def _get_empty_response(self) -> Dict[str, Any]:
        return {
            'filtered_articles': [],
            'highlights': [],
            'title': "This Week in Crypto & Blockchain",
            'summary': "No articles available."
        }

    def _process_ai_response(self, response: Any, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        try:
            result = json.loads(response.choices[0].message.content)
            
            filtered_articles = [
                articles[idx] for idx in result.get('filtered_indices', [])[:10]
                if 0 <= idx < len(articles)
            ]
            
            highlights = [
                {
                    'text': str(h.get('text', ''))[:170],
                }
                for h in result.get('highlights', [])[:5]
                if h.get('text') and h.get('category')
            ]

            return {
                'filtered_articles': filtered_articles,
                'highlights': highlights,
                'title': str(result.get('title', "This Week in Crypto & Blockchain")),
                'summary': str(result.get('summary', "Latest cryptocurrency and blockchain developments."))
            }
        except Exception as e:
            logger.error(f"Error processing AI response: {e}")
            return self._fallback_processing(filtered_articles)

    def _fallback_processing(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        filtered = articles[:10]
        highlights = [
            {
                'text': article['title'][:170],
            }
            for article in filtered[:5]
        ]
        
        return {
            'filtered_articles': filtered,
            'highlights': highlights,
            'title': "This Week in Crypto & Blockchain",
            'summary': "Latest developments in cryptocurrency, blockchain, and Web3 technology."
        }

    def generate_html_content(self, title: str, summary: str, highlights: List[Dict[str, Any]], 
                            articles: List[Dict[str, Any]]) -> str:
        template_path = os.path.join(os.path.dirname(__file__), 'weekly_newsletter_template.html')
        base_url = os.getenv('BASE_URL', 'https://www.thecuriodaily.com')

        highlights_html = "".join([
            f"""<li class="highlight-item">
                <i class="fas fa-circle"></i>
                <span class="highlight-text">{h['text']}</span>
            </li>"""
            for h in highlights
        ])
        
        articles_html = "".join([
            f"""<article class="article-card">
                <img src="{article.get('urlToImage', '/api/placeholder/400/300')}" 
                     alt="Article image" class="article-image">
                <div class="article-content">
                    <h3>{article.get('title', '')}</h3>
                    <p>{article.get('description', '')}</p>
                    <a href="{article.get('url', '#')}" class="read-more-btn" target="_blank">
                        Read More
                    </a>
                </div>
            </article>"""
            for article in articles
        ])

        try:
            with open(template_path, "r", encoding="utf-8") as f:
                template = f.read()
            
            return template.replace(
                '{{title}}', title
            ).replace(
                '{{summary}}', summary
            ).replace(
                '{{highlights}}', highlights_html
            ).replace(
                '{{articles}}', articles_html
            ).replace(
                '{{base_url}}', base_url
            ).replace(
                '{{topic}}', "Crypto & Blockchain Weekly"
            ).replace(
                '{{date}}', datetime.now().strftime("%b %d, %Y")
            )
        except Exception as e:
            logger.error(f"Error generating HTML content: {e}")
            return ""

    def store_weekly_newsletter(self, title: str, content: str, highlights: List[Dict[str, Any]]) -> Optional[int]:
        try:
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO public.weekly_newsletter 
                        (title, content, weeklynewsletter_topic_id, key_highlight)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id
                    """, (
                        title,
                        content,
                        7,  # Crypto & Blockchain Weekly topic ID
                        ", ".join(h['text'] for h in highlights[:3])
                    ))
                    
                    newsletter_id = cur.fetchone()[0]
                    conn.commit()
                    return newsletter_id
        except Exception as e:
            logger.error(f"Error storing newsletter: {e}")
            return None

async def main():
    try:
        fetcher = CryptoBlockchainWeeklyFetcher()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        logger.info(f"Fetching crypto & blockchain news for {start_date.date()} to {end_date.date()}")
        
        articles = await fetcher.fetch_news(start_date, end_date)
        if not articles:
            logger.warning("No articles found")
            return

        processed_results = await fetcher.process_articles_with_ai(articles)
        if not processed_results['filtered_articles']:
            logger.warning("No articles passed AI filtering")
            return

        html_content = fetcher.generate_html_content(
            title=processed_results['title'],
            summary=processed_results['summary'],
            highlights=processed_results['highlights'],
            articles=processed_results['filtered_articles']
        )

        if html_content:
            #filename = f"Crypto_Weekly_{end_date.strftime('%Y%m%d')}.html"
            #with open(filename, 'w', encoding='utf-8') as f:
            #    f.write(html_content)
            
            newsletter_id = fetcher.store_weekly_newsletter(
                title=processed_results['title'],
                content=html_content,
                highlights=processed_results['highlights']
            )
            
            if newsletter_id:
                logger.info(f"Newsletter generated and stored. ID: {newsletter_id}")
            else:
                logger.error("Failed to store newsletter")
        else:
            logger.error("Failed to generate HTML content")

    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())