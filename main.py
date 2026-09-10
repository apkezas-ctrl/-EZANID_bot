import os
from PIL import Image, ImageDraw, ImageFont
import qrcode

def create_fayda_id(name_am, name_en, dob, sex, expiry, fin, phone, address, photo_path=None, font_path="nyala.ttf"):
    # Standard CR80 ID Card dimensions in pixels (approx. 1012 x 638 for high quality)
    card_width = 1012
    card_height = 638
    
    # 1. Create Front Card Canvas (with a beautiful light gradient background)
    front_card = Image.new("RGB", (card_width, card_height), "#ffffff")
    draw = ImageDraw.Draw(front_card)
    
    # Draw background pattern (Light green and yellow gradient emulation)
    for y in range(card_height):
        # Simple color blend from light green to light yellow
        r = int(230 + (y / card_height) * 25)
        g = int(247 - (y / card_height) * 10)
        b = int(240 - (y / card_height) * 40)
        for x in range(card_width):
            front_card.putpixel((x, y), (r, g, b))
            
    # Load Font (Fallback to default if custom font not found)
    try:
        font_title = ImageFont.truetype(font_path, 24)
        font_text = ImageFont.truetype(font_path, 22)
        font_bold = ImageFont.truetype(font_path, 26)
        font_small = ImageFont.truetype(font_path, 16)
    except IOError:
        print(f"ማስጠንቀቂያ: '{font_path}' ፎንት አልተገኘም። የአማርኛ ፊደላት በትክክል እንዲታዩ እባክዎ ፎንቱን በፎልደሩ ውስጥ ያድርጉት።")
        font_title = font_text = font_bold = font_small = ImageFont.load_default()

    # Draw Ethiopian Flag (Top Right)
    flag_w, flag_h = 90, 60
    flag_x, flag_y = card_width - 120, 20
    draw.rectangle([flag_x, flag_y, flag_x + flag_w, flag_y + int(flag_h/3)], fill="#009a44") # Green
    draw.rectangle([flag_x, flag_y + int(flag_h/3), flag_x + flag_w, flag_y + int(2*flag_h/3)], fill="#fec10d") # Yellow
    draw.rectangle([flag_x, flag_y + int(2*flag_h/3), flag_x + flag_w, flag_y + flag_h], fill="#d11919") # Red

    # Header Text
    draw.text((30, 20), "የኢትዮጵያ ብሔራዊ መታወቂያ", fill="#0f172a", font=font_title)
    draw.text((30, 50), "Ethiopian National ID", fill="#475569", font=font_small)
    draw.text((450, 20), "የኢትዮጵያ ዲጂታል መታወቂያ", fill="#1e3a8a", font=font_bold)
    draw.text((450, 50), "Ethiopian Digital ID Card", fill="#1e40af", font=font_text)
    
    # Draw a thin blue separator line
    draw.line([(30, 90), (card_width - 30, 90)], fill="#3b82f6", width=2)

    # Insert User Photo (Right side)
    if photo_path and os.path.exists(photo_path):
        user_photo = Image.open(photo_path)
        user_photo = user_photo.resize((190, 240)) # Standard ID photo ratio
        front_card.paste(user_photo, (card_width - 220, 120))
    else:
        # Placeholder if no photo
        draw.rectangle([card_width - 220, 120, card_width - 30, 360], outline="#94a3b8", width=2)
        draw.text((card_width - 180, 220), "ፎቶ (Photo)", fill="#94a3b8", font=font_text)

    # Write ID Details (Middle)
    start_x = 240
    start_y = 120
    spacing = 55

    details = [
        ("ሙሉ ስም / Full Name:", f"{name_am}\n{name_en}"),
        ("የልደት ቀን / DOB:", dob),
        ("ጾታ / Sex:", sex),
        ("የሚያበቃበት ቀን / Expiry:", expiry)
    ]

    curr_y = start_y
    for label, val in details:
        draw.text((start_x, curr_y), label, fill="#64748b", font=font_small)
        draw.text((start_x + 180, curr_y), val, fill="#0f172a", font=font_bold if "ስም" in label else font_text)
        curr_y += spacing

    # Draw Small Photo (Left Side)
    if photo_path and os.path.exists(photo_path):
        small_photo = Image.open(photo_path).resize((90, 110))
        front_card.paste(small_photo, (50, 120))
    else:
        draw.rectangle([50, 120, 140, 230], outline="#cbd5e1", width=1)

    draw.text((55, 245), "Fayda ID", fill="#475569", font=font_small)

    # Footer Area: FIN Number
    draw.line([(30, 520), (card_width - 30, 520)], fill="#cbd5e1", width=1)
    draw.text((30, 535), "Fayda Identification Number (FIN)", fill="#64748b", font=font_small)
    draw.text((30, 560), fin, fill="#1e3a8a", font=font_bold)

    # Save Front Card
    front_card.save("fayda_front.png")
    print("የመታወቂያው የፊት ገጽ 'fayda_front.png' በሚል ስም ተቀምጧል!")

    # -------------------------------------------------------------
    # 2. Create Back Card Canvas
    back_card = Image.new("RGB", (card_width, card_height), "#f8fafc")
    draw_back = ImageDraw.Draw(back_card)

    # Generate QR Code for verification link
    qr_data = f"https://fayda.gov.et/verify/{fin}"
    qr = qrcode.QRCode(version=1, box_size=8, border=1)
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#1e293b", back_color="#ffffff").resize((280, 280))
    back_card.paste(qr_img, (50, 150))

    # Back Card Details
    draw_back.text((400, 50), "የመታወቂያው የጀርባ ገጽ / Card Back", fill="#94a3b8", font=font_small)
    
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

    # Back Card Footer
    draw_back.line([(30, 520), (card_width - 30, 520)], fill="#cbd5e1", width=1)
    draw_back.text((30, 550), "SN: 93143882", fill="#475569", font=font_text)
    draw_back.text((card_width - 250, 550), "National ID Ethiopia", fill="#1e3a8a", font=font_bold)

    # Save Back Card
    back_card.save("fayda_back.png")
    print("የመታወቂያው የጀርባ ገጽ 'fayda_back.png' በሚል ስም ተቀምጧል!")

# --- ኮዱን ለመሞከር (Example Run) ---
if __name__ == "__main__":
    # እዚህ ጋር መረጃዎችን መለወጥ ይችላሉ
    create_fayda_id(
        name_am="አሚናት ሰይድ ኢብራሂም",
        name_en="Aminat Seid Ebrahim",
        dob="05/12/1979 | 12/Sep/1952",
        sex="ሴት / Female",
        expiry="20/12/1402 | 30/Dec/2029",
        fin="30410835812882",
        phone="0911223344",
        address="Amhara / South Wollo Zone / Tehuledere",
        photo_path=None, # የፎቶ ፋይል ካለዎት እዚህ ጋር ስሙን ያስገቡ (ለምሳሌ "my_photo.jpg")
        font_path="nyala.ttf" # የአማርኛ ፎንት ፋይል ስም
    )
