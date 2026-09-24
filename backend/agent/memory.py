import json
import sqlite3
from datetime import datetime, timezone

from config import MEMORY_DB


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(MEMORY_DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                body TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def memory_set(key: str, value: str) -> str:
    with _conn() as c:
        c.execute(
            """
            INSERT INTO memories (key, value, updated_at) VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
            """,
            (key, value, _now()),
        )
    return f"Memory saved: {key}"


def memory_get(key: str) -> str:
    with _conn() as c:
        row = c.execute("SELECT value FROM memories WHERE key=?", (key,)).fetchone()
    return row["value"] if row else ""


def memory_list() -> list[dict]:
    with _conn() as c:
        rows = c.execute("SELECT key, value, updated_at FROM memories ORDER BY updated_at DESC").fetchall()
    return [dict(r) for r in rows]


def chat_append(role: str, content: str) -> None:
    with _conn() as c:
        c.execute(
            "INSERT INTO chat_history (role, content, created_at) VALUES (?, ?, ?)",
            (role, content, _now()),
        )


def chat_clear() -> None:
    with _conn() as c:
        c.execute("DELETE FROM chat_history")


def chat_recent(limit: int = 30) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT role, content, created_at FROM chat_history ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return list(reversed([dict(r) for r in rows]))


def note_add(title: str, body: str) -> int:
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO notes (title, body, created_at) VALUES (?, ?, ?)",
            (title or "Untitled", body, _now()),
        )
        return int(cur.lastrowid)


def notes_list() -> list[dict]:
    with _conn() as c:
        rows = c.execute("SELECT id, title, body, created_at FROM notes ORDER BY id DESC LIMIT 50").fetchall()
    return [dict(r) for r in rows]


def profile_summary() -> str:
    prefs = memory_get("user_profile")
    if prefs:
        return prefs
    return json.dumps({"language": "bn-en mix", "agent": "SENZ"}, ensure_ascii=False)
