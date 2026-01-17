import telebot
from telebot import types
import random
import time
import os

# ===================== RENDER CONFIG =====================
BOT_TOKEN = os.environ.get("BOT_TOKEN")          # REQUIRED
CHANNEL_USERNAME = os.environ.get("CHANNEL")    # e.g. @mychannel
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0")) # your telegram id
# ========================================================

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ------------------ IN-MEMORY DATABASE ------------------
users = {}
# users[user_id] = {
#   "upi": None,
#   "referrals": 0,
#   "referred": False
# }

# ------------------ HELPERS ------------------
def is_joined(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        return status in ("member", "administrator", "creator")
    except:
        return False


def random_mobile():
    return str(random.choice([6, 7, 8, 9])) + str(random.randint(100000000, 999999999))


def make_request_testing(step_name, payload):
    """
    🔁 MIRROR OF REAL API FUNCTION
    (API REMOVED – TESTING MODE)
    """
    time.sleep(1)
    print("===================================")
    print(f"[TESTING MODE] {step_name}")
    print("Payload:", payload)
    print("===================================")

    return {
        "success": True,
        "msg": f"{step_name} successful (TESTING)"
    }

# ------------------ /start ------------------
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    args = message.text.split()

    if user_id not in users:
        users[user_id] = {
            "upi": None,
            "referrals": 0,
            "referred": False
        }

        # ---------- REFERRAL MIRROR ----------
        if len(args) > 1:
            try:
                ref_id = int(args[1])
                if ref_id != user_id and ref_id in users and not users[user_id]["referred"]:
                    users[ref_id]["referrals"] += 1
                    users[user_id]["referred"] = True
                    bot.send_message(ref_id, "🎉 You received 1 referral!")
            except:
                pass

    if not is_joined(user_id):
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(
            "Join Channel",
            url=f"https://t.me/{CHANNEL_USERNAME[1:]}"
        ))
        bot.send_message(
            user_id,
            "❌ <b>Please join the channel to use this bot.</b>",
            reply_markup=kb
        )
        return

    bot.send_message(
        user_id,
        f"🤖 <b>Cashback Bot (Testing)</b>\n\n"
        f"👥 Referrals: <b>{users[user_id]['referrals']}</b>\n\n"
        f"🔗 <b>Your Referral Link</b>\n"
        f"https://t.me/{bot.get_me().username}?start={user_id}\n\n"
        f"/upi – Set UPI ID\n"
        f"/withdraw – Withdraw ₹1"
    )

# ------------------ /upi ------------------
@bot.message_handler(commands=["upi"])
def ask_upi(message):
    msg = bot.send_message(message.chat.id, "💳 <b>Send your UPI ID:</b>")
    bot.register_next_step_handler(msg, save_upi)

def save_upi(message):
    user_id = message.from_user.id
    upi = message.text.strip()

    if "@" not in upi or len(upi) < 6:
        bot.send_message(user_id, "❌ <b>Invalid UPI ID.</b>")
        return

    users[user_id]["upi"] = upi
    bot.send_message(user_id, "✅ <b>UPI saved successfully (Testing).</b>")

# ------------------ /withdraw ------------------
@bot.message_handler(commands=["withdraw"])
def withdraw(message):
    user_id = message.from_user.id

    if not is_joined(user_id):
        bot.send_message(user_id, "❌ <b>Please join the channel first.</b>")
        return

    if users[user_id]["referrals"] < 1:
        bot.send_message(user_id, "❌ <b>You need at least 1 referral.</b>")
        return

    if not users[user_id]["upi"]:
        bot.send_message(user_id, "❌ <b>Please set UPI using /upi.</b>")
        return

    # ========== MIRRORED REAL SCRIPT FLOW ==========
    mobile = random_mobile()
    name = "TestUser"
    email = f"user{random.randint(1000,9999)}@gmail.com"

    make_request_testing("Create User", {
        "msisdn": mobile,
        "firstName": name,
        "email": email
    })

    make_request_testing("Submit Answers", {
        "trivia1": "Once a week",
        "trivia2": "Coconut"
    })

    make_request_testing("Save UPI", {
        "vpa": users[user_id]["upi"]
    })

    make_request_testing("Request Cashback", {
        "redemptionType": "CASHBACK"
    })
    # ==============================================

    bot.send_message(
        user_id,
        "🎉 <b>Withdrawal Successful!</b>\n\n"
        "₹1 credited (TESTING MODE)\n"
        "⚠️ No real payment was made."
    )

    if ADMIN_ID:
        bot.send_message(
            ADMIN_ID,
            f"💸 Withdraw Request (Testing)\nUser: {user_id}\nUPI: {users[user_id]['upi']}"
        )

# ------------------ START BOT ------------------
print("Bot started (Render mode)")
bot.infinity_polling(skip_pending=True)
