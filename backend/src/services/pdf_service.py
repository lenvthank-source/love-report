"""
pdf_service.py
Coordinates PDF overlay report generation in pure Python using PyMuPDF (fitz).
This removes the dependency on Node.js/subprocess execution, enabling
it to run successfully in python-only serverless environments like Vercel.
"""
import os
import re
import fitz
from typing import Dict, List, Any, Optional

# Static coordinate alignments parsed from 'annotated_Blank Report.pdf'
LAYOUT_CONFIG = {
    1: {'x_left': 80.0, 'x_right': 522.0, 'y_bottom': 336.0, 'y_top': 647.0},
    2: {'x_left': 81.0, 'x_right': 523.0, 'y_bottom': 218.0, 'y_top': 622.0},
    5: {'x_left': 69.0, 'x_right': 526.0, 'y_bottom': 271.0, 'y_top': 633.0},
    6: {'x_left': 82.0, 'x_right': 524.0, 'y_bottom': 284.0, 'y_top': 627.0},
    7: {'x_left': 96.0, 'x_right': 522.0, 'y_bottom': 316.0, 'y_top': 646.0},
    8: {'x_left': 84.0, 'x_right': 523.0, 'y_bottom': 280.0, 'y_top': 607.0},
    9: {'x_left': 89.0, 'x_right': 516.0, 'y_bottom': 305.0, 'y_top': 623.0},
    10: {'x_left': 75.0, 'x_right': 517.0, 'y_bottom': 315.0, 'y_top': 619.0},
    11: {'x_left': 80.0, 'x_right': 522.0, 'y_bottom': 284.0, 'y_top': 624.0},
    12: {'x_left': 92.0, 'x_right': 509.0, 'y_bottom': 279.0, 'y_top': 618.0},
    13: {'x_left': 102.0, 'x_right': 520.0, 'y_bottom': 276.0, 'y_top': 593.0},
    14: {'x_left': 94.0, 'x_right': 527.0, 'y_bottom': 266.0, 'y_top': 602.0},
    15: {'x_left': 92.0, 'x_right': 507.0, 'y_bottom': 279.0, 'y_top': 621.0},
    16: {'x_left': 89.0, 'x_right': 529.0, 'y_bottom': 331.0, 'y_top': 618.0},
    17: {'x_left': 87.0, 'x_right': 526.0, 'y_bottom': 241.0, 'y_top': 626.0},
    18: {'x_left': 97.0, 'x_right': 509.0, 'y_bottom': 293.0, 'y_top': 604.0},
    19: {'x_left': 87.0, 'x_right': 528.0, 'y_bottom': 216.0, 'y_top': 604.0},
    20: {'x_left': 88.0, 'x_right': 527.0, 'y_bottom': 318.0, 'y_top': 625.0},
    21: {'x_left': 93.0, 'x_right': 528.0, 'y_bottom': 233.0, 'y_top': 622.0},
    22: {'x_left': 87.0, 'x_right': 519.0, 'y_bottom': 303.0, 'y_top': 615.0},
    23: {'x_left': 105.0, 'x_right': 523.0, 'y_bottom': 315.0, 'y_top': 623.0},
    24: {'x_left': 90.0, 'x_right': 520.0, 'y_bottom': 308.0, 'y_top': 604.0},
    25: {'x_left': 75.0, 'x_right': 525.0, 'y_bottom': 271.0, 'y_top': 629.0}
}

def strip_emojis(text: str) -> str:
    if not text:
        return ""
    # Strip emojis and variation selectors (0xFE00 to 0xFE0F inclusive)
    text = "".join(c for c in text if ord(c) < 0x10000 and not (0xFE00 <= ord(c) <= 0xFE0F))
    # Strip zero-width characters and markdown syntax
    for ctrl in ["\u200b", "\u200d", "\ufeff", "**", "*", "__"]:
        text = text.replace(ctrl, "")
    return text.strip()

