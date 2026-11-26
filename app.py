import io
import os
import re
import textwrap
import sqlite3

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


# ---------------- FREE TRIAL SETTINGS ----------------
# Keep PAID_MODE = False while offering the 3-letter trial.
# After the client pays, change PAID_MODE to True and redeploy
# to allow unlimited letter generation.
PAID_MODE = True
TRIAL_LETTER_LIMIT = 3
TRIAL_DB_PATH = os.path.join(os.path.dirname(__file__), "trial_usage.db")


def get_trial_count():
    """Return the number of letters generated on this installation."""
    with sqlite3.connect(TRIAL_DB_PATH, timeout=20, isolation_level=None) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trial_usage (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                letters_generated INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.execute("""
            INSERT OR IGNORE INTO trial_usage (id, letters_generated)
            VALUES (1, 0)
        """)
        row = conn.execute(
            "SELECT letters_generated FROM trial_usage WHERE id = 1"
        ).fetchone()
        return int(row[0])


def use_one_trial_letter():
    """Atomically consume one trial letter; prevents simultaneous overuse."""
    with sqlite3.connect(TRIAL_DB_PATH, timeout=20, isolation_level=None) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trial_usage (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                letters_generated INTEGER NOT NULL DEFAULT 0
            )
        """)

        # Start the write transaction before any INSERT/UPDATE.
        # isolation_level=None disables sqlite3's implicit transaction,
        # preventing "cannot start a transaction within a transaction".
        conn.execute("BEGIN IMMEDIATE")
        try:
            conn.execute("""
                INSERT OR IGNORE INTO trial_usage (id, letters_generated)
                VALUES (1, 0)
            """)
            row = conn.execute(
                "SELECT letters_generated FROM trial_usage WHERE id = 1"
            ).fetchone()
            used = int(row[0])

            if used >= TRIAL_LETTER_LIMIT:
                conn.rollback()
                return False, used

            conn.execute(
                "UPDATE trial_usage SET letters_generated = ? WHERE id = 1",
                (used + 1,)
            )
            conn.commit()
            return True, used + 1
        except Exception:
            conn.rollback()
            raise


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: linear-gradient(135deg, #f4f6fc 0%, #ffffff 58%, #f8f4f0 100%); color: #20263A; }
[data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stHeader"] { background: transparent; }
.block-container { max-width: 1400px; padding-top: 2rem; padding-bottom: 3rem; }
.stApp, .stApp p, .stApp label, .stApp span, .stApp li, .stApp h1, .stApp h2, .stApp h3 { color: #20263A; }
.stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stCaptionContainer"] * { color: #687086 !important; }
.stApp [data-testid="stTextInput"] input, .stApp [data-baseweb="input"] input {
    background: #FFFFFF !important; color: #20263A !important;
    -webkit-text-fill-color: #20263A !important; border-color: #D9DEEA !important;
}
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
    """Use bundled fonts so Streamlit Cloud renders readable text consistently."""
    filename = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    bundled = os.path.join(
        os.path.dirname(__file__), "assets", "fonts", filename
    )
    if os.path.exists(bundled):
        return bundled

    # Fallback locations for local development.
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return None


def get_font(size, bold=False):
    path = font_path(bold)
    if path:
        return ImageFont.truetype(path, size)
    # Scalable fallback is not available; fail clearly instead of silently
    # generating a tiny, unreadable default bitmap font.
    raise RuntimeError(
        "Font files are missing. Ensure assets/fonts/DejaVuSans.ttf and "
        "assets/fonts/DejaVuSans-Bold.ttf are committed to GitHub."
    )


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
    # Larger canvas + larger typography so the preview is readable at page width.
    W, H = 1600, 2000
    im = Image.new("RGB", (W, H), "#F5F6FA")
    d = ImageDraw.Draw(im)

    # Main paper and refined frame
    d.rounded_rectangle((42, 36, W-42, H-36), radius=34, fill=PAPER, outline="#E5E8F0", width=3)
    d.rounded_rectangle((65, 60, W-65, H-60), radius=25, outline=NAVY, width=4)
    d.rounded_rectangle((78, 73, W-78, H-73), radius=20, outline="#D7DDF4", width=2)

    # Logo and top accent
    d.rounded_rectangle((625, 105, 975, 115), radius=5, fill=GOLD)
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "keji_foda_logo.jpg")
    logo = Image.open(logo_path).convert("RGB")
    logo.thumbnail((390, 365), Image.Resampling.LANCZOS)
    lx = (W - logo.width) // 2
    im.paste(logo, (lx, 140))
    d = ImageDraw.Draw(im)

    title_font = get_font(56, True)
    title = "APPRECIATION"
    tw = d.textbbox((0, 0), title, font=title_font)[2]
    d.text(((W-tw)//2, 535), title, font=title_font, fill=NAVY)
    d.rounded_rectangle((620, 615, 980, 624), radius=4, fill=GOLD)

    body_font = get_font(39)
    body_bold = get_font(40, True)
    x, y, maxw = 170, 685, 1260
    line_height = 51
    para_gap = 15

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
            y += line_height
        y += para_gap

    # Signature block: compact vertical rhythm while retaining clear separation.
    y += 4
    d.text((x, y), "With deep appreciation,", font=body_font, fill=INK); y += 58
    d.text((x, y), "John Alinaitwe", font=body_bold, fill=NAVY); y += 54
    d.text((x, y), "Chairperson, KEJI-FODA", font=body_font, fill=INK); y += 54
    d.text((x, y), "TEL: 0772425718", font=body_font, fill=INK); y += 54
    d.text((x, y), "Email : kejifoda2015@gmail.com", font=body_font, fill=INK)

    # Footer
    d.line((170, 1880, 1430, 1880), fill="#DCE1F2", width=3)
    footer_font = get_font(23, True)
    footer = "KEJI-FODA  •  UNITED IN CHRIST"
    fw = d.textbbox((0, 0), footer, font=footer_font)[2]
    d.text(((W-fw)//2, 1900), footer, font=footer_font, fill=RED)

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

st.subheader("1. Recipient details")
form_col, help_col = st.columns([1.15, 0.85], gap="large")

with form_col:
    recipient = st.text_input(
        "Recipient name",
        placeholder="Enter the name to appear after Dear"
    )
    phone = st.text_input(
        "WhatsApp number",
        placeholder="e.g. 0772 425 718 or +256 772 425 718"
    )
    st.caption(
        "Ugandan numbers beginning with 0 are converted to the international +256 format."
    )

with help_col:
    st.markdown("""
    <div class="panel">
      <strong>How it works</strong>
      <ol>
        <li>Enter the recipient's name and number.</li>
        <li>Generate the personalised appreciation image.</li>
        <li>Download the image and open WhatsApp.</li>
        <li>Attach the image and manually press Send.</li>
      </ol>
      <p class="small-note">The original appreciation message is preserved. Only the name after Dear changes.</p>
    </div>
    """, unsafe_allow_html=True)

trial_count = get_trial_count()
trial_remaining = max(0, TRIAL_LETTER_LIMIT - trial_count)

if not PAID_MODE:
    st.info(f"Free trial: {trial_remaining} of {TRIAL_LETTER_LIMIT} appreciation letters remaining.")
    if trial_remaining == 0:
        st.error(
            "Your 3-letter free trial has ended. "
            "Please contact the system provider to activate the full version."
        )

generate = st.button(
    "✨ Generate appreciation letter",
    type="primary",
    use_container_width=True,
    disabled=(not PAID_MODE and trial_remaining <= 0)
)

if generate:
    if not recipient.strip():
        st.error("Please enter the recipient's name.")
    else:
        allowed = True
        if not PAID_MODE:
            allowed, total_used = use_one_trial_letter()

        if not allowed:
            st.error(
                "Your 3-letter free trial has ended. "
                "Please contact the system provider to activate the full version."
            )
        else:
            st.session_state["letter_recipient"] = recipient.strip()
            st.session_state["letter_png"] = create_letter_image(recipient.strip())
            st.session_state["letter_text"] = letter_text(recipient.strip())
            st.session_state["letter_phone"] = phone.strip()

            if not PAID_MODE:
                st.success(
                    f"Letter generated. {max(0, TRIAL_LETTER_LIMIT - total_used)} "
                    "free trial letter(s) remaining."
                )

st.markdown("---")
st.subheader("2. Appreciation letter preview")

if "letter_png" in st.session_state:
    st.image(
        st.session_state["letter_png"],
        use_container_width=True,
        output_format="PNG"
    )

    safe_name = re.sub(
        r"[^A-Za-z0-9_-]+",
        "_",
        st.session_state["letter_recipient"]
    ).strip("_")
    image_filename = f"KEJI-FODA_Appreciation_{safe_name or 'Letter'}.png"

    st.download_button(
        "⬇️ Download Appreciation Image (PNG)",
        data=st.session_state["letter_png"],
        file_name=image_filename,
        mime="image/png",
        use_container_width=True
    )

    st.markdown("---")
    st.subheader("3. Send Appreciation Image")

    phone_to_use = st.text_input(
        "Recipient WhatsApp number",
        value=st.session_state.get("letter_phone", ""),
        key="confirm_phone"
    )

    normalized = normalize_phone(phone_to_use)

    if normalized and len(normalized) >= 10:

        wa_url = "https://wa.me/" + normalized

        st.link_button(
            "📷 Send Appreciation Image via WhatsApp",
            wa_url,
            use_container_width=True
        )

        st.download_button(
            "⬇️ Download Image to Attach",
            data=st.session_state["letter_png"],
            file_name=image_filename,
            mime="image/png",
            use_container_width=True
        )

        st.info(
            "WhatsApp will open the recipient's chat. "
            "Attach the downloaded appreciation image and press Send."
        )

    else:
        st.warning("Please enter a valid WhatsApp number.")

else:
    st.info("Your personalised appreciation letter will appear here after you generate it.")
    st.image(
        os.path.join(os.path.dirname(__file__), "assets", "keji_foda_logo.jpg"),
        width=220
    )

st.markdown("""
<div style="text-align:center; color:#7a8193; padding:24px 0 0 0; font-size:.82rem;">
KEJI-FODA Appreciation Letter Studio · Local generation, manual WhatsApp sending
</div>
""", unsafe_allow_html=True)
