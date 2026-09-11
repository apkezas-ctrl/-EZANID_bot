import os
import io
import sqlite3
from datetime import datetime

import fitz
from PIL import Image, ImageDraw

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing. Add BOT_TOKEN in Render Environment Variables.")

PORT = int(os.getenv("PORT", "10000"))
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")
SUPPORT_USERNAME = "Ahm0710"
TELEBIRR_NUMBER = "0920210606"
DB_FILE = "bot.db"

MENU = [
    ["📄 PDF → Image", "🖼 Image → PDF"],
    ["📸 Screenshot → PDF", "🖼 Multiple Images → PDF"],
    ["📝 Convert to Word", "💰 Balance"],
    ["➕ Top Up", "📋 My Jobs"],
    ["⚙️ Settings", "🆘 Support"],
]

def db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0, created_at TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, job_type TEXT, created_at TEXT)")
    conn.commit()
    return conn

def ensure_user(uid):
    conn = db()
    if not conn.execute("SELECT 1 FROM users WHERE user_id=?", (uid,)).fetchone():
        conn.execute("INSERT INTO users VALUES (?,?,?)", (uid, 0, datetime.utcnow().isoformat()))
        conn.commit()
    conn.close()

def add_job(uid, job):
    ensure_user(uid)
    conn = db()
    conn.execute("INSERT INTO jobs(user_id,job_type,created_at) VALUES(?,?,?)", (uid, job, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def balance(uid):
    ensure_user(uid)
    conn = db()
    b = conn.execute("SELECT balance FROM users WHERE user_id=?", (uid,)).fetchone()[0]
    conn.close()
    return b

def keyboard():
    return ReplyKeyboardMarkup(MENU, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_user(update.effective_user.id)
    context.user_data.clear()
    await update.message.reply_text("👋 እንኳን ወደ EZA File Converter Bot በደህና መጡ!\n\nከታች ያለውን Menu ይጠቀሙ።", reply_markup=keyboard())

async def select_mode(update, context, mode, message):
    context.user_data["mode"] = mode
    await update.message.reply_text(message, reply_markup=keyboard())

async def pdf_image(update, context):
    await select_mode(update, context, "pdf_to_image", "📄 PDF ፋይል አሁን ይላኩ።")

async def image_pdf(update, context):
    await select_mode(update, context, "image_to_pdf", "🖼 Image አሁን ይላኩ።")

async def screenshot_pdf(update, context):
    await select_mode(update, context, "screenshot_to_pdf", "📸 Screenshot አሁን ይላኩ።")

async def multiple(update, context):
    context.user_data["mode"] = "multiple_images"
    context.user_data["images"] = []
    await update.message.reply_text("🖼 Images በተከታታይ ይላኩ። ሲጨርሱ /done ይጻፉ።", reply_markup=keyboard())

async def balance_cmd(update, context):
    await update.message.reply_text(f"💰 Balance: {balance(update.effective_user.id)} ETB", reply_markup=keyboard())

async def topup(update, context):
    await update.message.reply_text(f"➕ Top Up\n\nTelebirr: {TELEBIRR_NUMBER}\nSupport: @{SUPPORT_USERNAME}\n\nክፍያ ከፈጸሙ በኋላ Support ያነጋግሩ።", reply_markup=keyboard())

async def jobs(update, context):
    uid = update.effective_user.id
    ensure_user(uid)
    conn = db()
    rows = conn.execute("SELECT job_type,created_at FROM jobs WHERE user_id=? ORDER BY id DESC LIMIT 10", (uid,)).fetchall()
    conn.close()
    text = "📋 My Jobs\n\n" + ("ምንም job የለም።" if not rows else "\n".join(f"• {a} — {b[:19]}" for a,b in rows))
    await update.message.reply_text(text, reply_markup=keyboard())

async def settings(update, context):
    await update.message.reply_text("⚙️ Settings\n\nLanguage: Amharic\nBot status: Active", reply_markup=keyboard())

async def support(update, context):
    await update.message.reply_text(f"🆘 Support\n\nTelegram: @{SUPPORT_USERNAME}", reply_markup=keyboard())

async def word(update, context):
    await update.message.reply_text("📝 Convert to Word\n\nይህ አማራጭ በዚህ version ገና አልነቃም።", reply_markup=keyboard())

async def handle_document(update, context):
    if context.user_data.get("mode") != "pdf_to_image":
        await update.message.reply_text("PDF → Image ን ከMenu ይምረጡ።", reply_markup=keyboard())
        return
    doc = update.message.document
    if not doc.file_name.lower().endswith(".pdf"):
        await update.message.reply_text("PDF ፋይል ብቻ ይላኩ።")
        return
    f = await doc.get_file()
    data = await f.download_as_bytearray()
    pdf = fitz.open(stream=bytes(data), filetype="pdf")
    if len(pdf) > 20:
        pdf.close()
        await update.message.reply_text("PDF ከ20 ገጽ በላይ አይፈቀድም።")
        return
    for i, page in enumerate(pdf):
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5,1.5), alpha=False)
        out = io.BytesIO(pix.tobytes("png"))
        out.name = f"page_{i+1}.png"
        await update.message.reply_document(out, filename=out.name)
    pdf.close()
    add_job(update.effective_user.id, "PDF → Image")

async def handle_photo(update, context):
    mode = context.user_data.get("mode")
    if mode not in ("image_to_pdf", "screenshot_to_pdf", "multiple_images"):
        await update.message.reply_text("ከMenu አንድ conversion ይምረጡ።", reply_markup=keyboard())
        return
    f = await update.message.photo[-1].get_file()
    data = await f.download_as_bytearray()
    image = Image.open(io.BytesIO(bytes(data))).convert("RGB")
    if mode == "multiple_images":
        context.user_data.setdefault("images", []).append(image)
        await update.message.reply_text(f"✅ Image {len(context.user_data['images'])} ተቀብሏል። ሌላ ይላኩ ወይም /done ይጻፉ።")
        return
    out = io.BytesIO()
    out.name = "converted.pdf"
    image.save(out, "PDF", resolution=150)
    out.seek(0)
    await update.message.reply_document(out, filename="converted.pdf")
    add_job(update.effective_user.id, "Image → PDF" if mode == "image_to_pdf" else "Screenshot → PDF")

async def done(update, context):
    images = context.user_data.get("images", [])
    if not images:
        await update.message.reply_text("Image አልተላከም።")
        return
    out = io.BytesIO()
    out.name = "multiple_images.pdf"
    first, *rest = images
    first.save(out, "PDF", save_all=True, append_images=rest, resolution=150)
    out.seek(0)
    await update.message.reply_document(out, filename="multiple_images.pdf")
    add_job(update.effective_user.id, "Multiple Images → PDF")
    context.user_data["images"] = []

async def demo(update, context):
    img = Image.new("RGB", (1200,700), "white")
    d = ImageDraw.Draw(img)
    d.rectangle((20,20,1180,680), outline="black", width=4)
    d.text((70,70), "SAMPLE / DEMO", fill="black")
    d.text((70,140), "NOT AN OFFICIAL DOCUMENT", fill="black")
    d.text((70,240), "EZA File Converter Bot", fill="black")
    out = io.BytesIO()
    out.name = "demo_sample.png"
    img.save(out, "PNG")
    out.seek(0)
    await update.message.reply_photo(out, caption="⚠️ Sample/Demo only — not an official document.")

async def text_handler(update, context):
    actions = {
        "📄 PDF → Image": pdf_image, "🖼 Image → PDF": image_pdf,
        "📸 Screenshot → PDF": screenshot_pdf, "🖼 Multiple Images → PDF": multiple,
        "📝 Convert to Word": word, "💰 Balance": balance_cmd,
        "➕ Top Up": topup, "📋 My Jobs": jobs, "⚙️ Settings": settings,
        "🆘 Support": support,
    }
    fn = actions.get(update.message.text)
    if fn:
        await fn(update, context)
    else:
        await update.message.reply_text("Menu ውስጥ ያለውን አማራጭ ይጠቀሙ።", reply_markup=keyboard())

def main():
    if not RENDER_EXTERNAL_URL:
        raise RuntimeError("RENDER_EXTERNAL_URL is missing.")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(CommandHandler("demo", demo))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    url = RENDER_EXTERNAL_URL.rstrip("/") + "/telegram"
    print("Starting webhook:", url)
    app.run_webhook(listen="0.0.0.0", port=PORT, url_path="telegram",
                    webhook_url=url, allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
