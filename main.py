import os
import io
import sqlite3
import tempfile
from datetime import datetime

from PIL import Image
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ============================================================
# SETTINGS
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "Ahm0710")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing. Add BOT_TOKEN in Render Environment Variables.")

DB_FILE = "bot.db"


# ============================================================
# DATABASE
# ============================================================

def db():
    return sqlite3.connect(DB_FILE)


def init_db():
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0,
            created_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            job_type TEXT,
            status TEXT,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


def add_user(user_id):
    conn = db()
    cur = conn.cursor()

    cur.execute(
        "INSERT OR IGNORE INTO users (user_id, balance, created_at) VALUES (?, ?, ?)",
        (user_id, 0, datetime.now().isoformat())
    )

    conn.commit()
    conn.close()


def get_balance(user_id):
    add_user(user_id)

    conn = db()
    cur = conn.cursor()

    cur.execute(
        "SELECT balance FROM users WHERE user_id = ?",
        (user_id,)
    )

    result = cur.fetchone()
    conn.close()

    return result[0] if result else 0


def add_job(user_id, job_type, status="Completed"):
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO jobs (user_id, job_type, status, created_at)
        VALUES (?, ?, ?, ?)
    """, (
        user_id,
        job_type,
        status,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()


def get_jobs(user_id):
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT job_type, status, created_at
        FROM jobs
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 10
    """, (user_id,))

    results = cur.fetchall()
    conn.close()

    return results


# ============================================================
# KEYBOARD
# ============================================================

