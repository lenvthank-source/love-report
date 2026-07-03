"""
build_template.py  — 26-page static HTML template builder
Run once: python scratch/build_template.py
"""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.page_graphics import get_bottom_scene, get_page_watermark

WORKSPACE   = "e:/Report-Engine"
COVER_PATH  = f"file:///{WORKSPACE}/Coverpage.png"
BORDER_PATH = f"file:///{WORKSPACE}/PageBorder.png"
TOTAL_PAGES = 26

# ── Page meta (heading text + italic tagline) ─────────────────────────────────
PAGE_META = {
    2:  ("Your Cosmic Profile",
         "Your personal birth details — the foundation of every insight in this report."),
    3:  ("The Spiritual Disclaimer",
         "Framing this report as a sacred tool for emotional evolution, rooted in Vedic wisdom."),
    5:  ("Master Index",
         "A complete map of the twenty-six page journey ahead."),
    6:  ("Technical Astral Map — D1 Birth Chart",
         '"The celestial map that reveals who you were born to become."'),
    7:  ("1st House Energy — Nature & Core Essence",
         '"Discover how the world sees you… and who you truly are beneath it."'),
    8:  ("Moon Sign — Your Emotional Sanctuary",
         '"Your emotional language, hidden fears, comfort zones and deepest needs."'),
    9:  ("5th House Energy — The Spark of Romance",
         '"Understand your attraction style, dating patterns and emotional chemistry."'),
    10: ("The Language of Venus Conjunctions",
         '"The energy you radiate in relationships — and the kind of love you attract."'),
    11: ("Divisional Charts — D9 Navamsa & D30 Trimsamsha",
         '"The charts that reveal what unfolds when you think \'this is the one.\'"'),
    12: ("7th House Energy — The Sacred Sanctuary of Marriage",
         '"Decode the emotional foundation of your lifelong relationship."'),
    13: ("7th House Lord & Rashi — Your Spouse\'s Core Nature",
         '"Personality, appearance, emotional nature and relationship dynamics."'),
    14: ("The D1 Natal Promise vs. The D9 Navamsa Fruit",
         '"See how your love story evolves from youthful attraction to mature partnership."'),
    15: ("The D9 Navamsa Revelation — Inner Marital Dynamics",
         '"The hidden emotional world of your marriage and long-term compatibility."'),
    16: ("The D30 Trimsamsha Analysis — Unmasking Loyalty",
         '"Reveal unseen emotional wounds, loyalty tests and karmic challenges."'),
    17: ("Recurring Relationship Patterns & Karmic Loops",
         '"Identify recurring heartbreaks before they become lifelong habits."'),
    18: ("Planetary Blockages & Relationship Vulnerabilities",
         '"The astrological influences delaying connection and emotional peace."'),
    19: ("Cosmic Red Flags & Elemental Mismatches",
         '"Recognise the energies and personalities most likely to challenge your heart."'),
    20: ("The Comprehensive Relationship Risk Matrix",
         '"A clear summary of strengths, growth opportunities, and emotional patterns."'),
    21: ("Cosmic Seasons of Your Heart — Vimshottari Dasha Overview",
         '"Every relationship has its season. Discover yours."'),
    22: ("3-Year Advanced Dasha Forecast",
         '"The years and planetary periods most supportive for romance and commitment."'),
    23: ("Precision Sub-Minor Forecast — Pratyantar Dasha Tracking",
         '"Pinpoint the months where destiny quietly shifts in your favour."'),
    24: ("Mantras & Behavioural Shifts for Emotional Healing",
         '"Practical spiritual practices to release baggage and invite healthier love."'),
    25: ("Practical Remedies — Sacred Alignments & Ritual Clearances",
         '"Tailored rituals, gemstones and spiritual alignments designed for your chart."'),
    26: ("The Final Heart Synthesis & Sign-Off",
         '"A gentle reminder of who you are becoming — and the love you are truly meant for."'),
}

