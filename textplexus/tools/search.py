from ddgs import DDGS
from typing import List, Dict

def web_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Performs a web search using DuckDuckGo and returns a list of results.
    """
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r["title"],
                    "link": r["href"],
                    "body": r["body"]
                })
    except Exception as e:
        print(f"Search failed: {e}")
    return results