def wrap_text(text: str, max_width: float, fontsize: float, font: fitz.Font) -> List[str]:
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        width = font.text_length(test_line, fontsize)
        if width > max_width:
            lines.append(current_line)
            current_line = word
        else:
            current_line = test_line
    if current_line:
        lines.append(current_line)
    return lines

def get_wrapped_lines(text: str, max_width: float, fontsize: float, font: fitz.Font) -> List[str]:
    paragraphs = text.split("\n")
    all_lines = []
    for i, p in enumerate(paragraphs):
        p = p.strip()
        if not p:
            continue
        p_lines = wrap_text(p, max_width, fontsize, font)
        all_lines.extend(p_lines)
        if i < len(paragraphs) - 1:
            all_lines.append("")  # paragraph spacing line
    return all_lines

def draw_table(
    page: fitz.Page,
    x: float,
    y: float,
    col_widths: List[float],
    default_row_height: float,
    rows: List[List[str]],
    body_font: fitz.Font,
    bold_font: fitz.Font,
    page_height: float,
    reg_font_file: Optional[str],
    bold_font_file: Optional[str],
    font_size: float = 9.5
) -> float:
    rose_gold = (0.79, 0.59, 0.48)
    text_dark = (0.17, 0.1, 0.07)
    header_bg = (0.98, 0.96, 0.93)
    text_padding = 8
    
    current_y_pdflib = y
    
    for r, row in enumerate(rows):
        is_header = (r == 0)
        font = bold_font if is_header else body_font
        font_file = bold_font_file if is_header else reg_font_file
        
        # 1. Pre-calculate wrapped lines and row height
        cell_lines_list = []
        max_lines = 1
        for c, cell_text in enumerate(row):
            col_width = col_widths[c]
            max_text_width = col_width - (text_padding * 2)
            cleaned_text = str(cell_text)
            if not is_header:
                cleaned_text = cleaned_text.replace("/", " / ").replace("-", " - ")
            cell_lines = wrap_text(cleaned_text, max_text_width, font_size, font)
            cell_lines_list.append(cell_lines)
            max_lines = max(max_lines, len(cell_lines))
            
        row_height = max(default_row_height, max_lines * (font_size + 2.5) + 10)
        
        # 2. Draw cell boxes and text
        current_x = x
        for c, cell_text in enumerate(row):
            col_width = col_widths[c]
            cell_lines = cell_lines_list[c]
            
            rect = fitz.Rect(
                current_x, 
                page_height - current_y_pdflib, 
                current_x + col_width, 
                page_height - (current_y_pdflib - row_height)
            )
            
            if is_header:
                page.draw_rect(rect, color=rose_gold, fill=header_bg, width=1)
            else:
                page.draw_rect(rect, color=rose_gold, width=1)
                
            line_gap = font_size + 1.5
            text_block_height = len(cell_lines) * line_gap
            text_top_offset = (row_height - text_block_height) / 2
            
            for i, line in enumerate(cell_lines):
                y_text = rect.y0 + text_top_offset + (i * line_gap) + (font_size * 0.9)
                point = fitz.Point(rect.x0 + text_padding, y_text)
                page.insert_text(
                    point, 
                    line, 
                    fontsize=font_size, 
                    fontname="bold" if is_header else "body",
                    fontfile=font_file, 
                    color=text_dark
                )
                
            current_x += col_width
            
        current_y_pdflib -= row_height
        
    return current_y_pdflib

