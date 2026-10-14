import os
import logging
import asyncio
import threading
from flask import Flask
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import BufferedInputFile
from PIL import Image

# قراءة توكن البوت من متغيرات البيئة في Render بأمان
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set!")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# إعداد سيرفر Flask لكي يستجيب لمنفذ Render ولا يغلق التطبيق
app = Flask(__name__)

@app.route("/")
def home():
    return "Telegram Theme Bot is running successfully!"

def rgb_to_signed_int(r, g, b):
    val = (255 << 24) | (r << 16) | (g << 8) | b
    if val > 0x7FFFFFFF:
        val -= 0x100000000
    return val

def generate_theme_file(image_path, output_path):
    img = Image.open(image_path).convert('RGB')
    img = img.resize((60, 60))
    pixels = list(img.getdata())
    
    r_sum = sum(p[0] for p in pixels)
    g_sum = sum(p[1] for p in pixels)
    b_sum = sum(p[2] for p in pixels)
    total = len(pixels)
    
    r = r_sum // total
    g = g_sum // total
    b = b_sum // total
    
    # اشتقاق الألوان المتناسقة للوضع الداكن
    dark_bg = (max(0, r - 50), max(0, g - 50), max(0, b - 50))
    card_bg = (max(0, r - 35), max(0, g - 35), max(0, b - 35))
    bubble_out = (min(255, r + 20), max(0, g - 15), min(255, b + 30))
    accent = (min(255, r + 60), min(255, g + 60), min(255, b + 60))
    
    c_primary = rgb_to_signed_int(r, g, b)
    c_dark_bg = rgb_to_signed_int(*dark_bg)
    c_card_bg = rgb_to_signed_int(*card_bg)
    c_bubble_out = rgb_to_signed_int(*bubble_out)
    c_accent = rgb_to_signed_int(*accent)
    
    c_white = -1
    c_readable_gray = rgb_to_signed_int(175, 185, 200)

    theme_keys = {
        "WallpaperFileOffset": -1,
        "windowBackgroundWhite": c_dark_bg,
        "windowBackgroundGray": c_dark_bg,
        "dialogBackground": c_card_bg,
        "windowBackgroundWhiteBlackText": c_white,
        "windowBackgroundWhiteGrayText": c_readable_gray,
        "windowBackgroundWhiteValueText": c_white,
        "dialogTextBlack": c_white,
        "dialogTextGray": c_readable_gray,
        "dialogTextLink": c_accent,
        "actionBarDefault": c_primary,
        "actionBarDefaultIcon": c_white,
        "actionBarDefaultTitle": c_white,
        "actionBarDefaultSubtitle": c_readable_gray,
        "chats_menuBackground": c_card_bg,
        "chats_name": c_white,
        "chats_message": c_readable_gray,
        "chats_date": c_accent,
        "chats_unreadCounter": c_primary,
        "chats_onlineCircle": c_accent,
        "chat_inBubble": c_card_bg,
        "chat_outBubble": c_bubble_out,
        "chat_messageTextIn": c_white,
        "chat_messageTextOut": c_white,
        "chat_messageLinkIn": c_accent,
        "chat_messageLinkOut": c_accent,
        "chat_timeText": c_readable_gray,
        "chat_outTimeText": c_readable_gray,
        "chat_messagePanelBackground": c_card_bg,
        "chat_messagePanelText": c_white,
        "chat_messagePanelHint": c_readable_gray,
        "chat_messagePanelSend": c_primary,
        "profile_actionBackground": c_primary,
        "profile_title": c_white,
        "profile_status": c_readable_gray,
        "dialogButton": c_accent
    }
    
    file_content = "\n".join([f"{k}={v}" for k, v in theme_keys.items()])
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(file_content)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("✨ أهلاً بك! أرسل لي أي صورة وسأقوم بتوليد ثيم تيليجرام متناسق وواضح مخصص لها فوراً.")

@dp.message(F.photo)
async def handle_image(message: types.Message):
    processing_msg = await message.answer("🔄 جاري تحليل الصورة واستخراج لوحة الألوان وتوليد الثيم...")
    
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    
    input_path = f"img_{message.from_user.id}.jpg"
    output_path = f"theme_{message.from_user.id}.attheme"
    
    await bot.download(file, destination=input_path)
    
    generate_theme_file(input_path, output_path)
    
    with open(output_path, "rb") as f:
        file_bytes = f.read()
        document = BufferedInputFile(file_bytes, filename="Dynamic_Theme.attheme")
        await message.reply_document(document, caption="✨ تفضل ثيمك الديناميكي المتناسق مع الصورة!")
    
    await bot.delete_message(chat_id=message.chat.id, message_id=processing_msg.message_id)
    
    if os.path.exists(input_path): os.remove(input_path)
    if os.path.exists(output_path): os.remove(output_path)

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

async def main():
    # تشغيل سيرفر فلاسك في خلفية مستقلة ليلبي شروط الاستضافة
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    print("🤖 البوت يعمل الآن ويستمع للرسائل عبر aiogram...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
