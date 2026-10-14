import os
import logging
import asyncio
import threading
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
.range-label { display:flex; justify-content:space-between; gap:8px; }
.btn-row { display:flex; gap:10px; margin-top:16px; }
.btn {
    flex:1; background:var(--accent-color); color:#0f172a;
    border:none; padding:12px 9px; border-radius:12px;
    font-size:13px; font-weight:bold; cursor:pointer;
    text-align: center; text-decoration: none; display: inline-block;
}
.btn.secondary { background:rgba(255,255,255,.1); color:var(--text-color); }
.status { font-size:12px; text-align:center; color: var(--accent-color); margin-top:10px; font-weight: bold; word-break: break-all; }
@media (max-width: 380px) {
    body { padding: 10px; }
    .btn-row { flex-direction: column; }
}
</style>
</head>
<body>
<h2>🎨 صانع ثيمات تيليجرام الذكي</h2>

<label class="upload-box">
    📁 اضغط لاختيار صورة (استخراج ألوان ذكي وتطبيقها كخلفية حية)
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

<g transform="translate(75 75)" filter="url(#previewShadow)">
<rect width="420" height="910" rx="48" fill="var(--bg-color)" stroke="var(--card-color)" stroke-width="5"/>
<g clip-path="url(#leftClip)">
<image id="wallpaperImage" href="" width="420" height="910" preserveAspectRatio="xMidYMid slice" opacity="0.85"/>
<rect width="420" height="910" fill="var(--bg-color)" opacity="0.45"/>
<rect width="420" height="95" fill="var(--bg-color)" opacity="0.9"/>
<circle cx="50" cy="55" r="12" fill="var(--accent-color)"/>
<rect x="75" y="45" width="110" height="12" rx="6" fill="var(--text-color)"/>
<rect x="75" y="63" width="60" height="8" rx="4" fill="var(--secondary-color)"/>
<circle cx="375" cy="55" r="10" fill="var(--accent-color)"/>
</g></g>
</svg>
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
        <a class="btn" id="downloadDirectBtn" href="#" target="_blank">📥 تحميل الثيم مباشرة</a>
    </div>
    <div class="btn-row" style="margin-top:10px;">
        <button class="btn" id="sendTelegramBtn" type="button">🚀 إرسال الثيم إلى البوت</button>
    </div>
    <div class="status" id="statusMessage" role="status"></div>
</div>

<script>
const tg = window.Telegram && window.Telegram.WebApp;
if (tg) { tg.ready(); tg.expand(); }
const $ = (id) => document.getElementById(id);
const root = document.documentElement;
let telegramUserId = tg && tg.initDataUnsafe && tg.initDataUnsafe.user ? tg.initDataUnsafe.user.id : null;
if (!telegramUserId) { $('chatIdContainer').style.display = 'flex'; }

function updatePreview() {
    const bg = $('bgColor').value;
    const card = $('cardColor').value;
    const accent = $('accentColor').value;
    const outgoing = $('outColor').value;
    const secondary = $('secondaryColor').value;
    const opacity = Number($('opacityRange').value) / 100;

    root.style.setProperty('--bg-color', bg);
    root.style.setProperty('--card-color', card);
    root.style.setProperty('--accent-color', accent);
    root.style.setProperty('--bubble-out', outgoing);
    root.style.setProperty('--secondary-color', secondary);
    root.style.setProperty('--ui-opacity', opacity);
    $('opacityVal').textContent = Math.round(opacity * 100);

    const params = new URLSearchParams({
        bg: bg, card: card, accent: accent, outgoing: outgoing, secondary: secondary, opacity: $('opacityRange').value
    });
    $('downloadDirectBtn').href = '/download-theme?' + params.toString();
}

['accentColor', 'bgColor', 'cardColor', 'outColor', 'secondaryColor', 'opacityRange']
    .forEach(id => $(id).addEventListener('input', updatePreview));

function rgbToHsl(r, g, b) {
    r /= 255; g /= 255; b /= 255;
    const max = Math.max(r, g, b), min = Math.min(r, g, b);
    let h = 0, s = 0, l = (max + min) / 2;
    const delta = max - min;
    if (delta !== 0) {
        s = delta / (1 - Math.abs(2 * l - 1));
        if (max === r) h = ((g - b) / delta) % 6;
        else if (max === g) h = (b - r) / delta + 2;
        else h = (r - g) / delta + 4;
        h *= 60; if (h < 0) h += 360;
    }
    return { h, s, l };
}

function hslToHex(h, s, l) {
    s = Math.max(0, Math.min(1, s)); l = Math.max(0, Math.min(1, l));
    const c = (1 - Math.abs(2 * l - 1)) * s, x = c * (1 - Math.abs((h / 60) % 2 - 1)), m = l - c / 2;
    let rgb;
    if (h < 60) rgb = [c, x, 0];
    else if (h < 120) rgb = [x, c, 0];
    else if (h < 180) rgb = [0, c, x];
    else if (h < 240) rgb = [0, x, c];
    else if (h < 300) rgb = [x, 0, c];
    else rgb = [c, 0, x];
    return '#' + rgb.map(v => Math.round((v + m) * 255).toString(16).padStart(2, '0')).join('');
}

