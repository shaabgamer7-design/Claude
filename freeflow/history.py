"""Local SQLite log of dictations, with usage stats."""

from __future__ import annotations

import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at REAL NOT NULL,
    mode TEXT NOT NULL,
    app TEXT NOT NULL DEFAULT '',
    style TEXT NOT NULL DEFAULT '',
    raw_text TEXT NOT NULL,
    final_text TEXT NOT NULL,
    audio_seconds REAL NOT NULL DEFAULT 0,
    stt_ms INTEGER NOT NULL DEFAULT 0,
    llm_ms INTEGER NOT NULL DEFAULT 0,
    words INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS entries_created ON entries(created_at);
"""

TYPING_WPM = 40  # average typing speed, for "time saved"


@dataclass
class Entry:
    id: int
    created_at: float
    mode: str
    app: str
    style: str
    raw_text: str
    final_text: str
    audio_seconds: float
    stt_ms: int
    llm_ms: int
    words: int


@dataclass
class Stats:
    sessions: int
    words: int
    audio_seconds: float
    words_today: int

    @property
    def wpm(self) -> float:
        return self.words / (self.audio_seconds / 60) if self.audio_seconds else 0.0

    @property
    def minutes_saved(self) -> float:
        return max(0.0, self.words / TYPING_WPM - self.audio_seconds / 60)


class History:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(path), check_same_thread=False)
        self._db.executescript(SCHEMA)
        self._lock = threading.Lock()

    def add(self, mode: str, raw: str, final: str, app: str = "", style: str = "",
            audio_seconds: float = 0.0, stt_ms: int = 0, llm_ms: int = 0) -> int:
        with self._lock, self._db:
            cur = self._db.execute(
                "INSERT INTO entries (created_at, mode, app, style, raw_text, final_text,"
                " audio_seconds, stt_ms, llm_ms, words) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (time.time(), mode, app, style, raw, final, audio_seconds, stt_ms, llm_ms,
                 len(final.split())),
            )
            return int(cur.lastrowid)

    def recent(self, limit: int = 20, search: str = "") -> list[Entry]:
        sql = "SELECT * FROM entries"
        args: list = []
        if search:
            sql += " WHERE final_text LIKE ? OR raw_text LIKE ?"
            args += [f"%{search}%", f"%{search}%"]
        sql += " ORDER BY id DESC LIMIT ?"
        args.append(limit)
        with self._lock:
            rows = self._db.execute(sql, args).fetchall()
        return [Entry(*row) for row in rows]

    def last(self) -> Entry | None:
        rows = self.recent(1)
        return rows[0] if rows else None

    def stats(self) -> Stats:
        midnight = time.mktime(time.localtime()[:3] + (0, 0, 0, 0, 0, -1))
        with self._lock:
            sessions, words, audio = self._db.execute(
                "SELECT COUNT(*), COALESCE(SUM(words),0), COALESCE(SUM(audio_seconds),0)"
                " FROM entries"
            ).fetchone()
            (today,) = self._db.execute(
                "SELECT COALESCE(SUM(words),0) FROM entries WHERE created_at >= ?", (midnight,)
            ).fetchone()
        return Stats(sessions, words, audio, today)

    def clear(self) -> None:
        with self._lock, self._db:
            self._db.execute("DELETE FROM entries")

    def close(self) -> None:
        self._db.close()
