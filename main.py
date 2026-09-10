import os
import logging
from PIL import Image, ImageDraw, ImageFont
import qrcode
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ConversationHandler, ContextTypes
)

# Logging ማዘጋጃ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# የውይይት ደረጃዎች (States)
NAME_AM, NAME_EN, DOB, SEX, FIN_NUM, PHONE, ADDRESS = range(7)

# 1. መታወቂያ የመስራት ተግባር (Image Generator)
def create_fayda_id_demo(name_am, name_en, dob, sex, fin, phone, address, font_path="nyala.ttf"):
    card_width, card_height = 1012, 638
    
    # የፊት ገጽ
    front_card = Image.new("RGB", (card_width, card_height), "#e2f2e9")
    draw = ImageDraw.Draw(front_card)
            
    try:
        font_title = ImageFont.truetype(font_path, 24)
        font_text = ImageFont.truetype(font_path, 22)
        font_bold = ImageFont.truetype(font_path, 26)
        font_small = ImageFont.truetype(font_path, 16)
        font_watermark = ImageFont.truetype(font_path, 60)
    except IOError:
        font_title = font_text = font_bold = font_small = font_watermark = ImageFont.load_default()

    # የኢትዮጵያ ሰንደቅ ዓላማ
    flag_w, flag_h = 90, 60
    flag_x, flag_y = card_width - 120, 20
    draw.rectangle([flag_x, flag_y, flag_x + flag_w, flag_y + int(flag_h/3)], fill="#009a44")
    draw.rectangle([flag_x, flag_y + int(flag_h/3), flag_x + flag_w, flag_y + int(2*flag_h/3)], fill="#fec10d")
    draw.rectangle([flag_x, flag_y + int(2*flag_h/3), flag_x + flag_w, flag_y + flag_h], fill="#d11919")

    # Header
    draw.text((30, 20), "የኢትዮጵያ ብሔራዊ መታወቂያ (DEMO)", fill="#0f172a", font=font_title)
    draw.text((30, 50), "Ethiopian National ID (SAMPLE)", fill="#475569", font=font_small)
    draw.line([(30, 90), (card_width - 30, 90)], fill="#3b82f6", width=2)
    draw.text((220, 280), "SPECIMEN / DEMO", fill="#cbd5e1", font=font_watermark)

    # Details
    start_x, start_y, spacing = 240, 120, 55
    details = [
        ("ሙሉ ስም / Full Name:", f"{name_am}\n{name_en}"),
        ("የልደት ቀን / DOB:", dob),
        ("ጾታ / Sex:", sex),
        ("የሚያበቃበት ቀን / Expiry:", "01/01/2030")
    ]

    curr_y = start_y
    for label, val in details:
        draw.text((start_x, curr_y), label, fill="#64748b", font=font_small)
        draw.text((start_x + 180, curr_y), val, fill="#0f172a", font=font_bold if "ስም" in label else font_text)
        curr_y += spacing

    # FIN
    draw.line([(30, 520), (card_width - 30, 520)], fill="#cbd5e1", width=1)
    draw.text((30, 535), "Fayda Identification Number (FIN)", fill="#64748b", font=font_small)
    draw.text((30, 560), fin, fill="#1e3a8a", font=font_bold)

    front_path = "fayda_front_demo.png"
    front_card.save(front_path)

    # የጀርባ ገጽ
    back_card = Image.new("RGB", (card_width, card_height), "#f8fafc")
    draw_back = ImageDraw.Draw(back_card)

    qr_data = f"https://example.com/verify/{fin}"
    qr = qrcode.QRCode(version=1, box_size=8, border=1)
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#1e293b", back_color="#ffffff").resize((280, 280))
    back_card.paste(qr_img, (50, 150))

    draw_back.text((400, 50), "የመታወቂያው የጀርባ ገጽ / Card Back (DEMO)", fill="#94a3b8", font=font_small)
    
    back_details = [
        ("ስልክ ቁጥር / Phone Number:", phone),
        ("ዜግነት / Nationality:", "ኢትዮጵያዊ / Ethiopian"),
        ("አድራሻ / Address:", address)
    ]

    curr_y = 150
    for label, val in back_details:
        draw_back.text((400, curr_y), label, fill="#64748b", font=font_small)
        draw_back.text((400, curr_y + 25), val, fill="#0f172a", font=font_bold)
        curr_y += 80

    draw_back.line([(30, 520), (card_width - 30, 520)], fill="#cbd5e1", width=1)
    draw_back.text((30, 550), "SN: 00000000", fill="#475569", font=font_text)
    draw_back.text((card_width - 250, 550), "National ID Ethiopia", fill="#1e3a8a", font=font_bold)

    back_path = "fayda_back_demo.png"
    back_card.save(back_path)

    return front_path, back_path

# 2. የቴሌግራም ቦት የውይይት ሂደቶች (Conversation Steps)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ሰላም! የናሙና ፋይዳ መታወቂያ ለማዘጋጀት ይርዱዎታል።\n\nበቅድሚያ **ሙሉ ስምዎን በአማርኛ** ያስገቡ፡")
    return NAME_AM

async def get_name_am(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name_am'] = update.message.text
    await update.message.reply_text("ጥሩ! አሁን ደግሞ **ሙሉ ስምዎን በኢንግሊዝኛ** ያስገቡ፡")
    return NAME_EN

async def get_name_en(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name_en'] = update.message.text
    await update.message.reply_text("የልደት ቀንዎን ያስገቡ (ለምሳሌ፦ 01/01/1995)፡")
    return DOB

async def get_dob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['dob'] = update.message.text
    await update.message.reply_text("ጾታዎን ያስገቡ (ወንድ / ሴት)፡")
    return SEX

async def get_sex(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['sex'] = update.message.text
    await update.message.reply_text("የ FIN (መታወቂያ) ቁጥር ያስገቡ፡")
    return FIN_NUM

async def get_fin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['fin'] = update.message.text
    await update.message.reply_text("የስልክ ቁጥርዎን ያስገቡ፡")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone'] = update.message.text
    await update.message.reply_text("አድራሻዎን ያስገቡ (ለምሳሌ፦ Addis Ababa)፡")
    return ADDRESS

async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['address'] = update.message.text
    await update.message.reply_text("መረጃዎችዎ ተቀብለናል! መታወቂያው እየተሰራ ነው...")

    # ምስል ማዘጋጀት
    front_img, back_img = create_fayda_id_demo(
        name_am=context.user_data['name_am'],
        name_en=context.user_data['name_en'],
        dob=context.user_data['dob'],
        sex=context.user_data['sex'],
        fin=context.user_data['fin'],
        phone=context.user_data['phone'],
        address=context.user_data['address']
    )

    # ምስሎችን መላክ
    with open(front_img, "rb") as f:
        await update.message.reply_photo(photo=f, caption="የመታወቂያው የፊት ገጽ (Demo)")
    with open(back_img, "rb") as b:
        await update.message.reply_photo(photo=b, caption="የመታወቂያው የጀርባ ገጽ (Demo)")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ሂደቱ ተሰርዟል። እንደገና ለመጀመር `/start` ይበሉ።")
    return ConversationHandler.END

# 3. Main Engine
if __name__ == "__main__":
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN አልተገኘም! እባክዎ Environment Variable ላይ ያዘጋጁ።")

    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME_AM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name_am)],
            NAME_EN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name_en)],
            DOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_dob)],
            SEX: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_sex)],
            FIN_NUM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_fin)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(conv_handler)
    print("ቦቱ በGitHub/Server ላይ እየሰራ ነው...")
    app.run_polling()
