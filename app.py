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

PAID_MODE = False

TRIAL_LETTER_LIMIT = 3
TRIAL_DOWNLOAD_LIMIT = 3

# Increase this number to reset everyone's trial.
TRIAL_RESET_VERSION = 3

TRIAL_DB_PATH = os.path.join(
    os.path.dirname(__file__),
    "trial_usage.db"
)

def ensure_trial_usage(conn):
    """Create trial table and reset all counters when reset version changes."""

    conn.execute("""
        CREATE TABLE IF NOT EXISTS trial_usage (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            letters_generated INTEGER NOT NULL DEFAULT 0,
            downloads_generated INTEGER NOT NULL DEFAULT 0,
            reset_version INTEGER NOT NULL DEFAULT 0
        )
    """)

    columns = {
        row[1]
        for row in conn.execute(
            "PRAGMA table_info(trial_usage)"
        ).fetchall()
    }

    if "downloads_generated" not in columns:
        conn.execute("""
            ALTER TABLE trial_usage
            ADD COLUMN downloads_generated INTEGER NOT NULL DEFAULT 0
        """)

    if "reset_version" not in columns:
        conn.execute("""
            ALTER TABLE trial_usage
            ADD COLUMN reset_version INTEGER NOT NULL DEFAULT 0
        """)

    conn.execute("BEGIN IMMEDIATE")

    try:
        conn.execute("""
            INSERT OR IGNORE INTO trial_usage
            (id, letters_generated, downloads_generated, reset_version)
            VALUES (1, 0, 0, ?)
        """, (TRIAL_RESET_VERSION,))

        current_version = conn.execute("""
            SELECT reset_version
            FROM trial_usage
            WHERE id = 1
        """).fetchone()[0]

        if current_version != TRIAL_RESET_VERSION:
            conn.execute("""
                UPDATE trial_usage
                SET letters_generated = 0,
                    downloads_generated = 0,
                    reset_version = ?
                WHERE id = 1
            """, (TRIAL_RESET_VERSION,))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

def get_trial_count():
    with sqlite3.connect(
        TRIAL_DB_PATH, timeout=20, isolation_level=None
    ) as conn:
        ensure_trial_usage(conn)
        return conn.execute(
            "SELECT letters_generated FROM trial_usage WHERE id = 1"
        ).fetchone()[0]


def get_trial_download_count():
    with sqlite3.connect(
        TRIAL_DB_PATH, timeout=20, isolation_level=None
    ) as conn:
        ensure_trial_usage(conn)
        return conn.execute(
            "SELECT downloads_generated FROM trial_usage WHERE id = 1"
        ).fetchone()[0]


def use_one_trial_letter():
    with sqlite3.connect(
        TRIAL_DB_PATH, timeout=20, isolation_level=None
    ) as conn:
        ensure_trial_usage(conn)
        conn.execute("BEGIN IMMEDIATE")

        try:
            used = conn.execute(
                "SELECT letters_generated FROM trial_usage WHERE id = 1"
            ).fetchone()[0]

            if used >= TRIAL_LETTER_LIMIT:
                conn.rollback()
                return False, used

            used += 1

            conn.execute("""
                UPDATE trial_usage
                SET letters_generated = ?
                WHERE id = 1
            """, (used,))

            conn.commit()
            return True, used

        except Exception:
            conn.rollback()
            raise


def use_one_trial_download():
    with sqlite3.connect(
        TRIAL_DB_PATH, timeout=20, isolation_level=None
    ) as conn:
        ensure_trial_usage(conn)
        conn.execute("BEGIN IMMEDIATE")

        try:
            used = conn.execute(
                "SELECT downloads_generated FROM trial_usage WHERE id = 1"
            ).fetchone()[0]

            if used >= TRIAL_DOWNLOAD_LIMIT:
                conn.rollback()
                return False, used

            used += 1

            conn.execute("""
                UPDATE trial_usage
                SET downloads_generated = ?
                WHERE id = 1
            """, (used,))

            conn.commit()
            return True, used

        except Exception:
            conn.rollback()
            raise


