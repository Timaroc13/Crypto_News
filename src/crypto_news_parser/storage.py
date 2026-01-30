from __future__ import annotations

import json
import os
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def persistence_enabled() -> bool:
    return os.getenv("ENABLE_PERSISTENCE") == "1"


def db_path() -> str:
    # Default to a local file. In Cloud Run, /tmp is writable.
    return os.getenv("DB_PATH", str(Path(__file__).resolve().parents[2] / "data.sqlite3"))


def _connect() -> sqlite3.Connection:
    path = db_path()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS parse_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at INTEGER NOT NULL,
            input_id TEXT,
            source_url TEXT,
            source_name TEXT,
            source_published_at TEXT,
            text TEXT NOT NULL,
            response_json TEXT NOT NULL,
            schema_version TEXT NOT NULL,
            model_version TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at INTEGER NOT NULL,
            parse_run_id INTEGER,
            input_id TEXT,
            text TEXT,
            expected_json TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY(parse_run_id) REFERENCES parse_runs(id) ON DELETE SET NULL
        )
        """
    )
    conn.commit()


@dataclass(frozen=True)
class StoredParse:
    parse_id: int


def store_parse_run(
    *,
    input_id: str | None,
    source_url: str | None,
    source_name: str | None,
    source_published_at: str | None,
    text: str,
    response: dict[str, Any],
) -> StoredParse:
    conn = _connect()
    try:
        init_db(conn)
        cur = conn.execute(
            """
            INSERT INTO parse_runs (
                created_at, input_id, source_url, source_name, source_published_at,
                text, response_json, schema_version, model_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(time.time()),
                input_id,
                source_url,
                source_name,
                source_published_at,
                text,
                json.dumps(response, ensure_ascii=False),
                str(response.get("schema_version") or ""),
                str(response.get("model_version") or ""),
            ),
        )
        conn.commit()
        return StoredParse(parse_id=int(cur.lastrowid))
    finally:
        conn.close()


def _load_parse_text(conn: sqlite3.Connection, parse_id: int) -> str | None:
    row = conn.execute("SELECT text FROM parse_runs WHERE id = ?", (parse_id,)).fetchone()
    if row is None:
        return None
    return str(row["text"])


def store_feedback(
    *,
    parse_id: int | None,
    input_id: str | None,
    expected: dict[str, Any],
    notes: str | None,
) -> int:
    conn = _connect()
    try:
        init_db(conn)
        text: str | None = None
        parse_run_id: int | None = None
        if parse_id is not None:
            text = _load_parse_text(conn, parse_id)
            if text is None:
                raise ValueError("parse_id not found")
            parse_run_id = parse_id

        cur = conn.execute(
            """
            INSERT INTO feedback (created_at, parse_run_id, input_id, text, expected_json, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                int(time.time()),
                parse_run_id,
                input_id,
                text,
                json.dumps(expected, ensure_ascii=False),
                notes,
            ),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def export_feedback_cases() -> list[dict[str, Any]]:
    """Return eval-compatible JSONL objects: {id, text, expected}.

    Notes:
    - For feedback linked to a parse_id, we export the parse text.
    - For feedback submitted only with input_id, text may be null unless provided via parse linkage.
      (We intentionally keep this minimal; future iteration can store text on feedback submission.)
    """

    conn = _connect()
    try:
        init_db(conn)
        rows = conn.execute(
            "SELECT id, text, expected_json FROM feedback ORDER BY id ASC"
        ).fetchall()
        cases: list[dict[str, Any]] = []
        for r in rows:
            expected = json.loads(r["expected_json"]) if r["expected_json"] else {}
            text = r["text"]
            if not text:
                # Skip cases we cannot export into eval harness.
                continue
            cases.append({"id": f"feedback-{r['id']}", "text": text, "expected": expected})
        return cases
    finally:
        conn.close()
