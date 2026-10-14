import os
import logging
import asyncio
import threading
import requests
from flask import Flask, render_template_string, request, jsonify
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set!")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()
app = Flask(__name__)

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<meta name="theme-color" content="#0f172a">
<title>صانع ثيمات تيليجرام</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
:root {
    --bg-color: #0f172a;
    --card-color: #1e293b;
    --accent-color: #38bdf8;
    --bubble-out: #0284c7;
    --incoming-color: #B997D0;
    --text-color: #f8fafc;
    --gray-text: #94a3b8;
    --ui-opacity: .90;
}
* { box-sizing: border-box; }
body {
    font-family: "Segoe UI", Tahoma, sans-serif;
    background: var(--bg-color);
    color: var(--text-color);
    margin: 0;
    padding: 15px;
    transition: background .25s, color .25s;
}
h2 {
    text-align: center;
    margin: 5px 0 15px;
    font-size: 21px;
    color: var(--accent-color);
}
.upload-box {
    display: block;
    border: 2px dashed var(--accent-color);
    background: rgba(56,189,248,.05);
    padding: 15px;
    text-align: center;
    border-radius: 14px;
    cursor: pointer;
    margin-bottom: 14px;
}
.upload-box input { display: none; }
.svg-preview-container {
    width: 100%;
    max-width: 680px;
    margin: 0 auto 18px;
    border-radius: 18px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,.12);
    box-shadow: 0 8px 24px rgba(0,0,0,.3);
    background: #0B0E2C;
}
#telegramPreview { display: block; width: 100%; height: auto; }
.preview-note {
    color: var(--gray-text);
    font-size: 11px;
    text-align: center;
    margin: -8px 0 16px;
}
.palette-preview {
    display: flex;
    gap: 8px;
    justify-content: center;
    margin: 10px 0 16px;
    flex-wrap: wrap;
}
.color-dot {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    border: 2px solid rgba(255,255,255,.25);
}
.controls {
    background: rgba(255,255,255,.04);
    padding: 15px;
    border-radius: 16px;
    border: 1px solid rgba(255,255,255,.07);
}
.control-group {
    margin-bottom: 13px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
}
label { font-size: 13px; font-weight: 600; color: var(--gray-text); }
input[type=color] {
    border: none; width: 48px; height: 34px;
    border-radius: 8px; cursor: pointer; background: none;
}
input[type=range] {
    width: 100%; accent-color: var(--accent-color); margin-top: 8px;
}
.range-label { display:flex; justify-content:space-between; gap:8px; }
.btn-row { display:flex; gap:10px; margin-top:16px; }
.btn {
    flex:1; background:var(--accent-color); color:#0f172a;
    border:none; padding:12px 9px; border-radius:12px;
    font-size:13px; font-weight:bold; cursor:pointer;
}
.btn.secondary { background:rgba(255,255,255,.1); color:var(--text-color); }
.status { font-size:12px; text-align:center; color: var(--accent-color); margin-top:10px; font-weight: bold; }
@media (max-width: 380px) {
    body { padding: 10px; }
    .btn-row { flex-direction: column; }
}
</style>
</head>
<body>
<h2>🎨 صانع ثيمات تيليجرام</h2>

<label class="upload-box">
    📁 اضغط لاختيار صورة (ستظهر كخلفية للمعاينة ويتم استخراج ألوانها)
    <input type="file" id="imageInput" accept="image/*">
</label>

<div class="svg-preview-container">
<svg id="telegramPreview" xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 1080 1080" role="img" aria-label="معاينة ثيم تيليجرام">
<defs>
    <linearGradient id="previewBg" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#2D223B"/>
        <stop offset="50%" stop-color="var(--bg-color)"/>
        <stop offset="100%" stop-color="#0B0E2C"/>
    </linearGradient>
    <linearGradient id="previewAvatar" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="var(--accent-color)"/>
        <stop offset="100%" stop-color="var(--card-color)"/>
    </linearGradient>
    <filter id="previewShadow" x="-20%" y="-20%" width="140%" height="140%">
        <feDropShadow dx="0" dy="12" stdDeviation="16" flood-color="#000" flood-opacity=".45"/>
    </filter>
    <clipPath id="leftClip"><rect width="420" height="910" rx="48"/></clipPath>
    <clipPath id="rightClip"><rect width="420" height="910" rx="48"/></clipPath>
