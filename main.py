import os
import io
import sqlite3
from datetime import datetime

import fitz
from PIL import Image, ImageOps, ImageDraw

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing. Add it in Render Environment Variables.")

PORT = int(os.getenv("PORT", "10000"))
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")
SUPPORT_USERNAME = "Ahm0710"
TELEBIRR_NUMBER = "0920210606"
DB_FILE = "bot.db"

MENU = [
    ["📄 Print from PDF", "📸 Print from Screenshot"],
    ["🗂 Bulk Screenshot", "🖨 Group to A4"],
    ["💰 Balance", "📦 Top Up"],
    ["📊 My Jobs", "🔗 Refer"],
    ["🌐 Dashboard", "⚙️ Settings"],
    ["🆘 Support"],
]

def db():
    c = sqlite3.connect(DB_FILE)
    c.execute("CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY,balance INTEGER DEFAULT 0,created_at TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS jobs(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,job_type TEXT,created_at TEXT)")
    c.commit()
    return c

def ensure_user(uid):
    c = db()
    if not c.execute("SELECT 1 FROM users WHERE user_id=?", (uid,)).fetchone():
        c.execute("INSERT INTO users VALUES(?,?,?)", (uid,0,datetime.utcnow().isoformat()))
        c.commit()
    c.close()

def add_job(uid, typ):
    ensure_user(uid)
    c=db()
    c.execute("INSERT INTO jobs(user_id,job_type,created_at) VALUES(?,?,?)",(uid,typ,datetime.utcnow().isoformat()))
    c.commit(); c.close()

def kb():
    return ReplyKeyboardMarkup(MENU, resize_keyboard=True)

async def start(update, context):
    ensure_user(update.effective_user.id)
    context.user_data.clear()
    await update.message.reply_text(
        "👋 እንኳን ወደ EZA Print & Converter Bot በደህና መጡ!\\n\\n"
        "PDF እና ምስሎችን ለመደርደር፣ A4 ላይ ለመግጠም እና JPEG/PNG/PDF ለማውጣት ይጠቀሙ።",
        reply_markup=kb())

async def print_pdf(update, context):
    context.user_data["mode"]="print_pdf"
    context.user_data["pdfs"]=[]
    await update.message.reply_text(
        "📄 Print from PDF\\n\\nPDF ፋይል ይላኩ። ከዚያ የA4 አቀማመጥ እና output format ይመርጣሉ።",
        reply_markup=kb())

async def screenshot(update, context):
    context.user_data["mode"]="screenshot"
    context.user_data["images"]=[]
    await update.message.reply_text(
        "📸 Print from Screenshot\\n\\nScreenshot ይላኩ። ከዚያ A4 ላይ እንዲደረደር እና JPEG/PNG/PDF እንዲወጣ ይችላሉ።",
        reply_markup=kb())

async def bulk(update, context):
    context.user_data["mode"]="bulk"
    context.user_data["images"]=[]
    await update.message.reply_text(
        "🗂 Bulk Screenshot\\n\\nScreenshots በተከታታይ ይላኩ። ሲጨርሱ /done ይጻፉ።",
        reply_markup=kb())

async def group_a4(update, context):
    context.user_data["mode"]="group_a4"
    context.user_data["images"]=[]
    await update.message.reply_text(
        "🖨 Group to A4\\n\\nImages ይላኩ። ሲጨርሱ /done ይጻፉ።",
        reply_markup=kb())

def options():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎨 JPEG", callback_data="fmt_jpeg"),
         InlineKeyboardButton("🎨 PNG", callback_data="fmt_png"),
         InlineKeyboardButton("📄 PDF", callback_data="fmt_pdf")],
        [InlineKeyboardButton("⚫ Black & White", callback_data="bw"),
         InlineKeyboardButton("↔️ Mirror", callback_data="mirror")],
        [InlineKeyboardButton("📐 A4 Fit", callback_data="a4")],
    ])

