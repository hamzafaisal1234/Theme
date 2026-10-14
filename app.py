import os
import logging
import asyncio
import threading
from flask import Flask, render_template_string, request, send_file
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from PIL import Image

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set!")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

app = Flask(__name__)

# رابط الـ Web App سيتم تحديثه تلقائياً أو استبداله برابط Render الخاص بك
WEB_APP_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://your-app-name.onrender.com")

# تصميم واجهة الـ Mini App بـ HTML/CSS/JS مع معاينة حية تشبه الصور المرفقة
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>مخصص ثيمات تيليجرام الديناميكي</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        :root {
            --bg-color: #0f172a;
            --card-color: #1e293b;
            --accent-color: #38bdf8;
            --bubble-out: #0284c7;
            --text-color: #f8fafc;
            --gray-text: #94a3b8;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            padding: 15px;
            transition: background 0.3s, color 0.3s;
        }
        h2 { text-align: center; margin-bottom: 10px; font-size: 20px; }
        
        /* محاكي المعاينة الحية (يشبه الصور) */
        .preview-container {
            display: flex;
            gap: 10px;
            justify-content: center;
            margin-bottom: 20px;
        }
        .phone-mockup {
            width: 48%;
            background: var(--card-color);
            border-radius: 20px;
            padding: 10px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            border: 2px solid rgba(255,255,255,0.1);
            font-size: 10px;
        }
        .screen-header {
            background: var(--accent-color);
            color: #fff;
            padding: 8px;
            border-radius: 10px;
            margin-bottom: 8px;
            font-weight: bold;
            text-align: center;
        }
        .chat-bubble {
            background: rgba(255,255,255,0.07);
            padding: 6px 10px;
            border-radius: 10px;
            margin-bottom: 6px;
            max-width: 80%;
        }
        .chat-bubble.out {
            background: var(--bubble-out);
            margin-right: auto;
        }
        .chat-row {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 6px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        .avatar {
            width: 25px;
            height: 25px;
            background: var(--accent-color);
            border-radius: 50%;
        }

        /* لوحة التحكم والألوان */
        .controls {
            background: rgba(255,255,255,0.05);
            padding: 15px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        .control-group {
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        label { font-size: 14px; font-weight: 600; }
        input[type="color"] {
            border: none;
            width: 45px;
            height: 30px;
            border-radius: 6px;
            cursor: pointer;
            background: none;
        }
        .btn {
            width: 100%;
            background: var(--accent-color);
            color: #fff;
            border: none;
            padding: 12px;
            border-radius: 10px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            margin-top: 10px;
            transition: 0.2s;
        }
        .btn:active { transform: scale(0.98); }
    </style>
</head>
<body>

    <h2>🎨 مصمم ثيمات تيليجرام المباشر</h2>

    <!-- المعاينة الحية -->
    <div class="preview-container">
        <!-- شاشة المحادثة -->
        <div class="phone-mockup" id="mockupChat" style="background-color: var(--bg-color);">
            <div class="screen-header" id="headerPrev">رأس التطبيق</div>
            <div class="chat-bubble" style="color: var(--text-color);">أهلاً بك، هذه معاينة للرسائل الواردة</div>
            <div class="chat-bubble out" style="background-color: var(--bubble-out); color: var(--text-color);">رسالة صادرة بتنسيق الألوان الخاص بك</div>
        </div>
        <!-- شاشة القائمة الرئيسية -->
        <div class="phone-mockup" id="mockupList" style="background-color: var(--bg-color);">
            <div class="screen-header" id="headerPrev2">قائمة المحادثات</div>
            <div class="chat-row">
                <div class="avatar" id="avPrev"></div>
                <div>
                    <div style="font-weight:bold; color:var(--text-color);">محمد أحمد</div>
                    <div style="color:var(--gray-text); font-size:8px;">آخر رسالة هنا...</div>
                </div>
            </div>
        </div>
    </div>

    <!-- لوحة التحكم لتعديل الألوان بحرية -->
    <div class="controls">
        <div class="control-group">
            <label>لون الخلفية العامة (Dark BG):</label>
            <input type="color" id="bgColor" value="#0f172a" oninput="updatePreview()">
        </div>
        <div class="control-group">
            <label>لون البطاقات والفقاعات الواردة:</label>
            <input type="color" id="cardColor" value="#1e293b" oninput="updatePreview()">
        </div>
        <div class="control-group">
            <label>لون الفقاعات الصادرة (Bubble Out):</label>
            <input type="color" id="bubbleOutColor" value="#0284c7" oninput="updatePreview()">
        </div>
        <div class="control-group">
            <label>اللون الرئيسي والأزرار (Accent):</label>
            <input type="color" id="accentColor" value="#38bdf8" oninput="updatePreview()">
        </div>

        <button class="btn" onclick="generateAndSendTheme()">✨ توليد وتحميل الثيم فوراً</button>
    </div>

    <script>
        let tg = window.Telegram.WebApp;
        tg.expand();

        function hexToRgb(hex) {
            let bigint = parseInt(hex.slice(1), 16);
            let r = (bigint >> 16) & 255;
            let g = (bigint >> 8) & 255;
            let b = bigint & 255;
            return {r, g, b};
        }

        function updatePreview() {
            let bg = document.getElementById('bgColor').value;
            let card = document.getElementById('cardColor').value;
            let bubble = document.getElementById('bubbleOutColor').value;
            let accent = document.getElementById('accentColor').value;

            document.documentElement.style.setProperty('--bg-color', bg);
            document.documentElement.style.setProperty('--card-color', card);
            document.documentElement.style.setProperty('--bubble-out', bubble);
            document.documentElement.style.setProperty('--accent-color', accent);
            
            document.getElementById('mockupChat').style.backgroundColor = bg;
            document.getElementById('mockupList').style.backgroundColor = bg;
            document.getElementById('headerPrev').style.backgroundColor = accent;
            document.getElementById('headerPrev2').style.backgroundColor = accent;
            document.getElementById('avPrev').style.backgroundColor = accent;
        }

        function generateAndSendTheme() {
            let data = {
                bg: document.getElementById('bgColor').value,
                card: document.getElementById('cardColor').value,
                bubble: document.getElementById('bubbleOutColor').value,
                accent: document.getElementById('accentColor').value,
                user_id: tg.initDataUnsafe?.user?.id || 12345
            };

            fetch('/generate-custom-theme', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
            .then(response => response.blob())
            .then(blob => {
                let url = window.URL.createObjectURL(blob);
                let a = document.createElement('a');
                a.href = url;
                a.download = "Custom_Telegram_Theme.attheme";
                document.body.appendChild(a);
                a.click();
                a.remove();
                tg.close();
            });
        }
    </script>
</body>
</html>
"""

def hex_to_signed_int(hex_str):
    hex_str = hex_str.lstrip('#')
    r, g, b = int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)
    val = (255 << 24) | (r << 16) | (g << 8) | b
    if val > 0x7FFFFFFF:
        val -= 0x100000000
    return val

@app.route("/")
def home():
    return "Telegram Custom Theme Mini App Server is Running Live!"

@app.route("/webapp")
def webapp():
    return render_template_string(HTML_TEMPLATE)

@app.route("/generate-custom-theme", methods=['POST'])
def generate_custom_theme():
    req_data = request.get_json()
    bg_hex = req_data.get('bg', '#0f172a')
    card_hex = req_data.get('card', '#1e293b')
    bubble_hex = req_data.get('bubble', '#0284c7')
    accent_hex = req_data.get('accent', '#38bdf8')

    c_dark_bg = hex_to_signed_int(bg_hex)
    c_card_bg = hex_to_signed_int(card_hex)
    c_bubble_out = hex_to_signed_int(bubble_hex)
    c_accent = hex_to_signed_int(accent_hex)
    c_primary = c_accent
    c_white = -1
    c_readable_gray = hex_to_signed_int("#94a3b8")

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
    file_path = f"custom_theme_{req_data.get('user_id', 12345)}.attheme"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(file_content)

    return send_file(file_path, as_attachment=True, download_name="Custom_Theme.attheme")

# أوامر البوت في تيليجرام لإرسال زر الـ Mini App
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # استخدام رابط الخدمة على Render مع مسار /webapp
    web_app_url = f"{os.environ.get('RENDER_EXTERNAL_URL', 'https://your-app-name.onrender.com')}/webapp"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎨 افتح مصمم الثيمات المباشر (Mini App)", web_app=WebAppInfo(url=web_app_url))]
    ])
    
    await message.answer(
        "✨ أهلاً بك في بوت تصميم وتعديل ثيمات تيليجرام المباشر!\n\n"
        "اضغط على الزر بالأسفل لفتح الواجهة التفاعلية، عدل الألوان كما تحب مع المعاينة الحية، وحمل الثيم فوراً:",
        reply_markup=keyboard
    )

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

async def main():
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    print("🤖 البوت وسيرفر Mini App يعملان بكفاءة تامة...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