TOC_CARDS = [
    ("01", "Customer Profile\n&amp; Introduction",      "Pages 2 – 4",  "♡"),
    ("02", "Core Cosmic Personality\n&amp; Soul Mirror", "Pages 5 – 10", "✦"),
    ("03", "Marriage Gateway\n&amp; Divisional Charts",  "Pages 11 – 16","⊕"),
    ("04", "Karmic Loops\n&amp; Cosmic Red Flags",       "Pages 17 – 20","⚡"),
    ("05", "Sacred Timeline\n&amp; Planetary Seasons",   "Pages 21 – 23","◑"),
    ("06", "Practical Remedies\n&amp; Final Synthesis",  "Pages 24 – 26","❋"),
]

# ── Fixed author message text (condensed to fit one page) ────────────────────
AUTHOR_MESSAGE_HTML = """\
      <p class="author-salutation">Dear Reader, ✨</p>

      <p>Thank you for placing your trust in me and choosing this Personalised Love Analysis Report.
      It is a true honour to accompany you on this deeply personal journey toward understanding one of
      life&rsquo;s most profound experiences &mdash; love. Every relationship, whether it brings joy or
      heartbreak, carries a lesson waiting to be understood, and this report has been carefully prepared
      to help you discover those lessons with clarity and compassion.</p>

      <p>Through the timeless wisdom of Vedic Astrology, these pages will help you understand your
      emotional nature, recurring relationship patterns, karmic lessons, and the cosmic timing of your
      love journey. Remember &mdash; astrology is not a verdict, it is a map. The stars reveal
      possibilities, strengths, and timings, but every choice you make continues to shape your destiny.
      Let these insights become a source of awareness rather than fear, and confidence rather than
      confusion.</p>

      <p>May this report offer you the clarity you seek, the reassurance you deserve, and the wisdom
      to welcome love with an open heart and a peaceful mind. The power to walk your path has always
      been &mdash; and will always remain &mdash; yours.</p>

      <div class="author-sign-off">
        <div class="author-sign-text">With heartfelt blessings,</div>
        <div class="author-name">Acharya Savvy Singh</div>
        <div class="author-title">Astrologer &bull; Numerologist &bull; Vastu Consultant</div>
      </div>
"""


