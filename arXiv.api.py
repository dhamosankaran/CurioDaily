import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

def fetch_top_ai_articles(max_results=5, days=7):
    base_url = 'http://export.arxiv.org/api/query?'
    
    # Define the search query with expanded topics
    search_query = ('(cat:cs.AI OR cat:cs.LG OR cat:stat.ML) AND '
                    '("artificial intelligence" OR "machine learning" OR '
                    '"deep learning" OR "neural network" OR '
                    '"transformer architecture" OR GPT OR '
                    '"large language model" OR "generative AI" OR GenAI)')
    
    # Get articles from the last week
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
    
    # Construct the full query URL
    query_url = f"{base_url}search_query={search_query}&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending&submittedDate=[{start_date}+TO+*]"
    
    try:
        response = requests.get(query_url)
        response.raise_for_status()
        
        # Parse the XML response
        root = ET.fromstring(response.content)
        
        # Extract and format article information
        articles = []
        for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
            article = {
                'title': entry.find('{http://www.w3.org/2005/Atom}title').text.strip(),
                'authors': [author.find('{http://www.w3.org/2005/Atom}name').text for author in entry.findall('{http://www.w3.org/2005/Atom}author')],
                'summary': entry.find('{http://www.w3.org/2005/Atom}summary').text.strip(),
                'published': format_date(entry.find('{http://www.w3.org/2005/Atom}published').text),
                'link': entry.find('{http://www.w3.org/2005/Atom}id').text,
                'categories': [category.get('term') for category in entry.findall('{http://www.w3.org/2005/Atom}category')]
            }
            articles.append(article)
        
        return articles
    except requests.exceptions.RequestException as e:
        print(f"Error fetching articles: {e}")
        return []

def format_date(date_string):
    date = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ")
    return date.strftime("%Y-%m-%d")

def main():
    top_articles = fetch_top_ai_articles(max_results=5, days=7)
    
    if top_articles:
        print("Top 5 AI/ML/GenAI Articles from arXiv (Last Week):")
        for i, article in enumerate(top_articles, 1):
            print(f"\n{i}. {article['title']}")
            print(f"   Authors: {', '.join(article['authors'])}")
            print(f"   Published: {article['published']}")
            print(f"   Categories: {', '.join(article['categories'])}")
            print(f"   Link: {article['link']}")
            print(f"   Summary: {article['summary'][:200]}...")  # Truncate summary for brevity
    else:
        print("No articles found or an error occurred.")

if __name__ == "__main__":
    main()