def record_trial_download_click():
    """Streamlit download-button callback."""
    if PAID_MODE:
        return
    allowed, used = use_one_trial_download()
    st.session_state["trial_download_blocked"] = not allowed
    st.session_state["trial_downloads_used"] = used


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
    # Last-resort fallback: keep the app running if font assets were not uploaded.
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


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
    """
    Create a premium KEJI-FODA appreciation e-card.
    Keeps the supplied appreciation wording unchanged; only inserts the recipient name.
    """
    W, H = 1400, 2100
    im = Image.new("RGB", (W, H), "#F7F2E8")
    d = ImageDraw.Draw(im)

    # Warm ivory base with layered navy and gold frames
    d.rounded_rectangle((24, 24, W-24, H-24), radius=58,
                        fill="#FFFDF8", outline="#C8A45D", width=7)
    d.rounded_rectangle((48, 48, W-48, H-48), radius=46,
                        outline="#172B78", width=5)
    d.rounded_rectangle((66, 66, W-66, H-66), radius=36,
                        outline="#E8D6A8", width=3)

    # Deep navy header/footer panels give the card a richer greeting-card finish
    d.rounded_rectangle((72, 78, W-72, 350), radius=34, fill="#172B78")
    d.rectangle((72, 295, W-72, 350), fill="#172B78")
    d.rounded_rectangle((72, 1880, W-72, H-78), radius=34, fill="#172B78")
    d.rectangle((72, 1880, W-72, 1918), fill="#172B78")

    # Gold header detailing and corner ornaments
    d.rounded_rectangle((440, 105, 960, 116), radius=5, fill="#D9B765")
    d.ellipse((416, 101, 440, 125), fill="#F5E5B9", outline="#D9B765", width=3)
    d.ellipse((960, 101, 984, 125), fill="#F5E5B9", outline="#D9B765", width=3)
    for cx in (112, W-112):
        d.ellipse((cx-13, 135, cx+13, 161), outline="#E7CB83", width=3)
        d.ellipse((cx-5, 143, cx+5, 153), fill="#E7CB83")

    # Logo medallion: white with a gold ring and subtle navy outer ring
    d.ellipse((W//2-220, 125, W//2+220, 565),
              fill="#FFFFFF", outline="#D9B765", width=8)
    d.ellipse((W//2-205, 140, W//2+205, 550),
              outline="#172B78", width=3)
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "keji_foda_logo.jpg")
    logo = Image.open(logo_path).convert("RGB")
    logo.thumbnail((365, 365), Image.Resampling.LANCZOS)
    lx = (W-logo.width)//2
    ly = 150 + (365-logo.height)//2
    im.paste(logo, (lx, ly))
    d = ImageDraw.Draw(im)

    # Heading on a warm white title plaque
    d.rounded_rectangle((250, 585, 1150, 735), radius=28,
                        fill="#FFF9E9", outline="#D9B765", width=3)
    title_font = get_font(58, True)
    title = "APPRECIATION"
    tw = d.textbbox((0, 0), title, font=title_font)[2]
    d.text(((W-tw)//2, 602), title, font=title_font, fill="#172B78")

    subtitle_font = get_font(24, True)
    subtitle = "WITH GRATITUDE FROM THE KEJI-FODA FAMILY"
    sw = d.textbbox((0, 0), subtitle, font=subtitle_font)[2]
    d.text(((W-sw)//2, 680), subtitle, font=subtitle_font, fill="#9A702A")

    # Decorative gold divider with a central diamond
    d.rounded_rectangle((360, 765, 1040, 774), radius=4, fill="#D1AD5B")
    d.polygon([(700, 754), (712, 769), (700, 784), (688, 769)], fill="#B58A3B")

    # Original appreciation wording. Only the recipient's name is personalised.
    paragraphs = [
        f"Dear {recipient},",
        "Greetings in the name of our Lord.",
        "On behalf of the entire KEJI-FODA family, I want to sincerely thank you for the love, support, and sacrifice you showed us during the inauguration of our New KEJI-FODA Home at Nsambya, when we  hosted our Bishop, Rt. Rev. Robert Muhiirwa Akiiki, from 22nd to 27th September 2026.",
        "Thank you for your money, your prayers, and your time. Some gave financially, some prayed for us and some gave their time and strength to serve. Every contribution, big or small, made the celebration a great success. We could not have done it without you.",
        "May the Almighty God richly bless you, your family, and your work, and repay you abundantly.",
        "We are forever grateful.",
    ]

    # Message panel in pale champagne with a gold left accent
    panel = (105, 805, W-105, 1825)
    d.rounded_rectangle(panel, radius=32, fill="#FFFCF4",
                        outline="#E5D4AA", width=3)
    d.rounded_rectangle((105, 835, 122, 1545), radius=8, fill="#D1AD5B")
    d.rounded_rectangle((1278, 835, 1295, 1545), radius=8, fill="#E9DAB8")

    body_x, body_y, body_width = 165, 845, 1070
    body_font = get_font(32)
    greeting_font = get_font(35, True)
    line_height = 39
    paragraph_gap = 12

    for idx, para in enumerate(paragraphs):
        font = greeting_font if idx == 0 else body_font
        color = "#172B78" if idx == 0 else "#30384B"
        lines = wrap_by_pixels(d, para, font, body_width)
        for line in lines:
            d.text((body_x, body_y), line, font=font, fill=color)
            body_y += line_height
        body_y += paragraph_gap

    # Signature block; preserve exact wording and contact details
    body_y += 2
    sign_font = get_font(29)
    sign_bold = get_font(31, True)
    sign_lines = [
        ("With deep appreciation,", sign_font, "#30384B", 36),
        ("John Alinaitwe", sign_bold, "#172B78", 39),
        ("Chairperson, KEJI-FODA", sign_font, "#30384B", 36),
        ("TEL: 0772425718", sign_font, "#30384B", 36),
        ("Email : kejifoda2015@gmail.com", sign_font, "#30384B", 36),
    ]
    for text, font, color, advance in sign_lines:
        d.text((body_x, body_y), text, font=font, fill=color)
        body_y += advance

    # Footer message in gold on navy, framed by a gold flourish
    d.rounded_rectangle((470, 1925, 930, 1934), radius=4, fill="#D9B765")
    footer_font = get_font(30, True)
    footer = "UNITED IN CHRIST"
    fw = d.textbbox((0, 0), footer, font=footer_font)[2]
    d.text(((W-fw)//2, 1960), footer, font=footer_font, fill="#F6E6B8")

    # Small gold decorative marks at the footer corners
    for cx in (145, W-145):
        d.ellipse((cx-10, 2010, cx+10, 2030), outline="#D9B765", width=3)

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
with help_col:
    st.markdown("""
    <div class="panel">
      <strong>How it works</strong>
      <ol>
        <li>Enter the recipient's name.</li>
        <li>Generate the personalised appreciation image.</li>
        <li>Download your finished appreciation e-card.</li>
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

            if not PAID_MODE:
                st.success(
                    f"Letter generated. {max(0, TRIAL_LETTER_LIMIT - total_used)} "
                    "free trial letter(s) remaining."
                )

st.markdown("---")
st.subheader("2. Appreciation e-card preview")

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

    if PAID_MODE:
        download_remaining = None
        download_disabled = False
    else:
        downloads_used = get_trial_download_count()
        download_remaining = max(0, TRIAL_LETTER_LIMIT - downloads_used)
        download_disabled = download_remaining <= 0
        st.caption(
            f"Free trial downloads remaining: {download_remaining} of {TRIAL_LETTER_LIMIT}."
        )
        if download_disabled:
            st.warning(
                "Your 3 free e-card downloads have been used. "
                "Please contact the system provider to activate the full version."
            )

    st.download_button(
        "⬇️ Download Appreciation Image (PNG)",
        data=st.session_state["letter_png"],
        file_name=image_filename,
        mime="image/png",
        use_container_width=True,
        disabled=download_disabled,
        on_click=None if PAID_MODE else record_trial_download_click,
        key="download_appreciation_ecard",
    )

    if st.session_state.pop("trial_download_blocked", False):
        st.error(
            "Your 3 free e-card downloads have been used. "
            "Please contact the system provider to activate the full version."
        )

else:
    st.info("Your personalised KEJI-FODA appreciation e-card will appear here after you generate it.")
    st.image(
        os.path.join(os.path.dirname(__file__), "assets", "keji_foda_logo.jpg"),
        width=220
    )

st.markdown("""
<div style="text-align:center; color:#7a8193; padding:24px 0 0 0; font-size:.82rem;">
KEJI-FODA Appreciation E-card Studio
</div>
""", unsafe_allow_html=True)
