
import telebot
from telebot import types
import random
import json
import os

TOKEN = "7907038631:AAGjAic6_CezKFmmueYXBdR5k7Xs0MH-4Hc"
bot = telebot.TeleBot(TOKEN)

ADMIN_ID = 67794794
REQUIRED_CHANNELS = ["@pharmacy_college2", "@Pharmacy_AI"]
PARTICIPANTS_FILE = "participants.json"

# تحميل المشاركين من ملف
if os.path.exists(PARTICIPANTS_FILE):
    with open(PARTICIPANTS_FILE, "r") as f:
        participants = json.load(f)
else:
    participants = {}

def save_participants():
    with open(PARTICIPANTS_FILE, "w") as f:
        json.dump(participants, f)

def is_subscribed(user_id):
    """يتحقق من اشتراك المستخدم في جميع القنوات المطلوبة."""
    try:
        for channel in REQUIRED_CHANNELS:
            status = bot.get_chat_member(channel, user_id).status
            if status not in ['member', 'creator', 'administrator']:
                return False
        return True
    except Exception:
        return False

@bot.message_handler(commands=['start'])
def start(message):
    """رسالة البدء للمستخدمين الجدد."""
    user_id = message.chat.id
    if str(user_id) in participants:
        bot.send_message(user_id, "✅ لقد دخلت السحب مسبقًا.")
        return

    markup = types.InlineKeyboardMarkup()
    for channel in REQUIRED_CHANNELS:
        markup.add(
            types.InlineKeyboardButton(
                text=f"📢 اشترك في {channel}",
                url=f"https://t.me/{channel[1:]}"
            )
        )
    markup.add(
        types.InlineKeyboardButton(
            "✅ تحقّق من الاشتراك وادخل السحب",
            callback_data="join_draw"
        )
    )

    # ✅ النص المُعدَّل كما طلبت
    intro_text = (
        "🎉 للمشاركة في السحب على كورس التدريب الصيفي ل مهند فارما:"
        "\n1️⃣ اشترك في القناتين أدناه."
        "\n2️⃣ اضغط على الزر للدخول للسحب."
    )
    bot.send_message(user_id, intro_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "join_draw")
def join_draw(call):
    """إدخال المستخدم في السحب بعد التحقق من الاشتراك."""
    user = call.from_user
    user_id = user.id

    # التحقق من الاشتراك
    if not is_subscribed(user_id):
        bot.answer_callback_query(
            call.id, "❌ يجب الاشتراك في القنوات أولاً!", show_alert=True
        )
        return

    # التحقق من عدم تسجيله مسبقًا
    if str(user_id) in participants:
        bot.answer_callback_query(
            call.id, "✅ أنت مشترك بالفعل!", show_alert=True
        )
        return

    # إضافة المشارك
    participants[str(user_id)] = {
        "name": user.first_name,
        "username": f"@{user.username}" if user.username else "لا يوجد"
    }
    save_participants()
    bot.answer_callback_query(
        call.id, "✅ تم دخولك السحب بنجاح!", show_alert=True
    )
    bot.send_message(user_id, "🎉 تم تسجيلك في السحب! بالتوفيق 🍀")

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    """لوحة تحكم الادمن."""
    if message.chat.id != ADMIN_ID:
        return

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("👥 عرض المشاركين", callback_data="show_users"))
    markup.add(types.InlineKeyboardButton("🏆 اختيار فائز عشوائي", callback_data="pick_winner"))
    # الزر الجديد لفوز نبا
    markup.add(types.InlineKeyboardButton("🥇 فوز نبا", callback_data="pick_leftuo"))
    bot.send_message(ADMIN_ID, "👑 لوحة التحكم", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["show_users", "pick_winner", "pick_leftuo"])
def admin_actions(call):
    """إجراءات الادمن: عرض المشاركين، اختيار فائز عشوائي، أو اختيار فائز ثابت (@leftuo)."""
    if call.message.chat.id != ADMIN_ID:
        return

    if call.data == "show_users":
        if not participants:
            bot.send_message(ADMIN_ID, "📭 لا يوجد مشاركين حتى الآن.")
            return

        text = "📋 قائمة المشاركين:\n\n"
        for uid, data in participants.items():
            text += f"- {data['name']} | {data['username']} | {uid}\n"
        bot.send_message(ADMIN_ID, text)

    elif call.data == "pick_winner":
        if not participants:
            bot.send_message(ADMIN_ID, "❌ لا يوجد مشاركين.")
            return
        # اختيار عشوائي
        winner_id = random.choice(list(participants.keys()))
        winner = participants[winner_id]
        winner_text = f"🏆 الفائز هو:\n{winner['name']} | {winner['username']}"

        # إرسال لجميع المشاركين
        for uid in participants:
            try:
                bot.send_message(int(uid), winner_text)
            except Exception:
                continue
        bot.send_message(
            ADMIN_ID,
            f"✅ تم اختيار الفائز وإرسال اسمه للجميع:\n\n{winner_text}"
        )

    elif call.data == "pick_leftuo":
        # البحث عن المشارك @leftuo
        fixed_uid = None
        for uid, data in participants.items():
            if data['username'] == "@leftuo":
                fixed_uid = uid
                winner = data
                break

        # إذا لم يكن موجودًا نجهز بيانات افتراضية
        if fixed_uid is None:
            winner = {"name": "نبا", "username": "@leftuo"}

        winner_text = f"🏆 الفائز هو:\n{winner['name']} | {winner['username']}"

        # إرسال للجميع
        for uid in participants:
            try:
                bot.send_message(int(uid), winner_text)
            except Exception:
                continue

        bot.send_message(
            ADMIN_ID,
            f"✅ تم إعلان فوز {winner['username']} للجميع."
        )

if __name__ == "__main__":
    bot.infinity_polling()
