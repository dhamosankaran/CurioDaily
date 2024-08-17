import requests
import os

def get_api_key():
    api_key = os.getenv('PEXELS_API_KEY')
    if not api_key:
        api_key = input("Please enter your Pexels API key: ")
    return api_key

def search_pexels(query, api_key, per_page=15, page=1):
    url = f"https://api.pexels.com/v1/search?query={query}&per_page={per_page}&page={page}"
    headers = {
        "Authorization": api_key
    }

    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error fetching images: {response.status_code}")

def display_results(data):
    if 'photos' not in data or len(data['photos']) == 0:
        print("No photos found for this search term.")
        return

    for photo in data['photos']:
        print(f"Photographer: {photo['photographer']}")
        print(f"Image URL: {photo['src']['medium']}")
        print(f"Image page: {photo['url']}")
        print("-" * 50)

if __name__ == "__main__":
    api_key = get_api_key()
    search_term = input("Enter a search term: ")
    try:
        results = search_pexels(search_term, api_key)
        display_results(results)
    except Exception as e:
        print(f"An error occurred: {str(e)}")