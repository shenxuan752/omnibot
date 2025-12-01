from datetime import datetime

def format_digest(news_data):
    """Format news data into a nice Telegram message."""
    today = datetime.now().strftime("%b %d, %Y")
    
    message = f"📰 *Daily News Digest*\n{today}\n\n"
    
    # Tech News
    if news_data.get("tech"):
        message += "🔧 *TECH NEWS*\n\n"
        for i, article in enumerate(news_data["tech"], 1):
            title = article["title"][:100] + "..." if len(article["title"]) > 100 else article["title"]
            message += f"{i}\\. [{title}]({article['url']})\n\n"
        message += "━━━━━━━━━━━━━━━\n\n"
    
    # Financial News
    if news_data.get("financial"):
        message += "💰 *FINANCIAL & ECONOMIC NEWS*\n\n"
        for i, article in enumerate(news_data["financial"], 1):
            title = article["title"][:100] + "..." if len(article["title"]) > 100 else article["title"]
            message += f"{i}\\. [{title}]({article['url']})\n\n"
        message += "━━━━━━━━━━━━━━━\n\n"
    
    # Stock News
    if news_data.get("stock"):
        message += "📈 *STOCK MARKET NEWS*\n\n"
        for i, article in enumerate(news_data["stock"], 1):
            title = article["title"][:100] + "..." if len(article["title"]) > 100 else article["title"]
            message += f"{i}\\. [{title}]({article['url']})\n\n"
        message += "━━━━━━━━━━━━━━━\n\n"
    
    message += "_Powered by NewsAPI_"
    
    return message

if __name__ == "__main__":
    # Test formatting
    test_data = {
        "tech": [{"title": "OpenAI Releases GPT-5", "url": "https://example.com/1"}],
        "financial": [{"title": "Fed Holds Rates Steady", "url": "https://example.com/2"}],
        "stock": [{"title": "Tesla Stock Soars", "url": "https://example.com/3", "symbol": "TSLA"}]
    }
    print(format_digest(test_data))