# ── CSS ───────────────────────────────────────────────────────────────────────
CSS = r"""
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400;1,600&family=Lora:ital,wght@0,400;0,500;0,600;1,400;1,500&display=swap');

    @page { size: A4; margin: 0; }
    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: 'Lora', 'Georgia', 'Times New Roman', serif;
      font-weight: 400;
      background: #FAF8F5;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
      color: #1E1A18;
    }

    /* ── Page shell ── */
    .page {
      width: 210mm;
      height: 297mm;
      position: relative;
      page-break-after: always;
      overflow: hidden;
      background-size: 100% 100%;
      background-repeat: no-repeat;
    }
    .cover-page  { background-image: url("COVER_PATH_TOKEN"); }
    .content-page {
      background-image: url("BORDER_PATH_TOKEN");
      display: flex;
      flex-direction: column;
    }

    /* ── Content zone — increased top padding to clear border leaf decorations ── */
    .content-zone {
      padding: 36mm 24mm 22mm 24mm;
      flex: 1;
      min-height: 0;
      overflow: hidden;
      position: relative;
      z-index: 1;
    }

    /* ── Page number ── */
    .page-num {
      position: absolute;
      bottom: 7mm;
      left: 0;
      right: 0;
      text-align: center;
      font-family: 'Lora', serif;
      font-size: 13px;
      font-style: italic;
      font-weight: 400;
      letter-spacing: 1px;
      color: #6E5A50;
      z-index: 3;
    }

    /* ── Page heading ── */
    .page-heading {
      font-family: 'Cormorant Garamond', Georgia, serif;
      font-size: 22px;
      font-weight: 700;
      color: #2C1F1B;
      text-transform: uppercase;
      letter-spacing: 3px;
      border-bottom: 1.2px solid rgba(142,110,94,0.3);
      padding-bottom: 8px;
      margin-top: 22px;
      margin-bottom: 0;           /* subtitle sits immediately below */
    }
    .page-heading:first-child { margin-top: 0; }

    /* ── Tagline — BOXED style on every page, never repeated ── */
    .page-subtitle {
      font-family: 'Lora', serif;
      font-size: 17px;
      font-style: italic;
      font-weight: 400;
      color: #5D4035;
      background: rgba(212,166,140,0.12);
      border-left: 3.5px solid #C9967B;
      border-radius: 0 5px 5px 0;
      padding: 10px 18px;
      margin-top: 10px;
      margin-bottom: 28px;
      line-height: 1.7;
    }

    /* ── Body text ── */
    p {
      font-family: 'Lora', serif;
      font-size: 16px;
      font-weight: 400;
      line-height: 2.0;
      color: #1E1A18;
      margin-bottom: 22px;
      text-align: justify;
    }
    h3 {
      font-family: 'Cormorant Garamond', serif;
      font-size: 19px;
      font-weight: 600;
      color: #4A3028;
      margin-top: 22px;
      margin-bottom: 16px;
    }
    ul { margin: 0 0 22px 0; padding-left: 24px; }
    li {
      font-family: 'Lora', serif;
      font-size: 16px;
      font-weight: 400;
      line-height: 2.0;
      color: #1E1A18;
      margin-bottom: 8px;
    }
    blockquote {
      font-family: 'Lora', serif;
      font-size: 16px;
      font-style: italic;
      color: #6E4F40;
      border-left: 3.5px solid #C9967B;
      margin: 16px 0 22px 0;
      padding: 10px 18px;
      background: rgba(212,166,140,0.07);
      border-radius: 0 5px 5px 0;
      line-height: 2.0;
    }
    strong { font-weight: 600; }

    /* ── Customer info page (page 2) ── */
    .customer-profile-wrap {
      display: flex;
      flex-direction: column;
      gap: 28px;
      margin-top: 8px;
    }
    .customer-details-grid {
      border: 1px solid rgba(201,150,123,0.4);
      border-radius: 7px;
      overflow: hidden;
    }
    .detail-row {
      display: flex;
      border-bottom: 1px solid rgba(201,150,123,0.2);
      align-items: stretch;
    }
    .detail-row:last-child { border-bottom: none; }
    .detail-label {
      width: 36%;
      padding: 12px 16px;
      font-family: 'Cormorant Garamond', serif;
      font-size: 14px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 1.5px;
      color: #8E6E5E;
      background: rgba(243,237,228,0.65);
      border-right: 1px solid rgba(201,150,123,0.25);
      display: flex;
      align-items: center;
    }
    .detail-value {
      padding: 12px 18px;
      font-family: 'Lora', serif;
      font-size: 17px;
      font-weight: 500;
      color: #2C1F1B;
      line-height: 1.5;
      display: flex;
      align-items: center;
    }
    .customer-intro {
      font-family: 'Lora', serif;
      font-size: 16px;
      font-style: italic;
      line-height: 2.0;
      color: #3B2E2B;
      border-left: 3.5px solid #C9967B;
      padding-left: 18px;
    }

    /* ── Author message (page 4) — no subtitle div here, quote is first element ── */
    .author-salutation {
      font-family: 'Cormorant Garamond', serif;
      font-size: 18px;
      font-weight: 600;
      color: #3B2E2B;
      margin-bottom: 20px;
    }
    .author-sign-off {
      margin-top: 24px;
      padding-top: 14px;
      border-top: 1px solid rgba(142,110,94,0.25);
      text-align: right;
    }
    .author-sign-text  { font-family: 'Lora', serif; font-size: 16px; color: #5D4035; margin-bottom: 6px; font-style: italic; }
    .author-name       { font-family: 'Cormorant Garamond', serif; font-size: 20px; font-weight: 700; color: #2C1F1B; margin-bottom: 5px; }
    .author-title      { font-family: 'Lora', serif; font-size: 14px; color: #8E6E5E; letter-spacing: 0.6px; }

    /* ── Master Index cards ── */
    .toc-header-wrap {
      text-align: center;
      margin-bottom: 22px;
    }
    .toc-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 18px;
    }
    .toc-card {
      position: relative;
      background: linear-gradient(135deg, rgba(243,237,228,0.85) 0%, rgba(212,166,140,0.18) 100%);
      border: 1px solid rgba(201,150,123,0.4);
      border-radius: 9px;
      padding: 20px 18px 16px 18px;
      overflow: hidden;
      min-height: 110px;
    }
    .toc-card::before {
      content: '';
      position: absolute;
      top: 0; left: 0;
      width: 4px;
      height: 100%;
      background: linear-gradient(to bottom, #C9967B, #E8C9B6);
      border-radius: 9px 0 0 9px;
    }
    .toc-card-ghost-num {
      position: absolute;
      top: 4px;
      right: 12px;
      font-family: 'Cormorant Garamond', serif;
      font-size: 52px;
      font-weight: 700;
      color: rgba(201,150,123,0.18);
      line-height: 1;
      pointer-events: none;
    }
    .toc-card-icon {
      font-size: 22px;
      color: #C9967B;
      margin-bottom: 8px;
      display: block;
    }
    .toc-card-title {
      font-family: 'Cormorant Garamond', serif;
      font-size: 17px;
      font-weight: 600;
      color: #2C1F1B;
      line-height: 1.4;
      margin-bottom: 10px;
      position: relative;
      z-index: 1;
    }
    .toc-card-pages {
      font-family: 'Lora', serif;
      font-size: 14px;
      font-style: italic;
      color: #C9967B;
      font-weight: 500;
    }

    /* ── Chart containers ── */
    .chart-single { width: 270px; height: 270px; margin: 14px auto 10px; }
    .chart-double { display: flex; justify-content: center; gap: 28px; margin: 14px 0 10px; }
    .chart-box    { width: 220px; height: 220px; }
    .chart-label  {
      text-align: center;
      font-family: 'Lora', serif;
      font-size: 15px;
      font-style: italic;
      color: #6E4F40;
      margin-bottom: 10px;
      line-height: 1.5;
    }

    /* ── Data tables ── */
    .data-table {
      width: 100%;
      border-collapse: collapse;
      margin: 14px 0 22px;
    }
    .data-table th, .data-table td {
      border: 0.7px solid rgba(142,110,94,0.35);
      padding: 9px 12px;
      font-size: 15px;
      text-align: left;
      vertical-align: top;
      line-height: 1.7;
    }
    .data-table th {
      background: rgba(243,237,228,0.85);
      font-family: 'Cormorant Garamond', serif;
      font-weight: 700;
      font-size: 14px;
      color: #2C1F1B;
      text-transform: uppercase;
      letter-spacing: 0.8px;
    }
    .data-table td { font-family: 'Lora', serif; color: #1E1A18; }
    .data-table tr:nth-child(even) td { background: rgba(243,237,228,0.4); }
"""