async def choose_options(update, context):
    await update.message.reply_text(
        "Output options ይምረጡ።\\n\\n"
        "A4 Fit የተመረጠ እንደሆነ ምስሉ በA4 ገጽ ውስጥ ይገጠማል።",
        reply_markup=options())

def make_a4(img, mirror=False, bw=False):
    W,H=2480,3508
    canvas=Image.new("RGB",(W,H),"white")
    im=img.convert("RGB")
    if mirror: im=ImageOps.mirror(im)
    if bw: im=ImageOps.grayscale(im).convert("RGB")
    im.thumbnail((W-160,H-160),Image.Resampling.LANCZOS)
    x=(W-im.width)//2; y=(H-im.height)//2
    canvas.paste(im,(x,y))
    return canvas

async def callback(update, context):
    q=update.callback_query
    await q.answer()
    data=q.data
    if data.startswith("fmt_"):
        context.user_data["fmt"]=data[4:]
        await q.message.reply_text(f"✅ Output: {data[4:].upper()}\\n\\nA4 Fit ወይም ሌላ option ይምረጡ።")
    elif data=="bw":
        context.user_data["bw"]=True
        await q.message.reply_text("⚫ Black & White: ON")
    elif data=="mirror":
        context.user_data["mirror"]=True
        await q.message.reply_text("↔️ Mirror: ON")
    elif data=="a4":
        context.user_data["a4"]=True
        await q.message.reply_text("📐 A4 Fit: ON\\n\\n/done በማለት ሂደቱን ይጀምሩ።")