def main_keyboard():

    keyboard = [
        [
            InlineKeyboardButton("📄 PDF → Image", callback_data="pdf_to_image"),
            InlineKeyboardButton("🖼 Image → PDF", callback_data="image_to_pdf"),
        ],
        [
            InlineKeyboardButton("📸 Screenshot → PDF", callback_data="screenshot_pdf"),
            InlineKeyboardButton("📚 Multiple Images → PDF", callback_data="multi_pdf"),
        ],
        [
            InlineKeyboardButton("💰 Balance", callback_data="balance"),
            InlineKeyboardButton("💳 Top Up", callback_data="topup"),
        ],
        [
            InlineKeyboardButton("🗂 My Jobs", callback_data="jobs"),
            InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
        ],
        [
            InlineKeyboardButton("🆘 Support", callback_data="support"),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# ============================================================
# START
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    add_user(user.id)

    text = (
        f"👋 ሰላም {user.first_name}!\n\n"
        "🤖 ወደ File Converter Bot እንኳን በደህና መጣህ።\n\n"
        "ከታች ያሉትን አማራጮች ተጠቀም፦"
    )

    await update.message.reply_text(
        text,
        reply_markup=main_keyboard()
    )


# ============================================================
# PDF → IMAGE
# ============================================================

async def pdf_to_image(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    context.user_data["waiting_for"] = "pdf_to_image"

    await query.message.reply_text(
        "📄 PDF ፋይልህን አሁን ላክ።\n\n"
        "ከዚያ ወደ Image እቀይረዋለሁ።"
    )


# ============================================================
# IMAGE → PDF
# ============================================================

async def image_to_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    context.user_data["waiting_for"] = "image_to_pdf"

    await query.message.reply_text(
        "🖼️ JPG / JPEG / PNG ምስል ላክ።\n\n"
        "ወደ PDF እቀይረዋለሁ።"
    )


# ============================================================
# SCREENSHOT → PDF
# ============================================================

async def screenshot_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    context.user_data["waiting_for"] = "screenshot_pdf"

    await query.message.reply_text(
        "📸 Screenshot ላክ።\n\n"
        "ወደ PDF እቀይረዋለሁ።"
    )


# ============================================================
# MULTIPLE IMAGES → PDF
# ============================================================

async def multi_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    context.user_data["waiting_for"] = "multi_pdf"
    context.user_data["multi_images"] = []

    await query.message.reply_text(
        "📚 Multiple Images → PDF\n\n"
        "ምስሎችን አንድ በአንድ ላክ።\n"
        "ሲጨርስ /done ብለህ ላክ።"
    )


# ============================================================
# BALANCE
# ============================================================

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    amount = get_balance(query.from_user.id)

    keyboard = [
        [InlineKeyboardButton("💳 Top Up", callback_data="topup")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ]

    await query.message.reply_text(
        f"💰 Your Balance\n\n"
        f"Balance: {amount:.2f} ETB",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ============================================================
# TOP UP
# ============================================================

async def topup(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    text = (
        "💳 TOP UP\n\n"
        "በTelebirr ለመክፈል፦\n\n"
        "📱 Telebirr: 0920210606\n\n"
        "ክፍያውን ካደረግህ በኋላ "
        "የክፍያ ማረጋገጫውን ለAdmin/Support ላክ።\n\n"
        f"🆘 Support: @{SUPPORT_USERNAME}"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "🆘 Contact Support",
                url=f"https://t.me/{SUPPORT_USERNAME}"
            )
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="back")
        ]
    ]

    await query.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ============================================================
# MY JOBS
# ============================================================

async def jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_jobs = get_jobs(query.from_user.id)

    if not user_jobs:
        text = (
            "🗂 My Jobs\n\n"
            "እስካሁን ምንም job የለህም።"
        )

    else:
        text = "🗂 My Jobs\n\n"

        for job_type, status, created_at in user_jobs:
            text += (
                f"• {job_type}\n"
                f"  Status: {status}\n"
                f"  {created_at}\n\n"
            )

    keyboard = [
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ]

    await query.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ============================================================
# SETTINGS
# ============================================================

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇪🇹 አማርኛ", callback_data="lang_am")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ]

    await query.message.reply_text(
        "⚙️ Settings\n\n"
        "የቋንቋ ምርጫህን ከታች ምረጥ።",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ============================================================
# SUPPORT
# ============================================================

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton(
                "🆘 Contact Support",
                url=f"https://t.me/{SUPPORT_USERNAME}"
            )
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="back")
        ]
    ]

    await query.message.reply_text(
        "🆘 Support\n\n"
        "ችግር ካጋጠመህ Support ን አግኝ።",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ============================================================
# BACK
# ============================================================

async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "🏠 Main Menu",
        reply_markup=main_keyboard()
    )


# ============================================================
# IMAGE PROCESSING
# ============================================================

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    waiting = context.user_data.get("waiting_for")

    if not waiting:
        await update.message.reply_text(
            "📌 መጀመሪያ ከMenu አንድ አማራጭ ምረጥ።",
            reply_markup=main_keyboard()
        )
        return

    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)

    image_bytes = io.BytesIO()
    await file.download_to_memory(image_bytes)
    image_bytes.seek(0)

    if waiting == "multi_pdf":

        context.user_data.setdefault("multi_images", [])
        context.user_data["multi_images"].append(image_bytes.getvalue())

        count = len(context.user_data["multi_images"])

        await update.message.reply_text(
            f"✅ Image {count} ተቀብሏል።\n\n"
            "ተጨማሪ image ካለ ላክ።\n"
            "ሲጨርስ /done ብለህ ላክ።"
        )
        return

    if waiting in ("image_to_pdf", "screenshot_pdf"):

        image = Image.open(image_bytes).convert("RGB")

        output = io.BytesIO()
        image.save(output, format="PDF")
        output.seek(0)

        await update.message.reply_document(
            document=output,
            filename="converted.pdf",
            caption="✅ PDF ተዘጋጅቷል።"
        )

        add_job(
            user_id,
            "Image → PDF" if waiting == "image_to_pdf"
            else "Screenshot → PDF"
        )

        context.user_data["waiting_for"] = None
        return


