import os
import io
import sqlite3
from datetime import datetime

from PIL import Image
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================================================
# TELEGRAM BOT TOKEN
# =========================================================
# ከ @BotFather የሰጠህን Token እዚህ አስገባ።
# ለምሳሌ:
# BOT_TOKEN = "123456789:AAxxxxxxxxxxxxxxxxxxxx"

BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

SUPPORT_USERNAME = "Ahm0710"

DB_FILE = "bot.db"


# =========================================================
# DATABASE
# =========================================================

def init_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0,
            created_at TEXT
        )
    """)

    cursor.execute("""
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
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO users
        (user_id, balance, created_at)
        VALUES (?, ?, ?)
    """, (
        user_id,
        0,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()


def get_balance(user_id):
    add_user(user_id)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT balance FROM users WHERE user_id = ?",
        (user_id,)
    )

    result = cursor.fetchone()
    conn.close()

    return result[0] if result else 0


def add_job(user_id, job_type, status="Completed"):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO jobs
        (user_id, job_type, status, created_at)
        VALUES (?, ?, ?, ?)
    """, (
        user_id,
        job_type,
        status,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()


# =========================================================
# MAIN MENU
# =========================================================

def main_menu():

    keyboard = [
        [
            InlineKeyboardButton(
                "📄 PDF → Image",
                callback_data="pdf_to_image"
            ),
            InlineKeyboardButton(
                "🖼 Image → PDF",
                callback_data="image_to_pdf"
            ),
        ],

        [
            InlineKeyboardButton(
                "📸 Screenshot → PDF",
                callback_data="screenshot_pdf"
            ),
            InlineKeyboardButton(
                "📚 Multiple Images → PDF",
                callback_data="multi_pdf"
            ),
        ],

        [
            InlineKeyboardButton(
                "💰 Balance",
                callback_data="balance"
            ),
            InlineKeyboardButton(
                "💳 Top Up",
                callback_data="topup"
            ),
        ],

        [
            InlineKeyboardButton(
                "🗂 My Jobs",
                callback_data="jobs"
            ),
            InlineKeyboardButton(
                "⚙️ Settings",
                callback_data="settings"
            ),
        ],

        [
            InlineKeyboardButton(
                "🆘 Support",
                callback_data="support"
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# /START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    add_user(user.id)

    text = (
        f"👋 ሰላም {user.first_name}!\n\n"
        "🤖 እንኳን ወደ File Converter Bot በደህና መጣህ።\n\n"
        "ከታች ያለውን Menu ተጠቀም።"
    )

    await update.message.reply_text(
        text,
        reply_markup=main_menu()
    )


# =========================================================
# BUTTONS
# =========================================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

    # PDF → IMAGE
    if data == "pdf_to_image":

        context.user_data["mode"] = "pdf_to_image"

        await query.message.reply_text(
            "📄 PDF ፋይልህን አሁን ላክ።\n\n"
            "PDF ን ወደ Image እቀይረዋለሁ።"
        )

    # IMAGE → PDF
    elif data == "image_to_pdf":

        context.user_data["mode"] = "image_to_pdf"

        await query.message.reply_text(
            "🖼️ JPG / JPEG / PNG ምስል ላክ።\n\n"
            "ወደ PDF እቀይረዋለሁ።"
        )

    # SCREENSHOT → PDF
    elif data == "screenshot_pdf":

        context.user_data["mode"] = "screenshot_pdf"

        await query.message.reply_text(
            "📸 Screenshot ላክ።\n\n"
            "ወደ PDF እቀይረዋለሁ።"
        )

    # MULTIPLE IMAGES
    elif data == "multi_pdf":

        context.user_data["mode"] = "multi_pdf"
        context.user_data["images"] = []

        await query.message.reply_text(
            "📚 Multiple Images → PDF\n\n"
            "ምስሎችን አንድ በአንድ ላክ።\n\n"
            "ሲጨርስ /done ብለህ ላክ።"
        )

    # BALANCE
    elif data == "balance":

        balance = get_balance(query.from_user.id)

        keyboard = [
            [
                InlineKeyboardButton(
                    "💳 Top Up",
                    callback_data="topup"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 Back",
                    callback_data="back"
                )
            ]
        ]

        await query.message.reply_text(
            f"💰 Balance\n\n"
            f"Current Balance: {balance:.2f} ETB",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # TOP UP
    elif data == "topup":

        keyboard = [
            [
                InlineKeyboardButton(
                    "🆘 Contact Support",
                    url=f"https://t.me/{SUPPORT_USERNAME}"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 Back",
                    callback_data="back"
                )
            ]
        ]

        await query.message.reply_text(
            "💳 TOP UP\n\n"
            "Telebirr በመጠቀም ክፍያ ለመፈጸም፦\n\n"
            "📱 Telebirr: 0920210606\n\n"
            "ክፍያ ካደረግህ በኋላ "
            "የክፍያ ማረጋገጫውን Support ላክ።\n\n"
            f"🆘 Support: @{SUPPORT_USERNAME}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # MY JOBS
    elif data == "jobs":

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT job_type, status, created_at
            FROM jobs
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 10
        """, (query.from_user.id,))

        jobs = cursor.fetchall()
        conn.close()

        if not jobs:

            text = (
                "🗂 My Jobs\n\n"
                "እስካሁን job የለህም።"
            )

        else:

            text = "🗂 My Jobs\n\n"

            for job_type, status, created_at in jobs:

                text += (
                    f"• {job_type}\n"
                    f"  Status: {status}\n"
                    f"  {created_at}\n\n"
                )

        await query.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 Back",
                        callback_data="back"
                    )
                ]
            ])
        )

    # SETTINGS
    elif data == "settings":

        await query.message.reply_text(
            "⚙️ Settings\n\n"
            "🇪🇹 አማርኛ\n"
            "🇬🇧 English",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 Back",
                        callback_data="back"
                    )
                ]
            ])
        )

    # SUPPORT
    elif data == "support":

        await query.message.reply_text(
            "🆘 Support\n\n"
            "ችግር ካጋጠመህ Support ን አግኝ።",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🆘 Contact Support",
                        url=f"https://t.me/{SUPPORT_USERNAME}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔙 Back",
                        callback_data="back"
                    )
                ]
            ])
        )

    # BACK
    elif data == "back":

        await query.message.reply_text(
            "🏠 Main Menu",
            reply_markup=main_menu()
        )


# =========================================================
# PHOTO HANDLER
# =========================================================

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    mode = context.user_data.get("mode")

    if not mode:

        await update.message.reply_text(
            "📌 መጀመሪያ ከMenu አንድ አማራጭ ምረጥ።",
            reply_markup=main_menu()
        )
        return

    photo = update.message.photo[-1]

    file = await context.bot.get_file(photo.file_id)

    image_data = io.BytesIO()

    await file.download_to_memory(image_data)

    image_data.seek(0)

    # MULTIPLE IMAGES
    if mode == "multi_pdf":

        context.user_data.setdefault("images", [])

        context.user_data["images"].append(
            image_data.getvalue()
        )

        count = len(context.user_data["images"])

        await update.message.reply_text(
            f"✅ Image {count} ተቀብሏል።\n\n"
            "ተጨማሪ image ላክ።\n"
            "ሲጨርስ /done ብለህ ላክ።"
        )

        return

    # IMAGE → PDF
    if mode in ("image_to_pdf", "screenshot_pdf"):

        image = Image.open(image_data).convert("RGB")

        output = io.BytesIO()

        image.save(
            output,
            format="PDF"
        )

        output.seek(0)

        await update.message.reply_document(
            document=output,
            filename="converted.pdf",
            caption="✅ PDF ተዘጋጅቷል።"
        )

        add_job(
            update.effective_user.id,
            "Image → PDF"
            if mode == "image_to_pdf"
            else "Screenshot → PDF"
        )

        context.user_data["mode"] = None


# =========================================================
# /DONE
# =========================================================

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):

    mode = context.user_data.get("mode")

    if mode != "multi_pdf":

        await update.message.reply_text(
            "📌 Multiple Images mode ላይ አይደለህም።"
        )

        return

    images = context.user_data.get("images", [])

    if not images:

        await update.message.reply_text(
            "❌ Image አልላክህም።"
        )

        return

    pil_images = []

    for data in images:

        img = Image.open(
            io.BytesIO(data)
        ).convert("RGB")

        pil_images.append(img)

    output = io.BytesIO()

    first = pil_images[0]
    rest = pil_images[1:]

    first.save(
        output,
        format="PDF",
        save_all=True,
        append_images=rest
    )

    output.seek(0)

    await update.message.reply_document(
        document=output,
        filename="multiple_images.pdf",
        caption=f"✅ {len(images)} Images → PDF ተጠናቋል።"
    )

    add_job(
        update.effective_user.id,
        f"Multiple Images → PDF ({len(images)} images)"
    )

    context.user_data["mode"] = None
    context.user_data["images"] = []


# =========================================================
# PDF HANDLER
# =========================================================

async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):

    mode = context.user_data.get("mode")

    if mode != "pdf_to_image":

        await update.message.reply_text(
            "📌 መጀመሪያ PDF → Image የሚለውን ምረጥ።"
        )

        return

    document = update.message.document

    if not document.file_name.lower().endswith(".pdf"):

        await update.message.reply_text(
            "❌ PDF ፋይል ብቻ ላክ።"
        )

        return

    try:

        import fitz

        file = await context.bot.get_file(
            document.file_id
        )

        pdf_bytes = io.BytesIO()

        await file.download_to_memory(pdf_bytes)

        pdf_bytes.seek(0)

        pdf = fitz.open(
            stream=pdf_bytes.getvalue(),
            filetype="pdf"
        )

        page_count = len(pdf)

        if page_count > 20:

            await update.message.reply_text(
                "⚠️ PDF 20 pages በላይ ነው።"
            )

            pdf.close()
            return

        for i, page in enumerate(pdf):

            pix = page.get_pixmap(
                matrix=fitz.Matrix(2, 2)
            )

            image = pix.tobytes("png")

            await update.message.reply_document(
                document=io.BytesIO(image),
                filename=f"page_{i + 1}.png",
                caption=f"📄 Page {i + 1}/{page_count}"
            )

        pdf.close()

        add_job(
            update.effective_user.id,
            f"PDF → Image ({page_count} pages)"
        )

        context.user_data["mode"] = None

    except Exception as error:

        await update.message.reply_text(
            f"❌ PDF conversion failed.\n\n{error}"
        )


# =========================================================
# ERROR HANDLER
# =========================================================

async def error_handler(update, context):

    print("BOT ERROR:", context.error)


# =========================================================
# MAIN
# =========================================================

def main():

    init_database()

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
            handle_pdf
        )
    )

    application.add_error_handler(
        error_handler
    )

    print("🤖 Telegram Bot is running...")

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


# =========================================================
# START BOT
# =========================================================

if __name__ == "__main__":
    main()