async def document(update, context):
    if context.user_data.get("mode")!="print_pdf":
        await update.message.reply_text("📄 Print from PDF ከMenu ይምረጡ።",reply_markup=kb()); return
    doc=update.message.document
    if not (doc.file_name or "").lower().endswith(".pdf"):
        await update.message.reply_text("PDF ብቻ ይላኩ።"); return
    f=await doc.get_file()
    data=await f.download_as_bytearray()
    pdf=fitz.open(stream=bytes(data),filetype="pdf")
    if len(pdf)>30:
        pdf.close(); await update.message.reply_text("በአንድ batch እስከ 30 PDF pages ብቻ ይፈቀዳል።"); return
    imgs=[]
    for page in pdf:
        pix=page.get_pixmap(matrix=fitz.Matrix(1.3,1.3),alpha=False)
        imgs.append(Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB"))
    pdf.close()
    context.user_data["images"]=imgs
    context.user_data["mode"]="prepared"
    await update.message.reply_text(f"✅ {len(imgs)} page(s) captured.\\n\\nOutput options:",reply_markup=options())

async def photo(update, context):
    mode=context.user_data.get("mode")
    if mode not in ("screenshot","bulk","group_a4"):
        await update.message.reply_text("ከMenu አንድ አማራጭ ይምረጡ።",reply_markup=kb()); return
    f=await update.message.photo[-1].get_file()
    data=await f.download_as_bytearray()
    im=Image.open(io.BytesIO(bytes(data))).convert("RGB")
    context.user_data.setdefault("images",[]).append(im)
    await update.message.reply_text(f"✅ Image {len(context.user_data['images'])} captured. ሌላ ይላኩ ወይም /done ይጻፉ።")

async def done(update, context):
    imgs=context.user_data.get("images",[])
    if not imgs:
        await update.message.reply_text("Image/PDF page አልተዘጋጀም።"); return
    await produce(update, context, imgs)

async def produce(update, context, imgs):
    fmt=context.user_data.get("fmt","pdf")
    bw=context.user_data.get("bw",False)
    mirror=context.user_data.get("mirror",False)
    use_a4=context.user_data.get("a4",True)

    processed=[make_a4(im,mirror,bw) if use_a4 else (ImageOps.mirror(im) if mirror else im) for im in imgs]

    if fmt=="pdf":
        out=io.BytesIO(); out.name="processed_A4.pdf"
        first,*rest=processed
        first.save(out,"PDF",save_all=True,append_images=rest,resolution=150)
        out.seek(0)
        await update.message.reply_document(out,filename="processed_A4.pdf")
    elif fmt in ("jpeg","png"):
        # Send each processed page as a separate image.
        for i,im in enumerate(processed,1):
            out=io.BytesIO(); ext="JPEG" if fmt=="jpeg" else "PNG"
            out.name=f"processed_{i}.{fmt}"
            im.save(out,ext,quality=92 if ext=="JPEG" else None)
            out.seek(0)
            await update.message.reply_document(out,filename=out.name)

    add_job(update.effective_user.id,"Print/Group to A4")
    context.user_data.clear()
    await update.message.reply_text("✅ Processing finished.",reply_markup=kb())

async def balance(update, context):
    ensure_user(update.effective_user.id)
    c=db(); b=c.execute("SELECT balance FROM users WHERE user_id=?",(update.effective_user.id,)).fetchone()[0]; c.close()
    await update.message.reply_text(f"💰 Balance: {b} ETB",reply_markup=kb())

async def topup(update, context):
    await update.message.reply_text(f"📦 Top Up\\n\\nTelebirr: {TELEBIRR_NUMBER}\\nSupport: @{SUPPORT_USERNAME}\\n\\nክፍያ ከፈጸሙ በኋላ Support ያነጋግሩ።",reply_markup=kb())

async def jobs(update, context):
    ensure_user(update.effective_user.id)
    c=db(); rows=c.execute("SELECT job_type,created_at FROM jobs WHERE user_id=? ORDER BY id DESC LIMIT 10",(update.effective_user.id,)).fetchall(); c.close()
    text="📊 My Jobs\\n\\n"+("ምንም job የለም።" if not rows else "\\n".join(f"• {a} — {b[:19]}" for a,b in rows))
    await update.message.reply_text(text,reply_markup=kb())

async def refer(update, context):
    await update.message.reply_text("🔗 Refer\\n\\nReferral system በዚህ version ገና አልነቃም።",reply_markup=kb())

async def dashboard(update, context):
    await update.message.reply_text("🌐 Dashboard\\n\\nDashboard link በዚህ version ገና አልነቃም።",reply_markup=kb())

async def settings(update, context):
    await update.message.reply_text("⚙️ Settings\\n\\nLanguage: Amharic\\nOutput default: PDF\\nA4 Fit: ON",reply_markup=kb())

async def support(update, context):
    await update.message.reply_text(f"🆘 Support\\n\\nTelegram: @{SUPPORT_USERNAME}",reply_markup=kb())

async def text_handler(update, context):
    actions={
        "📄 Print from PDF":print_pdf,"📸 Print from Screenshot":screenshot,
        "🗂 Bulk Screenshot":bulk,"🖨 Group to A4":group_a4,
        "💰 Balance":balance,"📦 Top Up":topup,"📊 My Jobs":jobs,
        "🔗 Refer":refer,"🌐 Dashboard":dashboard,"⚙️ Settings":settings,
        "🆘 Support":support}
    fn=actions.get(update.message.text)
    if fn: await fn(update,context)
    else: await update.message.reply_text("Menu ውስጥ ያለውን ይጠቀሙ።",reply_markup=kb())

def main():
    if not RENDER_EXTERNAL_URL:
        raise RuntimeError("RENDER_EXTERNAL_URL is missing.")
    app=Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("done",done))
    app.add_handler(MessageHandler(filters.Document.ALL,document))
    app.add_handler(MessageHandler(filters.PHOTO,photo))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,text_handler))
    webhook=RENDER_EXTERNAL_URL.rstrip("/")+"/telegram"
    print("Starting webhook:",webhook)
    app.run_webhook(listen="0.0.0.0",port=PORT,url_path="telegram",webhook_url=webhook,allowed_updates=Update.ALL_TYPES)

if __name__=="__main__":
    main()
