# -*- coding: utf-8 -*-
"""SQLite 持久化：短连接模式（Streamlit 多线程 rerun 下禁用全局连接）。

落盘内容：trips / checkins / journals / photos / solo_conversations / group_conversations。
所有会话数据存 JSON 文本快照，档案页直接 json.loads 回放。
"""
import json
import sqlite3
from contextlib import contextmanager

from config import DB_PATH

_SCHEMA = """
CREATE TABLE IF NOT EXISTS trips (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
  city TEXT NOT NULL,
  route_name TEXT NOT NULL,
  mode TEXT NOT NULL,
  person_ids TEXT NOT NULL,
  preferences TEXT,
  route_json TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'ongoing'
);
CREATE TABLE IF NOT EXISTS checkins (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  trip_id INTEGER NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
  site_key TEXT NOT NULL,
  site_name TEXT NOT NULL,
  sequence INTEGER NOT NULL,
  dialogue_log TEXT,
  unlocked_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
  UNIQUE(trip_id, site_key)
);
CREATE TABLE IF NOT EXISTS journals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  trip_id INTEGER NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS photos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  trip_id INTEGER NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
  site_key TEXT,
  file_path TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS solo_conversations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  person_id TEXT NOT NULL,
  title TEXT,
  messages TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS group_conversations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  member_ids TEXT NOT NULL,
  title TEXT,
  messages TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db():
    """短连接上下文：正常退出提交 + 显式关闭；异常回滚。
    （sqlite3 自带的 with 只 commit 不 close；直接 close 又会回滚未提交事务——
    两者都做，补齐旧实现的连接泄漏与回滚语义。）"""
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with db() as conn:
        conn.executescript(_SCHEMA)
        conn.execute("PRAGMA journal_mode=WAL")


# ———— trips ————
def create_trip(city: str, route_name: str, mode: str, person_ids: list,
                preferences: dict, route: dict) -> int:
    with db() as conn:
        cur = conn.execute(
            "INSERT INTO trips (city, route_name, mode, person_ids, preferences, route_json) "
            "VALUES (?,?,?,?,?,?)",
            (city, route_name, mode, json.dumps(person_ids, ensure_ascii=False),
             json.dumps(preferences, ensure_ascii=False), json.dumps(route, ensure_ascii=False)),
        )
        return cur.lastrowid


def complete_trip(trip_id: int):
    with db() as conn:
        conn.execute("UPDATE trips SET status='completed' WHERE id=?", (trip_id,))


def list_trips() -> list[sqlite3.Row]:
    with db() as conn:
        return conn.execute(
            "SELECT t.*, "
            "(SELECT COUNT(*) FROM checkins c WHERE c.trip_id=t.id) AS unlocked_count "
            "FROM trips t ORDER BY t.created_at DESC, t.id DESC"
        ).fetchall()


def get_trip(trip_id: int) -> sqlite3.Row | None:
    with db() as conn:
        return conn.execute("SELECT * FROM trips WHERE id=?", (trip_id,)).fetchone()


def delete_trip(trip_id: int) -> list[str]:
    """删除行程（打卡/随笔/照片记录级联删除），返回被删照片文件名供清理文件。"""
    with db() as conn:
        rows = conn.execute(
            "SELECT file_path FROM photos WHERE trip_id=?", (trip_id,)
        ).fetchall()
        conn.execute("DELETE FROM trips WHERE id=?", (trip_id,))
        return [r["file_path"] for r in rows]


# ———— checkins ————
def add_checkin(trip_id: int, site_key: str, site_name: str, sequence: int,
                dialogue_log: list) -> bool:
    with db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO checkins (trip_id, site_key, site_name, sequence, dialogue_log) "
            "VALUES (?,?,?,?,?)",
            (trip_id, site_key, site_name, sequence, json.dumps(dialogue_log, ensure_ascii=False)),
        )
        return conn.total_changes > 0


def get_checkins(trip_id: int) -> list[sqlite3.Row]:
    with db() as conn:
        return conn.execute(
            "SELECT * FROM checkins WHERE trip_id=? ORDER BY sequence", (trip_id,)
        ).fetchall()


# ———— journals / photos ————
def add_journal(trip_id: int, content: str) -> int:
    with db() as conn:
        return conn.execute(
            "INSERT INTO journals (trip_id, content) VALUES (?,?)", (trip_id, content)
        ).lastrowid


def get_journals(trip_id: int) -> list[sqlite3.Row]:
    with db() as conn:
        return conn.execute(
            "SELECT * FROM journals WHERE trip_id=? ORDER BY created_at", (trip_id,)
        ).fetchall()


def add_photo(trip_id: int, site_key: str, file_path: str) -> int:
    with db() as conn:
        return conn.execute(
            "INSERT INTO photos (trip_id, site_key, file_path) VALUES (?,?,?)",
            (trip_id, site_key, file_path),
        ).lastrowid


def get_photos(trip_id: int) -> list[sqlite3.Row]:
    with db() as conn:
        return conn.execute(
            "SELECT * FROM photos WHERE trip_id=? ORDER BY created_at", (trip_id,)
        ).fetchall()


# ———— 对话落库 ————
def create_solo_convo(person_id: str, title: str) -> int:
    with db() as conn:
        return conn.execute(
            "INSERT INTO solo_conversations (person_id, title, messages) VALUES (?,?,?)",
            (person_id, title, json.dumps([], ensure_ascii=False)),
        ).lastrowid


def update_solo_convo(convo_id: int, messages: list):
    with db() as conn:
        conn.execute(
            "UPDATE solo_conversations SET messages=? WHERE id=?",
            (json.dumps(messages, ensure_ascii=False), convo_id),
        )


def create_group_convo(member_ids: list, title: str) -> int:
    with db() as conn:
        return conn.execute(
            "INSERT INTO group_conversations (member_ids, title, messages) VALUES (?,?,?)",
            (json.dumps(member_ids, ensure_ascii=False), title,
             json.dumps([], ensure_ascii=False)),
        ).lastrowid


def update_group_convo(convo_id: int, messages: list):
    with db() as conn:
        conn.execute(
            "UPDATE group_conversations SET messages=? WHERE id=?",
            (json.dumps(messages, ensure_ascii=False), convo_id),
        )
