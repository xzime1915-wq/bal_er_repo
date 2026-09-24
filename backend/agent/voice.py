"""Voice: listen via microphone, speak via edge-tts."""

import asyncio
import os
import subprocess
import tempfile
import threading

import speech_recognition as sr

from config import settings

_listening = False
_wake_thread: threading.Thread | None = None


async def speak(text: str) -> None:
    if not text.strip():
        return
    try:
        import edge_tts

        voice = "en-US-GuyNeural"
        communicate = edge_tts.Communicate(text[:300], voice)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            path = f.name
        await communicate.save(path)
        subprocess.Popen(
            ["powershell", "-c", f"(New-Object Media.SoundPlayer); Start-Process -WindowStyle Hidden '{path}'"],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        await asyncio.sleep(min(len(text) * 0.04, 6))
    except Exception:
        pass


def listen_once_text(timeout: int = 7) -> str:
    """Record one phrase from mic; return transcript or empty string."""
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.4)
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=15)
        # Bengali + English
        for lang in ("bn-BD", "en-US"):
            try:
                text = recognizer.recognize_google(audio, language=lang)
                if text.strip():
                    return text.strip()
            except sr.UnknownValueError:
                continue
            except sr.RequestError:
                break
    except sr.WaitTimeoutError:
        return ""
    except Exception:
        return ""
    return ""


def stop_wake_listener() -> None:
    global _listening
    _listening = False