</defs>
<rect width="1080" height="1080" fill="url(#previewBg)"/>

<!-- الهاتف الأيسر: شاشة محادثة مع خلفية الصورة المرفوعة -->
<g transform="translate(75 75)" filter="url(#previewShadow)">
<rect width="420" height="910" rx="48" fill="var(--bg-color)" stroke="var(--card-color)" stroke-width="5"/>
<g clip-path="url(#leftClip)">
<!-- صورة الخلفية التي يرفعها المستخدم -->
<image id="wallpaperImage" href="" width="420" height="910" preserveAspectRatio="xMidYMid slice" opacity="0.85"/>
<rect width="420" height="910" fill="var(--bg-color)" opacity="0.45"/>

<!-- عناصر الهيدر والرسائل -->
<rect width="420" height="95" fill="var(--bg-color)" opacity="0.9"/>
<circle cx="50" cy="55" r="12" fill="var(--accent-color)"/>
<rect x="75" y="45" width="110" height="12" rx="6" fill="var(--text-color)"/>
<rect x="75" y="63" width="60" height="8" rx="4" fill="var(--incoming-color)"/>
<circle cx="375" cy="55" r="10" fill="var(--accent-color)"/>

<g transform="translate(220 125)">
<rect width="170" height="42" rx="16" fill="var(--bubble-out)" opacity="var(--ui-opacity)"/>
<rect x="15" y="17" width="110" height="8" rx="4" fill="var(--text-color)"/>
</g>
<g transform="translate(30 185)">
<rect width="210" height="70" rx="16" fill="var(--card-color)" opacity="var(--ui-opacity)"/>
<rect x="15" y="14" width="3" height="42" rx="1.5" fill="var(--accent-color)"/>
<rect x="26" y="18" width="80" height="8" rx="4" fill="var(--text-color)"/>
<rect x="26" y="34" width="140" height="8" rx="4" fill="var(--incoming-color)"/>
</g>
<g transform="translate(200 270)">
<rect width="190" height="45" rx="16" fill="var(--bubble-out)" opacity="var(--ui-opacity)"/>
<rect x="15" y="18" width="130" height="8" rx="4" fill="var(--text-color)"/>
</g>
<g transform="translate(140 385)">
<rect width="250" height="68" rx="20" fill="var(--bubble-out)" opacity="var(--ui-opacity)"/>
<circle cx="35" cy="34" r="20" fill="var(--accent-color)"/>
<g fill="var(--text-color)">
<rect x="70" y="30" width="3" height="10" rx="1.5"/><rect x="77" y="22" width="3" height="24" rx="1.5"/>
<rect x="84" y="18" width="3" height="32" rx="1.5"/><rect x="91" y="26" width="3" height="16" rx="1.5"/>
<rect x="98" y="20" width="3" height="28" rx="1.5"/>
</g>
<g fill="var(--incoming-color)">
<rect x="105" y="28" width="3" height="12" rx="1.5"/><rect x="112" y="23" width="3" height="22" rx="1.5"/>
<rect x="119" y="19" width="3" height="30" rx="1.5"/><rect x="126" y="25" width="3" height="18" rx="1.5"/>
<rect x="133" y="30" width="3" height="8" rx="1.5"/><rect x="140" y="22" width="3" height="24" rx="1.5"/>
<rect x="147" y="27" width="3" height="14" rx="1.5"/><rect x="154" y="31" width="3" height="6" rx="1.5"/>
</g>
<rect x="70" y="50" width="45" height="4" rx="2" fill="var(--accent-color)"/>
</g>
<g transform="translate(30 500)">
<rect width="210" height="72" rx="18" fill="var(--card-color)" opacity="var(--ui-opacity)"/>
<circle cx="30" cy="36" r="16" fill="var(--accent-color)"/>
<rect x="56" y="22" width="100" height="8" rx="4" fill="var(--text-color)"/>
<rect x="56" y="38" width="70" height="8" rx="4" fill="var(--incoming-color)"/>
<circle cx="30" cy="36" r="5" fill="var(--bg-color)"/>
</g>
<g transform="translate(200 585)">
<rect width="190" height="42" rx="16" fill="var(--bubble-out)" opacity="var(--ui-opacity)"/>
<rect x="15" y="17" width="140" height="8" rx="4" fill="var(--text-color)"/>
</g>
<g transform="translate(0 830)">
<rect width="420" height="80" fill="var(--bg-color)" opacity="0.9"/>
<circle cx="35" cy="40" r="14" fill="var(--accent-color)"/>
<rect x="65" y="22" width="220" height="36" rx="18" fill="var(--card-color)"/>
<circle cx="340" cy="40" r="14" fill="var(--accent-color)"/>
<circle cx="385" cy="40" r="14" fill="var(--accent-color)"/>
</g>
</g></g>

