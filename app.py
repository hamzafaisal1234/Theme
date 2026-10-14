import os
import logging
import asyncio
import threading
import sqlite3
import tempfile
import requests
from flask import Flask, render_template_string, request, jsonify, Response
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

# --- قاعدة البيانات المحلية SQLite لتسجيل الثيمات ---
DB_NAME = "themes_history.db"

def init_db():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS saved_themes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                bg_color TEXT,
                bg_grad_color TEXT,
                card_color TEXT,
                accent_color TEXT,
                outgoing_color TEXT,
                secondary_color TEXT,
                opacity INTEGER,
                mode TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Database init error: {e}")

init_db()

def save_theme_to_db(user_id, bg, bg_grad, card, accent, outgoing, secondary, opacity, mode):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO saved_themes (user_id, bg_color, bg_grad_color, card_color, accent_color, outgoing_color, secondary_color, opacity, mode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (str(user_id), bg, bg_grad, card, accent, outgoing, secondary, opacity, mode))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Database insert error: {e}")

# --- واجهة المستخدم المطورة مع الحماية ضد الأخطاء والتباين التلقائي ---
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<meta name="theme-color" content="#0f172a">
<title>صانع ثيمات تيليجرام الذكي</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
:root {
    --bg-color: #0f172a;
    --bg-grad: #2D223B;
    --card-color: #1e293b;
    --accent-color: #38bdf8;
    --secondary-color: #B997D0;
    --bubble-out: #0284c7;
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
input[type=text] {
    width: 100%; padding: 8px 12px; border-radius: 8px;
    border: 1px solid rgba(255,255,255,.2); background: rgba(0,0,0,.2);
    color: var(--text-color); font-size: 13px; outline: none;
}
input[type=range] {
    width: 100%; accent-color: var(--accent-color); margin-top: 8px;
}
.checkbox-group {
    display: flex;
    align-items: center;
    gap: 10px;
    background: rgba(56,189,248,.08);
    padding: 10px 12px;
    border-radius: 10px;
    margin-bottom: 14px;
    border: 1px solid rgba(56,189,248,.2);
}
.checkbox-group input { width: 18px; height: 18px; accent-color: var(--accent-color); cursor: pointer; }
.range-label { display:flex; justify-content:space-between; gap:8px; }
.btn-row { display:flex; gap:10px; margin-top:12px; }
.btn {
    flex:1; background:var(--accent-color); color:#0f172a;
    border:none; padding:12px 9px; border-radius:12px;
    font-size:13px; font-weight:bold; cursor:pointer;
    text-align: center; text-decoration: none; display: inline-block;
}
.btn.secondary { background:rgba(255,255,255,.1); color:var(--text-color); }
.btn.mode-toggle { background: #334155; color: #f8fafc; margin-bottom: 10px; flex: unset; width: 100%; }
.status { font-size:12px; text-align:center; color: var(--accent-color); margin-top:10px; font-weight: bold; word-break: break-all; }
@media (max-width: 380px) {
    body { padding: 10px; }
    .btn-row { flex-direction: column; }
}
</style>
</head>
<body>
<h2>🎨 صانع ثيمات تيليجرام الذكي</h2>

<button class="btn mode-toggle" id="modeToggleBtn" type="button">☀️ التبديل إلى الوضع الفاتح (المريح للعين)</button>

<div class="checkbox-group">
    <input type="checkbox" id="autoContrastToggle" checked>
    <label for="autoContrastToggle" style="color:var(--text-color); cursor:pointer;">🛡️ تفعيل مُحسّن التباين التلقائي (منع الألوان المؤذية للعين)</label>
</div>

<label class="upload-box">
    📁 اضغط لاختيار صورة (استخراج ألوان ذكي وتطبيقها كخلفية حية)
    <input type="file" id="imageInput" accept="image/*">
</label>

<div class="svg-preview-container">
<svg id="telegramPreview" xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink"
     viewBox="0 0 1080 1080" role="img" aria-label="معاينة ثيم تيليجرام">
<defs>
    <linearGradient id="previewBg" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" id="stopGradStart" stop-color="var(--bg-grad)"/>
        <stop offset="50%" stop-color="var(--bg-color)"/>
        <stop offset="100%" id="stopGradEnd" stop-color="#0B0E2C"/>
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

<g transform="translate(75 75)" filter="url(#previewShadow)">
<rect width="420" height="910" rx="48" fill="var(--bg-color)" stroke="var(--card-color)" stroke-width="5"/>
<g clip-path="url(#leftClip)">
<image id="wallpaperImage" href="" xlink:href="" width="420" height="910" preserveAspectRatio="xMidYMid slice" opacity="0.85"/>
<rect width="420" height="910" fill="var(--bg-color)" opacity="0.45"/>
<rect width="420" height="95" fill="var(--bg-color)" opacity="0.9"/>
<circle cx="50" cy="55" r="12" fill="var(--accent-color)"/>
<rect x="75" y="45" width="110" height="12" rx="6" fill="var(--text-color)"/>
<rect x="75" y="63" width="60" height="8" rx="4" fill="var(--secondary-color)"/>
<circle cx="375" cy="55" r="10" fill="var(--accent-color)"/>

<g transform="translate(220 125)">
<rect width="170" height="42" rx="16" fill="var(--bubble-out)" opacity="var(--ui-opacity)"/>
<rect x="15" y="17" width="110" height="8" rx="4" fill="var(--text-color)"/>
</g>
<g transform="translate(30 185)">
<rect width="210" height="70" rx="16" fill="var(--card-color)" opacity="var(--ui-opacity)"/>
<rect x="15" y="14" width="3" height="42" rx="1.5" fill="var(--accent-color)"/>
<rect x="26" y="18" width="80" height="8" rx="4" fill="var(--text-color)"/>
<rect x="26" y="34" width="140" height="8" rx="4" fill="var(--secondary-color)"/>
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
<g fill="var(--secondary-color)">
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
<rect x="56" y="38" width="70" height="8" rx="4" fill="var(--secondary-color)"/>
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
<rect x="65" y="81" width="70" height="8" rx="4" fill="var(--secondary-color)"/>
<circle cx="345" cy="85" r="8" fill="var(--accent-color)"/>
<circle cx="380" cy="85" r="8" fill="var(--accent-color)"/>

<g transform="translate(0 130)">
<circle cx="48" cy="40" r="30" fill="url(#previewAvatar)"/>
<rect x="95" y="24" width="75" height="11" rx="5.5" fill="var(--text-color)"/>
<rect x="95" y="44" width="75" height="9" rx="4.5" fill="var(--secondary-color)"/>
<rect x="355" y="24" width="30" height="8" rx="4" fill="var(--accent-color)" opacity=".8"/>
<circle cx="370" cy="46" r="6" fill="var(--accent-color)"/>
</g>
<g transform="translate(0 215)">
<circle cx="48" cy="40" r="30" fill="url(#previewAvatar)"/>
<rect x="95" y="24" width="95" height="11" rx="5.5" fill="var(--text-color)"/>
<rect x="95" y="44" width="60" height="9" rx="4.5" fill="var(--secondary-color)"/>
<rect x="355" y="24" width="30" height="8" rx="4" fill="var(--accent-color)" opacity=".8"/>
</g>
<g transform="translate(0 300)">
<circle cx="48" cy="40" r="30" fill="url(#previewAvatar)"/>
<rect x="95" y="24" width="105" height="11" rx="5.5" fill="var(--text-color)"/>
<rect x="95" y="44" width="70" height="9" rx="4.5" fill="var(--secondary-color)"/>
<circle cx="368" cy="42" r="9" fill="var(--card-color)"/>
</g>
<g transform="translate(0 385)">
<circle cx="48" cy="40" r="30" fill="url(#previewAvatar)"/>
<rect x="95" y="24" width="60" height="11" rx="5.5" fill="var(--text-color)"/>
<rect x="95" y="44" width="170" height="9" rx="4.5" fill="var(--secondary-color)"/>
<rect x="355" y="24" width="30" height="8" rx="4" fill="var(--accent-color)" opacity=".8"/>
</g>
<g transform="translate(0 470)">
<circle cx="48" cy="40" r="30" fill="url(#previewAvatar)"/>
<rect x="95" y="24" width="85" height="11" rx="5.5" fill="var(--text-color)"/>
<rect x="95" y="44" width="50" height="9" rx="4.5" fill="var(--secondary-color)"/>
<rect x="355" y="24" width="30" height="8" rx="4" fill="var(--accent-color)" opacity=".8"/>
</g>
<g transform="translate(325 785)">
<circle cx="36" cy="36" r="32" fill="var(--accent-color)"/>
<circle cx="36" cy="36" r="14" fill="var(--bg-color)" opacity=".9"/>
</g>
</g></g>
</svg>
</div>

<div style="text-align:center;font-size:12px;color:var(--gray-text)">لوحة الألوان المستخرجة ذكياً</div>
<div class="palette-preview" id="palettePreview">
    <div class="color-dot" style="background:#38bdf8"></div>
    <div class="color-dot" style="background:#0284c7"></div>
    <div class="color-dot" style="background:#1e293b"></div>
    <div class="color-dot" style="background:#0f172a"></div>
</div>

<div class="controls">
    <div class="control-group" id="chatIdContainer" style="display:none; flex-direction:column; align-items:flex-start;">
        <label for="manualChatId">معرف تيليجرام الخاص بك (Chat ID):</label>
        <input type="text" id="manualChatId" placeholder="مثال: 123456789">
    </div>

    <div class="control-group">
        <label for="accentColor">اللون الأساسي / الأيقونات</label>
        <input type="color" id="accentColor" value="#38bdf8">
    </div>
    <div class="control-group">
        <label for="bgColor">لون خلفية التطبيق الأساسي</label>
        <input type="color" id="bgColor" value="#0f172a">
    </div>
    <div class="control-group">
        <label for="bgGradColor">لون تدرج الخلفية الثانوي</label>
        <input type="color" id="bgGradColor" value="#2D223B">
    </div>
    <div class="control-group">
        <label for="cardColor">لون الرسائل الواردة والبطاقات</label>
        <input type="color" id="cardColor" value="#1e293b">
    </div>
    <div class="control-group">
        <label for="outColor">لون الرسائل الصادرة</label>
        <input type="color" id="outColor" value="#0284c7">
    </div>
    <div class="control-group">
        <label for="secondaryColor">لون النصوص الثانوية والتمييز</label>
        <input type="color" id="secondaryColor" value="#B997D0">
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
        <button class="btn secondary" id="shareLinkButton" type="button">🔗 نسخ رابط المشاركة</button>
    </div>
    <div class="btn-row">
        <a class="btn" id="downloadDirectBtn" href="#" target="_blank">📥 تحميل الثيم مباشرة</a>
        <button class="btn" id="sendTelegramBtn" type="button">🚀 إرسال الثيم إلى البوت</button>
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

let telegramUserId = tg && tg.initDataUnsafe && tg.initDataUnsafe.user ? tg.initDataUnsafe.user.id : null;

if (!telegramUserId) {
    $('chatIdContainer').style.display = 'flex';
}

let currentMode = 'dark';

// دالة آمنة لمعالجة الأكواد السداسية (تدعم 3 أو 6 خانات)
function hexToRgb(hex) {
    if (!hex) return [15, 23, 42];
    hex = hex.replace('#', '').trim();
    if (hex.length === 3) {
        hex = hex.split('').map(c => c + c).join('');
    }
    const num = parseInt(hex, 16);
    if (isNaN(num)) return [15, 23, 42];
    return [
        (num >> 16) & 255,
        (num >> 8) & 255,
        num & 255
    ];
}

function getLuminance(hex) {
    const rgb = hexToRgb(hex);
    const [r, g, b] = rgb.map(v => {
        v /= 255;
        return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    });
    return r * 0.2126 + g * 0.7152 + b * 0.0722;
}

function getContrastRatio(hex1, hex2) {
    const lum1 = getLuminance(hex1);
    const lum2 = getLuminance(hex2);
    const brightest = Math.max(lum1, lum2);
    const darkest = Math.min(lum1, lum2);
    return (brightest + 0.05) / (darkest + 0.05);
}

window.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('bg')) {
        if (urlParams.get('bg')) $('bgColor').value = '#' + urlParams.get('bg').replace('#','');
        if (urlParams.get('bgGrad')) $('bgGradColor').value = '#' + urlParams.get('bgGrad').replace('#','');
        if (urlParams.get('card')) $('cardColor').value = '#' + urlParams.get('card').replace('#','');
        if (urlParams.get('accent')) $('accentColor').value = '#' + urlParams.get('accent').replace('#','');
        if (urlParams.get('outgoing')) $('outColor').value = '#' + urlParams.get('outgoing').replace('#','');
        if (urlParams.get('secondary')) $('secondaryColor').value = '#' + urlParams.get('secondary').replace('#','');
        if (urlParams.get('opacity')) $('opacityRange').value = urlParams.get('opacity');
        if (urlParams.get('mode')) {
            currentMode = urlParams.get('mode');
            if (currentMode === 'light') {
                $('modeToggleBtn').textContent = '🌙 التبديل إلى الوضع الداكن (Dark Mode)';
            }
        }
        updatePreview();
        setStatus('🔗 تم تحميل الثيم المخصص من رابط المشاركة بنجاح!');
    }
});

