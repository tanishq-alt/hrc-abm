"""Shared DDG search with 4-retry exponential backoff."""
import time
from duckduckgo_search import DDGS


def ddg_search(query: str, max_results: int = 10, retries: int = 4) -> list:
    """Run a DuckDuckGo text search with retry/backoff on rate limits.

    Returns a list of result dicts with keys: href, title, body.
    Returns [] on unrecoverable error.
    """
    for attempt in range(retries):
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                if results:
                    return results
                time.sleep(8 * (attempt + 1))
        except Exception as e:
            if "rate" in str(e).lower() or "202" in str(e):
                wait = 20 * (attempt + 1)
                print(f"  DDG rate-limited (attempt {attempt+1}), waiting {wait}s...", flush=True)
                time.sleep(wait)
            else:
                print(f"  DDG error: {e}", flush=True)
                return []
    return []
