import io
import os
import re
import textwrap
from urllib.parse import quote

import streamlit as st
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(
    page_title="KEJI-FODA Appreciation Letter",
    page_icon="💙",
    layout="wide",
)

NAVY = "#172B87"
RED = "#B92735"
GOLD = "#C9A45C"
INK = "#20263A"
MUTED = "#687086"
PAPER = "#FFFFFF"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: linear-gradient(135deg, #f4f6fc 0%, #ffffff 58%, #f8f4f0 100%); }
.block-container { max-width: 1180px; padding-top: 2rem; padding-bottom: 3rem; }
.hero { background: linear-gradient(115deg, #172B87, #263eaa); color: white; padding: 26px 30px;
        border-radius: 20px; box-shadow: 0 12px 30px rgba(23,43,135,.16); margin-bottom: 22px; }
.hero h1 { font-family: 'Playfair Display', serif; font-size: 2rem; margin: 0 0 5px 0; color: white; }
.hero p { margin: 0; color: #e7eaff; }
.panel { background: white; padding: 22px; border: 1px solid #e8ebf4; border-radius: 18px;
         box-shadow: 0 8px 24px rgba(30,45,90,.06); }
.small-note { color: #687086; font-size: .88rem; }
div.stButton > button, div.stDownloadButton > button, div.stLinkButton > a {
    border-radius: 10px; font-weight: 700; min-height: 2.8rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>KEJI-FODA · Appreciation Letter Studio</h1>
  <p>Create a personalised appreciation letter image and prepare it for manual WhatsApp sending.</p>
</div>
""", unsafe_allow_html=True)

def font_path(bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None

def get_font(size, bold=False):
    path = font_path(bold)
    return ImageFont.truetype(path, size) if path else ImageFont.load_default()

def wrap_by_pixels(draw, text, font, max_width):
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = word if not current else current + " " + word
        if draw.textbbox((0, 0), test, font=font)[2] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

def create_letter_image(recipient):
    W, H = 1200, 1600
    im = Image.new("RGB", (W, H), "#F5F6FA")
    d = ImageDraw.Draw(im)

    # Main paper and refined frame
    d.rounded_rectangle((42, 36, W-42, H-36), radius=34, fill=PAPER, outline="#E5E8F0", width=3)
    d.rounded_rectangle((65, 60, W-65, H-60), radius=25, outline=NAVY, width=4)
    d.rounded_rectangle((78, 73, W-78, H-73), radius=20, outline="#D7DDF4", width=2)

    # Top accent and logo
    d.rounded_rectangle((450, 92, 750, 101), radius=5, fill=GOLD)
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "keji_foda_logo.jpg")
    logo = Image.open(logo_path).convert("RGB")
    logo.thumbnail((300, 285), Image.Resampling.LANCZOS)
    lx = (W - logo.width) // 2
    im.paste(logo, (lx, 118))
    d = ImageDraw.Draw(im)

    title_font = get_font(43, True)
    title = "APPRECIATION"
    tw = d.textbbox((0,0), title, font=title_font)[2]
    d.text(((W-tw)//2, 420), title, font=title_font, fill=NAVY)
    d.rounded_rectangle((475, 480, 725, 487), radius=4, fill=GOLD)

    body_font = get_font(27)
    body_bold = get_font(28, True)
    x, y, maxw = 145, 535, 910
    line_gap = 13
    para_gap = 20

    paragraphs = [
        f"Dear {recipient},",
        "Greetings in the name of our Lord.",
        "On behalf of the entire KEJI-FODA family, I want to sincerely thank you for the love, support, and sacrifice you showed us during the inauguration of our New KEJI-FODA Home at Nsambya, when we  hosted our Bishop, Rt. Rev. Robert Muhiirwa Akiiki, from 22nd to 27th September 2026.",
        "Thank you for your money, your prayers, and your time. Some gave financially, some prayed for us and some gave their time and strength to serve. Every contribution, big or small, made the celebration a great success. We could not have done it without you.",
        "May the Almighty God richly bless you, your family, and your work, and repay you abundantly.",
        "We are forever grateful.",
    ]

    for idx, para in enumerate(paragraphs):
        f = body_bold if idx == 0 else body_font
        lines = wrap_by_pixels(d, para, f, maxw)
        for line in lines:
            d.text((x, y), line, font=f, fill=INK)
            y += 39
        y += para_gap

    # Signature block
    y += 2
    d.text((x, y), "With deep appreciation,", font=body_font, fill=INK); y += 49
    d.text((x, y), "John Alinaitwe", font=body_bold, fill=NAVY); y += 42
    d.text((x, y), "Chairperson, KEJI-FODA", font=body_font, fill=INK); y += 42
    d.text((x, y), "TEL: 0772425718", font=body_font, fill=INK); y += 42
    d.text((x, y), "Email : kejifoda2015@gmail.com", font=body_font, fill=INK)

    # Footer line and understated brand label
    d.line((145, 1480, 1055, 1480), fill="#DCE1F2", width=3)
    footer_font = get_font(18, True)
    footer = "KEJI-FODA  •  UNITED IN CHRIST"
    fw = d.textbbox((0,0), footer, font=footer_font)[2]
    d.text(((W-fw)//2, 1495), footer, font=footer_font, fill=RED)

    out = io.BytesIO()
    im.save(out, format="PNG", optimize=True)
    return out.getvalue()

def letter_text(recipient):
    return f"""Dear {recipient},

Greetings in the name of our Lord.

On behalf of the entire KEJI-FODA family, I want to sincerely thank you for the love, support, and sacrifice you showed us during the inauguration of our New KEJI-FODA Home at Nsambya, when we  hosted our Bishop, Rt. Rev. Robert Muhiirwa Akiiki, from 22nd to 27th September 2026.

Thank you for your money, your prayers, and your time. Some gave financially, some prayed for us and some gave their time and strength to serve. Every contribution, big or small, made the celebration a great success. We could not have done it without you.

May the Almighty God richly bless you, your family, and your work, and repay you abundantly.

We are forever grateful.

With deep appreciation,
John Alinaitwe
Chairperson, KEJI-FODA
TEL: 0772425718
Email : kejifoda2015@gmail.com"""

def normalize_phone(raw):
    digits = re.sub(r"\D", "", raw or "")
    if digits.startswith("00"):
        digits = digits[2:]
    if digits.startswith("0"):
        digits = "256" + digits[1:]
    return digits

left, right = st.columns([0.92, 1.08], gap="large")

with left:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("1. Recipient details")
    recipient = st.text_input("Recipient name", placeholder="Enter the name to appear after Dear")
    phone = st.text_input("WhatsApp number", placeholder="e.g. 0772 425 718 or +256 772 425 718")
    st.caption("Use the recipient's number. Ugandan numbers beginning with 0 are converted to +256 automatically.")
    generate = st.button("✨ Generate appreciation letter", type="primary", use_container_width=True)
    st.markdown('<p class="small-note">The appreciation message, wording, dates, contact details and signature are kept as supplied. Only the recipient name is filled in.</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("")
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("2. Sending instructions")
    st.markdown("""
1. Generate the letter.
2. Download the PNG image.
3. Press **Open WhatsApp chat**.
4. In WhatsApp, attach the downloaded PNG and send it. The message text will also be prefilled.
""")
    st.markdown('<p class="small-note">WhatsApp does not let a standard website button automatically attach and send an image. You remain in control of the final send.</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

if generate:
    if not recipient.strip():
        st.error("Please enter the recipient's name.")
    else:
        st.session_state["letter_recipient"] = recipient.strip()
        st.session_state["letter_png"] = create_letter_image(recipient.strip())
        st.session_state["letter_text"] = letter_text(recipient.strip())
        st.session_state["letter_phone"] = phone.strip()

with right:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("3. Letter preview")
    if "letter_png" in st.session_state:
        st.image(st.session_state["letter_png"], use_container_width=True)
        filename = "KEJI-FODA_Appreciation_" + re.sub(r"[^A-Za-z0-9_-]+", "_", st.session_state["letter_recipient"]).strip("_") + ".png"
        st.download_button(
            "⬇️ Download letter image (PNG)",
            data=st.session_state["letter_png"],
            file_name=filename,
            mime="image/png",
            use_container_width=True,
        )
        st.markdown("---")
        st.subheader("4. WhatsApp")
        phone_to_use = st.text_input("Confirm WhatsApp number", value=st.session_state.get("letter_phone", ""), key="confirm_phone")
        normalized = normalize_phone(phone_to_use)
        if normalized and len(normalized) >= 10:
            wa_url = "https://wa.me/" + normalized + "?text=" + quote(st.session_state["letter_text"])
            st.link_button("💬 Open WhatsApp chat with letter text", wa_url, use_container_width=True)
        else:
            st.info("Enter a valid WhatsApp number above, then generate the letter or confirm the number here.")
        with st.expander("View exact WhatsApp message text"):
            st.text(st.session_state["letter_text"])
    else:
        st.info("Your personalised appreciation letter will appear here after you enter a name and press Generate.")
        st.image(os.path.join(os.path.dirname(__file__), "assets", "keji_foda_logo.jpg"), width=210)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center; color:#7a8193; padding:24px 0 0 0; font-size:.82rem;">
KEJI-FODA Appreciation Letter Studio · Local generation, manual WhatsApp sending
</div>
""", unsafe_allow_html=True)
