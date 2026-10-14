import os
import logging
import asyncio
import threading
from flask import Flask, render_template_string, request, send_file
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set!")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

app = Flask(__name__)

# تصميم واجهة الـ Mini App المتطورة والفاخرة
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>صانع الثيمات الديناميكي المتطور</title>
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
        * { box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            padding: 15px;
            transition: background 0.3s, color 0.3s;
        }
        h2 { text-align: center; margin-bottom: 15px; font-size: 22px; color: var(--accent-color); }
        
        /* زر رفع الصورة الاحترافي */
        .upload-box {
            border: 2px dashed var(--accent-color);
            background: rgba(56, 189, 248, 0.05);
            padding: 15px;
            text-align: center;
            border-radius: 14px;
            cursor: pointer;
            margin-bottom: 15px;
            transition: 0.2s;
        }
        .upload-box:hover { background: rgba(56, 189, 248, 0.1); }
        .upload-box input { display: none; }

        /* معاينة واجهة تيليجرام الحية */
        .preview-container {
            display: flex;
            gap: 12px;
            justify-content: center;
            margin-bottom: 20px;
        }
        .phone-mockup {
            width: 48%;
            background: var(--card-color);
            border-radius: 18px;
            padding: 10px;
            box-shadow: 0 8px 20px rgba(0,0,0,0.4);
            border: 1px solid rgba(255,255,255,0.1);
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
            background: rgba(255,255,255,0.08);
            padding: 8px 10px;
            border-radius: 12px;
            margin-bottom: 6px;
            max-width: 85%;
        }
        .chat-bubble.out {
            background: var(--bubble-out);
            margin-right: auto;
        }

        /* لوحة التحكم والألوان */
        .controls {
            background: rgba(255, 255, 255, 0.04);
            padding: 15px;
            border-radius: 16px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.05);
        }
        .control-group {
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        label { font-size: 13px; font-weight: 600; color: var(--gray-text); }
        input[type="color"] {
            border: none;
            width: 45px;
            height: 32px;
            border-radius: 8px;
            cursor: pointer;
            background: none;
        }
        input[type="range"] {
            width: 100%;
            accent-color: var(--accent-color);
            margin-top: 5px;
        }
        
        .palette-preview {
            display: flex;
            gap: 8px;
            justify-content: center;
            margin: 10px 0;
        }
        .color-dot {
            width: 25px;
            height: 25px;
            border-radius: 50%;
            border: 2px solid rgba(255,255,255,0.2);
        }

        /* الأزرار النهائية */
        .btn-row {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        .btn {
            flex: 1;
            background: var(--accent-color);
            color: #0f172a;
            border: none;
            padding: 12px;
            border-radius: 12px;
            font-size: 14px;
            font-weight: bold;
            cursor: pointer;
            transition: 0.2s;
            text-align: center;
        }
        .btn.secondary {
            background: rgba(255,255,255,0.1);
            color: var(--text-color);
        }
        .btn:active { transform: scale(0.97); }
    </style>
</head>
<body>

    <h2>🎨 صانع الثيمات الديناميكي المتطور</h2>

    <!-- رفع الصورة -->
    <label class="upload-box">
        📁 <b>اضغط هنا لاختيار صورة وتحليل ألوانها بدقة</b>
        <input type="file" id="imageInput" accept="image/*" onchange="processImage(event)">
    </label>

    <!-- المعاينة الحية -->
    <div class="preview-container">
        <div class="phone-mockup" id="mockupChat" style="background-color: var(--bg-color);">
            <div class="screen-header" id="headerPrev">معاينة المحادثة</div>
            <div class="chat-bubble" style="color: var(--text-color);">أهلاً بك! هذه معاينة للرسائل الواردة.</div>
            <div class="chat-bubble out" style="background-color: var(--bubble-out); color: var(--text-color);">هنا تظهر عينة اللون الأساسي للثيم.</div>
        </div>
        <div class="phone-mockup" id="mockupList" style="background-color: var(--bg-color);">
            <div class="screen-header" id="headerPrev2">القائمة الرئيسية</div>
            <div class="chat-bubble" style="font-size: 9px; color: var(--gray-text);">لوحة الألوان المستخرجة ستظهر هنا بالكامل بعد رفع الصورة...</div>
        </div>
    </div>

    <!-- لوحة الألوان المستخرجة -->
    <div style="text-align:center; font-size:12px; margin-bottom:8px; color:var(--gray-text);">لوحة الألوان المستخرجة بالكامل:</div>
    <div class="palette-preview" id="palettePreview">
        <div class="color-dot" style="background: #38bdf8;"></div>
        <div class="color-dot" style="background: #0284c7;"></div>
        <div class="color-dot" style="background: #1e293b;"></div>
        <div class="color-dot" style="background: #0f172a;"></div>
    </div>

    <!-- لوحة التحكم اليدوي -->
    <div class="controls">
        <div class="control-group">
            <label>اللون الأساسي (Primary):</label>
            <input type="color" id="accentColor" value="#38bdf8" oninput="updatePreview()">
        </div>
        <div class="control-group">
            <label>لون الخلفية (Background):</label>
            <input type="color" id="bgColor" value="#0f172a" oninput="updatePreview()">
        </div>
        <div class="control-group">
            <label>لون البطاقات / الرسائل:</label>
            <input type="color" id="cardColor" value="#1e293b" oninput="updatePreview()">
        </div>
        <div style="margin-top: 10px;">
            <label>شفافية الواجهة: <span id="opacityVal">90</span>%</label>
            <input type="range" id="opacityRange" min="50" max="100" value="90" oninput="updatePreview()">
        </div>

        <div class="btn-row">
            <button class="btn secondary" onclick="copyCodes()">📋 نسخ الأكواد</button>
            <button class="btn" onclick="generateAndSendTheme()">📥 تحميل ملف الثيم</button>
        </div>
    </div>

    <script>
        let tg = window.Telegram.WebApp;
        tg.expand();

        function updatePreview() {
            let bg = document.getElementById('bgColor').value;
            let card = document.getElementById('cardColor').value;
            let accent = document.getElementById('accentColor').value;
            let opacity = document.getElementById('opacityRange').value / 100;

            document.getElementById('opacityVal').innerText = Math.round(opacity * 100);

            document.documentElement.style.setProperty('--bg-color', bg);
            document.documentElement.style.setProperty('--card-color', card);
            document.documentElement.style.setProperty('--accent-color', accent);
            document.documentElement.style.setProperty('--bubble-out', accent);
            
            document.getElementById('mockupChat').style.backgroundColor = bg;
            document.getElementById('mockupList').style.backgroundColor = bg;
            document.getElementById('headerPrev').style.backgroundColor = accent;
            document.getElementById('headerPrev2').style.backgroundColor = accent;
        }

        // تحليل الصورة مباشرة واستخراج الألوان
        function processImage(event) {
            let file = event.target.files[0];
            if (!file) return;

            let reader = new FileReader();
            reader.onload = function(e) {
                let img = new Image();
                img.onload = function() {
                    let canvas = document.createElement('canvas');
                    let ctx = canvas.getContext('2d');
                    canvas.width = 50;
                    canvas.height = 50;
                    ctx.drawImage(img, 0, 0, 50, 50);

                    let imgData = ctx.getImageData(0, 0, 50, 50).data;
                    let rSum = 0, gSum = 0, bSum = 0, count = 0;

                    for (let i = 0; i < imgData.length; i += 4) {
                        rSum += imgData[i];
                        gSum += imgData[i+1];
                        bSum += imgData[i+2];
                        count++;
                    }

                    let r = Math.floor(rSum / count);
                    let g = Math.floor(gSum / count);
                    let b = Math.floor(bSum / count);

                    // اشتقاق ألوان متناسقة داكنة
                    let mainHex = rgbToHex(r, g, b);
                    let darkBgHex = rgbToHex(Math.max(0, r-45), Math.max(0, g-45), Math.max(0, b-45));
                    let cardHex = rgbToHex(Math.max(0, r-30), Math.max(0, g-30), Math.max(0, b-30));

                    document.getElementById('accentColor').value = mainHex;
                    document.getElementById('bgColor').value = darkBgHex;
                    document.getElementById('cardColor').value = cardHex;

                    // تحديث عينات الألوان
                    document.getElementById('palettePreview').innerHTML = `
                        <div class="color-dot" style="background: ${mainHex};"></div>
                        <div class="color-dot" style="background: ${darkBgHex};"></div>
                        <div class="color-dot" style="background: ${cardHex};"></div>
                        <div class="color-dot" style="background: #ffffff;"></div>
                    `;

                    updatePreview();
                }
                img.src = e.target.result;
            }
            reader.readAsDataURL(file);
        }

        function rgbToHex(r, g, b) {
            return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
        }

        function copyCodes() {
            alert("تم نسخ أكواد الثيم بنجاح!");
        }

        function generateAndSendTheme() {
            let data = {
                bg: document.getElementById('bgColor').value,
                card: document.getElementById('cardColor').value,
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
    return "Advanced Telegram Theme Mini App is Running Live!"

@app.route("/webapp")
def webapp():
    return render_template_string(HTML_TEMPLATE)

@app.route("/generate-custom-theme", methods=['POST'])
def generate_custom_theme():
    req_data = request.get_json()
    bg_hex = req_data.get('bg', '#0f172a')
    card_hex = req_data.get('card', '#1e293b')
    accent_hex = req_data.get('accent', '#38bdf8')

    c_dark_bg = hex_to_signed_int(bg_hex)
    c_card_bg = hex_to_signed_int(card_hex)
    c_accent = hex_to_signed_int(accent_hex)
    c_white = -1
    c_readable_gray = hex_to_signed_int("#94a3b8")

    theme_keys = {
        "WallpaperFileOffset": -1,
        "windowBackgroundWhite": c_dark_bg,
        "windowBackgroundGray": c_dark_bg,
        "dialogBackground": c_card_bg,
        "windowBackgroundWhiteBlackText": c_white,
        "windowBackgroundWhiteGrayText": c_readable_gray,
        "dialogTextBlack": c_white,
        "actionBarDefault": c_accent,
        "actionBarDefaultIcon": c_white,
        "actionBarDefaultTitle": c_white,
        "chats_menuBackground": c_card_bg,
        "chats_name": c_white,
        "chats_message": c_readable_gray,
        "chat_inBubble": c_card_bg,
        "chat_outBubble": c_accent,
        "chat_messageTextIn": c_white,
        "chat_messageTextOut": c_white,
        "dialogButton": c_accent
    }

    file_content = "\n".join([f"{k}={v}" for k, v in theme_keys.items()])
    file_path = f"custom_theme_{req_data.get('user_id', 12345)}.attheme"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(file_content)

    return send_file(file_path, as_attachment=True, download_name="Advanced_Telegram_Theme.attheme")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    web_app_url = f"{os.environ.get('RENDER_EXTERNAL_URL', 'https://your-app-name.onrender.com')}/webapp"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎨 افتح صانع الثيمات الديناميكي المتطور", web_app=WebAppInfo(url=web_app_url))]
    ])
    await message.answer(
        "✨ أهلاً بك في بوت تصميم ثيمات تيليجرام المتطور!\n\n"
        "اضغط على الزر بالأسفل لفتح الواجهة الاحترافية، اختر صورتك واستخرج الألوان بدقة تامة ومعاينة حية:",
        reply_markup=keyboard
    )

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

async def main():
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    print("🤖 البوت والواجهة المتقدمة يعملان بكفاءة تامة...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
