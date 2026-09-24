import asyncio
import json
import time
from dataclasses import dataclass, field

from agent import memory
from agent.gemini_client import agent_turn, friendly_gemini_error
from agent.local_brain import _is_casual_chat, _norm, local_turn, parse_local
from agent.natural_parser import parse_natural
from agent.ollama_client import check_ollama, ollama_turn
from agent.sub_agents import list_jobs
from agent.tools.registry import execute_tool


@dataclass
class ModuleLog:
    name: str
    duration_ms: float
    status: str = "ok"
    detail: str = ""


@dataclass
class AgentState:
    active: bool = True
    headlines: list[dict] = field(default_factory=list)
    diagram: str = "flowchart LR\n  User --> SENZ\n  SENZ --> PC"
    module_logs: list[ModuleLog] = field(default_factory=list)
    last_reply: str = ""
    use_cloud: bool = True
    prefer_ollama: bool = True


state = AgentState()

GEMINI_TIMEOUT = 22.0
OLLAMA_TIMEOUT = 75.0


def _speak_text(reply: str) -> str:
    import re

    line = reply.split("\n")[0].strip()
    line = re.sub(r"\[ok\].*", "", line).strip()
    if line.startswith("SENZ:"):
        line = line[5:].strip()
    return (line[:220] if line else "Thik ache, hoye geche.") or "Done."


async def _try_ollama(text: str, context: str) -> tuple[str, list[dict], str] | None:
    if not state.prefer_ollama or not await check_ollama():
        return None
    try:
        reply, tools = await asyncio.wait_for(ollama_turn(text, context), timeout=OLLAMA_TIMEOUT)
        return reply, tools, "ollama"
    except Exception:
        return None


async def _brain(text: str, context: str) -> tuple[str, list[dict], str]:
    """Priority: exact command → natural long command → Ollama chat → Gemini → local."""

    parsed = parse_local(text)
    if parsed:
        return parsed[0], parsed[1], "local"

    natural = parse_natural(text)
    if natural:
        return natural[0], natural[1], "natural"

    word_count = len(_norm(text).split())

    # Long / multi-sentence → Ollama (free local brain for real conversation)
    if word_count >= 4 or not _is_casual_chat(_norm(text)):
        ollama = await _try_ollama(text, context)
        if ollama:
            return ollama

    # Short casual chat
    if _is_casual_chat(_norm(text)):
        ollama = await _try_ollama(text, context)
        if ollama:
            return ollama
        fb = await local_turn(text)
        return fb[0], fb[1], "local"

    # Gemini (if quota OK)
    if state.use_cloud:
        try:
            reply, tools = await asyncio.wait_for(agent_turn(text, context), timeout=GEMINI_TIMEOUT)
            return reply, tools, "cloud"
        except Exception as e:
            if "quota" in str(e).lower() or "429" in str(e):
                state.use_cloud = False

    ollama = await _try_ollama(text, context)
    if ollama:
        return ollama

    fb = await local_turn(text)
    return fb[0], fb[1], "local"


async def run_instruction(text: str) -> dict:
    memory.chat_append("user", text)
    logs: list[ModuleLog] = []

    context = (
        f"Profile: {memory.profile_summary()}\n"
        f"Recent: {json.dumps(memory.chat_recent(6), ensure_ascii=False)[:1200]}"
    )

    t0 = time.perf_counter()
    reply, tool_calls, mode = await _brain(text, context)
    logs.append(ModuleLog(f"brain_{mode}", (time.perf_counter() - t0) * 1000))

    tool_results = []
    for call in tool_calls:
        name = call.get("name", "")
        args = call.get("args", {}) or {}
        t1 = time.perf_counter()
        try:
            result = await execute_tool(name, args)
            status = "ok"
        except Exception as ex:
            result = str(ex)
            status = "error"
        dur = (time.perf_counter() - t1) * 1000
        logs.append(ModuleLog(name, dur, status, result[:200]))
        tool_results.append({"name": name, "result": result})

        if name == "print_news":
            try:
                state.headlines = json.loads(result)
            except json.JSONDecodeError:
                pass
        if name == "generate_diagram":
            try:
                data = json.loads(result)
                state.diagram = data.get("mermaid", state.diagram)
            except json.JSONDecodeError:
                pass

    if tool_results and not reply.strip():
        reply = "Done!"

    full_reply = reply
    if tool_results:
        full_reply += "\n\n" + "\n".join(
            f"[ok] {t['name']}: {str(t['result'])[:200]}" for t in tool_results
        )

    memory.chat_append("assistant", full_reply)
    state.module_logs = logs[-20:]
    state.last_reply = full_reply

    return {
        "reply": full_reply,
        "speak_text": _speak_text(full_reply),
        "mode": mode,
        "tools": [{"name": l.name, "duration_ms": round(l.duration_ms, 1), "status": l.status} for l in logs],
        "headlines": state.headlines,
        "diagram": state.diagram,
        "sub_agents": list_jobs(),
        "active": state.active,
    }


def terminate() -> None:
    state.active = False
