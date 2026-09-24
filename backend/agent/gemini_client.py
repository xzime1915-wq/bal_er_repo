import asyncio
import json
import re

import httpx

from config import settings

API_BASE = "https://generativelanguage.googleapis.com/v1beta"

# User key e available (list_models theke)
PREFERRED_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash-001",
    "gemini-2.0-flash-lite-001",
]

_cached_models: list[str] | None = None


async def _fetch_available_models() -> list[str]:
    global _cached_models
    if _cached_models is not None:
        return _cached_models
    if not settings.gemini_api_key:
        _cached_models = PREFERRED_MODELS
        return _cached_models
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(
                f"{API_BASE}/models",
                params={"key": settings.gemini_api_key},
            )
            if r.status_code == 200:
                names = []
                for m in r.json().get("models", []):
                    n = m.get("name", "").split("/")[-1]
                    if n and "generateContent" in m.get("supportedGenerationMethods", []):
                        names.append(n)
                flash = [n for n in names if "gemini" in n and "flash" in n]
                _cached_models = flash or PREFERRED_MODELS
                return _cached_models
    except Exception:
        pass
    _cached_models = PREFERRED_MODELS
    return _cached_models


def _model_candidates() -> list[str]:
    primary = settings.gemini_model.strip()
    available = _cached_models or PREFERRED_MODELS
    out: list[str] = []
    for m in [primary, *PREFERRED_MODELS, *available]:
        if m and m not in out:
            out.append(m)
    return out


def _is_rate_limit(status: int, body: str) -> bool:
    return status == 429 or "quota" in body.lower() or "rate" in body.lower()


def _retry_seconds(body: str) -> int:
    m = re.search(r"retry in ([\d.]+)s", body, re.I)
    if m:
        return min(60, max(3, int(float(m.group(1)) + 1)))
    return 10


def friendly_gemini_error(exc: Exception) -> str:
    msg = str(exc)
    if "429" in msg or "quota" in msg.lower():
        wait = _retry_seconds(msg)
        return (
            "SENZ: Gemini quota full (free limit).\n\n"
            f"• {wait}s por abar try korun\n"
            "• Local mode: 'chrome kholo', 'screenshot nao' — API chara o kaj korbe\n"
            "• Billing: https://aistudio.google.com"
        )
    if "timeout" in msg.lower():
        return "SENZ: AI response slow — local command try korun (chrome kholo)."
    if "api key" in msg.lower():
        return "SENZ: GEMINI_API_KEY check korun (.env)."
    return f"SENZ: {msg[:220]}"


async def _generate_rest(prompt: str, model: str) -> tuple[int, str]:
    url = f"{API_BASE}/models/{model}:generateContent"
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 1024, "temperature": 0.7},
    }
    async with httpx.AsyncClient(timeout=httpx.Timeout(20.0, connect=5.0)) as client:
        r = await client.post(url, params={"key": settings.gemini_api_key}, json=body)
        return r.status_code, r.text


async def _generate_with_fallback(prompt: str) -> str:
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY missing")

    await _fetch_available_models()
    last_body = ""

    for model in _model_candidates()[:4]:
        status, body = await _generate_rest(prompt, model)
        if status == 200:
            data = json.loads(body)
            parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
            text = "".join(p.get("text", "") for p in parts)
            if text:
                return text
            last_body = "empty response"
            continue
        last_body = body
        if _is_rate_limit(status, body):
            raise RuntimeError(body)
        if status == 404:
            continue
        raise RuntimeError(body[:300])

    raise RuntimeError(last_body[:300] or "All models failed")


SYSTEM_PROMPT = """You are SENZ, a Windows PC assistant. Reply short. Use Banglish if user does.
To run PC actions, include ONLY this JSON block (no extra keys):
```json
{"tools":[{"name":"tool_name","args":{}}]}
```
Tools: open_app, close_app, run_command, set_volume, screenshot, list_dir, web_search, print_news, parent_delegate_task.
"""


def _extract_tool_calls(text: str) -> tuple[str, list[dict]]:
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
    return clean.strip(), tools


async def chat_simple(prompt: str) -> str:
    return await _generate_with_fallback(prompt)


async def agent_turn(user_message: str, context: str) -> tuple[str, list[dict]]:
    from agent.tools.registry import tools_prompt_block

    prompt = f"{SYSTEM_PROMPT}\n{tools_prompt_block()}\n{context}\nUser: {user_message}\nSENZ:"
    text = await _generate_with_fallback(prompt)
    reply, tool_calls = _extract_tool_calls(text)
    return reply or text, tool_calls


# Sync helper for health endpoint
def get_model_names_sync() -> list[str]:
    return _cached_models or PREFERRED_MODELS
