import httpx
from bs4 import BeautifulSoup


async def web_search(query: str, max_results: int = 5) -> str:
    """DuckDuckGo HTML scrape — no API key needed."""
    url = "https://html.duckduckgo.com/html/"
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        r = await client.post(url, data={"q": query})
        r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    results = []
    for a in soup.select(".result__a")[:max_results]:
        title = a.get_text(strip=True)
        href = a.get("href", "")
        snippet_el = a.find_parent(class_="result")
        snippet = ""
        if snippet_el:
            sn = snippet_el.select_one(".result__snippet")
            snippet = sn.get_text(strip=True) if sn else ""
        results.append(f"• {title}\n  {href}\n  {snippet}")
    return "\n\n".join(results) if results else f"No results for: {query}"


async def fetch_headlines() -> list[dict]:
    """RSS-free headlines via DuckDuckGo news-style search."""
    q = "world news today headlines"
    text = await web_search(q, max_results=6)
    lines = [ln.strip() for ln in text.split("\n") if ln.strip().startswith("•")]
    headlines = []
    for ln in lines[:5]:
        title = ln.lstrip("• ").split("\n")[0][:120]
        headlines.append({"title": title, "source": "SENZ Feed"})
    if not headlines:
        headlines = [
            {"title": "SENZ online — connect Gemini API for live news", "source": "System"},
        ]
    return headlines