<!-- الهاتف الأيمن: قائمة المحادثات -->
<g transform="translate(585 120)" filter="url(#previewShadow)">
<rect width="420" height="910" rx="48" fill="var(--bg-color)" stroke="var(--card-color)" stroke-width="5"/>
<g clip-path="url(#rightClip)">
<rect width="420" height="910" fill="var(--bg-color)"/>
<rect width="420" height="110" fill="var(--bg-color)"/>
<circle cx="45" cy="40" r="10" fill="var(--accent-color)"/>
<rect x="75" y="34" width="100" height="12" rx="6" fill="var(--text-color)"/>
<circle cx="345" cy="40" r="10" fill="var(--accent-color)"/>
<circle cx="380" cy="40" r="10" fill="var(--accent-color)"/>
<circle cx="45" cy="85" r="8" fill="var(--accent-color)"/>
<rect x="65" y="81" width="70" height="8" rx="4" fill="var(--incoming-color)"/>
<circle cx="345" cy="85" r="8" fill="var(--accent-color)"/>
<circle cx="380" cy="85" r="8" fill="var(--accent-color)"/>

<g transform="translate(0 130)">
<circle cx="48" cy="40" r="30" fill="url(#previewAvatar)"/>
<rect x="95" y="24" width="75" height="11" rx="5.5" fill="var(--text-color)"/>
<rect x="95" y="44" width="75" height="9" rx="4.5" fill="var(--incoming-color)"/>
<rect x="355" y="24" width="30" height="8" rx="4" fill="var(--accent-color)" opacity=".8"/>
<circle cx="370" cy="46" r="6" fill="var(--accent-color)"/>
</g>
<g transform="translate(0 215)">
<circle cx="48" cy="40" r="30" fill="url(#previewAvatar)"/>
<rect x="95" y="24" width="95" height="11" rx="5.5" fill="var(--text-color)"/>
<rect x="95" y="44" width="60" height="9" rx="4.5" fill="var(--incoming-color)"/>
<rect x="355" y="24" width="30" height="8" rx="4" fill="var(--accent-color)" opacity=".8"/>
</g>
<g transform="translate(0 300)">
<circle cx="48" cy="40" r="30" fill="url(#previewAvatar)"/>
<rect x="95" y="24" width="105" height="11" rx="5.5" fill="var(--text-color)"/>
<rect x="95" y="44" width="70" height="9" rx="4.5" fill="var(--incoming-color)"/>
<circle cx="368" cy="42" r="9" fill="var(--card-color)"/>
</g>
<g transform="translate(0 385)">
<circle cx="48" cy="40" r="30" fill="url(#previewAvatar)"/>
<rect x="95" y="24" width="60" height="11" rx="5.5" fill="var(--text-color)"/>
<rect x="95" y="44" width="170" height="9" rx="4.5" fill="var(--incoming-color)"/>
<rect x="355" y="24" width="30" height="8" rx="4" fill="var(--accent-color)" opacity=".8"/>
</g>
<g transform="translate(0 470)">
<circle cx="48" cy="40" r="30" fill="url(#previewAvatar)"/>
<rect x="95" y="24" width="85" height="11" rx="5.5" fill="var(--text-color)"/>
<rect x="95" y="44" width="50" height="9" rx="4.5" fill="var(--incoming-color)"/>
<rect x="355" y="24" width="30" height="8" rx="4" fill="var(--accent-color)" opacity=".8"/>
</g>
<g transform="translate(325 785)">
<circle cx="36" cy="36" r="32" fill="var(--accent-color)"/>
<circle cx="36" cy="36" r="14" fill="var(--bg-color)" opacity=".9"/>
</g>
</g></g>
</svg>
</div>

