import requests


class RealTimeSearchError(RuntimeError):
    pass


class RealTimeSearch:
    """Thin wrapper around the Tavily real-time search API."""

    def __init__(self, api_key: str, endpoint: str = "https://api.tavily.com/search"):
        self._api_key = api_key
        self._endpoint = endpoint

    def search(self, query: str, max_results: int = 5) -> list:
        if not self._api_key:
            raise RealTimeSearchError(
                "TAVILY_API_KEY is not configured; real-time search is unavailable"
            )
        response = requests.post(
            self._endpoint,
            json={
                "api_key": self._api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": "basic",
            },
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        return [
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("content", ""),
            }
            for item in payload.get("results", [])
        ]
