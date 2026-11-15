import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.config import DB_PATH


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        skill_id TEXT NOT NULL,
        skill_title TEXT NOT NULL,
        category TEXT NOT NULL,
        title TEXT NOT NULL,
        phase TEXT DEFAULT 'Phase 1: Warm-up',
        status TEXT DEFAULT 'active',
        model TEXT DEFAULT 'gemini-pro-latest',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        action_type TEXT DEFAULT 'chat',
        timestamp TEXT NOT NULL,
        FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS evaluations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        score INTEGER,
        recommendation TEXT,
        rubric_json TEXT,
        feedback_markdown TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
    );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages (session_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_updated ON sessions (updated_at DESC);")
    conn.commit()
    conn.close()


def create_session(session_id: str, skill_id: str, skill_title: str, category: str, title: str, model: str) -> dict:
    conn = get_connection()
    now = datetime.utcnow().isoformat()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sessions (id, skill_id, skill_title, category, title, phase, status, model, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 'Phase 1: Warm-up', 'active', ?, ?, ?)
    """, (session_id, skill_id, skill_title, category, title, model, now, now))
    conn.commit()
    conn.close()
    return get_session(session_id)


def get_session(session_id: str) -> Optional[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)


def list_sessions(limit: int = 50) -> List[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions ORDER BY updated_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_session_phase(session_id: str, phase: str, status: Optional[str] = None):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    if status:
        cursor.execute("UPDATE sessions SET phase = ?, status = ?, updated_at = ? WHERE id = ?", (phase, status, now, session_id))
    else:
        cursor.execute("UPDATE sessions SET phase = ?, updated_at = ? WHERE id = ?", (phase, now, session_id))
    conn.commit()
    conn.close()


def delete_session(session_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    cursor.execute("DELETE FROM evaluations WHERE session_id = ?", (session_id,))
    cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()


def add_message(session_id: str, role: str, content: str, action_type: str = "chat") -> dict:
    conn = get_connection()
    now = datetime.utcnow().isoformat()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO messages (session_id, role, content, action_type, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (session_id, role, content, action_type, now))
    msg_id = cursor.lastrowid
    cursor.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id))
    conn.commit()
    conn.close()
    return {
        "id": msg_id,
        "session_id": session_id,
        "role": role,
        "content": content,
        "action_type": action_type,
        "timestamp": now,
    }


def get_messages(session_id: str) -> List[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messages WHERE session_id = ? ORDER BY id ASC", (session_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_evaluation(session_id: str, score: int, recommendation: str, rubric_json: dict, feedback_markdown: str):
    conn = get_connection()
    now = datetime.utcnow().isoformat()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO evaluations (session_id, score, recommendation, rubric_json, feedback_markdown, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (session_id, score, recommendation, json.dumps(rubric_json), feedback_markdown, now))
    cursor.execute("UPDATE sessions SET status = 'completed', updated_at = ? WHERE id = ?", (now, session_id))
    conn.commit()
    conn.close()


def get_evaluation(session_id: str) -> Optional[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM evaluations WHERE session_id = ? ORDER BY id DESC LIMIT 1", (session_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    res = dict(row)
    if res.get("rubric_json"):
        try:
            res["rubric_json"] = json.loads(res["rubric_json"])
        except Exception:
            pass
    return res
