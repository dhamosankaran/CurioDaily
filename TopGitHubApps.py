import requests
import datetime
import os
from dotenv import load_dotenv

def fetch_top_ai_repos(api_token, num_repos=10):
    headers = {
        'Authorization': f'token {api_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Simplified search query
    query = 'artificial intelligence machine learning language model'
    url = f'https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page={num_repos}'
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        repos = response.json()['items']
        return [format_repo_info(repo) for repo in repos]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching repositories: {e}")
        if response.status_code == 422:
            print("This might be due to an invalid search query or exceeding the search rate limit.")
        elif response.status_code == 403:
            print("This might be due to exceeding the API rate limit. Please try again later.")
        print(f"Response content: {response.text}")
        return []

def format_repo_info(repo):
    return {
        'name': repo['full_name'],
        'description': repo['description'],
        'stars': repo['stargazers_count'],
        'url': repo['html_url'],
        'created_at': format_date(repo['created_at']),
        'updated_at': format_date(repo['updated_at']),
        'language': repo['language']
    }

def format_date(date_string):
    date = datetime.datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ")
    return date.strftime("%Y-%m-%d")

def main():
    load_dotenv()  # Load environment variables from .env file
    api_token = os.getenv('GITHUB_API_TOKEN')
    
    if not api_token:
        print("Error: GitHub API token not found. Please set the GITHUB_API_TOKEN environment variable.")
        return

    top_repos = fetch_top_ai_repos(api_token)
    
    if top_repos:
        print("Top AI/LLM Repositories on GitHub:")
        for i, repo in enumerate(top_repos, 1):
            print(f"\n{i}. {repo['name']} ({repo['stars']} stars)")
            print(f"   Description: {repo['description']}")
            print(f"   URL: {repo['url']}")
            print(f"   Language: {repo['language']}")
            print(f"   Created: {repo['created_at']}, Last updated: {repo['updated_at']}")
    else:
        print("No repositories found or an error occurred.")

if __name__ == "__main__":
    main()