# ── Helper builders ────────────────────────────────────────────────────────────

def _scene_div(page_num: int) -> str:
    """Bottom scene illustrations disabled."""
    return ""


def _page_num_div(page_num: int) -> str:
    return f'    <div class="page-num">— {page_num} of {TOTAL_PAGES} —</div>\n'


def _heading_and_subtitle(page_num: int, custom_heading: str = "", custom_sub: str = "") -> str:
    if custom_heading:
        h, s = custom_heading, custom_sub
    elif page_num in PAGE_META:
        h, s = PAGE_META[page_num]
    else:
        return ""
    return (
        f'      <div class="page-heading">{h}</div>\n'
        f'      <div class="page-subtitle">{s}</div>\n'
    )


# ── Page builders ──────────────────────────────────────────────────────────────

def build_customer_page() -> str:
    return f"""  <!-- PAGE 2: CUSTOMER PROFILE -->
  <div class="page content-page" id="page-2">
    <div class="content-zone">
{_heading_and_subtitle(2)}
      <div class="customer-profile-wrap">
        <div class="customer-details-grid">
          <div class="detail-row">
            <span class="detail-label">Full Name</span>
            <span class="detail-value">{{{{CLIENT_FULL_NAME}}}}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Date of Birth</span>
            <span class="detail-value">{{{{CLIENT_DOB}}}}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Time of Birth</span>
            <span class="detail-value">{{{{CLIENT_TOB}}}}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Place of Birth</span>
            <span class="detail-value">{{{{CLIENT_POB}}}}</span>
          </div>
        </div>
        <div class="customer-intro">{{{{CLIENT_INTRO}}}}</div>
      </div>
    </div>
{_scene_div(2)}{_page_num_div(2)}  </div>
"""


