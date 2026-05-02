import sqlite3
import time
from datetime import date

DB_NAME = "nyx.db"


def connect():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        balance INTEGER DEFAULT 0,
        last_daily TEXT
    )
    """)

    for column in [
        "emoji_status TEXT",
        "emoji_until INTEGER",
        "role TEXT",
        "role_until INTEGER",
        "last_msg_time INTEGER",
        "last_msg_text TEXT",
        "last_pay_time INTEGER",
        "last_case_time INTEGER"
    ]:
        try:
            cur.execute(f"ALTER TABLE users ADD COLUMN {column}")
        except sqlite3.OperationalError:
            pass

    cur.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        action TEXT,
        amount INTEGER,
        item TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def register_user(user_id, username):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR IGNORE INTO users (user_id, username, balance)
    VALUES (?, ?, 0)
    """, (user_id, username))

    cur.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))

    conn.commit()
    conn.close()


def get_balance(user_id):
    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()

    conn.close()
    return row[0] if row else 0


def add_balance(user_id, amount):
    register_user(user_id, None)

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    UPDATE users
    SET balance = balance + ?
    WHERE user_id = ?
    """, (amount, user_id))

    conn.commit()
    conn.close()


def spend_balance(user_id, amount):
    if get_balance(user_id) < amount:
        return False

    add_balance(user_id, -amount)
    return True


def can_daily(user_id):
    today = str(date.today())

    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT last_daily FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()

    conn.close()
    return not row or row[0] != today


def set_daily(user_id):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    UPDATE users
    SET last_daily = ?
    WHERE user_id = ?
    """, (str(date.today()), user_id))

    conn.commit()
    conn.close()


def get_top(limit=10):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    SELECT username, user_id, balance
    FROM users
    ORDER BY balance DESC
    LIMIT ?
    """, (limit,))

    rows = cur.fetchall()
    conn.close()
    return rows


def set_emoji_status(user_id, emoji):
    expire = int(time.time()) + 86400

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    UPDATE users
    SET emoji_status = ?, emoji_until = ?
    WHERE user_id = ?
    """, (emoji, expire, user_id))

    conn.commit()
    conn.close()


def get_active_emoji(user_id):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    SELECT emoji_status, emoji_until
    FROM users
    WHERE user_id = ?
    """, (user_id,))

    row = cur.fetchone()
    conn.close()

    if not row:
        return ""

    emoji, emoji_until = row

    if not emoji or not emoji_until:
        return ""

    if int(time.time()) > int(emoji_until):
        return ""

    return emoji


def set_basic_role(user_id):
    expire = int(time.time()) + 86400

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    UPDATE users
    SET role = ?, role_until = ?
    WHERE user_id = ?
    """, ("basic", expire, user_id))

    conn.commit()
    conn.close()


def get_active_role(user_id):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    SELECT role, role_until
    FROM users
    WHERE user_id = ?
    """, (user_id,))

    row = cur.fetchone()
    conn.close()

    if not row:
        return ""

    role, role_until = row

    if not role or not role_until:
        return ""

    if int(time.time()) > int(role_until):
        return ""

    return role


def update_last_msg(user_id, text):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    UPDATE users
    SET last_msg_time = ?, last_msg_text = ?
    WHERE user_id = ?
    """, (int(time.time()), text, user_id))

    conn.commit()
    conn.close()


def get_last_msg(user_id):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    SELECT last_msg_time, last_msg_text
    FROM users
    WHERE user_id = ?
    """, (user_id,))

    row = cur.fetchone()
    conn.close()

    return row if row else (0, "")


def get_last_pay_time(user_id):
    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT last_pay_time FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()

    conn.close()
    return row[0] if row and row[0] else 0


def set_last_pay_time(user_id):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    UPDATE users
    SET last_pay_time = ?
    WHERE user_id = ?
    """, (int(time.time()), user_id))

    conn.commit()
    conn.close()


def get_last_case_time(user_id):
    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT last_case_time FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()

    conn.close()
    return row[0] if row and row[0] else 0


def set_last_case_time(user_id):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    UPDATE users
    SET last_case_time = ?
    WHERE user_id = ?
    """, (int(time.time()), user_id))

    conn.commit()
    conn.close()


def add_log(user_id, username, action, amount, item):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO logs (user_id, username, action, amount, item)
    VALUES (?, ?, ?, ?, ?)
    """, (user_id, username, action, amount, item))

    conn.commit()
    conn.close()


def get_logs(limit=15):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    SELECT username, user_id, action, amount, item, created_at
    FROM logs
    ORDER BY id DESC
    LIMIT ?
    """, (limit,))

    rows = cur.fetchall()
    conn.close()
    return rows


def get_top_donates(limit=10):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    SELECT username, user_id, SUM(amount) as total
    FROM logs
    WHERE action = 'donate_stars'
    GROUP BY user_id
    ORDER BY total DESC
    LIMIT ?
    """, (limit,))

    rows = cur.fetchall()
    conn.close()
    return rows