<div style="text-align:center;font-size:12px;color:var(--gray-text)">لوحة الألوان الحالية</div>
<div class="palette-preview" id="palettePreview">
    <div class="color-dot" style="background:#38bdf8"></div>
    <div class="color-dot" style="background:#0284c7"></div>
    <div class="color-dot" style="background:#1e293b"></div>
    <div class="color-dot" style="background:#0f172a"></div>
</div>

<div class="controls">
    <div class="control-group">
        <label for="accentColor">اللون الأساسي / الأيقونات</label>
        <input type="color" id="accentColor" value="#38bdf8">
    </div>
    <div class="control-group">
        <label for="bgColor">لون خلفية التطبيق</label>
        <input type="color" id="bgColor" value="#0f172a">
    </div>
    <div class="control-group">
        <label for="cardColor">لون الرسائل الواردة والبطاقات</label>
        <input type="color" id="cardColor" value="#1e293b">
    </div>
    <div class="control-group">
        <label for="outColor">لون الرسائل الصادرة</label>
        <input type="color" id="outColor" value="#0284c7">
    </div>
    <div>
        <div class="range-label">
            <label for="opacityRange">شفافية فقاعات الرسائل</label>
            <label><span id="opacityVal">90</span>%</label>
        </div>
        <input type="range" id="opacityRange" min="20" max="100" value="90">
    </div>
    <div class="btn-row">
        <button class="btn secondary" id="copyButton" type="button">📋 نسخ الأكواد</button>
        <button class="btn" id="downloadButton" type="button">📥 توليد وإرسال الثيم للبوت</button>
    </div>
    <div class="status" id="statusMessage" role="status"></div>
</div>

<script>
const tg = window.Telegram && window.Telegram.WebApp;
if (tg) {
    tg.ready();
    tg.expand();
}

const $ = (id) => document.getElementById(id);
const root = document.documentElement;

function updatePreview() {
    const bg = $('bgColor').value;
    const card = $('cardColor').value;
    const accent = $('accentColor').value;
    const outgoing = $('outColor').value;
    const opacity = Number($('opacityRange').value) / 100;

    root.style.setProperty('--bg-color', bg);
    root.style.setProperty('--card-color', card);
    root.style.setProperty('--accent-color', accent);
    root.style.setProperty('--bubble-out', outgoing);
    root.style.setProperty('--ui-opacity', opacity);
    $('opacityVal').textContent = Math.round(opacity * 100);
}

['accentColor', 'bgColor', 'cardColor', 'outColor', 'opacityRange']
    .forEach(id => $(id).addEventListener('input', updatePreview));

function rgbToHex(r, g, b) {
    return '#' + [r, g, b].map(v => Math.max(0, Math.min(255, Math.round(v)))
        .toString(16).padStart(2, '0')).join('');
}
function hexToRgb(hex) {
    const value = hex.replace('#', '');
    return {
        r: parseInt(value.slice(0, 2), 16),
        g: parseInt(value.slice(2, 4), 16),
        b: parseInt(value.slice(4, 6), 16)
    };
}
function darken(hex, amount) {
    const c = hexToRgb(hex);
    return rgbToHex(c.r - amount, c.g - amount, c.b - amount);
}
function setStatus(message) {
    $('statusMessage').textContent = message;
}

