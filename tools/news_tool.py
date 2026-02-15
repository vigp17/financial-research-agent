"""
News Tool — Fetches recent news headlines for a stock.

Uses yfinance's built-in news feed so no additional API key is needed.
Gives the agent context about WHY a stock is moving, not just WHAT it's doing.
"""

import yfinance as yf
from datetime import datetime


# === TOOL SCHEMA ===

NEWS_TOOL_SCHEMA = {
    "name": "get_stock_news",
    "description": (
        "Fetch recent news headlines and articles for a stock ticker. "
        "Returns titles, publishers, publication dates, and article links. "
        "Use this tool to understand WHY a stock is moving — earnings reports, "
        "analyst upgrades/downgrades, product launches, regulatory news, etc. "
        "Complements price and technical data with narrative context."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "Stock ticker symbol (e.g., 'AAPL', 'TSLA', 'NVDA')"
            }
        },
        "required": ["ticker"]
    }
}


# === TOOL HANDLER ===

def get_stock_news(ticker: str) -> dict:
    """Fetch recent news for a stock ticker."""
    try:
        stock = yf.Ticker(ticker)
        news = stock.news

        if not news:
            return {
                "ticker": ticker.upper(),
                "article_count": 0,
                "articles": [],
                "note": "No recent news found for this ticker."
            }

        articles = []
        for item in news[:8]:  # Limit to 8 most recent
            # Extract from the content structure
            content = item.get("content", {})
            
            article = {
                "title": content.get("title", item.get("title", "N/A")),
                "publisher": content.get("provider", {}).get("displayName", 
                            item.get("publisher", "N/A")),
            }

            # Try to get publish date
            pub_date = content.get("pubDate", item.get("providerPublishTime", None))
            if pub_date:
                if isinstance(pub_date, (int, float)):
                    article["date"] = datetime.fromtimestamp(pub_date).strftime("%Y-%m-%d %H:%M")
                else:
                    article["date"] = str(pub_date)[:16]

            # Try to get summary/description
            summary = content.get("summary", item.get("summary", None))
            if summary:
                article["summary"] = summary[:200]

            # Get link
            link = content.get("canonicalUrl", {}).get("url", item.get("link", None))
            if link:
                article["link"] = link

            articles.append(article)

        return {
            "ticker": ticker.upper(),
            "article_count": len(articles),
            "articles": articles,
        }

    except Exception as e:
        return {"error": f"Failed to fetch news: {str(e)}"}