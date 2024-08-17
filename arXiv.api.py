import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

def fetch_top_genai_articles(max_results=10):
    base_url = 'http://export.arxiv.org/api/query?'
    
    # Define the search query
    search_query = 'cat:cs.AI AND (GPT OR "large language model" OR "generative AI" OR GenAI)'
    
    # Get articles from the last month
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
    
    # Construct the full query URL
    query_url = f"{base_url}search_query={search_query}&start=0&max_results={max_results}&sortBy=relevance&sortOrder=descending&submittedDate=[{start_date}+TO+*]"
    
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
                'link': entry.find('{http://www.w3.org/2005/Atom}id').text
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
    top_articles = fetch_top_genai_articles()
    
    if top_articles:
        print("Top GenAI/LLM Articles from arXiv (Last Month):")
        for i, article in enumerate(top_articles, 1):
            print(f"\n{i}. {article['title']}")
            print(f"   Authors: {', '.join(article['authors'])}")
            print(f"   Published: {article['published']}")
            print(f"   Link: {article['link']}")
            print(f"   Summary: {article['summary'][:200]}...")  # Truncate summary for brevity
    else:
        print("No articles found or an error occurred.")

if __name__ == "__main__":
    main()