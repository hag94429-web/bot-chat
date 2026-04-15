import sqlite3

DB_NAME = "antiraid.db"


def connect():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS whitelist (
            user_id INTEGER PRIMARY KEY
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            invite TEXT,
            time INTEGER
        )
    """)

    conn.commit()
    conn.close()


def add_wl(uid: int):
    conn = connect()
    conn.execute(
        "INSERT OR IGNORE INTO whitelist (user_id) VALUES (?)",
        (uid,)
    )
    conn.commit()
    conn.close()


def del_wl(uid: int):
    conn = connect()
    conn.execute(
        "DELETE FROM whitelist WHERE user_id = ?",
        (uid,)
    )
    conn.commit()
    conn.close()


def is_wl(uid: int) -> bool:
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM whitelist WHERE user_id = ? LIMIT 1",
        (uid,)
    )
    res = cur.fetchone()
    conn.close()
    return res is not None


def get_wl():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM whitelist ORDER BY user_id ASC")
    rows = cur.fetchall()
    conn.close()
    return [row[0] for row in rows]


def log_join(uid: int, invite: str):
    conn = connect()
    conn.execute(
        """
        INSERT INTO logs (user_id, invite, time)
        VALUES (?, ?, strftime('%s','now'))
        """,
        (uid, invite)
    )
    conn.commit()
    conn.close()


def get_logs(limit: int = 10):
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT user_id, invite
        FROM logs
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,)
    )
    rows = cur.fetchall()
    conn.close()
    return rows