import sqlite3
import time

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
        full_name TEXT,
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
        "last_case_time INTEGER",
        "last_bonus_time INTEGER",
        "last_roulette_time INTEGER"
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

    cur.execute("""
    CREATE TABLE IF NOT EXISTS duel_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    challenger_id INTEGER,
    opponent_id INTEGER,

    winner_id INTEGER,
    winner_name TEXT,

    bet INTEGER,
    fee INTEGER,

    chat_id INTEGER,

    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

    conn.commit()
    conn.close()

def register_user(user_id, username=None, full_name=None):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR IGNORE INTO users (user_id, username, full_name, balance)
    VALUES (?, ?, ?, 0)
    """, (user_id, username, full_name))

    if username:
        cur.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))

    if full_name:
        cur.execute("UPDATE users SET full_name = ? WHERE user_id = ?", (full_name, user_id))

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
    register_user(user_id)

    conn = connect()
    cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def spend_balance(user_id, amount):
    if get_balance(user_id) < amount:
        return False

    add_balance(user_id, -amount)
    return True

# --- DAILY ---

def can_daily(user_id):
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT last_daily FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()

    if not row or not row[0]:
        return True

    try:
        last = int(row[0])
    except Exception:
        return True

    return time.time() - last >= 18000

def set_daily(user_id):
    conn = connect()
    cur = conn.cursor()
    cur.execute("UPDATE users SET last_daily = ? WHERE user_id = ?", (int(time.time()), user_id))
    conn.commit()
    conn.close()

def get_daily_remaining(user_id):
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT last_daily FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()

    if not row or not row[0]:
        return 0

    try:
        last = int(row[0])
    except Exception:
        return 0

    remaining = 18000 - (time.time() - last)
    return int(remaining) if remaining > 0 else 0

# --- TOP ---

def get_top(limit=10):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    SELECT username, full_name, user_id, balance
    FROM users
    ORDER BY balance DESC
    LIMIT ?
    """, (limit,))

    rows = cur.fetchall()
    conn.close()
    return rows

# --- EMOJI ---

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

    emoji, until = row

    if not emoji or not until:
        return ""

    if int(time.time()) > int(until):
        return ""

    return emoji

# --- VIP ---

def set_basic_role(user_id, days=1):
    expire = int(time.time()) + days * 86400

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

    role, until = row

    if not role or not until:
        return ""

    if int(time.time()) > int(until):
        return ""

    return role


# --- ACTIVITY ---

def update_last_msg(user_id, timestamp, text):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    UPDATE users
    SET last_msg_time = ?, last_msg_text = ?
    WHERE user_id = ?
    """, (timestamp, text, user_id))

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
    return row if row else (None, None)

# --- TIME FIELDS ---

def get_time(user_id, field):
    conn = connect()
    cur = conn.cursor()
    cur.execute(f"SELECT {field} FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row and row[0] else 0

def set_time(user_id, field):
    conn = connect()
    cur = conn.cursor()
    cur.execute(f"UPDATE users SET {field} = ? WHERE user_id = ?", (int(time.time()), user_id))
    conn.commit()
    conn.close()

def get_last_bonus_time(user_id):
    return get_time(user_id, "last_bonus_time")

def set_last_bonus_time(user_id):
    set_time(user_id, "last_bonus_time")

def get_last_roulette_time(user_id):
    return get_time(user_id, "last_roulette_time")


def set_last_roulette_time(user_id):
    set_time(user_id, "last_roulette_time")


def get_last_pay_time(user_id):
    return get_time(user_id, "last_pay_time")


def set_last_pay_time(user_id):
    set_time(user_id, "last_pay_time")


def get_last_case_time(user_id):
    return get_time(user_id, "last_case_time")


def set_last_case_time(user_id):
    set_time(user_id, "last_case_time")

# --- LOGS ---

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
    SELECT username, user_id, SUM(amount)
    FROM logs
    WHERE action = 'donate_stars'
    GROUP BY user_id
    ORDER BY SUM(amount) DESC
    LIMIT ?
    """, (limit,))

    rows = cur.fetchall()
    conn.close()
    return rows

# --- DUELS ---

def add_duel_log(challenger_id, opponent_id, winner_id, bet, fee):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO duel_logs (challenger_id, opponent_id, winner_id, bet, fee)
    VALUES (?, ?, ?, ?, ?)
    """, (challenger_id, opponent_id, winner_id, bet, fee))

    conn.commit()
    conn.close()

def get_duel_logs(limit=10):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    SELECT challenger_id, opponent_id, winner_id, bet, fee, created_at
    FROM duel_logs
    ORDER BY id DESC
    LIMIT ?
    """, (limit,))

    rows = cur.fetchall()
    conn.close()
    return rows