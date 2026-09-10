import os, io, sqlite3
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPPORT_USERNAME = "Ahm0710"
DB_FILE = "bot.db"
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing. Add it in Render Environment Variables.")

def conn(): return sqlite3.connect(DB_FILE)

def init_database():
    c=conn()
    c.execute("CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY,balance REAL DEFAULT 0,created_at TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS jobs(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,job_type TEXT,status TEXT,created_at TEXT)")
    c.commit(); c.close()

def add_user(uid):
    c=conn()
    c.execute("INSERT OR IGNORE INTO users VALUES(?,?,?)",(uid,0,datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    c.commit(); c.close()

def balance(uid):
    add_user(uid); c=conn()
    r=c.execute("SELECT balance FROM users WHERE user_id=?",(uid,)).fetchone()
    c.close(); return float(r[0]) if r else 0

def job(uid,typ,status="Completed"):
    c=conn()
    c.execute("INSERT INTO jobs(user_id,job_type,status,created_at) VALUES(?,?,?,?)",
              (uid,typ,status,datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    c.commit(); c.close()

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📄 PDF → Image",callback_data="pdf"),
         InlineKeyboardButton("🖼 Image → PDF",callback_data="image")],
        [InlineKeyboardButton("📸 Screenshot → PDF",callback_data="screen"),
         InlineKeyboardButton("📚 Multiple Images → PDF",callback_data="multi")],
        [InlineKeyboardButton("📝 Convert to Word",callback_data="word")],
        [InlineKeyboardButton("💰 Balance",callback_data="balance"),
         InlineKeyboardButton("💳 Top Up",callback_data="topup")],
        [InlineKeyboardButton("🗂 My Jobs",callback_data="jobs"),
         InlineKeyboardButton("⚙️ Settings",callback_data="settings")],
        [InlineKeyboardButton("🆘 Support",callback_data="support")]
    ])


def create_demo_document(title, name, reference, output_path="demo_document.png"):
    """Create a clearly marked, non-official sample document."""
    w, h = 1012, 638
    img = Image.new("RGB", (w, h), "#f8fafc")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("nyala.ttf", 28)
        small = ImageFont.truetype("nyala.ttf", 20)
        big = ImageFont.truetype("nyala.ttf", 42)
    except OSError:
        font = small = big = ImageFont.load_default()

    draw.rectangle((20, 20, w-20, h-20), outline="#64748b", width=3)
    draw.text((55, 55), title, fill="#0f172a", font=big)
    draw.text((55, 125), "SAMPLE / DEMO — NOT AN OFFICIAL DOCUMENT",
              fill="#b91c1c", font=font)
    draw.line((55, 175, w-55, 175), fill="#94a3b8", width=2)

    draw.text((55, 220), "Name:", fill="#475569", font=small)
    draw.text((220, 220), name, fill="#111827", font=font)
    draw.text((55, 285), "Reference:", fill="#475569", font=small)
    draw.text((220, 285), reference, fill="#111827", font=font)

    draw.text((55, 390),
              "For software testing and UI demonstration only.",
              fill="#475569", font=small)
    draw.text((55, 450),
              "This sample has no government status or verification function.",
              fill="#b91c1c", font=small)

    img.save(output_path)
    return output_path

async def start(update:Update, context:ContextTypes.DEFAULT_TYPE):
    add_user(update.effective_user.id)
    await update.message.reply_text(
        f"👋 ሰላም {update.effective_user.first_name or 'ጓደኛ'}!\n\n"
        "🤖 እንኳን ወደ File Converter Bot በደህና መጣህ።\n\nከታች ያለውን Menu ተጠቀም።",
        reply_markup=menu())

async def buttons(update:Update, context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer(); d=q.data
    if d=="pdf":
        context.user_data["mode"]="pdf"; await q.message.reply_text("📄 PDF ፋይል ላክ። ወደ PNG images እቀይረዋለሁ።")
    elif d=="image":
        context.user_data["mode"]="image"; await q.message.reply_text("🖼️ JPG/JPEG/PNG ምስል ላክ። ወደ PDF እቀይረዋለሁ።")
    elif d=="screen":
        context.user_data["mode"]="screen"; await q.message.reply_text("📸 Screenshot ላክ። ወደ PDF እቀይረዋለሁ።")
    elif d=="multi":
        context.user_data["mode"]="multi"; context.user_data["images"]=[]
        await q.message.reply_text("📚 Images አንድ በአንድ ላክ። ሲጨርስ /done ብለህ ላክ።")
    elif d=="word":
        await q.message.reply_text("📝 Convert to Word\n\nየWord/OCR engine በዚህ ስሪት አልተጨመረም።")
    elif d=="balance":
        await q.message.reply_text(f"💰 Balance\n\nCurrent Balance: {balance(q.from_user.id):.2f} ETB",
          reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💳 Top Up",callback_data="topup")],[InlineKeyboardButton("🔙 Back",callback_data="back")]]))
    elif d=="topup":
        await q.message.reply_text("💳 TOP UP\n\nTelebirr: 0920210606\n\nክፍያ ካደረግህ የክፍያ ማረጋገጫውን Support ላክ።\n\n🆘 Support: @"+SUPPORT_USERNAME,
          reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🆘 Contact Support",url="https://t.me/"+SUPPORT_USERNAME)],[InlineKeyboardButton("🔙 Back",callback_data="back")]]))
    elif d=="jobs":
        c=conn(); rows=c.execute("SELECT job_type,status,created_at FROM jobs WHERE user_id=? ORDER BY id DESC LIMIT 10",(q.from_user.id,)).fetchall(); c.close()
        text="🗂 My Jobs\n\n" if rows else "🗂 My Jobs\n\nእስካሁን job የለህም።"
        for a,b,t in rows: text+=f"• {a}\n  Status: {b}\n  {t}\n\n"
        await q.message.reply_text(text,reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back",callback_data="back")]]))
    elif d=="settings":
        await q.message.reply_text("⚙️ Settings\n\n🇪🇹 አማርኛ\n🇬🇧 English",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back",callback_data="back")]]))
    elif d=="support":
        await q.message.reply_text("🆘 Support\n\nችግር ካጋጠመህ Support ን አግኝ።",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🆘 Contact Support",url="https://t.me/"+SUPPORT_USERNAME)],[InlineKeyboardButton("🔙 Back",callback_data="back")]]))
    elif d=="back": await q.message.reply_text("🏠 Main Menu",reply_markup=menu())

async def photo(update:Update, context:ContextTypes.DEFAULT_TYPE):
    mode=context.user_data.get("mode")
    if not mode:
        await update.message.reply_text("📌 መጀመሪያ Menu አንድ አማራጭ ምረጥ።",reply_markup=menu()); return
    f=await context.bot.get_file(update.message.photo[-1].file_id); data=io.BytesIO(); await f.download_to_memory(data); data.seek(0)
    if mode=="multi":
        context.user_data.setdefault("images",[]).append(data.getvalue())
        await update.message.reply_text(f"✅ Image {len(context.user_data['images'])} ተቀብሏል። ተጨማሪ image ላክ፤ ሲጨርስ /done በል።"); return
    if mode in ("image","screen"):
        img=Image.open(data).convert("RGB"); out=io.BytesIO(); img.save(out,"PDF"); out.seek(0)
        await update.message.reply_document(out,filename="converted.pdf",caption="✅ PDF ተዘጋጅቷል።")
        job(update.effective_user.id,"Image → PDF" if mode=="image" else "Screenshot → PDF"); context.user_data["mode"]=None

async def done(update:Update, context:ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("mode")!="multi": await update.message.reply_text("📌 Multiple Images mode ላይ አይደለህም።"); return
    items=context.user_data.get("images",[])
    if not items: await update.message.reply_text("❌ Image አልላክህም።"); return
    imgs=[Image.open(io.BytesIO(x)).convert("RGB") for x in items]; out=io.BytesIO()
    imgs[0].save(out,"PDF",save_all=True,append_images=imgs[1:]); out.seek(0)
    await update.message.reply_document(out,filename="multiple_images.pdf",caption=f"✅ {len(imgs)} Images → PDF ተጠናቋል።")
    job(update.effective_user.id,f"Multiple Images → PDF ({len(imgs)} images)")
    context.user_data["mode"]=None; context.user_data["images"]=[]

async def pdf(update:Update, context:ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("mode")!="pdf": await update.message.reply_text("📌 መጀመሪያ PDF → Image ምረጥ።"); return
    doc=update.message.document
    if not (doc.file_name or "").lower().endswith(".pdf"): await update.message.reply_text("❌ PDF ፋይል ብቻ ላክ።"); return
    try:
        import fitz
        f=await context.bot.get_file(doc.file_id); b=io.BytesIO(); await f.download_to_memory(b); b.seek(0)
        p=fitz.open(stream=b.getvalue(),filetype="pdf")
        if len(p)>20: await update.message.reply_text("⚠️ PDF 20 pages በላይ ነው።"); p.close(); return
        for i,page in enumerate(p):
            x=page.get_pixmap(matrix=fitz.Matrix(2,2)).tobytes("png")
            await update.message.reply_document(io.BytesIO(x),filename=f"page_{i+1}.png",caption=f"📄 Page {i+1}/{len(p)}")
        n=len(p); p.close(); job(update.effective_user.id,f"PDF → Image ({n} pages)"); context.user_data["mode"]=None
    except Exception as e:
        print("PDF ERROR:",e); await update.message.reply_text("❌ PDF conversion failed.")


async def demo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    path = create_demo_document(
        "Demo Document",
        update.effective_user.first_name or "Sample User",
        str(update.effective_user.id),
    )
    with open(path, "rb") as f:
        await update.message.reply_document(
            f,
            filename="demo_document.png",
            caption="✅ Demo document created. NOT an official ID."
        )

async def errors(update,context): print("BOT ERROR:",context.error)

def main():
    init_database()
    app=Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("done",done))
    app.add_handler(CommandHandler("demo",demo))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.PHOTO,photo))
    app.add_handler(MessageHandler(filters.Document.PDF,pdf))
    app.add_error_handler(errors)
    print("🤖 Telegram Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__=="__main__": main()
