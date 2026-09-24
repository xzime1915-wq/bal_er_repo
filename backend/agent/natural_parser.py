"""Long / natural Banglish sentences → PC commands."""

import re

from agent.tools.pc_tools import APP_ALIASES

OPEN_VERBS = r"(khul|kholo|open|start|chalu|run|dao|daw|de|den|lite|lagbe|lagbe\?)"
CLOSE_VERBS = r"(bandho|bondho|close|kill|off koro)"


def _norm(text: str) -> str:
    return text.strip().lower()


def _find_app(t: str) -> str | None:
    # longest match first
    keys = sorted(APP_ALIASES.keys(), key=len, reverse=True)
    for key in keys:
        if key in t:
            return key
    # single word after "the" 
    m = re.search(
        r"(?:chrome|firefox|edge|notepad|calculator|vscode|code|spotify|discord|explorer|terminal|cmd)",
        t,
    )
    if m:
        return m.group(0)
    return None


def parse_natural(text: str) -> tuple[str, list[dict]] | None:
    """Extract intent from long natural language (Banglish/English)."""
    t = _norm(text)
    if len(t) < 4:
        return None

    # Screenshot
    if re.search(r"screenshot|screen\s*shot|skrin\s*shot|chobi\s*nao|screen\s*capture", t):
        return ("Thik ache, screenshot nichi apnar jonno.", [{"name": "screenshot", "args": {}}])

    # Volume
    m = re.search(r"volume(?:\s*ta)?\s*(?:\w+\s*){0,3}(\d{1,3})|(\d{1,3})\s*(?:percent|%|volume)", t)
    if m and re.search(r"volume|awaz|sound|audio", t):
        lvl = int(m.group(1) or m.group(2))
        return (f"Volume {lvl} kore dilam.", [{"name": "set_volume", "args": {"level": lvl}}])

    app = _find_app(t)

    # Open / close first (before search)
    if app and re.search(OPEN_VERBS, t) and not re.search(CLOSE_VERBS, t):
        return (f"Thik ache, {app} khulchi ekhon.", [{"name": "open_app", "args": {"name": app}}])

    if app and re.search(CLOSE_VERBS, t):
        return (f"{app} bandho korchi.", [{"name": "close_app", "args": {"name": app}}])

    if re.search(r"news|khobor|headline|ajker|songbad", t) and re.search(
        r"(dao|daw|dekhao|show|an|fetch|bol)", t
    ):
        return ("Ajker headlines anchi...", [{"name": "print_news", "args": {}}])

    m = re.search(r"(?:search|khujo|khujte|find)\s+(?:koro\s+)?(.+)", t)
    if m:
        q = m.group(1).strip(" ?.,!")
        if len(q) > 2:
            return (f"'{q}' niye khujchi...", [{"name": "web_search", "args": {"query": q}}])

    # "chrome kholo" inside long sentence
    m = re.search(rf"(\w+(?:\s+\w+)?)\s+{OPEN_VERBS}", t)
    if m:
        word = m.group(1).strip()
        if word in APP_ALIASES or len(word) < 20:
            return (f"{word} khulchi.", [{"name": "open_app", "args": {"name": word}}])

    return None
