from ddgs import DDGS


def get_live_news_context(sport_name, max_results=3):
    """
    Searches the live web for recent sport news, matches, or events.
    Returns a unified text summary of search snippets.
    Falls back gracefully if the search fails (rate limit, network, etc.)
    """
    search_query = f"{sport_name} latest tournament results championship winners news 2026"
    retrieved_texts = []

    print(f"[INFO] Executing web search for: '{search_query}'...")
    try:
        with DDGS() as ddgs:
            results = ddgs.text(search_query, max_results=max_results)

            for index, r in enumerate(results, start=1):
                title = r.get("title", "No Title")
                snippet = r.get("body", "No Snippet Content Available")
                retrieved_texts.append(f"Web Source {index}: {title}\nSnippet: {snippet}")

    except Exception as e:
        print(f"[WARNING] Web search failed or was rate-limited: {e}")
        return "No recent live web updates available (search temporarily unavailable)."

    if not retrieved_texts:
        return "No recent live web updates found for this sport."

    return "\n\n".join(retrieved_texts)