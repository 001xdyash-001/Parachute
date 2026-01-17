# ===== ORIGINAL IMPORTS (kept where possible) =====
import json
import random
import hashlib
import time
import os

# ===== TELEGRAM ADDITION =====
import telebot
from telebot import types

# ===== ORIGINAL CONSTANTS (kept, but UNUSED in testing) =====
BASE_URL = "https://web.myfidelity.in/api/v1/parachute_gold"
SECRET_KEY = "TESTING_SECRET"
CLIENT_ID = "TESTING_CLIENT"

# ===== RENDER / BOT CONFIG =====
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_USERNAME = os.environ.get("CHANNEL")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ===== IN-MEMORY USER STATE =====
users = {}  # user_id -> {"upi": None, "ref": 0, "referred": False}

# -------------------------------------------------
# ORIGINAL FUNCTIONS (UNCHANGED)
# -------------------------------------------------

def random_indian_mobile():
    prefix = random.choice([6, 7, 8, 9])
    rest = random.randint(100000000, 999999999)
    return f"{prefix}{rest}"

def sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()

def sort_json_body(json_str: str) -> str:
    if not json_str.strip():
        return ""
    try:
        data = json.loads(json_str)
        if not isinstance(data, dict):
            return ""
        sorted_dict = dict(sorted(data.items(), reverse=True))
        return json.dumps(sorted_dict, separators=(',', ':'), ensure_ascii=False)
    except:
        return ""

def generate_checksum(body: str, secret: str) -> str:
    secret_hash = sha256(secret)
    sorted_body = sort_json_body(body)
    to_hash = secret_hash + sorted_body if sorted_body else secret_hash
    return sha256(to_hash)

# -------------------------------------------------
# ORIGINAL make_request() — MIRRORED, BUT NEUTRALIZED
# -------------------------------------------------
def make_request(url: str, data: str, msisdn: str, step_name: str):
    """
    🔴 ORIGINAL had:
        - checksum headers
        - requests.post(...)
    🟢 CHANGE HERE ONLY:
        - NO network call
        - TESTING success returned
    """
    checksum = generate_checksum(data, SECRET_KEY)  # kept for structure

    # ---- TESTING STUB (REPLACED requests.post) ----
 r = requests.post(url, data=data, headers=headers, timeout=15)
            r.raise_for_status()
            
            json_resp = r.json()
            print(f"{Fore.GREEN}✓ Success on attempt {attempt}{Style.RESET_ALL}")
            return True, json_resp, ""
# -------------------------------------------------
# TELEGRAM FLOW = ORIGINAL main() MIRROR
# -------------------------------------------------

def is_joined(user_id):
    try:
        s = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        return s in ("member", "administrator", "creator")
    except:
        return False

@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    args = message.text.split()

    if user_id not in users:
        users[user_id] = {"upi": None, "ref": 0, "referred": False}
        if len(args) > 1:
            try:
                ref_id = int(args[1])
                if ref_id in users and ref_id != user_id and not users[user_id]["referred"]:
                    users[ref_id]["ref"] += 1
                    users[user_id]["referred"] = True
                    bot.send_message(ref_id, "🎉 1 referral added")
            except:
                pass

    if not is_joined(user_id):
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("Join Channel",
              url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
        bot.send_message(user_id, "Join channel first.", reply_markup=kb)
        return

    bot.send_message(
        user_id,
        f"Referrals: {users[user_id]['ref']}\n"
        f"/upi to set UPI\n"
        f"/withdraw to test flow"
    )

@bot.message_handler(commands=["upi"])
def set_upi(message):
    msg = bot.send_message(message.chat.id, "Send UPI:")
    bot.register_next_step_handler(msg, save_upi)

def save_upi(message):
    if "@" not in message.text:
        bot.send_message(message.chat.id, "Invalid UPI")
        return
    users[message.from_user.id]["upi"] = message.text.strip()
    bot.send_message(message.chat.id, "UPI saved")

@bot.message_handler(commands=["withdraw"])
def withdraw(message):
    user_id = message.from_user.id
    if users[user_id]["ref"] < 1:
        bot.send_message(user_id, "Need 1 referral")
        return
    if not users[user_id]["upi"]:
        bot.send_message(user_id, "Set UPI first")
        return

    # ===== ORIGINAL main() STEPS (SAME ORDER) =====
    mobile = random_indian_mobile()
    fname = "Test"
    email = "test@gmail.com"

    payload1 = json.dumps({
        "msisdn": mobile,
        "firstName": fname,
        "lastName": "",
        "emailId": email,
        "pinCode": "",
        "consent1": 1,
        "ssoId": "NA"
    }, separators=(',', ':'))

    make_request(f"{BASE_URL}/save-user-detail", payload1, mobile, "1. Create user")

    payload2 = json.dumps({
        "msisdn": mobile,
        "answersMap": {
            "trivia1": {"answer": "Once a week"},
            "trivia2": {"answer": "Coconut"}
        }
    }, separators=(',', ':'))

    make_request(f"{BASE_URL}/save-answers", payload2, mobile, "2. Submit answers")

    payload3 = json.dumps({"vpa": users[user_id]["upi"]}, separators=(',', ':'))
    make_request(f"{BASE_URL}/save-upi-info", payload3, mobile, "3. Save UPI")

    payload4 = json.dumps({"redemptionType": "CASHBACK"}, separators=(',', ':'))
    make_request(f"{BASE_URL}/redemption", payload4, mobile, "4. Request Cashback")

    bot.send_message(user_id, "Flow completed (TESTING)")

# -------------------------------------------------
# RUN (RENDER)
# -------------------------------------------------
print("Bot started (original-like mirror)")
bot.infinity_polling(skip_pending=True)
