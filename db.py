import hmac
import hashlib
import json
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime

DB_PATH = "app.db"


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            pages_json TEXT NOT NULL,
            results_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE
        );
        """)


def _now():
    return datetime.now().isoformat(timespec="seconds")


# ---------- Users ----------
def _hash(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000).hex()


def create_user(username: str, password: str) -> bool:
    salt = secrets.token_bytes(16)
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO users (username, password_hash, salt, created_at) "
                "VALUES (?, ?, ?, ?)",
                (username.lower(), _hash(password, salt), salt.hex(), _now()),
            )
        return True
    except sqlite3.IntegrityError:   # username already taken
        return False


def verify_user(username: str, password: str):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username.lower(),)
        ).fetchone()
    if not row:
        return None
    actual = _hash(password, bytes.fromhex(row["salt"]))
    if hmac.compare_digest(row["password_hash"], actual):
        return {"id": row["id"], "username": row["username"]}
    return None


# ---------- Documents ----------
def add_document(user_id: int, name: str, pages, results: dict) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO documents (user_id, name, pages_json, results_json, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, name, json.dumps(pages, ensure_ascii=False),
             json.dumps(results, ensure_ascii=False), _now()),
        )
        return cur.lastrowid


def list_documents(user_id: int):
    with get_conn() as conn:
        return conn.execute(
            "SELECT id, name, created_at FROM documents "
            "WHERE user_id = ? ORDER BY id DESC", (user_id,)
        ).fetchall()


def get_document(user_id: int, doc_id: int):
    """Filters by user_id too, so one user can never open another user's document."""
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM documents WHERE id = ? AND user_id = ?", (doc_id, user_id)
        ).fetchone()


def delete_document(user_id: int, doc_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM documents WHERE id = ? AND user_id = ?",
                     (doc_id, user_id))


# ---------- Chat messages ----------
def add_message(doc_id: int, role: str, content: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO messages (doc_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (doc_id, role, content, _now()),
        )


def get_messages(doc_id: int):
    with get_conn() as conn:
        return conn.execute(
            "SELECT role, content FROM messages WHERE doc_id = ? ORDER BY id", (doc_id,)
        ).fetchall()