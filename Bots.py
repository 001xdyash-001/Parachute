import telebot
from telebot import types
import sqlite3
import os
import time

# ================= CONFIG =================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))
CHANNEL_1 = os.environ.get("CHANNEL_1")  # @channel1
CHANNEL_2 = os.environ.get("CHANNEL_2")  # @channel2
REWARD_CHANNEL_LINK = os.environ.get("REWARD_CHANNEL_LINK")
# =========================================

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ================= DATABASE =================
db = sqlite3.connect("users.db", check_same_thread=False)
sql = db.cursor()

sql.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    ref_count INTEGER DEFAULT 0,
    referred_by INTEGER,
    reward_unlocked INTEGER DEFAULT 0
)
""")
db.commit()

# ================= HELPERS =================
def is_joined(user_id):
    try:
        s1 = bot.get_chat_member(CHANNEL_1, user_id).status
        s2 = bot.get_chat_member(CHANNEL_2, user_id).status
        return s1 in ["member","administrator","creator"] and \
               s2 in ["member","administrator","creator"]
    except:
        return False

def get_user(user_id):
    sql.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    return sql.fetchone()

def add_user(user_id, username, ref_by=None):
    sql.execute(
        "INSERT OR IGNORE INTO users (user_id, username, referred_by) VALUES (?, ?, ?)",
        (user_id, username, ref_by)
    )
    db.commit()

def add_ref(ref_id):
    sql.execute("UPDATE users SET ref_count = ref_count + 1 WHERE user_id=?", (ref_id,))
    db.commit()

# ================= MENU =================
def main_menu(user_id):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("👥 My Referrals", callback_data="refs"),
        types.InlineKeyboardButton("🎁 Reward Status", callback_data="reward")
    )
    bot.send_message(
        user_id,
        "✨ <b>Refer & Earn Program</b>\n\n"
        "🔹 Join both channels\n"
        "🔹 Refer 5 users\n"
        "🔹 Unlock premium channel\n\n"
        f"🔗 <b>Your Referral Link</b>\n"
        f"https://t.me/{bot.get_me().username}?start={user_id}",
        reply_markup=kb
    )

# ================= START =================
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"
    args = message.text.split()

    if not get_user(user_id):
        ref_by = None
        if len(args) > 1 and args[1].isdigit():
            ref_by = int(args[1])
            if ref_by == user_id:
                ref_by = None

        add_user(user_id, username, ref_by)

        if ref_by and get_user(ref_by):
            if is_joined(user_id):
                add_ref(ref_by)
                bot.send_message(ref_by, "🎉 You got a new referral!")

    if not is_joined(user_id):
        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton("Join Channel 1", url=f"https://t.me/{CHANNEL_1[1:]}"),
            types.InlineKeyboardButton("Join Channel 2", url=f"https://t.me/{CHANNEL_2[1:]}")
        )
        bot.send_message(
            user_id,
            "❌ <b>You must join both channels to continue</b>",
            reply_markup=kb
        )
        return

    main_menu(user_id)

# ================= CALLBACKS =================
@bot.callback_query_handler(func=lambda c: True)
def callbacks(call):
    user_id = call.from_user.id
    user = get_user(user_id)

    if call.data == "refs":
        bot.send_message(
            user_id,
            f"👥 <b>Your Referrals:</b> {user[2]}/5"
        )

    elif call.data == "reward":
        if user[2] >= 5:
            if not user[4]:
                sql.execute("UPDATE users SET reward_unlocked=1 WHERE user_id=?", (user_id,))
                db.commit()
            bot.send_message(
                user_id,
                f"🎉 <b>Congratulations!</b>\n\n"
                f"🔓 <a href='{REWARD_CHANNEL_LINK}'>Join Premium Channel</a>"
            )
        else:
            bot.send_message(
                user_id,
                f"❌ You need {5 - user[2]} more referrals."
            )

    elif call.data == "admin_stats" and user_id == ADMIN_ID:
        sql.execute("SELECT COUNT(*) FROM users")
        total_users = sql.fetchone()[0]

        sql.execute("SELECT SUM(ref_count) FROM users")
        total_refs = sql.fetchone()[0] or 0

        sql.execute("SELECT username FROM users WHERE ref_count >= 5")
        winners = [u[0] for u in sql.fetchall()]

        msg = (
            f"📊 <b>Admin Stats</b>\n\n"
            f"👥 Users: {total_users}\n"
            f"🔗 Referrals: {total_refs}\n"
            f"🎁 Completed 5 Ref:\n" +
            ("\n".join(winners) if winners else "None")
        )
        bot.send_message(ADMIN_ID, msg)

# ================= ADMIN =================
@bot.message_handler(commands=["admin"])
def admin(message):
    if message.from_user.id != ADMIN_ID:
        return

    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
        types.InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")
    )
    bot.send_message(ADMIN_ID, "🛠 <b>Admin Panel</b>", reply_markup=kb)

broadcast_mode = False

@bot.message_handler(func=lambda m: broadcast_mode, content_types=["text","photo"])
def broadcast(message):
    global broadcast_mode
    broadcast_mode = False

    sql.execute("SELECT user_id FROM users")
    users = sql.fetchall()

    sent = 0
    for u in users:
        try:
            if message.content_type == "text":
                bot.send_message(u[0], message.text)
            else:
                bot.send_photo(u[0], message.photo[-1].file_id, caption=message.caption or "")
            sent += 1
            time.sleep(0.05)
        except:
            pass

    bot.send_message(ADMIN_ID, f"✅ Broadcast sent to {sent} users")

# ================= RUN =================
print("Bot running...")
bot.infinity_polling(skip_pending=True)