def build_author_page() -> str:
    """Page 4 — fixed author text. Subtitle shown ONLY inside the boxed quote, not as a separate div."""
    return f"""  <!-- PAGE 4: MESSAGE FROM THE AUTHOR (fixed text, no subtitle div) -->
  <div class="page content-page" id="page-4">
    <div class="content-zone">
      <div class="page-heading">A Message From the Author</div>
      <div class="page-subtitle">&#8220;The stars may reveal your path, but the power to walk it has always been yours.&#8221; ✨</div>
{AUTHOR_MESSAGE_HTML}
    </div>
{_scene_div(4)}{_page_num_div(4)}  </div>
"""


def build_toc_page() -> str:
    cards = ""
    for num, title, pages, icon in TOC_CARDS:
        # Replace \n with <br> for two-line titles
        title_html = title.replace("\n", "<br>")
        cards += f"""        <div class="toc-card">
          <span class="toc-card-ghost-num">{num}</span>
          <span class="toc-card-icon">{icon}</span>
          <div class="toc-card-title">{title_html}</div>
          <div class="toc-card-pages">{pages}</div>
        </div>
"""
    return f"""  <!-- PAGE 5: MASTER INDEX -->
  <div class="page content-page" id="page-5">
    <div class="content-zone">
      <div class="page-heading" style="text-align:center;">Master Index</div>
      <div class="page-subtitle" style="text-align:center;">A complete map of the twenty-six page journey ahead.</div>
      <div class="toc-grid">
{cards}      </div>
    </div>
{_scene_div(5)}{_page_num_div(5)}  </div>
"""


def build_d1_page() -> str:
    return f"""  <!-- PAGE 6: D1 BIRTH CHART -->
  <div class="page content-page" id="page-6">
    <div class="content-zone">
{_heading_and_subtitle(6)}
      <div class="chart-single">{{{{D1_CHART_SVG}}}}</div>
      <div class="chart-label">D1 Birth Chart &mdash; Lagna (Ascendant): <strong>{{{{LAGNA_SIGN}}}}</strong></div>
      <p>This chart is a snapshot of the cosmos at the exact moment of your birth. Each house is
      numbered from your Ascendant sign, mapping the alignment of all planetary energies across
      every dimension of your life — from identity and relationships to career and spirituality.</p>
    </div>
{_scene_div(6)}{_page_num_div(6)}  </div>
"""


def build_d9d30_page() -> str:
    return f"""  <!-- PAGE 11: D9 & D30 CHARTS -->
  <div class="page content-page" id="page-11">
    <div class="content-zone">
{_heading_and_subtitle(11)}
      <div class="chart-double">
        <div>
          <div class="chart-box">{{{{D9_CHART_SVG}}}}</div>
          <div class="chart-label">D9 Navamsa &mdash; <strong>{{{{NAVAMSA_SIGN}}}}</strong></div>
        </div>
        <div>
          <div class="chart-box">{{{{D30_CHART_SVG}}}}</div>
          <div class="chart-label">D30 Trimsamsha &mdash; <strong>{{{{TRIMSAMSHA_SIGN}}}}</strong></div>
        </div>
      </div>
      <p>The <strong>D9 Navamsa</strong> reveals the inner landscape of your marriage and long-term
      spiritual growth. The <strong>D30 Trimsamsha</strong> unmasks hidden psychological patterns,
      loyalty tests, and the karmic challenges you are called to transcend through love.</p>
    </div>
{_scene_div(11)}{_page_num_div(11)}  </div>
"""


def build_risk_matrix_page() -> str:
    return f"""  <!-- PAGE 20: RISK MATRIX -->
  <div class="page content-page" id="page-20">
    <div class="content-zone">
{_heading_and_subtitle(20)}
      <table class="data-table">
        <thead>
          <tr><th>Core Challenge</th><th>Psychological Impact</th><th>Transformative Solution</th></tr>
        </thead>
        <tbody>{{{{RISK_MATRIX_ROWS}}}}</tbody>
      </table>
      {{{{SECTION_19}}}}
    </div>
{_scene_div(20)}{_page_num_div(20)}  </div>
"""