$('modeToggleBtn').addEventListener('click', function() {
    if (currentMode === 'dark') {
        currentMode = 'light';
        $('bgColor').value = '#f8fafc';
        $('bgGradColor').value = '#e2e8f0';
        $('cardColor').value = '#e2e8f0';
        $('secondaryColor').value = '#475569';
        $('modeToggleBtn').textContent = '🌙 التبديل إلى الوضع الداكن (Dark Mode)';
        setStatus('☀️ تم تفعيل الوضع الفاتح المريح للعين.');
    } else {
        currentMode = 'dark';
        $('bgColor').value = '#0f172a';
        $('bgGradColor').value = '#2D223B';
        $('cardColor').value = '#1e293b';
        $('secondaryColor').value = '#B997D0';
        $('modeToggleBtn').textContent = '☀️ التبديل إلى الوضع الفاتح (المريح للعين)';
        setStatus('🌙 تم تفعيل الوضع الداكن.');
    }
    updatePreview();
});

function applyAutoContrastGuard() {
    if (!$('autoContrastToggle').checked) return;

    let card = $('cardColor').value;
    let textCol = currentMode === 'light' ? '#0f172a' : '#f8fafc';
    let ratio = getContrastRatio(card, textCol);
    if (ratio < 2.5) {
        if (currentMode === 'light') {
            $('cardColor').value = '#cbd5e1';
        } else {
            $('cardColor').value = '#334155';
        }
        setStatus('🛡️ تم تعديل تباين البطاقات تلقائياً بواسطة مُحسّن التباين.');
    }
}