function extractThemePalette(image) {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    canvas.width = 96; canvas.height = 96;
    ctx.drawImage(image, 0, 0, 96, 96);
    const pixels = ctx.getImageData(0, 0, 96, 96).data;
    const bins = new Map();
    for (let i = 0; i < pixels.length; i += 4) {
        const r = pixels[i], g = pixels[i + 1], b = pixels[i + 2], a = pixels[i + 3];
        if (a < 200) continue;
        const hsl = rgbToHsl(r, g, b);
        if (hsl.l > 0.96 || hsl.l < 0.025) continue;
        const key = `${Math.round(r/16)},${Math.round(g/16)},${Math.round(b/16)}`;
        const old = bins.get(key) || { r: 0, g: 0, b: 0, count: 0 };
        old.r += r; old.g += g; old.b += b; old.count++;
        bins.set(key, old);
    }
    const colors = [...bins.values()].filter(c => c.count >= 2).sort((a, b) => b.count - a.count).slice(0, 12)
        .map(c => ({ count: c.count, ...rgbToHsl(c.r / c.count, c.g / c.count, c.b / c.count) }));
    if (!colors.length) throw new Error('لم أستطع استخراج ألوان صالحة.');
    const dominant = colors[0];
    const bg = hslToHex(dominant.h, Math.min(dominant.s, 0.48), 0.105);
    const accentSource = [...colors].filter(c => c.s >= 0.18).sort((a, b) => b.count * (0.65 + b.s) - a.count * (0.65 + a.s))[0] || dominant;
    const accent = hslToHex(accentSource.h, Math.min(Math.max(accentSource.s, 0.38), 0.68), 0.59);
    const secondarySource = [...colors].filter(c => Math.abs(c.h - accentSource.h) > 20 && c.s >= 0.12).sort((a, b) => b.count - a.count)[0];
    const secondary = secondarySource ? hslToHex(secondarySource.h, Math.min(secondarySource.s, 0.48), 0.70) : hslToHex((accentSource.h + 55) % 360, 0.34, 0.70);
    const card = hslToHex(dominant.h, Math.min(dominant.s, 0.38), 0.17);
    const outgoing = hslToHex(accentSource.h, Math.min(Math.max(accentSource.s, 0.34), 0.60), 0.25);
    return { bg, card, accent, outgoing, secondary };
}

$('imageInput').addEventListener('change', function(event) {
    const file = event.target.files && event.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function(e) {
        const dataUrl = e.target.result;
        $('wallpaperImage').setAttribute('href', dataUrl);
        const img = new Image();
        img.onload = function() {
            try {
                const palette = extractThemePalette(img);
                $('bgColor').value = palette.bg;
                $('cardColor').value = palette.card;
                $('accentColor').value = palette.accent;
                $('outColor').value = palette.outgoing;
                $('secondaryColor').value = palette.secondary;
                updatePreview();
                setStatus('✨ تم استخراج لوحة الألوان وتطبيقها بنجاح!');
            } catch (error) { setStatus('تعذر تحليل ألوان الصورة.'); }
        };
        img.src = dataUrl;
    };
    reader.readAsDataURL(file);
});

function currentThemeData() {
    let userId = telegramUserId;
    if (!userId && $('manualChatId')) { userId =$('manualChatId'].value.trim(); }
    return {
        bg: $('bgColor').value, card: $('cardColor').value, accent:$('accentColor').value,
        outgoing: $('outColor').value, secondary:$('secondaryColor').value,
        opacity: Number($('opacityRange').value), user_id: userId
    };
}

$('copyButton').addEventListener('click', async function() {
    const d = currentThemeData();
    const text = 'Background=' + d.bg + '\nCard=' + d.card + '\nAccent=' + d.accent;
    try { await navigator.clipboard.writeText(text); setStatus('📋 تم النسخ.'); } catch (e) {}
});

$('sendTelegramBtn').addEventListener('click', async function() {
    const data = currentThemeData();
    if (!data.user_id) { setStatus('⚠️ يرجى إدخال معرف تيليجرام (Chat ID).'); $('chatIdContainer').style.display = 'flex'; return; }$('sendTelegramBtn').disabled = true;
    setStatus('⏳ جارٍ الإرسال للبوت...');
    try {
        const response = await fetch('/generate-custom-theme', {
            method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)
        });
        const resJson = await response.json();
        if (resJson.success) {
            setStatus('✅ تم إرسال الثيم إلى محادثتك بنجاح!');
            setTimeout(() => { if (tg && typeof tg.close === 'function') tg.close(); }, 2000);
        } else { setStatus('❌ فشل: ' + resJson.error); }
    } catch (error) { setStatus('❌ خطأ في الاتصال.'); } finally { $('sendTelegramBtn').disabled = false; }
});

