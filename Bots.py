import telebot
from telebot import types
import random
import time

# ===================== CONFIG =====================
BOT_TOKEN = "YOUR_BOT_TOKEN"
CHANNEL_USERNAME = "@YourChannelUsername"
ADMIN_ID = 123456789
# =================================================

bot = telebot.TeleBot(BOT_TOKEN)

# ------------------ DATABASE (Testing) ------------------
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
        return status in ["member", "administrator", "creator"]
    except:
        return False


def random_mobile():
    return str(random.choice([6,7,8,9])) + str(random.randint(100000000,999999999))


def make_request_testing(step_name, payload):
    """
    🔴 MIRROR OF make_request() FROM REAL SCRIPT
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

        # 🔁 MIRROR OF REFERRAL LOGIC
        if len(args) > 1:
            try:
                ref_id = int(args[1])
                if ref_id != user_id and ref_id in users and not users[user_id]["referred"]:
                    users[ref_id]["referrals"] += 1
                    users[user_id]["referred"] = True
                    bot.send_message(ref_id, "🎉 You got 1 referral!")
            except:
                pass

    if not is_joined(user_id):
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(
            "Join Channel",
            url=f"https://t.me/{CHANNEL_USERNAME[1:]}"
        ))
        bot.send_message(user_id, "❌ Please join the channel first.", reply_markup=kb)
        return

    bot.send_message(
        user_id,
        "🤖 Cashback Bot (Testing)\n\n"
        "Steps:\n"
        "1️⃣ Refer 1 user\n"
        "2️⃣ Set UPI\n"
        "3️⃣ Withdraw\n\n"
        f"👥 Referrals: {users[user_id]['referrals']}\n\n"
        f"🔗 Referral Link:\n"
        f"https://t.me/{bot.get_me().username}?start={user_id}\n\n"
        "/upi – Set UPI\n"
        "/withdraw – Withdraw ₹1"
    )

# ------------------ /upi ------------------
@bot.message_handler(commands=["upi"])
def ask_upi(message):
    msg = bot.send_message(message.chat.id, "💳 Enter your UPI ID:")
    bot.register_next_step_handler(msg, save_upi)

def save_upi(message):
    user_id = message.from_user.id
    upi = message.text.strip()

    if "@" not in upi:
        bot.send_message(user_id, "❌ Invalid UPI.")
        return

    users[user_id]["upi"] = upi
    bot.send_message(user_id, "✅ UPI saved (Testing)")

# ------------------ /withdraw ------------------
@bot.message_handler(commands=["withdraw"])
def withdraw(message):
    user_id = message.from_user.id

    if not is_joined(user_id):
        bot.send_message(user_id, "❌ Join channel first.")
        return

    if users[user_id]["referrals"] < 1:
        bot.send_message(user_id, "❌ You need at least 1 referral.")
        return

    if not users[user_id]["upi"]:
        bot.send_message(user_id, "❌ Set UPI using /upi.")
        return

    # ================= MIRRORED REAL SCRIPT FLOW =================

    mobile = random_mobile()
    name = "TestUser"
    email = f"user{random.randint(1000,9999)}@gmail.com"

    # STEP 1 – Create User
    step1 = make_request_testing(
        "Create User",
        {
            "msisdn": mobile,
            "firstName": name,
            "email": email
        }
    )

    # STEP 2 – Submit Answers
    step2 = make_request_testing(
        "Submit Answers",
        {
            "trivia1": "Once a week",
            "trivia2": "Coconut"
        }
    )

    # STEP 3 – Save UPI
    step3 = make_request_testing(
        "Save UPI",
        {
            "vpa": users[user_id]["upi"]
        }
    )

    # STEP 4 – Cashback Redemption
    step4 = make_request_testing(
        "Request Cashback",
        {
            "redemptionType": "CASHBACK"
        }
    )

    # ============================================================

    bot.send_message(
        user_id,
        "🎉 Withdrawal Successful!\n\n"
        "₹1 credited (TESTING MODE)\n"
        "⚠ No real API was called."
    )

    bot.send_message(
        ADMIN_ID,
        f"💸 Withdraw Request (Testing)\nUser: {user_id}\nUPI: {users[user_id]['upi']}"
    )

# ------------------ RUN ------------------
bot.infinity_polling()
