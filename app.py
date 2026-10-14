import os
import threading
from flask import Flask
import telebot

# قراءة توكن البوت من متغيرات البيئة بأمان
TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

@app.route("/")
def home():
    return "Telegram Theme Bot is running successfully!"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "أهلاً بك في بوت توليد الثيمات! البوت يعمل الآن بكفاءة.")

# دالة لتشغيل البوت في الخلفية
def run_bot():
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"Polling error: {e}")

if __name__ == "__main__":
    # تشغيل البوت في خيط منفصل لكي لا يتعطل السيرفر
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    # تشغيل سيرفر فلاسك بالمنفذ المخصص من Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