function setStatus(msg) { $('statusMessage').textContent = msg; }
updatePreview();
</script>
</body>
</html>"""

def hex_to_signed_int(hex_str, alpha=255):
    hex_str = hex_str.strip().lstrip("#")
    r = int(hex_str[0:2], 16)
    g = int(hex_str[2:4], 16)
    b = int(hex_str[4:6], 16)
    value = (alpha << 24) | (r << 16) | (g << 8) | b
    if value > 0x7FFFFFFF:
        value -= 0x100000000
    return value

def build_theme_content(bg_hex, card_hex, accent_hex, outgoing_hex, secondary_hex, opacity_val):
    bubble_alpha = round((opacity_val / 100.0) * 255)

    c_bg = hex_to_signed_int(bg_hex)
    c_card = hex_to_signed_int(card_hex)
    c_accent = hex_to_signed_int(accent_hex)
    c_outgoing = hex_to_signed_int(outgoing_hex)
    c_secondary = hex_to_signed_int(secondary_hex)
    
    c_bubble_in = hex_to_signed_int(card_hex, alpha=bubble_alpha)
    c_bubble_out = hex_to_signed_int(outgoing_hex, alpha=bubble_alpha)
    c_selected = hex_to_signed_int("#334155")
    c_white = -1
    c_text_main = c_accent  # مطابقة لخوارزمية الثيم القديم: النصوص الرئيسية والأسماء تأخذ لون الأساس

    # القاموس الكامل والشامل لجميع مفاتيح الثيم (بدون استثناء أي مفتاح من بياناتك الأصلية)
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
        "chat_mediaTimeText": c_white,
        "chat_messageLinkIn": c_secondary,
        "chat_messageLinkOut": c_secondary,
        "chat_messagePanelBackground": c_bg,
        "chat_messagePanelCancelInlineBot": c_accent,
        "chat_messagePanelHint": c_secondary,
        "chat_messagePanelIcons": c_accent,
        "ChatShadow": c_accent,
        "chat_messagePanelSend": c_accent,
        "chat_messagePanelShadow": c_bg,
        "chat_messagePanelText": c_accent,
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
        "chats_menuName": c_accent,
        "chats_menuPhone": c_accent,
        "chats_menuPhoneCats": c_accent,
        "chats_menuTopShadow": c_selected,
        "chats_message": c_secondary,
        "chats_message_threeLines": c_accent,
        "chats_muteIcon": c_accent,
        "chats_name": c_accent,
        "chats_nameArchived": c_accent,
        "chats_nameIcon": c_accent,
        "chats_nameMessage": c_accent,
        "chats_nameMessage_threeLines": c_accent,
        "chats_nameMessageArchived": c_accent,
        "chats_nameMessageArchived_threeLines": c_accent,
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
        "dialogTextBlack": c_accent,
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
        "windowBackgroundWhiteBlackText": c_accent,
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
        "windowBackgroundWhiteGrayText": c_accent,
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
    return "Advanced Telegram Theme Mini App is running."

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

    file_content = build_theme_content(bg_hex, card_hex, accent_hex, outgoing_hex, secondary_hex, opacity_val)
    return Response(
        file_content,
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment;filename=Custom_Smart_Theme.attheme"}
    )

@app.route("/generate-custom-theme", methods=["POST"])
def generate_custom_theme():
    req_data = request.get_json(silent=True) or {}
    bg_hex = req_data.get("bg", "#0f172a")
    card_hex = req_data.get("card", "#1e293b")
    accent_hex = req_data.get("accent", "#38bdf8")
    outgoing_hex = req_data.get("outgoing", "#0284c7")
    secondary_hex = req_data.get("secondary", "#B997D0")
    opacity_val = int(req_data.get("opacity", 90))
    user_id = req_data.get("user_id")

    if not user_id:
        return jsonify({"success": False, "error": "معرف تيليجرام غير متوفر."}), 400

    file_content = build_theme_content(bg_hex, card_hex, accent_hex, outgoing_hex, secondary_hex, opacity_val)
    
    import tempfile
    handle = tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix=".attheme", prefix="custom_theme_", delete=False
    )
    file_path = handle.name
    
    try:
        handle.write(file_content)
        handle.close()

        url = f"https://api.telegram.org/bot{TOKEN}/sendDocument"
        with open(file_path, "rb") as f:
            files = {"document": ("Custom_Smart_Theme.attheme", f)}
            data = {
                "chat_id": user_id, 
                "caption": "✨ تفضل ملف الثيم الشامل بكافة مفاتيحه دون أي نقص!"
            }
            resp = requests.post(url, data=data, files=files)
            if not resp.ok:
                try:
                    err_desc = resp.json().get("description", resp.text)
                except:
                    err_desc = resp.text
                return jsonify({"success": False, "error": err_desc}), 400

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
            text="🎨 افتح صانع الثيمات الذكي",
            web_app=WebAppInfo(url=f"{base_url}/webapp")
        )]
    ])
    await message.answer(
        "✨ أهلاً بك في صانع ثيمات تيليجرام المتطور!\n\n"
        "تم استعادة كافة المفاتيح الأصلية بالكامل:",
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
