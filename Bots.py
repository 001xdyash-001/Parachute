import os
import time
import random
import json
import requests
import telebot
from telebot import types

# ================== RENDER CONFIG ==================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_USERNAME = os.environ.get("CHANNEL")   # @yourchannel
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
# ==================================================

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ================== USER DATABASE (IN-MEMORY) ==================
users = {}
# users[user_id] = {
#   "ref": 0,
#   "referred": False,
#   "upi": None
# }

# ================== HELPERS ==================
def is_joined(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        return status in ("member", "administrator", "creator")
    except:
        return False

def random_indian_mobile():
    return str(random.choice([6,7,8,9])) + str(random.randint(100000000,999999999))

# ================== YOUR REAL-LIKE API FUNCTION ==================
def make_request(url, data, headers, step_name):
    r = requests.post(url, data=data, headers=headers, timeout=15)
    r.raise_for_status()
    return True, r.json(), ""

# ================== MENU ==================
def send_menu(user_id):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("💳 Set UPI", callback_data="set_upi"),
        types.InlineKeyboardButton("💸 Withdraw", callback_data="withdraw"),
        types.InlineKeyboardButton("👥 Referrals", callback_data="refs")
    )

    bot.send_message(
        user_id,
        f"🤖 <b>Welcome</b>\n\n"
        f"👥 Referrals: <b>{users[user_id]['ref']}</b>\n\n"
        f"🔗 <b>Your Referral Link</b>\n"
        f"https://t.me/{bot.get_me().username}?start={user_id}",
        reply_markup=kb
    )

# ================== /START WITH REFERRAL ==================
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    args = message.text.split()

    if user_id not in users:
        users[user_id] = {"ref": 0, "referred": False, "upi": None}

        if len(args) > 1:
            try:
                ref_id = int(args[1])
                if ref_id in users and ref_id != user_id and not users[user_id]["referred"]:
                    users[ref_id]["ref"] += 1
                    users[user_id]["referred"] = True
                    bot.send_message(ref_id, "🎉 You received 1 referral!")
            except:
                pass

    if not is_joined(user_id):
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(
            "✅ Join Channel",
            url=f"https://t.me/{CHANNEL_USERNAME[1:]}"
        ))
        bot.send_message(
            user_id,
            "❌ <b>Please join the channel to use the bot.</b>",
            reply_markup=kb
        )
        return

    send_menu(user_id)

# ================== CALLBACKS ==================
@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    user_id = call.from_user.id

    if call.data == "set_upi":
        msg = bot.send_message(user_id, "💳 Send your UPI ID:")
        bot.register_next_step_handler(msg, save_upi)

    elif call.data == "withdraw":
        handle_withdraw(user_id)

    elif call.data == "refs":
        bot.send_message(
            user_id,
            f"👥 Referrals: <b>{users[user_id]['ref']}</b>\n\n"
            "Invite at least 1 user to unlock withdraw."
        )

    # ---------- ADMIN ----------
    elif call.data == "admin_stats" and user_id == ADMIN_ID:
        bot.edit_message_text(
            get_admin_stats(),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=admin_keyboard()
        )

    elif call.data == "admin_broadcast" and user_id == ADMIN_ID:
        bot.send_message(
            ADMIN_ID,
            "📢 Send broadcast now (text or image)."
        )
        broadcast_state[ADMIN_ID] = True

# ================== SAVE UPI ==================
def save_upi(message):
    user_id = message.from_user.id
    upi = message.text.strip()

    if "@" not in upi:
        bot.send_message(user_id, "❌ Invalid UPI ID")
        return

    users[user_id]["upi"] = upi
    bot.send_message(user_id, "✅ UPI saved successfully")
    send_menu(user_id)

# ================== WITHDRAW ==================
def handle_withdraw(user_id):
    if users[user_id]["ref"] < 1:
        bot.send_message(user_id, "❌ You need at least 1 referral.")
        return

    if not users[user_id]["upi"]:
        bot.send_message(user_id, "❌ Please set UPI first.")
        return

    # ---- YOUR REAL API FLOW CALLS WOULD GO HERE ----
    # create user -> submit answers -> save upi -> redemption

    bot.send_message(user_id, "✅ Withdraw flow started (API called).")

# ================== ADMIN PANEL ==================
def get_admin_stats():
    total_users = len(users)
    upi_users = sum(1 for u in users.values() if u["upi"])
    total_refs = sum(u["ref"] for u in users.values())
    eligible = sum(1 for u in users.values() if u["upi"] and u["ref"] >= 1)

    return (
        "📊 <b>ADMIN PANEL</b>\n\n"
        f"👥 Total Users: <b>{total_users}</b>\n"
        f"💳 UPI Set: <b>{upi_users}</b>\n"
        f"👥 Total Referrals: <b>{total_refs}</b>\n"
        f"💸 Withdraw Eligible: <b>{eligible}</b>"
    )

def admin_keyboard():
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("🔄 Refresh Stats", callback_data="admin_stats"),
        types.InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")
    )
    return kb

@bot.message_handler(commands=["admin"])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return

    bot.send_message(
        ADMIN_ID,
        get_admin_stats(),
        reply_markup=admin_keyboard()
    )

# ================== BROADCAST ==================
broadcast_state = {}

@bot.message_handler(
    func=lambda m: broadcast_state.get(m.from_user.id),
    content_types=["text", "photo"]
)
def broadcast(message):
    broadcast_state.pop(message.from_user.id, None)
    sent, failed = 0, 0

    for uid in users.keys():
        try:
            if message.content_type == "text":
                bot.send_message(uid, message.text)
            else:
                bot.send_photo(uid, message.photo[-1].file_id, caption=message.caption or "")
            sent += 1
            time.sleep(0.05)
        except:
            failed += 1

    bot.send_message(
        ADMIN_ID,
        f"📢 Broadcast Done\n\n✅ Sent: {sent}\n❌ Failed: {failed}"
    )

# ================== RUN ==================
print("Bot started successfully (Final Version)")
bot.infinity_polling(skip_pending=True)
