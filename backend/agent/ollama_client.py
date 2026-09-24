"""Local LLM via Ollama — long natural conversation, no API quota."""

import json
import re

import httpx

from config import settings

_ollama_up: bool | None = None

SYSTEM = """You are SENZ, a friendly Windows PC assistant. User speaks Bangla, Banglish, or English.
Reply naturally in 2-5 sentences (can mix Banglish). Be warm like Jarvis.

If user wants a PC action, ALSO include this JSON block:
```json
{"tools":[{"name":"TOOL","args":{}}]}
```
Tools: open_app(name), close_app(name), screenshot, set_volume(level 0-100), web_search(query), print_news.
If just chatting, no JSON needed. Never fake actions — only JSON when user clearly wants an action."""


async def check_ollama() -> bool:
    global _ollama_up
    if not settings.ollama_enabled:
        _ollama_up = False
        return False
    try:
        async with httpx.AsyncClient(timeout=3) as c:
            r = await c.get(f"{settings.ollama_url.rstrip('/')}/api/tags")
            _ollama_up = r.status_code == 200
    except Exception:
        _ollama_up = False
    return bool(_ollama_up)


def _extract_tools(text: str) -> tuple[str, list[dict]]:
    tools: list[dict] = []
    clean = text
    for match in re.finditer(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL):
        try:
            data = json.loads(match.group(1))
            if isinstance(data.get("tools"), list):
                tools.extend(data["tools"])
                clean = clean.replace(match.group(0), "").strip()
        except json.JSONDecodeError:
            pass
    return clean.strip() or text.strip(), tools


async def ollama_turn(user_message: str, context: str) -> tuple[str, list[dict]]:
    if not await check_ollama():
        raise RuntimeError("Ollama not running")

    url = f"{settings.ollama_url.rstrip('/')}/api/chat"
    payload = {
        "model": settings.ollama_model,
        "stream": False,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"{context}\n\nUser: {user_message}"},
        ],
    }
    async with httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=5.0)) as c:
        r = await c.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
    text = data.get("message", {}).get("content", "") or ""
    reply, tools = _extract_tools(text)
    return reply or text, tools