# ============================================================
# MULTIPLE IMAGES DONE
# ============================================================

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if context.user_data.get("waiting_for") != "multi_pdf":
        await update.message.reply_text(
            "📌 Multiple Images → PDF mode ላይ አይደለህም።"
        )
        return

    images = context.user_data.get("multi_images", [])

    if not images:
        await update.message.reply_text(
            "❌ እስካሁን image አልላክህም።"
        )
        return

    pil_images = []

    for data in images:
        img = Image.open(io.BytesIO(data)).convert("RGB")
        pil_images.append(img)

    output = io.BytesIO()

    first = pil_images[0]
    others = pil_images[1:]

    first.save(
        output,
        format="PDF",
        save_all=True,
        append_images=others
    )

    output.seek(0)

    await update.message.reply_document(
        document=output,
        filename="multiple_images.pdf",
        caption=f"✅ {len(images)} images → PDF ተጠናቋል።"
    )

    add_job(
        update.effective_user.id,
        f"Multiple Images → PDF ({len(images)} images)"
    )

    context.user_data["waiting_for"] = None
    context.user_data["multi_images"] = []


# ============================================================
# PDF HANDLER
# ============================================================

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):

    waiting = context.user_data.get("waiting_for")

    if waiting != "pdf_to_image":
        await update.message.reply_text(
            "📌 መጀመሪያ ከMenu ተገቢውን አማራጭ ምረጥ።"
        )
        return

    document = update.message.document

    if not document.file_name.lower().endswith(".pdf"):
        await update.message.reply_text(
            "❌ PDF ፋይል ብቻ ላክ።"
        )
        return

    file = await context.bot.get_file(document.file_id)

    with tempfile.NamedTemporaryFile(
        suffix=".pdf",
        delete=False
    ) as temp:

        temp_path = temp.name

    await file.download_to_drive(temp_path)

    # PDF conversion needs PyMuPDF
    try:
        import fitz

        pdf = fitz.open(temp_path)

        page_count = len(pdf)

        # Limit very large PDFs
        if page_count > 20:
            await update.message.reply_text(
                "⚠️ PDF ከ20 pages በላይ ነው። "
                "እባክህ ትንሽ PDF ላክ።"
            )

            os.remove(temp_path)
            return

        for index, page in enumerate(pdf):

            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))

            image_bytes = pix.tobytes("png")

            await update.message.reply_document(
                document=io.BytesIO(image_bytes),
                filename=f"page_{index + 1}.png",
                caption=f"📄 Page {index + 1}/{page_count}"
            )

        pdf.close()

        add_job(
            update.effective_user.id,
            f"PDF → Image ({page_count} pages)"
        )

        context.user_data["waiting_for"] = None

    except Exception as e:

        await update.message.reply_text(
            "❌ PDF conversion failed.\n"
            f"Error: {str(e)}"
        )

    finally:

        if os.path.exists(temp_path):
            os.remove(temp_path)


# ============================================================
# CALLBACK ROUTER
# ============================================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    data = query.data

    if data == "pdf_to_image":
        await pdf_to_image(update, context)

    elif data == "image_to_pdf":
        await image_to_pdf(update, context)

    elif data == "screenshot_pdf":
        await screenshot_pdf(update, context)

    elif data == "multi_pdf":
        await multi_pdf(update, context)

    elif data == "balance":
        await balance(update, context)

    elif data == "topup":
        await topup(update, context)

    elif data == "jobs":
        await jobs(update, context)

    elif data == "settings":
        await settings(update, context)

    elif data == "support":
        await support(update, context)

    elif data == "back":
        await back(update, context)

    elif data == "lang_en":
        await query.answer("English selected")

        await query.message.reply_text(
            "🇬🇧 English selected.",
            reply_markup=main_keyboard()
        )

    elif data == "lang_am":
        await query.answer("አማርኛ selected")

        await query.message.reply_text(
            "🇪🇹 አማርኛ ተመርጧል።",
            reply_markup=main_keyboard()
        )

    else:
        await query.answer("Unknown option")


# ============================================================
# ERROR HANDLER
# ============================================================

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):

    print("ERROR:", context.error)


# ============================================================
# MAIN
# ============================================================

def main():

    init_db()

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("done", done)
    )

    application.add_handler(
        CallbackQueryHandler(button_handler)
    )

    application.add_handler(
        MessageHandler(
            filters.PHOTO,
            handle_photo
        )
    )

    application.add_handler(
        MessageHandler(
            filters.Document.ALL,
            handle_document
        )
    )

    application.add_error_handler(error_handler)

    print("🤖 Bot is starting...")

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()
