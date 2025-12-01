import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
ALPHAVANTAGE_KEY = os.getenv("ALPHAVANTAGE_KEY")

def fetch_tech_news(limit=5):
    """Fetch top tech news from NewsAPI."""
    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "category": "technology",
        "country": "us",
        "pageSize": limit,
        "apiKey": NEWSAPI_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        articles = []
        for article in data.get("articles", [])[:limit]:
            if article.get("title") and article.get("title") != "[Removed]":
                articles.append({
                    "title": article.get("title", "No title"),
                    "url": article.get("url", "")
                })
        return articles
    except Exception as e:
        print(f"Error fetching tech news: {e}")
        return []

def fetch_financial_news(limit=5):
    """Fetch business/financial news from NewsAPI."""
    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "category": "business",
        "country": "us",
        "pageSize": limit,
        "apiKey": NEWSAPI_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        articles = []
        for article in data.get("articles", [])[:limit]:
            if article.get("title") and article.get("title") != "[Removed]":
                articles.append({
                    "title": article.get("title", "No title"),
                    "url": article.get("url", "")
                })
        return articles
    except Exception as e:
        print(f"Error fetching financial news: {e}")
        return []

def fetch_stock_news(limit=5):
    """Fetch stock market related news using search."""
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": "stock market OR earnings OR fed OR inflation",
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": limit,
        "apiKey": NEWSAPI_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        articles = []
        for article in data.get("articles", [])[:limit]:
            if article.get("title") and article.get("title") != "[Removed]":
                articles.append({
                    "title": article.get("title", "No title"),
                    "url": article.get("url", "")
                })
        return articles
    except Exception as e:
        print(f"Error fetching stock news: {e}")
        return []

def fetch_all_news():
    """Fetch all news categories."""
    return {
        "tech": fetch_tech_news(),
        "financial": fetch_financial_news(),
        "stock": fetch_stock_news()
    }

if __name__ == "__main__":
    # Test the functions
    print("Fetching news...")
    news = fetch_all_news()
    print(f"Tech: {len(news['tech'])} articles")
    print(f"Financial: {len(news['financial'])} articles")
    print(f"Stock: {len(news['stock'])} articles")