function updatePreview() {
    applyAutoContrastGuard();

    const bg = $('bgColor').value;
    const bgGrad = $('bgGradColor').value;
    const card = $('cardColor').value;
    const accent = $('accentColor').value;
    const outgoing = $('outColor').value;
    const secondary = $('secondaryColor').value;
    const opacity = Number($('opacityRange').value) / 100;

    root.style.setProperty('--bg-color', bg);
    root.style.setProperty('--bg-grad', bgGrad);
    root.style.setProperty('--card-color', card);
    root.style.setProperty('--accent-color', accent);
    root.style.setProperty('--bubble-out', outgoing);
    root.style.setProperty('--secondary-color', secondary);
    root.style.setProperty('--ui-opacity', opacity);
    $('opacityVal').textContent = Math.round(opacity * 100);

    const stopStart = $('stopGradStart');
    if (stopStart) stopStart.setAttribute('stop-color', bgGrad);

    const params = new URLSearchParams({
        bg, bgGrad, card, accent, outgoing, secondary,
        opacity: $('opacityRange').value,
        mode: currentMode
    });
    $('downloadDirectBtn').href = '/download-theme?' + params.toString();
}

['accentColor', 'bgColor', 'bgGradColor', 'cardColor', 'outColor', 'secondaryColor', 'opacityRange', 'autoContrastToggle']
    .forEach(id => $(id).addEventListener('input', updatePreview));

$('shareLinkButton').addEventListener('click', async function() {
    const bg = $('bgColor').value;
    const bgGrad = $('bgGradColor').value;
    const card = $('cardColor').value;
    const accent = $('accentColor').value;
    const outgoing = $('outColor').value;
    const secondary = $('secondaryColor').value;
    const opacity = $('opacityRange').value;

    const shareParams = new URLSearchParams({
        bg, bgGrad, card, accent, outgoing, secondary, opacity, mode: currentMode
    });
    const shareUrl = window.location.origin + window.location.pathname + '?' + shareParams.toString();

    try {
        await navigator.clipboard.writeText(shareUrl);
        setStatus('🔗 تم نسخ رابط المشاركة المباشر بنجاح!');
    } catch (e) {
        setStatus('تعذر نسخ الرابط تلقائياً.');
    }
});

function extractThemePalette(image) {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    canvas.width = 96;
    canvas.height = 96;
    ctx.drawImage(image, 0, 0, 96, 96);
    const pixels = ctx.getImageData(0, 0, 96, 96).data;
    const bins = new Map();

    for (let i = 0; i < pixels.length; i += 4) {
        const r = pixels[i], g = pixels[i + 1], b = pixels[i + 2], a = pixels[i + 3];
        if (a < 200) continue;
        const max = Math.max(r,g,b), min = Math.min(r,g,b);
        const l = (max + min) / 510;
        if (l > 0.96 || l < 0.025) continue;

        const qr = Math.round(r / 16), qg = Math.round(g / 16), qb = Math.round(b / 16);
        const key = `${qr},${qg},${qb}`;
        const old = bins.get(key) || { r: 0, g: 0, b: 0, count: 0 };
        old.r += r; old.g += g; old.b += b; old.count++;
        bins.set(key, old);
    }

    const colors = [...bins.values()]
        .filter(c => c.count >= 2)
        .sort((a, b) => b.count - a.count)
        .slice(0, 12);

    if (!colors.length) throw new Error('لم أستطع استخراج ألوان صالحة.');

    const toHex = (r, g, b) => '#' + [r, g, b].map(v => Math.round(Math.max(0, Math.min(255, v))).toString(16).padStart(2, '0')).join('');
    const dom = colors[0];
    const domR = dom.r / dom.count, domG = dom.g / dom.count, domB = dom.b / dom.count;

    const bg = toHex(domR * 0.25, domG * 0.25, domB * 0.25);
    const bgGrad = toHex(domR * 0.45, domG * 0.35, domB * 0.55);
    const card = toHex(domR * 0.4, domG * 0.4, domB * 0.4);
    const accent = toHex(domR * 1.4, domG * 1.4, 255);
    const outgoing = toHex(domR * 0.6, domG * 0.8, domB * 1.2);
    const secondary = toHex(200, 180, 220);

    return { bg, bgGrad, card, accent, outgoing, secondary };
}

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
        const wallpaperImg = $('wallpaperImage');
        wallpaperImg.setAttribute('href', dataUrl);
        wallpaperImg.setAttributeNS('http://www.w3.org/1999/xlink', 'xlink:href', dataUrl);

        const img = new Image();
        img.onload = function() {
            try {
                const palette = extractThemePalette(img);
                $('bgColor').value = palette.bg;
                $('bgGradColor').value = palette.bgGrad;
                $('cardColor').value = palette.card;
                $('accentColor').value = palette.accent;
                $('outColor').value = palette.outgoing;
                $('secondaryColor').value = palette.secondary;

                $('palettePreview').innerHTML = [
                    palette.bg, palette.bgGrad, palette.card, palette.accent, palette.secondary, palette.outgoing
                ].map(color => '<div class="color-dot" title="' + color + '" style="background:' + color + '"></div>').join('');

                updatePreview();
                setStatus('✨ تم استخراج لوحة الألوان الذكية وتطبيقها بنجاح!');
            } catch (error) {
                console.error(error);
                setStatus(error.message || 'تعذر تحليل ألوان الصورة.');
            }
        };
        img.src = dataUrl;
    };
    reader.readAsDataURL(file);
});

function currentThemeData() {
    let userId = telegramUserId;
    if (!userId && $('manualChatId')) {
        userId = $('manualChatId').value.trim();
    }
    return {
        bg: $('bgColor').value,
        bgGrad: $('bgGradColor').value,
        card: $('cardColor').value,
        accent: $('accentColor').value,
        outgoing: $('outColor').value,
        secondary: $('secondaryColor').value,
        opacity: Number($('opacityRange').value),
        mode: currentMode,
        user_id: userId
    };
}

