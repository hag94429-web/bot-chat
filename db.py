import sqlite3
from typing import Optional

DB_NAME = "antiraid.db"


def connect():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS whitelist (
            user_id INTEGER PRIMARY KEY
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_seen_at INTEGER,
            messages_count INTEGER DEFAULT 0,
            trust_level TEXT DEFAULT 'new'
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS join_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            invite TEXT,
            entry_type TEXT,
            time INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS mute_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            reason TEXT,
            time INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS ban_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            reason TEXT,
            time INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS raid_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT,
            reason TEXT,
            time INTEGER
        )
    """)

    conn.commit()
    conn.close()


# ---------- whitelist ----------
def add_wl(uid: int):
    conn = connect()
    conn.execute("INSERT OR IGNORE INTO whitelist (user_id) VALUES (?)", (uid,))
    conn.commit()
    conn.close()


def del_wl(uid: int):
    conn = connect()
    conn.execute("DELETE FROM whitelist WHERE user_id = ?", (uid,))
    conn.commit()
    conn.close()


def is_wl(uid: int) -> bool:
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM whitelist WHERE user_id = ? LIMIT 1", (uid,))
    row = cur.fetchone()
    conn.close()
    return row is not None


def get_wl():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM whitelist ORDER BY user_id ASC")
    rows = cur.fetchall()
    conn.close()
    return [row["user_id"] for row in rows]


# ---------- users / trust ----------
def ensure_user(uid: int, now_ts: int):
    conn = connect()
    conn.execute("""
        INSERT OR IGNORE INTO users (user_id, first_seen_at, messages_count, trust_level)
        VALUES (?, ?, 0, 'new')
    """, (uid, now_ts))
    conn.commit()
    conn.close()


def increment_user_messages(uid: int):
    conn = connect()
    conn.execute("""
        UPDATE users
        SET messages_count = messages_count + 1
        WHERE user_id = ?
    """, (uid,))
    conn.commit()
    conn.close()


def set_user_trust(uid: int, trust_level: str):
    conn = connect()
    conn.execute("UPDATE users SET trust_level = ? WHERE user_id = ?", (trust_level, uid))
    conn.commit()
    conn.close()


def get_user(uid: int) -> Optional[sqlite3.Row]:
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = ? LIMIT 1", (uid,))
    row = cur.fetchone()
    conn.close()
    return row


# ---------- logs ----------
def log_join(uid: int, invite: str, entry_type: str = "user"):
    conn = connect()
    conn.execute("""
        INSERT INTO join_logs (user_id, invite, entry_type, time)
        VALUES (?, ?, ?, strftime('%s','now'))
    """, (uid, invite, entry_type))
    conn.commit()
    conn.close()


def get_join_logs(limit: int = 15):
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT user_id, invite, entry_type, time
        FROM join_logs
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows


def log_mute(uid: int, reason: str):
    conn = connect()
    conn.execute("""
        INSERT INTO mute_logs (user_id, reason, time)
        VALUES (?, ?, strftime('%s','now'))
    """, (uid, reason))
    conn.commit()
    conn.close()


def get_mute_logs(limit: int = 15):
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT user_id, reason, time
        FROM mute_logs
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows


def log_ban(uid: int, reason: str):
    conn = connect()
    conn.execute("""
        INSERT INTO ban_logs (user_id, reason, time)
        VALUES (?, ?, strftime('%s','now'))
    """, (uid, reason))
    conn.commit()
    conn.close()


def get_ban_logs(limit: int = 15):
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT user_id, reason, time
        FROM ban_logs
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows


def log_raid_event(event_type: str, reason: str):
    conn = connect()
    conn.execute("""
        INSERT INTO raid_events (event_type, reason, time)
        VALUES (?, ?, strftime('%s','now'))
    """, (event_type, reason))
    conn.commit()
    conn.close()


def get_raid_events(limit: int = 15):
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT event_type, reason, time
        FROM raid_events
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows