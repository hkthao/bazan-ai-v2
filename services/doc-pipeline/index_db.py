"""SQLite index để track file đã xử lý — tránh re-process."""

import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime
from config import settings


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.index_db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS doc_index (
                file_path       TEXT PRIMARY KEY,
                md5_hash        TEXT NOT NULL,
                processed_at    TEXT NOT NULL,
                quality_score   INTEGER,
                topic           TEXT,
                region          TEXT,
                doc_type        TEXT,
                language        TEXT,
                status          TEXT,   -- uploaded | review | rejected | error
                webui_file_id   TEXT,
                error_message   TEXT
            )
        """)
        conn.commit()


def get_file_hash(file_path: Path) -> str:
    return hashlib.md5(file_path.read_bytes()).hexdigest()


def is_already_processed(file_path: Path) -> bool:
    current_hash = get_file_hash(file_path)
    with get_connection() as conn:
        row = conn.execute(
            "SELECT md5_hash FROM doc_index WHERE file_path = ?", (str(file_path),)
        ).fetchone()
    return row is not None and row["md5_hash"] == current_hash


def save_result(file_path: Path, result: dict) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO doc_index
            (file_path, md5_hash, processed_at, quality_score, topic,
             region, doc_type, language, status, webui_file_id, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                str(file_path),
                get_file_hash(file_path),
                datetime.now().isoformat(),
                result.get("quality_score"),
                result.get("topic"),
                result.get("region"),
                result.get("doc_type"),
                result.get("language"),
                result.get("status"),
                result.get("webui_file_id"),
                result.get("error_message"),
            ),
        )
        conn.commit()


def get_review_files() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM doc_index WHERE status = 'review' ORDER BY quality_score DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_stats() -> dict:
    with get_connection() as conn:
        stats = {}
        for status in ["uploaded", "review", "rejected", "error"]:
            count = conn.execute(
                "SELECT COUNT(*) FROM doc_index WHERE status = ?", (status,)
            ).fetchone()[0]
            stats[status] = count
    return stats