$('copyButton').addEventListener('click', async function() {
    const d = currentThemeData();
    const text = [
        'Background=' + d.bg,
        'Card=' + d.card,
        'Accent=' + d.accent,
        'Outgoing=' + d.outgoing,
        'Secondary=' + d.secondary
    ].join('\n');

    try {
        await navigator.clipboard.writeText(text);
        setStatus('📋 تم نسخ أكواد الألوان.');
    } catch (error) {
        setStatus('تعذر النسخ تلقائياً.');
    }
});

$('sendTelegramBtn').addEventListener('click', async function() {
    const data = currentThemeData();
    if (!data.user_id) {
        setStatus('⚠️ يرجى إدخال معرف تيليجرام (Chat ID) أولاً.');
        $('chatIdContainer').style.display = 'flex';
        return;
    }

    $('sendTelegramBtn').disabled = true;
    setStatus('⏳ جارٍ إرسال الثيم إلى دردشتك في البوت...');

    try {
        const response = await fetch('/generate-custom-theme', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        const resJson = await response.json();
        if (resJson.success) {
            setStatus('✅ تم إرسال ملف الثيم إلى محادثتك في البوت بنجاح!');
            setTimeout(() => { if (tg && typeof tg.close === 'function') tg.close(); }, 2000);
        } else {
            setStatus('❌ فشل الإرسال: ' + (resJson.error || 'خطأ غير معروف'));
        }
    } catch (error) {
        setStatus('❌ خطأ في الاتصال: ' + error.message);
    } finally {
        $('sendTelegramBtn').disabled = false;
    }
});

function setStatus(msg) {
    $('statusMessage').textContent = msg;
}

updatePreview();
</script>
</body>
</html>"""


def hex_to_signed_int(hex_str, alpha=255):
    try:
        hex_str = str(hex_str).strip().lstrip("#")
        if len(hex_str) == 3:
            hex_str = "".join([c*2 for c in hex_str])
        if len(hex_str) != 6:
            hex_str = "0f172a"
        r = int(hex_str[0:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:6], 16)
        value = (alpha << 24) | (r << 16) | (g << 8) | b
        if value > 0x7FFFFFFF:
            value -= 0x100000000
        return value
    except Exception:
        return -9868954 # Default safe color int


def build_theme_content(bg_hex, card_hex, accent_hex, outgoing_hex, secondary_hex, opacity_val, mode="dark"):
    bubble_alpha = round((opacity_val / 100.0) * 255)

    c_bg = hex_to_signed_int(bg_hex)
    c_card = hex_to_signed_int(card_hex)
    c_accent = hex_to_signed_int(accent_hex)
    c_outgoing = hex_to_signed_int(outgoing_hex)
    c_secondary = hex_to_signed_int(secondary_hex)
    
    c_bubble_in = hex_to_signed_int(card_hex, alpha=bubble_alpha)
    c_bubble_out = hex_to_signed_int(outgoing_hex, alpha=bubble_alpha)
    
    c_selected = hex_to_signed_int("#cbd5e1" if mode == "light" else "#334155")
    c_text_main = hex_to_signed_int("#0f172a") if mode == "light" else c_accent

    theme_keys = {
        "WallpaperFileOffset": -1,
        "windowBackgroundWhite": c_bg,
        "windowBackgroundGray": c_bg,
        "windowBackgroundGrayShadow": 0,
        "dialogBackground": c_card,
        "dialogBackgroundGray": c_card,
        "windowBackgroundWhiteBlackText": c_text_main,
        "windowBackgroundWhiteGrayText": c_secondary,
        "dialogTextBlack": c_text_main,
        "actionBarActionModeDefault": c_bg,
        "actionBarActionModeDefaultIcon": c_accent,
        "actionBarActionModeDefaultSelector": c_accent,
        "actionBarActionModeDefaultTop": c_bg,
        "actionBarDefault": c_bg,
        "actionBarDefaultArchived": c_bg,
        "actionBarDefaultArchivedIcon": c_accent,
        "actionBarDefaultArchivedSearch": c_accent,
        "actionBarDefaultArchivedSelector": c_accent,
        "actionBarDefaultArchivedTitle": c_accent,
        "actionBarDefaultIcon": c_accent,
        "actionBarDefaultSearch": c_accent,
        "actionBarDefaultSearchArchivedPlaceholder": c_accent,
        "actionBarDefaultSearchPlaceholder": c_accent,
        "actionBarDefaultSelector": c_accent,
        "actionBarDefaultSubmenuBackground": c_card,
        "actionBarDefaultSubmenuItem": c_accent,
        "actionBarDefaultSubtitle": c_secondary,
        "actionBarDefaultTitle": c_text_main,
        "actionBarWhiteSelector": c_secondary,
        "avatar_actionBarIconBlue": c_accent,
        "avatar_actionBarIconCyan": c_accent,
        "avatar_actionBarIconGreen": c_accent,
        "avatar_actionBarIconOrange": c_accent,
        "avatar_actionBarIconPink": c_accent,
        "avatar_actionBarIconRed": c_accent,
        "avatar_actionBarIconViolet": c_accent,
        "avatar_actionBarSelectorBlue": c_accent,
        "avatar_actionBarSelectorCyan": c_accent,
        "avatar_actionBarSelectorGreen": c_accent,
        "avatar_actionBarSelectorOrange": c_accent,
        "avatar_actionBarSelectorPink": c_accent,
        "avatar_actionBarSelectorRed": c_accent,
        "avatar_actionBarSelectorViolet": c_accent,
        "avatar_backgroundActionBarBlue": c_bg,
        "avatar_backgroundActionBarCyan": c_bg,
        "avatar_backgroundActionBarGreen": c_bg,
        "avatar_backgroundActionBarOrange": c_bg,
        "avatar_backgroundActionBarPink": c_bg,
        "avatar_backgroundActionBarRed": c_bg,
        "avatar_backgroundActionBarViolet": c_bg,
        "avatar_backgroundArchived": c_accent,
        "avatar_backgroundArchivedHidden": c_accent,
        "avatar_backgroundBlue": c_accent,
        "avatar_backgroundBlueShadow": c_secondary,
        "avatar_backgroundCyan": c_accent,
        "avatar_backgroundCyanShadow": c_secondary,
        "avatar_backgroundGreen": c_accent,
        "avatar_backgroundGreenShadow": c_secondary,
        "avatar_backgroundGroupCreateSpanBlue": c_accent,
        "avatar_backgroundInProfileBlue": c_accent,
        "avatar_backgroundInProfileCyan": c_accent,
        "avatar_backgroundInProfileGreen": c_accent,
        "avatar_backgroundInProfileOrange": c_accent,
        "avatar_backgroundInProfilePink": c_accent,
        "avatar_backgroundInProfileRed": c_accent,
        "avatar_backgroundInProfileViolet": c_accent,
        "avatar_backgroundOrange": c_accent,
        "avatar_backgroundOrangeShadow": c_secondary,
        "avatar_backgroundPink": c_accent,
        "avatar_backgroundRed": c_accent,
        "avatar_backgroundRedShadow": c_secondary,
        "avatar_backgroundSaved": c_accent,
        "avatar_backgroundViolet": c_accent,
        "avatar_backgroundVioletShadow": c_secondary,
        "avatar_nameInMessageBlue": c_accent,
        "avatar_nameInMessageCyan": c_accent,
        "avatar_nameInMessageGreen": c_accent,
        "avatar_nameInMessageOrange": c_accent,
        "avatar_nameInMessagePink": c_accent,
        "avatar_nameInMessageRed": c_accent,
        "avatar_nameInMessageViolet": c_accent,
        "avatar_subtitleInProfileBlue": c_accent,
        "avatar_subtitleInProfileCyan": c_accent,
        "avatar_subtitleInProfileGreen": c_accent,
        "avatar_subtitleInProfileOrange": c_accent,
        "avatar_subtitleInProfilePink": c_accent,
        "avatar_subtitleInProfileRed": c_accent,
        "avatar_subtitleInProfileViolet": c_accent,
        "avatar_text": c_bg,
        "calls_callReceivedGreenIcon": c_accent,
        "calls_callReceivedRedIcon": c_accent,
        "changephoneinfo_image": c_secondary,
        "chat_addContact": c_accent,
        "chat_adminSelectedText": c_accent,
        "chat_adminText": c_accent,
        "chat_attachAudioBackground": c_secondary,
        "chat_attachAudioIcon": c_bg,
        "chat_attachCameraIcon1": c_secondary,
        "chat_attachCameraIcon2": c_secondary,
        "chat_attachCameraIcon3": c_secondary,
        "chat_attachCameraIcon4": c_secondary,
        "chat_attachCameraIcon5": c_secondary,
        "chat_attachCameraIcon6": c_secondary,
        "chat_attachContactBackground": c_secondary,
        "chat_attachContactIcon": c_bg,
        "chat_attachFileBackground": c_secondary,
        "chat_attachFileIcon": c_bg,
        "chat_attachGalleryBackground": c_secondary,
        "chat_attachGalleryIcon": c_bg,
        "chat_attachHideBackground": c_secondary,
        "chat_attachHideIcon": c_bg,
        "chat_attachLocationBackground": c_secondary,
        "chat_attachLocationIcon": c_bg,
        "chat_attachMediaBanBackground": c_secondary,
        "chat_attachMediaBanText": c_bg,
        "chat_attachSendBackground": c_secondary,
        "chat_attachSendIcon": c_bg,
        "chat_attachVideoBackground": c_secondary,
        "chat_attachVideoIcon": c_bg,
        "chat_botButtonText": c_accent,
        "chat_botKeyboardButtonBackground": c_accent,
        "chat_botKeyboardButtonBackgroundPressed": c_secondary,
        "chat_botKeyboardButtonText": c_bg,
        "chat_botProgress": c_accent,
        "chat_botSwitchToInlineText": c_secondary,
        "chat_editDoneIcon": c_accent,
        "chat_emojiPanelBackground": c_bg,
        "chat_emojiPanelBackspace": c_accent,
        "chat_emojiPanelBadgeBackground": c_accent,
        "chat_emojiPanelBadgeText": c_bg,
        "chat_emojiPanelEmptyText": c_accent,
        "chat_emojiPanelIcon": c_secondary,
        "chat_emojiPanelIconSelected": c_accent,
        "chat_emojiPanelIconSelector": c_accent,
        "chat_emojiPanelMasksIcon": c_secondary,
        "chat_emojiPanelMasksIconSelected": c_accent,
        "chat_emojiPanelNewTrending": c_accent,
        "chat_emojiPanelShadowLine": c_bg,
        "chat_emojiPanelStickerPackSelector": c_selected,
        "chat_emojiPanelStickerSetName": c_secondary,
        "chat_emojiPanelStickerSetNameIcon": c_accent,
        "chat_emojiPanelTrendingDescription": c_accent,
        "chat_emojiPanelTrendingTitle": c_accent,
        "chat_emojiSearchBackground": c_accent,
        "chat_fieldOverlayText": c_accent,
        "chat_goDownButton": c_bg,
        "chat_goDownButtonCounter": c_accent,
        "chat_goDownButtonCounterBackground": c_bg,
        "chat_goDownButtonIcon": c_accent,
        "chat_goDownButtonShadow": c_accent,
        "chat_inAudioDurationSelectedText": c_secondary,
        "chat_inAudioDurationText": c_secondary,
        "chat_inAudioPerfomerSelectedText": c_secondary,
        "chat_inAudioPerfomerText": c_secondary,
        "chat_inAudioPerformerSelectedText": c_secondary,
        "chat_inAudioProgress": c_bg,
        "chat_inAudioSeekbar": c_secondary,
        "chat_inAudioSeekbarFill": c_accent,
        "chat_inAudioSeekbarSelected": c_secondary,
        "chat_inAudioSelectedProgress": c_bg,
        "chat_inAudioTitleText": c_text_main,
        "chat_inBubble": c_bubble_in,
        "chat_inBubbleSelected": c_selected,
        "chat_inBubbleShadow": c_secondary,
        "chat_inContactBackground": c_accent,
        "chat_inContactIcon": c_bg,
        "chat_inContactNameText": c_accent,
        "chat_inContactPhoneText": c_accent,
        "chat_inFileBackground": c_bg,
        "chat_inFileBackgroundSelected": c_bg,
        "chat_inFileIcon": c_accent,
        "chat_inFileInfoSelectedText": c_accent,
        "chat_inFileInfoText": c_accent,
        "chat_inFileNameText": c_text_main,
        "chat_inFileProgress": c_bg,
        "chat_inFileProgressSelected": c_bg,
        "chat_inFileSelectedIcon": c_accent,
        "chat_inForwardedNameText": c_accent,
        "chat_inInstant": c_accent,
        "chat_inInstantSelected": c_accent,
        "chat_inlineResultIcon": c_accent,
        "chat_inLoader": c_accent,
        "chat_inLoaderPhoto": c_bg,
        "chat_inLoaderPhotoIcon": c_accent,
        "chat_inLoaderPhotoIconSelected": c_accent,
        "chat_inLoaderPhotoSelected": c_bg,
        "chat_inLoaderSelected": c_secondary,
        "chat_inLocationBackground": c_bg,
        "chat_inLocationIcon": c_bg,
        "chat_inMenu": c_accent,
        "chat_inMenuSelected": c_accent,
        "chat_inPreviewInstantSelectedText": c_accent,
        "chat_inPreviewInstantText": c_accent,
        "chat_inPreviewLine": c_accent,
        "chat_inReplyLine": c_accent,
        "chat_inReplyMediaMessageSelectedText": c_accent,
        "chat_inReplyMediaMessageText": c_accent,
        "chat_inReplyMessageText": c_accent,
        "chat_inReplyNameText": c_accent,
        "chat_inSentClock": c_accent,
        "chat_inSentClockSelected": c_accent,
        "chat_inSiteNameText": c_accent,
        "chat_inTimeSelectedText": c_secondary,
        "chat_inTimeText": c_secondary,
        "chat_inVenueInfoSelectedText": c_secondary,
        "chat_inVenueInfoText": c_secondary,
        "chat_inVenueNameText": c_secondary,
        "chat_inViaBotNameText": c_accent,
        "chat_inViews": c_accent,
        "chat_inViewsSelected": c_accent,
        "chat_inVoiceSeekbar": c_secondary,
        "chat_inVoiceSeekbarFill": c_accent,
        "chat_inVoiceSeekbarSelected": c_secondary,
        "chat_linkSelectBackground": c_selected,
        "chat_lockIcon": c_accent,
        "chat_mediaLoaderPhotoIcon": c_accent,
        "chat_mediaLoaderPhotoIconSelected": c_accent,
        "chat_mediaTimeText": c_text_main,
        "chat_messageLinkIn": c_secondary,
        "chat_messageLinkOut": c_secondary,
        "chat_messagePanelBackground": c_bg,
        "chat_messagePanelCancelInlineBot": c_accent,
        "chat_messagePanelHint": c_secondary,
        "chat_messagePanelIcons": c_accent,
        "ChatShadow": c_accent,
        "chat_messagePanelSend": c_accent,
        "chat_messagePanelShadow": c_bg,
        "chat_messagePanelText": c_text_main,
        "chat_messagePanelVoiceBackground": c_bg,
        "chat_messagePanelVoiceDelete": c_accent,
        "chat_messagePanelVoiceDuration": c_accent,
        "chat_messagePanelVoicePressed": c_accent,
        "chat_messagePanelVoiceShadow": c_secondary,
        "chat_messageTextIn": c_text_main,
        "chat_messageTextOut": c_text_main,
        "chat_muteIcon": c_accent,
        "chat_outAudioDurationSelectedText": c_secondary,
        "chat_outAudioDurationText": c_secondary,
        "chat_outAudioPerfomerText": c_secondary,
        "chat_outAudioPerformerSelectedText": c_secondary,
        "chat_outAudioProgress": c_bg,
        "chat_outAudioSeekbar": c_secondary,
        "chat_outAudioSeekbarFill": c_accent,
        "chat_outAudioSeekbarSelected": c_secondary,
        "chat_outAudioSelectedProgress": c_bg,
        "chat_outAudioTitleText": c_text_main,
        "chat_outBubble": c_bubble_out,
        "chat_outBubbleSelected": c_selected,
        "chat_outBubbleShadow": c_secondary,
        "chat_outContactBackground": c_accent,
        "chat_outContactIcon": c_bg,
        "chat_outContactNameText": c_accent,
        "chat_outContactPhoneText": c_accent,
        "chat_outFileBackground": c_bg,
        "chat_outFileBackgroundSelected": c_bg,
        "chat_outFileIcon": c_accent,
        "chat_outFileInfoSelectedText": c_accent,
        "chat_outFileInfoText": c_accent,
        "chat_outFileNameText": c_text_main,
        "chat_outFileProgress": c_bg,
        "chat_outFileProgressSelected": c_bg,
        "chat_outFileSelectedIcon": c_accent,
        "chat_outForwardedNameText": c_accent,
        "chat_outInstant": c_accent,
        "chat_outInstantSelected": c_accent,
        "chat_outLoader": c_accent,
        "chat_outLoaderPhoto": c_bg,
        "chat_outLoaderPhotoIcon": c_accent,
        "chat_outLoaderPhotoIconSelected": c_accent,
        "chat_outLoaderPhotoSelected": c_bg,
        "chat_outLoaderSelected": c_secondary,
        "chat_outLocationBackground": c_bg,
        "chat_outLocationIcon": c_bg,
        "chat_outMenu": c_accent,
        "chat_outMenuSelected": c_accent,
        "chat_outPreviewInstantSelectedText": c_accent,
        "chat_outPreviewInstantText": c_accent,
        "chat_outPreviewLine": c_accent,
        "chat_outReplyLine": c_accent,
        "chat_outReplyMediaMessageSelectedText": c_accent,
        "chat_outReplyMediaMessageText": c_accent,
        "chat_outReplyMessageText": c_accent,
        "chat_outReplyNameText": c_accent,
        "chat_outSentCheck": c_accent,
        "chat_outSentCheckSelected": c_accent,
        "chat_outSentClock": c_accent,
        "chat_outSentClockSelected": c_accent,
        "chat_outSiteNameText": c_accent,
        "chat_outTimeSelectedText": c_secondary,
        "chat_outTimeText": c_secondary,
        "chat_outVenueInfoSelectedText": c_secondary,
        "chat_outVenueInfoText": c_secondary,
        "chat_outVenueNameText": c_secondary,
        "chat_outViaBotNameText": c_accent,
        "chat_outViews": c_accent,
        "chat_outViewsSelected": c_accent,
        "chat_outVoiceSeekbar": c_secondary,
        "chat_outVoiceSeekbarFill": c_accent,
        "chat_outVoiceSeekbarSelected": c_secondary,
        "chat_previewDurationText": c_accent,
        "chat_previewGameText": c_accent,
        "chat_recordedVoiceBackground": c_bg,
        "chat_recordedVoiceDot": c_accent,
        "chat_recordedVoicePlayPause": c_accent,
        "chat_recordedVoicePlayPausePressed": c_secondary,
        "chat_recordedVoiceProgress": c_secondary,
        "chat_recordedVoiceProgressInner": c_accent,
        "chat_recordTime": c_accent,
        "chat_recordVoiceCancel": c_accent,
        "chat_replyPanelClose": c_accent,
        "chat_replyPanelIcons": c_accent,
        "chat_replyPanelLine": c_accent,
        "chat_replyPanelMessage": c_accent,
        "chat_replyPanelName": c_accent,
        "chat_reportSpam": c_accent,
        "chat_searchPanelIcons": c_accent,
        "chat_searchPanelText": c_accent,
        "chat_secretTimerBackground": c_bg,
        "chat_secretTimerText": c_bg,
        "chat_secretTimeText": c_accent,
        "chat_selectedBackground": c_selected,
        "chat_sentError": c_accent,
        "chat_sentErrorIcon": c_bg,
        "chat_serviceBackground": c_card,
        "chat_serviceBackgroundSelected": c_card,
        "chat_serviceIcon": c_accent,
        "chat_serviceLink": c_accent,
        "chat_serviceText": c_accent,
        "chat_stickerReplyLine": c_accent,
        "chat_stickerReplyMessageText": c_accent,
        "chat_stickerReplyNameText": c_accent,
        "chat_stickersHintPanel": c_bg,
        "chat_stickerViaBotNameText": c_accent,
        "chat_textSelectBackground": c_selected,
        "chat_topPanelBackground": c_bg,
        "chat_topPanelClose": c_accent,
        "chat_topPanelLine": c_accent,
        "chat_topPanelMessage": c_accent,
        "chat_topPanelTitle": c_accent,
        "chat_unreadMessagesStartArrowIcon": c_accent,
        "chat_unreadMessagesStartBackground": c_bg,
        "chat_unreadMessagesStartText": c_accent,
        "chats_actionBackground": c_accent,
        "chats_actionIcon": c_bg,
        "chats_actionMessage": c_secondary,
        "chats_actionPressedBackground": c_accent,
        "chats_archiveBackground": c_accent,
        "chats_archiveIcon": c_bg,
        "chats_archivePinBackground": c_bg,
        "chats_archiveText": c_bg,
        "chats_attachMessage": c_secondary,
        "chats_date": c_accent,
        "chats_draft": c_accent,
        "chats_mentionIcon": c_bg,
        "chats_menuBackground": c_bg,
        "chats_menuCloud": c_accent,
        "chats_menuCloudBackgroundCats": c_accent,
        "chats_menuItemCheck": c_bg,
        "chats_menuItemIcon": c_accent,
        "chats_menuItemText": c_accent,
        "chats_menuName": c_text_main,
        "chats_menuPhone": c_accent,
        "chats_menuPhoneCats": c_accent,
        "chats_menuTopShadow": c_selected,
        "chats_message": c_secondary,
        "chats_message_threeLines": c_accent,
        "chats_muteIcon": c_accent,
        "chats_name": c_text_main,
        "chats_nameArchived": c_text_main,
        "chats_nameIcon": c_accent,
        "chats_nameMessage": c_text_main,
        "chats_nameMessage_threeLines": c_text_main,
        "chats_nameMessageArchived": c_text_main,
        "chats_nameMessageArchived_threeLines": c_text_main,
        "chats_pinnedIcon": c_accent,
        "chats_pinnedOverlay": c_bg,
        "chats_secretIcon": c_accent,
        "chats_secretName": c_accent,
        "chats_sentCheck": c_accent,
        "chats_sentClock": c_accent,
        "chats_sentError": c_accent,
        "chats_sentErrorIcon": c_bg,
        "chats_tabletSelectedOverlay": c_accent,
        "chats_unreadCounter": c_accent,
        "chats_unreadCounterMuted": c_secondary,
        "chats_unreadCounterText": c_bg,
        "chats_verifiedBackground": c_accent,
        "chats_verifiedCheck": c_bg,
        "checkbox": c_accent,
        "checkboxCheck": c_bg,
        "checkboxSquareBackground": c_accent,
        "checkboxSquareCheck": c_bg,
        "checkboxSquareDisabled": c_secondary,
        "checkboxSquareUnchecked": c_accent,
        "contacts_inviteBackground": c_bg,
        "contacts_inviteText": c_accent,
        "contextProgressInner1": c_secondary,
        "contextProgressOuter1": c_accent,
        "dialogBackground": c_bg,
        "dialogBackgroundGray": c_bg,
        "dialogBadgeBackground": c_accent,
        "dialogBadgeText": c_bg,
        "dialogButton": c_accent,
        "dialogButtonSelector": c_selected,
        "dialogCheckboxSquareBackground": c_accent,
        "dialogCheckboxSquareCheck": c_bg,
        "dialogCheckboxSquareDisabled": c_accent,
        "dialogCheckboxSquareUnchecked": c_accent,
        "dialogFloatingButton": c_accent,
        "dialogFloatingButtonPressed": c_bg,
        "dialogFloatingIcon": c_bg,
        "dialogGrayLine": c_accent,
        "dialogIcon": c_accent,
        "dialogInputField": c_accent,
        "dialogInputFieldActivated": c_bg,
        "dialogLineProgress": c_accent,
        "dialogLineProgressBackground": c_secondary,
        "dialogLinkSelection": c_selected,
        "dialogProgressCircle": c_accent,
        "dialogRadioBackground": c_bg,
        "dialogRadioBackgroundChecked": c_accent,
        "dialogRoundCheckBox": c_accent,
        "dialogRoundCheckBoxCheck": c_bg,
        "dialogScrollGlow": c_accent,
        "dialogSearchBackground": c_selected,
        "dialogSearchHint": c_secondary,
        "dialogSearchIcon": c_secondary,
        "dialogSearchText": c_accent,
        "dialogShadowLine": c_secondary,
        "dialogTextBlack": c_text_main,
        "dialogTextBlue2": c_accent,
        "dialogTextBlue3": c_accent,
        "dialogTextBlue4": c_accent,
        "dialogTextBlue": c_accent,
        "dialogTextGray2": c_accent,
        "dialogTextGray": c_accent,
        "dialogTextLink": c_accent,
        "dialogTextRed": c_accent,
        "divider": c_selected,
        "emptyListPlaceholder": c_secondary,
        "fastScrollActive": c_accent,
        "fastScrollInactive": c_secondary,
        "fastScrollText": c_bg,
        "featuredStickers_addButton": c_accent,
        "featuredStickers_addButtonPressed": c_secondary,
        "featuredStickers_addedIcon": c_accent,
        "featuredStickers_buttonText": c_bg,
        "files_folderIcon": c_secondary,
        "files_folderIconBackground": c_bg,
        "files_iconText": c_bg,
        "graySection": c_bg,
        "groupcreate_checkbox": c_accent,
        "groupcreate_checkboxCheck": c_bg,
        "groupcreate_cursor": c_accent,
        "groupcreate_hintText": c_accent,
        "groupcreate_offlineText": c_accent,
        "groupcreate_onlineText": c_accent,
        "groupcreate_sectionShadow": c_bg,
        "groupcreate_sectionText": c_accent,
        "groupcreate_spanBackground": c_accent,
        "inappPlayerBackground": c_bg,
        "inappPlayerClose": c_accent,
        "inappPlayerPerformer": c_accent,
        "inappPlayerPlayPause": c_accent,
        "inappPlayerTitle": c_accent,
        "key_chat_messagePanelVoiceLock": c_accent,
        "key_chat_messagePanelVoiceLockBackground": c_bg,
        "key_chat_messagePanelVoiceLockShadow": c_bg,
        "key_sheet_other": c_accent,
        "key_sheet_scrollUp": c_accent,
        "listSelectorSDK21": c_accent,
        "location_liveLocationProgress": c_secondary,
        "location_placeLocationBackground": c_secondary,
        "location_sendLiveLocationBackground": c_secondary,
        "location_sendLocationBackground": c_secondary,
        "location_sendLocationIcon": c_bg,
        "musicPicker_buttonBackground": c_bg,
        "musicPicker_buttonIcon": c_secondary,
        "musicPicker_checkbox": c_secondary,
        "musicPicker_checkboxCheck": c_bg,
        "picker_badge": c_accent,
        "picker_badgeText": c_bg,
        "picker_disabledButton": c_secondary,
        "picker_enabledButton": c_accent,
        "player_actionBar": c_bg,
        "player_actionBarItems": c_accent,
        "player_actionBarSelector": c_accent,
        "player_actionBarSubtitle": c_accent,
        "player_actionBarTitle": c_accent,
        "player_actionBarTop": c_bg,
        "player_background": c_bg,
        "player_button": c_accent,
        "player_buttonActive": c_secondary,
        "player_placeholder": c_accent,
        "player_placeholderBackground": c_bg,
        "player_progress": c_accent,
        "player_progressBackground": c_secondary,
        "player_time": c_accent,
        "profile_actionBackground": c_bg,
        "profile_actionIcon": c_accent,
        "profile_actionPressedBackground": c_accent,
        "profile_adminIcon": c_secondary,
        "profile_creatorIcon": c_accent,
        "profile_title": c_accent,
        "profile_verifiedBackground": c_accent,
        "profile_verifiedCheck": c_bg,
        "progressCircle": c_accent,
        "radioBackground": c_accent,
        "radioBackgroundChecked": c_accent,
        "returnToCallBackground": c_bg,
        "returnToCallText": c_accent,
        "sessions_devicesImage": c_secondary,
        "sharedMedia_actionMode": c_bg,
        "sharedMedia_startStopLoadIcon": c_accent,
        "stickers_menu": c_accent,
        "stickers_menuSelector": c_accent,
        "switch2Check": c_bg,
        "switch2Thumb": c_secondary,
        "switch2ThumbChecked": c_secondary,
        "switch2Track": c_accent,
        "switch2TrackChecked": c_secondary,
        "switchThumb": 0,
        "switchThumbChecked": 0,
        "switchTrack": c_accent,
        "switchTrackChecked": c_secondary,
        "undo_background": c_accent,
        "undo_cancelColor": c_bg,
        "undo_infoColor": c_bg,
        "windowBackgroundGray": c_bg,
        "windowBackgroundGrayShadow": 0,
        "windowBackgroundWhite": c_bg,
        "PreviewBackLinear": c_secondary,
        "PreviewBackLinearShadow": c_bg,
        "windowBackgroundWhiteBlackText": c_text_main,
        "windowBackgroundWhiteBlueHeader": c_accent,
        "windowBackgroundWhiteBlueText3": c_accent,
        "windowBackgroundWhiteBlueText4": c_accent,
        "windowBackgroundWhiteBlueText6": c_secondary,
        "windowBackgroundWhiteBlueText7": c_secondary,
        "windowBackgroundWhiteBlueText": c_accent,
        "windowBackgroundWhiteGrayIcon": c_accent,
        "windowBackgroundWhiteGrayText2": c_secondary,
        "windowBackgroundWhiteGrayText3": c_secondary,
        "windowBackgroundWhiteGrayText4": c_secondary,
        "windowBackgroundWhiteGrayText8": c_secondary,
        "windowBackgroundWhiteGrayText": c_text_main,
        "windowBackgroundWhiteGreenText2": c_accent,
        "windowBackgroundWhiteLinkSelection": c_selected,
        "windowBackgroundWhiteLinkText": c_secondary,
        "windowBackgroundWhiteRedText2": c_accent,
        "windowBackgroundWhiteRedText3": c_accent,
        "windowBackgroundWhiteRedText4": c_accent,
        "windowBackgroundWhiteRedText5": c_accent,
        "windowBackgroundWhiteRedText6": c_accent,
        "windowBackgroundWhiteRedText": c_accent,
        "windowBackgroundWhiteValueText": c_secondary,
        "PreviewBack": c_secondary
    }

    return "\n".join(f"{key}={value}" for key, value in theme_keys.items()) + "\n"

@app.route("/")
def home():
    return "Advanced Telegram Theme Mini App is running stably."

@app.route("/webapp")
def webapp():
    return render_template_string(HTML_TEMPLATE)

@app.route("/download-theme", methods=["GET"])
def download_theme():
    bg_hex = request.args.get("bg", "#0f172a")
    card_hex = request.args.get("card", "#1e293b")
    accent_hex = request.args.get("accent", "#38bdf8")
    outgoing_hex = request.args.get("outgoing", "#0284c7")
    secondary_hex = request.args.get("secondary", "#B997D0")
    opacity_val = int(request.args.get("opacity", 90))
    mode = request.args.get("mode", "dark")

    file_content = build_theme_content(
        bg_hex, card_hex, accent_hex, outgoing_hex, secondary_hex, opacity_val, mode
    )
    return Response(
        file_content,
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment;filename=Custom_Smart_Theme.attheme"}
    )

@app.route("/generate-custom-theme", methods=["POST"])
def generate_custom_theme():
    req_data = request.get_json(silent=True) or {}
    bg_hex = req_data.get("bg", "#0f172a")
    bg_grad = req_data.get("bgGrad", "#2D223B")
    card_hex = req_data.get("card", "#1e293b")
    accent_hex = req_data.get("accent", "#38bdf8")
    outgoing_hex = req_data.get("outgoing", "#0284c7")
    secondary_hex = req_data.get("secondary", "#B997D0")
    opacity_val = int(req_data.get("opacity", 90))
    mode = req_data.get("mode", "dark")
    user_id = req_data.get("user_id")

    if not user_id:
        return jsonify({"success": False, "error": "معرف تيليجرام غير متوفر."}), 400

    save_theme_to_db(user_id, bg_hex, bg_grad, card_hex, accent_hex, outgoing_hex, secondary_hex, opacity_val, mode)

    file_content = build_theme_content(
        bg_hex, card_hex, accent_hex, outgoing_hex, secondary_hex, opacity_val, mode
    )
    
    file_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".attheme", prefix="custom_theme_", delete=False
        ) as handle:
            file_path = handle.name
            handle.write(file_content)

        url = f"https://api.telegram.org/bot{TOKEN}/sendDocument"
        with open(file_path, "rb") as f:
            files = {"document": ("Custom_Smart_Theme.attheme", f)}
            data = {
                "chat_id": user_id, 
                "caption": "✨ تفضل ملف الثيم الشامل بكافة مفاتيحه، وتم حفظ تفاصيل الثيم في قاعدة البيانات بنجاح!"
            }
            resp = requests.post(url, data=data, files=files)
            if not resp.ok:
                try:
                    err_desc = resp.json().get("description", resp.text)
                except:
                    err_desc = resp.text
                return jsonify({"success": False, "error": err_desc}), 400

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    base_url = os.environ.get("RENDER_EXTERNAL_URL", "").rstrip("/")
    if not base_url:
        await message.answer("عذراً، رابط الخدمة غير مضبوط على Render.")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎨 افتح صانع الثيمات الذكي",
            web_app=WebAppInfo(url=f"{base_url}/webapp")
        )]
    ])
    await message.answer(
        "✨ أهلاً بك في صانع ثيمات تيليجرام المتطور!\n\n"
        "الكود محمي الآن بالكامل ضد الأخطاء وجاهز للاستخدام:",
        reply_markup=keyboard
    )

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, use_reloader=False, threaded=True)

async def main():
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logging.info("Flask Mini App and Telegram bot are running securely.")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
