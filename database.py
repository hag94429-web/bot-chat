import sqlite3
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

    conn.commit()
    conn.close()


def register_user(user_id, username):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR IGNORE INTO users (user_id, username, balance)
    VALUES (?, ?, 0)
    """, (user_id, username))

    cur.execute("""
    UPDATE users SET username = ?
    WHERE user_id = ?
    """, (username, user_id))

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
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    UPDATE users SET balance = balance + ?
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
    UPDATE users SET last_daily = ?
    WHERE user_id = ?
    """, (str(date.today()), user_id))

    conn.commit()
    conn.close()


def get_top():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    SELECT username, user_id, balance
    FROM users
    ORDER BY balance DESC
    LIMIT 10
    """)

    rows = cur.fetchall()
    conn.close()
    return rows