def build_dasha_forecast_page() -> str:
    return f"""  <!-- PAGE 22: 3-YEAR DASHA FORECAST -->
  <div class="page content-page" id="page-22">
    <div class="content-zone">
{_heading_and_subtitle(22)}
      <table class="data-table">
        <thead>
          <tr><th>Dasha Period</th><th>Date Range</th><th>Active Theme &amp; Spiritual Energy</th></tr>
        </thead>
        <tbody>{{{{DASHA_TIMELINE_ROWS}}}}</tbody>
      </table>
      {{{{SECTION_21}}}}
    </div>
{_scene_div(22)}{_page_num_div(22)}  </div>
"""


# Standard page: section_key = old sections[] dict key
STANDARD_PAGES = {
    3:  2,   7:  6,   8:  7,   9:  8,   10: 9,
    12: 11,  13: 12,  14: 13,  15: 14,  16: 15,
    17: 16,  18: 17,  19: 18,  21: 20,
    23: 22,  24: 23,  25: 24,  26: 25,
}


def build_standard_page(page_num: int, section_key: int) -> str:
    if page_num not in PAGE_META:
        return ""
    h, s = PAGE_META[page_num]
    return f"""  <!-- PAGE {page_num} -->
  <div class="page content-page" id="page-{page_num}">
    <div class="content-zone">

      <div class="page-heading">{h}</div>
      <div class="page-subtitle">{s}</div>

      {{{{SECTION_{section_key}}}}}

    </div>
{_scene_div(page_num)}{_page_num_div(page_num)}  </div>
"""


# ── Assemble ──────────────────────────────────────────────────────────────────

def build_template() -> str:
    css = CSS.replace("COVER_PATH_TOKEN", COVER_PATH).replace("BORDER_PATH_TOKEN", BORDER_PATH)

    parts = [
        "<!DOCTYPE html>",
        "<html lang='en'>",
        "<head>",
        "  <meta charset='utf-8'>",
        "  <meta name='viewport' content='width=device-width, initial-scale=1'>",
        "  <title>Cosmic Individual Love &amp; Marriage Report</title>",
        f"  <style>{css}  </style>",
        "</head>",
        "<body>",
        "",
        "  <!-- PAGE 1: COVER -->",
        '  <div class="page cover-page" id="page-1"></div>',
        "",
        build_customer_page(),
        build_standard_page(3, 2),   # Disclaimer
        build_author_page(),          # Fixed author message
        build_toc_page(),             # Master Index
        build_d1_page(),              # D1 Chart
    ]

    for pg, sk in [(7,6),(8,7),(9,8),(10,9)]:
        parts.append(build_standard_page(pg, sk))

    parts.append(build_d9d30_page())  # D9/D30 charts

    for pg, sk in [(12,11),(13,12),(14,13),(15,14),(16,15),(17,16),(18,17),(19,18)]:
        parts.append(build_standard_page(pg, sk))

    parts.append(build_risk_matrix_page())       # Page 20
    parts.append(build_standard_page(21, 20))   # Dasha overview
    parts.append(build_dasha_forecast_page())    # Page 22

    for pg, sk in [(23,22),(24,23),(25,24),(26,25)]:
        parts.append(build_standard_page(pg, sk))

    parts += ["</body>", "</html>"]
    return "\n".join(parts)


if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "..", "src", "templates")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "report_template.html")
    template = build_template()
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(template)
    size_kb = len(template.encode()) // 1024
    print(f"[OK] Template written to {os.path.abspath(out_path)}")
    print(f"     Size: {size_kb} KB | Pages: {TOTAL_PAGES}")

    required = [
        "{{CLIENT_FULL_NAME}}", "{{CLIENT_DOB}}", "{{CLIENT_TOB}}",
        "{{CLIENT_POB}}", "{{CLIENT_INTRO}}",
        "{{D1_CHART_SVG}}", "{{D9_CHART_SVG}}", "{{D30_CHART_SVG}}",
        "{{LAGNA_SIGN}}", "{{NAVAMSA_SIGN}}", "{{TRIMSAMSHA_SIGN}}",
        "{{RISK_MATRIX_ROWS}}", "{{DASHA_TIMELINE_ROWS}}",
    ] + [f"{{{{SECTION_{n}}}}}" for n in
         [2, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25]]
    missing = [p for p in required if p not in template]
    if missing:
        print(f"[WARN] Missing placeholders: {missing}")
    else:
        print(f"[OK]  All {len(required)} placeholders present.")