class PDFService:
    def __init__(self):
        # We use the revised blank report as our single clean template base
        self.template_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "Blank Report Revised.pdf")
        )

    def _svg_to_png(self, svg_str: str, output_path: str):
        """Renders an SVG string to a 300 DPI high-resolution PNG using PyMuPDF."""
        doc = fitz.open(stream=svg_str.encode("utf-8"), filetype="svg")
        page = doc[0]
        pix = page.get_pixmap(dpi=300)
        pix.save(output_path)
        doc.close()

    def _load_fonts(self) -> tuple[Optional[str], Optional[str]]:
        # 1. Try local Windows Georgia system fonts (instant & offline)
        local_reg = 'C:/Windows/Fonts/georgia.ttf'
        local_bold = 'C:/Windows/Fonts/georgiab.ttf'
        if os.path.exists(local_reg) and os.path.exists(local_bold):
            return local_reg, local_bold
            
        # 2. Server/Linux environment fallback to Cormorant Garamond inside writable /tmp
        if os.getenv("VERCEL") or os.environ.get("AMAZON_AWS_LAMBDA_STAGE") or not os.access(".", os.W_OK):
            fonts_dir = "/tmp/fonts"
        else:
            workspace_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            fonts_dir = os.path.join(workspace_dir, "fonts")
            
        os.makedirs(fonts_dir, exist_ok=True)
        reg_path = os.path.join(fonts_dir, "Gelasio-Regular.ttf")
        bold_path = os.path.join(fonts_dir, "Gelasio-Bold.ttf")
        
        # If files exist and are not empty/html placeholders, return them
        if os.path.exists(reg_path) and os.path.getsize(reg_path) > 1000 and os.path.exists(bold_path) and os.path.getsize(bold_path) > 1000:
            return reg_path, bold_path
            
        # Download from Google Fonts CSS API using old Android user-agent to force TTF format
        import requests
        import re
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; U; Android 2.2; en-us; Nexus One Build/FRF91) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1"
        }
        css_url = "https://fonts.googleapis.com/css2?family=Gelasio:wght@400;700"
        
        try:
            print(f"[PDFService] Fetching Google Fonts CSS...")
            r = requests.get(css_url, headers=headers, timeout=10)
            ttf_urls = re.findall(r'url\((https://fonts\.gstatic\.com/[^)]+\.ttf)\)', r.text)
            
            if len(ttf_urls) >= 2:
                print(f"[PDFService] Downloading Gelasio-Regular from {ttf_urls[0]}")
                reg_data = requests.get(ttf_urls[0], timeout=15).content
                with open(reg_path, "wb") as f:
                    f.write(reg_data)
                    
                print(f"[PDFService] Downloading Gelasio-Bold from {ttf_urls[1]}")
                bold_data = requests.get(ttf_urls[1], timeout=15).content
                with open(bold_path, "wb") as f:
                    f.write(bold_data)
                    
                return reg_path, bold_path
        except Exception as e:
            print(f"[PDFService] Dynamic font download failed: {e}. Falling back to standard Helvetica/Times.")
            
        return None, None

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    def build_pdf_report(
        self,
        output_path: str,
        sections: Dict[int, str],
        d1_placements: Dict[str, List[str]],
        d9_placements: Dict[str, List[str]],
        d30_placements: Dict[str, List[str]],
        risk_matrix: List[List[str]],
        dasha_timeline: List[List[str]],
        client_name: str,
        birth_details: str,          # kept for backward-compat (not injected)
        lagna_sign: str,
        navamsa_lagna_sign: str,
        trimsamsha_lagna_sign: str,
        # ── New individual birth detail params ──
        client_dob: str = "",
        client_tob: str = "",
        client_pob: str = "",
        rudraksha_name: Optional[str] = None,
        rudraksha_url: Optional[str] = None,
    ):
        """Coordinates PDF overlay report generation via pure Python PyMuPDF (fitz) operations."""
        from src.utils.chart_drawer import draw_north_indian_chart
        
        # Parse birth_details fallback if individual params are empty
        if not client_dob and " at " in birth_details:
            parts = birth_details.split(" at ", 1)
            client_dob = parts[0].strip()
            rest = parts[1].split(" in ", 1)
            client_tob = rest[0].strip()
            client_pob = rest[1].strip() if len(rest) > 1 else ""

        print(f"[PDFService] Generating PDF report for '{client_name}' using pure PyMuPDF overlay...")

        if not os.path.exists(self.template_path):
            raise FileNotFoundError(f"Clean PDF Template not found at: {self.template_path}")

        # 1. Setup temp output directory for PNG charts
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(output_path)), f"temp_{os.path.basename(output_path).replace('.', '_')}")
        os.makedirs(temp_dir, exist_ok=True)

        d1_png_path = os.path.join(temp_dir, "d1.png")
        d9_png_path = os.path.join(temp_dir, "d9.png")
        d30_png_path = os.path.join(temp_dir, "d30.png")

        # Render SVGs to PNG
        d1_svg  = draw_north_indian_chart(lagna_sign,            d1_placements,  "D1 Chart")
        d9_svg  = draw_north_indian_chart(navamsa_lagna_sign,    d9_placements,  "D9 Navamsa")
        d30_svg = draw_north_indian_chart(trimsamsha_lagna_sign, d30_placements, "D30 Chart")

        self._svg_to_png(d1_svg, d1_png_path)
        self._svg_to_png(d9_svg, d9_png_path)
        self._svg_to_png(d30_svg, d30_png_path)

        # 2. Setup Fonts
        reg_font_file, bold_font_file = self._load_fonts()
        body_font = fitz.Font(fontfile=reg_font_file) if reg_font_file else fitz.Font("helv")
        bold_font = fitz.Font(fontfile=bold_font_file) if bold_font_file else fitz.Font("helv-bold")

        # 3. Format timeline details
        def format_dasa_date_window(date_window_str: str) -> str:
            parts = [p.strip() for p in re.split(r'[-–—to]', date_window_str) if p.strip()]
            if len(parts) != 2:
                return date_window_str.replace("-", "to")
            formatted_parts = []
            for part in parts:
                match_slash = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})', part)
                if match_slash:
                    day = int(match_slash.group(1))
                    month = int(match_slash.group(2))
                    year = match_slash.group(3)
                    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                    month_name = months[month - 1] if 1 <= month <= 12 else "Month"
                    suffix = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
                    formatted_parts.append(f"{day}{suffix} {month_name} {year}")
                else:
                    formatted_parts.append(part)
            return f"{formatted_parts[0]} to {formatted_parts[1]}"

        formatted_dasha_timeline = []
        for row in dasha_timeline:
            if len(row) >= 3:
                formatted_dasha_timeline.append([row[0], format_dasa_date_window(row[1]), row[2]])
            else:
                formatted_dasha_timeline.append(row)

        formatted_prayantar_dasha = []
        for row in [
            ["Jupiter-Saturn-Merc", "Jul 2026 - Sep 2026", "High. Ideal window for proposals or serious talks."],
            ["Jupiter-Saturn-Ketu", "Sep 2026 - Nov 2026", "Moderate. Lessons in patient detachment."],
            ["Jupiter-Saturn-Venus", "Nov 2026 - Mar 2027", "Very High. Harmonious celestial support for union."]
        ]:
            formatted_prayantar_dasha.append([row[0], format_dasa_date_window(row[1]), row[2]])

        # 4. Open template and perform page overlays
        doc = fitz.open(self.template_path)
        page_count = len(doc)
        
        fontSize = 12.0
        lineSpacing = fontSize * 1.85
        textColorDark = (0.17, 0.1, 0.07)  # #2C1A11

        overflowLines = {}
        client_gender = "Male" if "male" in birth_details.lower() else "Female"
        
        moon_sign = "Unknown"
        for sign, planets in d1_placements.items():
            if "Moon" in planets or "Mo" in planets:
                moon_sign = sign
                break

        for pageIdx in range(page_count):
            page = doc[pageIdx]
            page_height = page.rect.height
            
            rect = LAYOUT_CONFIG.get(pageIdx)
            if rect:
                # Override margins to match compile_report.js wider margins
                rect = {
                    'x_left': 70.0,
                    'x_right': 525.0,
                    'y_top': rect['y_top'],
                    'y_bottom': rect['y_bottom']
                }

            # Page 2 (index 1): User Details Table
            if pageIdx == 1:
                if rect:
                    print(f"[PDFService] Page {pageIdx + 1}: Drawing User Details Table...")
                    rows = [
                        ["Birth Profile Field", "Personal Astrological Details"],
                        ["Full Name", client_name.title()],
                        ["Gender", client_gender],
                        ["Date of Birth", client_dob],
                        ["Time of Birth", client_tob],
                        ["Place of Birth", client_pob],
                        ["Lagna (Ascendant Sign)", lagna_sign],
                        ["Moon Sign", moon_sign]
                    ]
                    colWidths = [160.0, 295.0]
                    rowHeight = 32.0
                    totalTableHeight = rowHeight * len(rows)
                    yStart = rect['y_bottom'] + (rect['y_top'] - rect['y_bottom'] - totalTableHeight) / 2 + totalTableHeight
                    
                    draw_table(
                        page, rect['x_left'], yStart, colWidths, rowHeight, rows, 
                        body_font, bold_font, page_height, reg_font_file, bold_font_file,
                        font_size=11.5
                    )
                continue

            # Page 6 (index 5): D1 Chart and explanation text below
            if pageIdx == 5:
                if rect and os.path.exists(d1_png_path):
                    print(f"[PDFService] Page {pageIdx + 1}: Drawing D1 Chart...")
                    chartSize = 250.0
                    xChart = rect['x_left'] + (rect['x_right'] - rect['x_left'] - chartSize) / 2
                    yChart_pdflib = rect['y_top'] - chartSize - 10.0
                    
                    # Draw D1 image on page
                    img_rect = fitz.Rect(xChart, page_height - rect['y_top'] + 10.0, xChart + chartSize, page_height - yChart_pdflib)
                    page.insert_image(img_rect, filename=d1_png_path)
                    
                    explanation = strip_emojis(sections.get(5, "This is your D1 Birth Chart, the blueprint of your soul's current life journey."))
                    wrappedExp = get_wrapped_lines(explanation, rect['x_right'] - rect['x_left'], fontSize, body_font)
                    
                    expY = yChart_pdflib - 20.0
                    for line in wrappedExp:
                        if line:
                            point = fitz.Point(rect['x_left'], page_height - expY)
                            page.insert_text(point, line, fontsize=fontSize, fontname="body", fontfile=reg_font_file, color=textColorDark)
                        expY -= lineSpacing
                continue

            # Page 11 (index 10): D9 and D30 side-by-side
            if pageIdx == 10:
                if rect:
                    print(f"[PDFService] Page {pageIdx + 1}: Drawing D9 and D30 Charts...")
                    chartSize = 200.0
                    spacing = (rect['x_right'] - rect['x_left'] - (chartSize * 2)) / 3.0
                    yChart_pdflib = rect['y_bottom'] + (rect['y_top'] - rect['y_bottom'] - chartSize) / 2.0 + 10.0
                    
                    # D9
                    if os.path.exists(d9_png_path):
                        xD9 = rect['x_left'] + spacing
                        img_rect = fitz.Rect(xD9, page_height - (yChart_pdflib + chartSize), xD9 + chartSize, page_height - yChart_pdflib)
                        page.insert_image(img_rect, filename=d9_png_path)
                        
                        txt = "D9 NAVAMSA CHART"
                        w = bold_font.text_length(txt, 12.0)
                        point = fitz.Point(xD9 + (chartSize - w) / 2.0, page_height - (yChart_pdflib - 20.0))
                        page.insert_text(point, txt, fontsize=12.0, fontname="bold", fontfile=bold_font_file, color=textColorDark)
                    
                    # D30
                    if os.path.exists(d30_png_path):
                        xD30 = rect['x_left'] + spacing * 2.0 + chartSize
                        img_rect = fitz.Rect(xD30, page_height - (yChart_pdflib + chartSize), xD30 + chartSize, page_height - yChart_pdflib)
                        page.insert_image(img_rect, filename=d30_png_path)
                        
                        txt = "D30 TRIMSAMSHA CHART"
                        w = bold_font.text_length(txt, 12.0)
                        point = fitz.Point(xD30 + (chartSize - w) / 2.0, page_height - (yChart_pdflib - 20.0))
                        page.insert_text(point, txt, fontsize=12.0, fontname="bold", fontfile=bold_font_file, color=textColorDark)
                continue

            # Page 20 (index 19): Risk Matrix Table
            if pageIdx == 19:
                if rect:
                    print(f"[PDFService] Page {pageIdx + 1}: Drawing Compatibility/Risk Matrix...")
                    rows = [
                        ["Astrological Influence", "Subconscious Shadows & Friction Points", "Empowered Remedies & Actions"]
                    ]
                    if risk_matrix:
                        rows.extend(risk_matrix)
                    else:
                        rows.append(["General friction", "Minor friction points in communication.", "Commit to open dialogue."])
                        
                    colWidths = [125.0, 165.0, 165.0]
                    rowHeight = 24.0
                    tableY = rect['y_top'] - 10.0
                    finalTableY = draw_table(
                        page, rect['x_left'], tableY, colWidths, rowHeight, rows, 
                        body_font, bold_font, page_height, reg_font_file, bold_font_file
                    )
                    
                    textBelow = strip_emojis(sections.get(19, ""))
                    if textBelow:
                        wrapped = get_wrapped_lines(textBelow, rect['x_right'] - rect['x_left'], fontSize, body_font)
                        txtY = finalTableY - 25.0
                        for line in wrapped:
                            if line:
                                point = fitz.Point(rect['x_left'], page_height - txtY)
                                page.insert_text(point, line, fontsize=fontSize, fontname="body", fontfile=reg_font_file, color=textColorDark)
                            txtY -= lineSpacing
                continue

            # Page 22 (index 21): 3-Year Love Timeline
            if pageIdx == 21:
                if rect:
                    print(f"[PDFService] Page {pageIdx + 1}: Drawing 3-Year Timeline Table...")
                    rows = [
                        ["Vimshottari Period", "Timeline Windows", "Romantic Potential & Themes"]
                    ]
                    if formatted_dasha_timeline:
                        rows.extend(formatted_dasha_timeline)
                    else:
                        rows.append(["Jupiter - Saturn", "Current - Dec 2026", "Subtle, steady emotional growth and marriage gateway."])
                        
                    colWidths = [125.0, 135.0, 195.0]
                    rowHeight = 24.0
                    tableY = rect['y_top'] - 10.0
                    finalTableY = draw_table(
                        page, rect['x_left'], tableY, colWidths, rowHeight, rows, 
                        body_font, bold_font, page_height, reg_font_file, bold_font_file
                    )
                    
                    textBelow = strip_emojis(sections.get(21, ""))
                    if textBelow:
                        wrapped = get_wrapped_lines(textBelow, rect['x_right'] - rect['x_left'], fontSize, body_font)
                        txtY = finalTableY - 25.0
                        for line in wrapped:
                            if line:
                                point = fitz.Point(rect['x_left'], page_height - txtY)
                                page.insert_text(point, line, fontsize=fontSize, fontname="body", fontfile=reg_font_file, color=textColorDark)
                            txtY -= lineSpacing
                continue

            # Page 23 (index 22): Prayantar Dasha Timing
            if pageIdx == 22:
                if rect:
                    print(f"[PDFService] Page {pageIdx + 1}: Drawing Prayantar Dasha Table...")
                    rows = [
                        ["Sub-Sub Cycle", "Exact Date Window", "Intensity & Opportunity Key"]
                    ]
                    if formatted_prayantar_dasha:
                        rows.extend(formatted_prayantar_dasha)
                    else:
                        rows.append(["Jupiter-Saturn-Merc", "Jul 2026 - Sep 2026", "High. Ideal window for proposals or serious talks."])
                        
                    colWidths = [125.0, 135.0, 195.0]
                    rowHeight = 24.0
                    tableY = rect['y_top'] - 10.0
                    finalTableY = draw_table(
                        page, rect['x_left'], tableY, colWidths, rowHeight, rows, 
                        body_font, bold_font, page_height, reg_font_file, bold_font_file
                    )
                    
                    textBelow = strip_emojis(sections.get(22, ""))
                    if textBelow:
                        wrapped = get_wrapped_lines(textBelow, rect['x_right'] - rect['x_left'], fontSize, body_font)
                        txtY = finalTableY - 25.0
                        for line in wrapped:
                            if line:
                                point = fitz.Point(rect['x_left'], page_height - txtY)
                                page.insert_text(point, line, fontsize=fontSize, fontname="body", fontfile=reg_font_file, color=textColorDark)
                            txtY -= lineSpacing
                continue

            # Standard wrapped text pages
            if not rect:
                continue

            linesToDraw = []
            pageText = strip_emojis(sections.get(pageIdx, ""))
            if pageText:
                wrapped = get_wrapped_lines(pageText, rect['x_right'] - rect['x_left'], fontSize, body_font)
                linesToDraw.extend(wrapped)
                
            if not linesToDraw:
                continue

            print(f"[PDFService] Page {pageIdx + 1}: Writing {len(linesToDraw)} lines of text...")
            currentY = rect['y_top'] - fontSize
            
            for line in linesToDraw:
                # Page overflow check
                if currentY < rect['y_bottom']:
                    print(f"[PDFService] Page {pageIdx + 1} overflowed! Stopping rendering on this page.")
                    break
                    
                if line:
                    point = fitz.Point(rect['x_left'], page_height - currentY)
                    page.insert_text(point, line, fontsize=fontSize, fontname="body", fontfile=reg_font_file, color=textColorDark)
                currentY -= lineSpacing

        # 4.5. Add hyperlinks on Page 24 (Practical Remedies, index 23)
        # Search page for target words and insert links with underlines
        # 4.5. Add hyperlinks on Page 24 (Practical Remedies, index 23)
        # Search page for target words and insert links with underlines
        if len(doc) > 23:
            page24 = doc[23]
            
            # Anchor 1: Divy Love Bracelet
            bracelet_rects = page24.search_for("Divy Love Bracelet")
            for r in bracelet_rects:
                page24.draw_line(fitz.Point(r.x0, r.y1 + 1.0), fitz.Point(r.x1, r.y1 + 1.0), color=(0.1, 0.4, 0.8), width=0.8)
                page24.insert_link({"kind": fitz.LINK_URI, "from": r, "uri": "https://www.astrosavvysingh.com/product/divy-love-bracelet"})
                
            # Anchor 2: Rudraksha Suggestion (dynamic)
            if rudraksha_url:
                # Search for single word "Rudraksha" on remedies page
                rud_rects = page24.search_for("Rudraksha")
                for r in rud_rects:
                    page24.draw_line(fitz.Point(r.x0, r.y1 + 1.0), fitz.Point(r.x1, r.y1 + 1.0), color=(0.1, 0.4, 0.8), width=0.8)
                    page24.insert_link({"kind": fitz.LINK_URI, "from": r, "uri": rudraksha_url})
                    
            # Anchor 3: Consultation booking
            consult_rects = page24.search_for("live consultation")
            for r in consult_rects:
                page24.draw_line(fitz.Point(r.x0, r.y1 + 1.0), fitz.Point(r.x1, r.y1 + 1.0), color=(0.1, 0.4, 0.8), width=0.8)
                page24.insert_link({"kind": fitz.LINK_URI, "from": r, "uri": "https://www.astrosavvysingh.com/kundli-analysis"})

        # 5. Save document
        print(f"[PDFService] Saving compiled PDF to: {output_path}")
        doc.save(output_path)
        doc.close()
        print("[PDFService] PDF overlay compilation completed successfully!")

        # 6. Clean up temporary files
        try:
            os.remove(d1_png_path)
            os.remove(d9_png_path)
            os.remove(d30_png_path)
            os.rmdir(temp_dir)
            print("[PDFService] Temporary files cleaned up.")
        except Exception as ex:
            print(f"[PDFService] Error cleaning up temporary files: {ex}")
