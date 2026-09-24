"""Local chat + commands — no Gemini needed."""

import re

from agent.natural_parser import parse_natural


def _norm(text: str) -> str:
    return text.strip().lower()


def _has_action_intent(t: str) -> bool:
    actions = (
        "kholo", "khul", "open", "close", "bandho", "screenshot", "volume",
        "search", "khujo", "news", "headline", "khobor", "run ", "command",
        "powershell", "list ", "dekhao", "background", "move ", "folder",
    )
    return any(a in t for a in actions)


def _is_casual_chat(t: str) -> bool:
    """Short talk — never send to Gemini."""
    return len(t.split()) <= 12 and not _has_action_intent(t)


def parse_local(text: str) -> tuple[str, list[dict]] | None:
    t = _norm(text)
    if not t:
        return None

    if re.match(r"^(hi|hello|helo|hey|salam|assalam|asalam|hlw|hii)\b", t):
        return (
            "Assalamualaikum! Ami SENZ — apnar sathe achi. Bolun ki korbo?",
            [],
        )

    # Short greeting only (long sentences → Ollama)
    if len(t.split()) <= 8 and re.search(
        r"(k+e?m+o?n+|kamon|kmn|keno)\s*(acho|achis|achen|aso)?", t
    ):
        return ("Alhamdulillah, ami valo achi! Apni bolen, ki help lagbe?", [])

    if re.search(r"(ki\s*)?khobor|how are you|how r u", t):
        return ("Shob thik! Apnar jonno ki korte pari?", [])

    if any(x in t for x in ("tumi ke", "who are you", "apni ke", "senz ki", "ke tumi")):
        return (
            "Ami SENZ — apnar PC er AI. App, file, search, news — shob korte pari. LIVE TALK eo kotha bolte parben.",
            [],
        )

    if any(x in t for x in ("ki korte paro", "help", "sahajjo", "commands", "ki paro")):
        return (
            "Parbo: chrome kholo, screenshot, volume, file khujo, news. LIVE TALK chapun — ami shunbo ar bolbo.",
            [],
        )

    if any(x in t for x in ("dhonnobad", "thanks", "thank you", "shukriya", "tnx")):
        return ("Apnar service e! Ar ki lagbe?", [])

    if any(x in t for x in ("bye", "allah hafez", "goodbye", "cholen", "see you")):
        return ("Allah hafez! Abar ashben.", [])

    if any(x in t for x in ("ha", "hya", "hmm", "ok", "thik", "accha", "acha", "hmm")):
        return ("Ji, bolun — ami shunchi.", [])

    # Open app
    m = re.search(r"(?:open|kholo|chalu|start|run)\s+(.+)", t)
    if m:
        app = m.group(1).strip()
        return (f"Thik ache, {app} khulchi.", [{"name": "open_app", "args": {"name": app}}])

    m = re.search(r"(.+)\s+(?:kholo|open koro|open)\s*$", t)
    if m and len(m.group(1)) < 30:
        app = m.group(1).strip()
        return (f"{app} khulchi.", [{"name": "open_app", "args": {"name": app}}])

    m = re.search(r"(?:close|bandho|bondho|kill)\s+(.+)", t)
    if m:
        return (f"{m.group(1)} bandho korchi.", [{"name": "close_app", "args": {"name": m.group(1).strip()}}])

    if any(x in t for x in ("screenshot", "screen shot", "skrin", "chobi nao")):
        return ("Screenshot nichi...", [{"name": "screenshot", "args": {}}])

    m = re.search(r"volume\s*(\d+)", t)
    if m:
        return (f"Volume {m.group(1)} korchi.", [{"name": "set_volume", "args": {"level": int(m.group(1))}}])

    if any(x in t for x in ("headline", "news", "khobor", "ajker")):
        return ("Headlines anchi...", [{"name": "print_news", "args": {}}])

    m = re.search(r"(?:search|khujo|find)\s+(.+)", t)
    if m:
        return (f"Web e khujchi: {m.group(1)}", [{"name": "web_search", "args": {"query": m.group(1).strip()}}])

    m = re.search(r"(?:list|dekhao)\s+(.+)", t)
    if m:
        return ("Folder list...", [{"name": "list_dir", "args": {"path": m.group(1).strip()}}])

    if "background" in t or "sub-agent" in t or "sub agent" in t:
        task = re.sub(r"^(senz|please|plz)\s*", "", text).strip()
        return (
            "Background worker pathalam.",
            [{"name": "parent_delegate_task", "args": {"task": task, "label": "Worker"}}],
        )

    m = re.search(r"(?:run|command|powershell)\s+(.+)", t, re.I)
    if m:
        return ("Command chalachi...", [{"name": "run_command", "args": {"command": m.group(1)}}])

    # Casual chat fallback (no Gemini)
    if _is_casual_chat(t):
        return (
            "Bujhlam! Apni ar ektu clear bolen — ba command din: chrome kholo, screenshot nao. "
            "Ami taratari korbo.",
            [],
        )

    return None


async def local_turn(user_message: str) -> tuple[str, list[dict]]:
    parsed = parse_local(user_message)
    if parsed:
        return parsed
    natural = parse_natural(user_message)
    if natural:
        return natural
    return (
        "Command try korun: chrome kholo | screenshot nao | volume 50 | ajker news",
        [],
    )
