import urllib.parse
from urllib.parse import urlparse
import feedparser
import requests
from tavily import TavilyClient


class NewsAggregator:
    """Multi-source news fetching engine with fallback and source diversity check."""

    def __init__(self, tavily_api_key: str = None, news_api_key: str = None):
        self.tavily_client = TavilyClient(api_key=tavily_api_key) if tavily_api_key else None
        self.news_api_key = news_api_key

    def _extract_domain(self, url: str) -> str:
        try:
            domain = urlparse(url).netloc
            return domain.replace("www.", "")
        except Exception:
            return "unknown"

    def fetch_google_rss(self, query: str, limit: int = 4) -> list:
        results = []
        try:
            encoded_query = urllib.parse.quote(query)
            rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
            feed = feedparser.parse(rss_url)
            for entry in feed.entries[:limit]:
                source_title = entry.get("source", {}).get("title", "Google News")
                results.append({
                    "source": source_title,
                    "title": entry.get("title", "").strip(),
                    "summary": entry.get("summary", entry.get("title", "")).strip(),
                    "url": entry.get("link", ""),
                    "origin": "Google RSS"
                })
        except Exception as e:
            print(f"[Warning] Google RSS failed: {e}")
        return results

    def fetch_newsapi(self, query: str, limit: int = 3) -> list:
        if not self.news_api_key:
            return []
        results = []
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": query,
                "sortBy": "publishedAt",
                "pageSize": limit,
                "language": "en",
                "apiKey": self.news_api_key
            }
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                articles = resp.json().get("articles", [])
                for art in articles[:limit]:
                    if art.get("title") and art.get("title") != "[Removed]":
                        results.append({
                            "source": art.get("source", {}).get("name", "NewsAPI"),
                            "title": art.get("title", "").strip(),
                            "summary": (art.get("description") or art.get("title", "")).strip(),
                            "url": art.get("url", ""),
                            "origin": "NewsAPI"
                        })
        except Exception as e:
            print(f"[Warning] NewsAPI failed: {e}")
        return results

    def fetch_tavily(self, query: str, limit: int = 3) -> list:
        if not self.tavily_client:
            return []
        results = []
        try:
            resp = self.tavily_client.search(
                query=query,
                topic="news",
                search_depth="advanced",
                max_results=limit
            )
            for item in resp.get("results", []):
                domain = self._extract_domain(item.get("url", ""))
                results.append({
                    "source": domain.upper(),
                    "title": item.get("title", "").strip(),
                    "summary": item.get("content", "").strip(),
                    "url": item.get("url", ""),
                    "origin": "Tavily Deep Search"
                })
        except Exception as e:
            print(f"[Warning] Tavily failed: {e}")
        return results

    def get_news(self, query: str, limit_per_source: int = 2) -> list:
        raw_items = []
        # ১. গভীর তথ্যের জন্য Tavily
        raw_items.extend(self.fetch_tavily(query, limit=limit_per_source))
        # ২. ব্রেকিং আপডেটের জন্য Google RSS
        raw_items.extend(self.fetch_google_rss(query, limit=limit_per_source + 1))
        # ৩. ব্যাকআপ কভারেজের জন্য NewsAPI
        raw_items.extend(self.fetch_newsapi(query, limit=limit_per_source))

        # URL এবং Title ডি-ডুপ্লিকেশন
        seen_urls = set()
        seen_titles = set()
        unique_news = []

        for item in raw_items:
            url = item.get("url", "").strip()
            title_key = item.get("title", "").lower()[:50]

            if url and url not in seen_urls and title_key not in seen_titles:
                seen_urls.add(url)
                seen_titles.add(title_key)
                unique_news.append(item)

        return unique_news
