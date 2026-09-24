import asyncio
import json
import sys
from contextlib import asynccontextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from agent import memory
from agent.core import run_instruction, state, terminate
from agent.gemini_client import _fetch_available_models
from agent.sub_agents import list_jobs
from agent.tools import web_tools
from agent.voice import listen_once_text, speak, stop_wake_listener
from config import settings

memory.init_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await _fetch_available_models()
    except Exception:
        pass
    yield


app = FastAPI(title="SENZ Agent API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_connections: set[WebSocket] = set()


async def broadcast(event: dict) -> None:
    dead = set()
    for ws in _connections:
        try:
            await ws.send_json(event)
        except Exception:
            dead.add(ws)
    _connections -= dead


@app.get("/")
async def root():
    return {"name": "SENZ", "hint": "Use start.bat desktop app"}


@app.get("/api/health")
async def health():
    from agent.gemini_client import get_model_names_sync
    from agent.ollama_client import check_ollama

    ollama = await check_ollama()
    return {
        "name": "SENZ",
        "active": state.active,
        "gemini_configured": bool(settings.gemini_api_key),
        "gemini_model": settings.gemini_model,
        "models_available": get_model_names_sync(),
        "ollama_online": ollama,
        "ollama_model": settings.ollama_model if ollama else None,
        "brain_hint": "ollama" if ollama else "local+commands",
        "wake_phrase": settings.senz_wake_phrase,
    }


@app.get("/api/state")
async def get_state():
    headlines = state.headlines
    if not headlines:
        try:
            headlines = await web_tools.fetch_headlines()
            state.headlines = headlines
        except Exception:
            headlines = []
    return {
        "active": state.active,
        "headlines": headlines,
        "diagram": state.diagram,
        "sub_agents": list_jobs(),
        "chat": memory.chat_recent(20),
        "notes": memory.notes_list(),
        "wake_phrase": settings.senz_wake_phrase,
    }


async def _safe_run_instruction(text: str) -> dict:
    try:
        return await asyncio.wait_for(run_instruction(text), timeout=55.0)
    except asyncio.TimeoutError:
        reply = "Timeout holo. Abar bolun: chrome kholo"
        return {
            "reply": reply,
            "speak_text": reply,
            "mode": "timeout",
            "tools": [],
            "headlines": state.headlines,
            "diagram": state.diagram,
            "sub_agents": list_jobs(),
            "active": state.active,
        }
    except Exception as e:
        reply = f"Error: {e}"
        return {
            "reply": reply,
            "speak_text": "Kichu problem holo, abar try korun",
            "mode": "error",
            "tools": [],
            "headlines": state.headlines,
            "diagram": state.diagram,
            "sub_agents": list_jobs(),
            "active": state.active,
        }


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    _connections.add(ws)
    await ws.send_json({"type": "connected", "agent": "SENZ"})
    try:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)
            mtype = msg.get("type", "chat")

            if mtype == "chat":
                text = msg.get("text", "").strip()
                if not text:
                    continue
                await ws.send_json({"type": "thinking"})
                result = await _safe_run_instruction(text)
                await ws.send_json({"type": "response", **result})

            elif mtype == "voice_transcript":
                text = msg.get("text", "").strip()
                if not text:
                    await ws.send_json({"type": "voice_error", "message": "Kichu shona jayni"})
                    continue
                await ws.send_json({"type": "thinking"})
                result = await _safe_run_instruction(text)
                await ws.send_json({"type": "response", **result})

            elif mtype == "voice_listen":
                await ws.send_json({"type": "voice_listening"})
                loop = asyncio.get_event_loop()
                text = await loop.run_in_executor(None, listen_once_text)
                if text:
                    await ws.send_json({"type": "voice_heard", "text": text})
                    await ws.send_json({"type": "thinking"})
                    result = await _safe_run_instruction(text)
                    await ws.send_json({"type": "response", **result})
                else:
                    await ws.send_json({"type": "voice_error", "message": "Mic/shona jayni — abar try korun"})

            elif mtype == "terminate":
                terminate()
                await ws.send_json({"type": "terminated"})
                stop_wake_listener()

            elif mtype == "voice_enable":
                await ws.send_json({
                    "type": "voice_on",
                    "phrase": settings.senz_wake_phrase,
                    "hint": "Mic button chapun — bole din command",
                })

            elif mtype == "voice_disable":
                stop_wake_listener()
                await ws.send_json({"type": "voice_off"})

            elif mtype == "clear_chat":
                memory.chat_clear()
                await ws.send_json({"type": "chat_cleared"})

            elif mtype == "ping":
                await ws.send_json({"type": "pong"})

    except WebSocketDisconnect:
        pass
    finally:
        _connections.discard(ws)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=settings.senz_port, reload=False)