/* رفع الصورة وعرضها كخلفية حقيقية للمعاينة واستخراج الألوان منها */
$('imageInput').addEventListener('change', function(event) {
    const file = event.target.files && event.target.files[0];
    if (!file) return;
    if (!file.type.startsWith('image/')) {
        setStatus('الملف المختار ليس صورة.');
        return;
    }

    const reader = new FileReader();
    reader.onerror = () => setStatus('تعذرت قراءة الصورة.');
    reader.onload = function(e) {
        const dataUrl = e.target.result;
        // وضع الصورة كخلفية للمعاينة اليسرى
        $('wallpaperImage').setAttribute('href', dataUrl);

        const img = new Image();
        img.onload = function() {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d', {willReadFrequently: true});
            canvas.width = 64;
            canvas.height = 64;
            ctx.drawImage(img, 0, 0, 64, 64);
            const pixels = ctx.getImageData(0, 0, 64, 64).data;
            let r = 0, g = 0, b = 0, count = 0;

            for (let i = 0; i < pixels.length; i += 4) {
                if (pixels[i + 3] < 30) continue;
                r += pixels[i]; g += pixels[i + 1]; b += pixels[i + 2];
                count++;
            }
            if (!count) return;

            const avg = rgbToHex(r / count, g / count, b / count);
            const darkBg = darken(avg, 45);
            const card = darken(avg, 25);
            const accent = avg;

            $('accentColor').value = accent;
            $('bgColor').value = darkBg;
            $('cardColor').value = card;
            $('outColor').value = accent;

            $('palettePreview').innerHTML = [accent, darkBg, card, '#FFFFFF']
                .map(color => '<div class="color-dot" title="' + color +
                    '" style="background:' + color + '"></div>').join('');

            updatePreview();
            setStatus('✨ تم تطبيق الصورة كخلفية واستخراج الألوان بنجاح!');
        };
        img.src = dataUrl;
    };
    reader.readAsDataURL(file);
});

function currentThemeData() {
    return {
        bg: $('bgColor').value,
        card: $('cardColor').value,
        accent: $('accentColor').value,
        outgoing: $('outColor').value,
        user_id: tg && tg.initDataUnsafe && tg.initDataUnsafe.user
            ? tg.initDataUnsafe.user.id : null
    };
}

$('copyButton').addEventListener('click', async function() {
    const d = currentThemeData();
    const text = [
        'Background=' + d.bg,
        'Card=' + d.card,
        'Accent=' + d.accent,
        'Outgoing=' + d.outgoing
    ].join('\n');

    try {
        await navigator.clipboard.writeText(text);
        setStatus('📋 تم نسخ أكواد الألوان.');
    } catch (error) {
        setStatus('تعذر النسخ تلقائياً.');
    }
});

