import telebot
from telebot import types
import random
import time
import os

# ===================== RENDER CONFIG =====================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_USERNAME = os.environ.get("CHANNEL")      # e.g. @mychannel
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))  # your telegram id
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
    🔁 MIRROR OF REAL API FUNCTION (TESTING MODE)
    """
    time.sleep(0.8)
    print(f"[TESTING] {step_name} -> {payload}")
    return {"success": True}

# ------------------ ADMIN STATS ------------------
def admin_stats_text():
    total_users = len(users)
    upi_users = sum(1 for u in users.values() if u["upi"])
    total_refs = sum(u["referrals"] for u in users.values())
    withdraw_eligible = sum(
        1 for u in users.values() if u["upi"] and u["referrals"] >= 1
    )

    return (
        "📊 <b>ADMIN PANEL</b>\n\n"
        f"👥 Total Users: <b>{total_users}</b>\n"
        f"💳 UPI Set: <b>{upi_users}</b>\n"
        f"👥 Total Referrals: <b>{total_refs}</b>\n"
        f"💸 Withdraw Eligible: <b>{withdraw_eligible}</b>\n"
    )

# ====================== USER COMMANDS ======================

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
        f"/upi – Set UPI\n"
        f"/withdraw – Withdraw ₹1"
    )

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
    bot.send_message(user_id, "✅ <b>UPI saved (Testing).</b>")

@bot.message_handler(commands=["withdraw"])
def withdraw(message):
    user_id = message.from_user.id

    if users[user_id]["referrals"] < 1:
        bot.send_message(user_id, "❌ <b>You need at least 1 referral.</b>")
        return

    if not users[user_id]["upi"]:
        bot.send_message(user_id, "❌ <b>Please set UPI first.</b>")
        return

    # ===== MIRRORED REAL SCRIPT FLOW =====
    make_request_testing("Create User", {})
    make_request_testing("Submit Answers", {})
    make_request_testing("Save UPI", {})
    make_request_testing("Request Cashback", {})
    # ====================================

    bot.send_message(
        user_id,
        "🎉 <b>Withdrawal Successful!</b>\n\n"
        "₹1 credited (TESTING MODE)\n"
        "⚠️ No real payment made."
    )

# ====================== ADMIN PANEL ======================

@bot.message_handler(commands=["admin"])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return

    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("🔄 Refresh Stats", callback_data="admin_refresh"),
        types.InlineKeyboardButton("📋 User List", callback_data="admin_users"),
        types.InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")
    )

    bot.send_message(
        ADMIN_ID,
        admin_stats_text(),
        reply_markup=kb
    )

# ====================== BROADCAST ======================

broadcast_state = {}

@bot.callback_query_handler(func=lambda c: True)
def callbacks(call):
    if call.from_user.id != ADMIN_ID:
        return

    if call.data == "admin_refresh":
        bot.edit_message_text(
            admin_stats_text(),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=call.message.reply_markup
        )

    elif call.data == "admin_users":
        text = "📋 <b>Users (Top 30)</b>\n\n"
        for uid, d in list(users.items())[:30]:
            text += f"{uid} | Ref:{d['referrals']} | UPI:{'Yes' if d['upi'] else 'No'}\n"
        bot.send_message(ADMIN_ID, text)

    elif call.data == "admin_broadcast":
        broadcast_state[ADMIN_ID] = True
        bot.send_message(
            ADMIN_ID,
            "📢 <b>Send broadcast message now.</b>\n\n"
            "You can send:\n"
            "• Text\n"
            "• Image\n"
            "• Image with caption"
        )

# ---------- Handle broadcast content ----------
@bot.message_handler(
    func=lambda m: broadcast_state.get(m.from_user.id),
    content_types=["text", "photo"]
)
def handle_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return

    broadcast_state.pop(ADMIN_ID, None)

    sent = 0
    failed = 0

    for uid in users.keys():
        try:
            if message.content_type == "text":
                bot.send_message(uid, message.text)
            elif message.content_type == "photo":
                bot.send_photo(
                    uid,
                    message.photo[-1].file_id,
                    caption=message.caption or ""
                )
            sent += 1
            time.sleep(0.05)
        except:
            failed += 1

    bot.send_message(
        ADMIN_ID,
        f"✅ <b>Broadcast Completed</b>\n\n"
        f"📤 Sent: <b>{sent}</b>\n"
        f"❌ Failed: <b>{failed}</b>"
    )

# ====================== RUN ======================
print("Bot started with Admin Panel + Broadcast (Render)")
bot.infinity_polling(skip_pending=True)
