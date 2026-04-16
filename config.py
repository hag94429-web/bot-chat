import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
CHAT_ID = int(os.getenv("CHAT_ID", "0"))

FRIENDS_LINK = os.getenv("FRIENDS_LINK", "").strip()
TOP_LINK = os.getenv("TOP_LINK", "").strip()
ADS_LINK = os.getenv("ADS_LINK", "").strip()

# ---- limits ----
WARNING_JOIN_THRESHOLD = 3
RAID_JOIN_THRESHOLD = 5
JOIN_WINDOW = 10

FRIENDS_LIMIT = 8
TOP_LIMIT = 3
ADS_LIMIT = 4
EXTERNAL_LIMIT = 3

SPAM_LIMIT = 12
SPAM_WINDOW = 5

RAID_MESSAGE_LIMIT = 10
RAID_MESSAGE_WINDOW = 5

DUPLICATE_TEXT_LIMIT = 3
DUPLICATE_TEXT_WINDOW = 12

CAPTCHA_TIMEOUT = 60
RAID_COOLDOWN = 120

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set")
if not CHAT_ID:
    raise ValueError("CHAT_ID not set")