/* إرسال طلب التوليد وسحب الملف مباشرة من البوت */
$('downloadButton').addEventListener('click', async function() {
    const data = currentThemeData();
    if (!data.user_id) {
        setStatus('⚠️ يجدر فتح هذه الواجهة من داخل بوت تيليجرام حصرياً.');
        return;
    }

    $('downloadButton').disabled = true;
    setStatus('⏳ جارٍ توليد الثيم وإرساله إلى دردشتك...');

    try {
        const response = await fetch('/generate-custom-theme', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        const resJson = await response.json();
        if (resJson.success) {
            setStatus('✅ تم إرسال ملف الثيم إلى محادثتك في البوت بنجاح!');
            setTimeout(() => { if (tg) tg.close(); }, 2000);
        } else {
            setStatus('❌ فشل في إرسال الملف.');
        }
    } catch (error) {
        setStatus('❌ حدث خطأ في الاتصال بالسيرفر.');
    } finally {
        $('downloadButton').disabled = false;
    }
});

updatePreview();
</script>
</body>
</html>"""


def hex_to_signed_int(hex_str):
    hex_str = hex_str.strip().lstrip("#")
    r = int(hex_str[0:2], 16)
    g = int(hex_str[2:4], 16)
    b = int(hex_str[4:6], 16)
    value = (255 << 24) | (r << 16) | (g << 8) | b
    if value > 0x7FFFFFFF:
        value -= 0x100000000
    return value

@app.route("/")
def home():
    return "Advanced Telegram Theme Mini App is running."

@app.route("/webapp")
def webapp():
    return render_template_string(HTML_TEMPLATE)

@app.route("/generate-custom-theme", methods=["POST"])
def generate_custom_theme():
    req_data = request.get_json(silent=True) or {}
    bg_hex = req_data.get("bg", "#0f172a")
    card_hex = req_data.get("card", "#1e293b")
    accent_hex = req_data.get("accent", "#38bdf8")
    outgoing_hex = req_data.get("outgoing", "#0284c7")
    user_id = req_data.get("user_id")

    c_bg = hex_to_signed_int(bg_hex)
    c_card = hex_to_signed_int(card_hex)
    c_accent = hex_to_signed_int(accent_hex)
    c_outgoing = hex_to_signed_int(outgoing_hex)
    c_white = -1
    c_gray = hex_to_signed_int("#94a3b8")

    theme_keys = {
        "WallpaperFileOffset": -1,
        "windowBackgroundWhite": c_bg,
        "windowBackgroundGray": c_bg,
        "dialogBackground": c_card,
        "windowBackgroundWhiteBlackText": c_white,
        "windowBackgroundWhiteGrayText": c_gray,
        "dialogTextBlack": c_white,
        "actionBarDefault": c_bg,
        "actionBarDefaultIcon": c_accent,
        "actionBarDefaultTitle": c_white,
        "chats_menuBackground": c_bg,
        "chats_name": c_white,
        "chats_message": c_gray,
        "chat_inBubble": c_card,
        "chat_outBubble": c_outgoing,
        "chat_messageTextIn": c_white,
        "chat_messageTextOut": c_white,
        "dialogButton": c_accent,
    }

    file_content = "\n".join(f"{key}={value}" for key, value in theme_keys.items()) + "\n"
    
    import tempfile
    handle = tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix=".attheme", prefix="custom_theme_", delete=False
    )
    file_path = handle.name
    
    try:
        handle.write(file_content)
        handle.close()

        # إرسال الملف مباشرة للمستخدم عبر البوت باستخدام Telegram API
        if user_id:
            url = f"https://api.telegram.org/bot{TOKEN}/sendDocument"
            with open(file_path, "rb") as f:
                files = {"document": ("Custom_Telegram_Theme.attheme", f)}
                data = {
                    "chat_id": user_id, 
                    "caption": "✨ تفضل ملف الثيم المخصص الخاص بك جاهزاً للتطبيق!"
                }
                requests.post(url, data=data, files=files)

        if os.path.exists(file_path):
            os.remove(file_path)

        return jsonify({"success": True})
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({"success": False, "error": str(e)}), 500

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    base_url = os.environ.get("RENDER_EXTERNAL_URL", "").rstrip("/")
    if not base_url:
        await message.answer("عذراً، رابط الخدمة غير مضبوط على Render.")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎨 افتح صانع الثيمات",
            web_app=WebAppInfo(url=f"{base_url}/webapp")
        )]
    ])
    await message.answer(
        "✨ أهلاً بك في صانع ثيمات تيليجرام المتطور!\n\n"
        "اضغط على الزر أدناه لفتح الواجهة، اختر صورتك لتظهر كخلفية حية واستخراج ألوانها، ثم احصل على ملف الثيم مباشرة في محادثتك:",
        reply_markup=keyboard
    )

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, use_reloader=False, threaded=True)

async def main():
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logging.info("Flask Mini App and Telegram bot are starting.")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
