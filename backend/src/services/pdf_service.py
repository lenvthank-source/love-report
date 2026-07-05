"""
pdf_service.py
Coordinates PDF overlay report generation by compiling charts and table models,
writing text layouts onto the clean "Blank Report Revised.pdf" template using
PDF-lib overlay compilation in a Node.js subprocess.
"""
import os
from typing import Dict, List

from src.utils.chart_drawer import draw_north_indian_chart

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


class PDFService:
    def __init__(self):
        # We use the revised blank report as our single clean template base
        self.template_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "Blank Report Revised.pdf")
        )

    def _svg_to_png(self, svg_str: str, output_path: str):
        """Renders an SVG string to a 300 DPI high-resolution PNG using PyMuPDF."""
        import fitz
        doc = fitz.open(stream=svg_str.encode("utf-8"), filetype="svg")
        page = doc[0]
        pix = page.get_pixmap(dpi=300)
        pix.save(output_path)
        doc.close()

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
    ):
        """Coordinates PDF overlay report generation via Node.js compile_report.js subprocess."""
        import json
        import subprocess
        
        # Parse birth_details fallback if individual params are empty
        if not client_dob and " at " in birth_details:
            parts = birth_details.split(" at ", 1)
            client_dob = parts[0].strip()
            rest = parts[1].split(" in ", 1)
            client_tob = rest[0].strip()
            client_pob = rest[1].strip() if len(rest) > 1 else ""

        print(f"[PDFService] Generating PDF report for '{client_name}' using PDF-lib overlay...")

        if not os.path.exists(self.template_path):
            raise FileNotFoundError(f"Clean PDF Template not found at: {self.template_path}")

        # 1. Use static layout configuration directly
        layout = LAYOUT_CONFIG

        # 2. Setup temp output directory for PNG charts and JSON data payload
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(output_path)), f"temp_{os.path.basename(output_path).replace('.', '_')}")
        os.makedirs(temp_dir, exist_ok=True)

        # Draw SVGs
        d1_svg  = draw_north_indian_chart(lagna_sign,            d1_placements,  "D1 Chart")
        d9_svg  = draw_north_indian_chart(navamsa_lagna_sign,    d9_placements,  "D9 Navamsa")
        d30_svg = draw_north_indian_chart(trimsamsha_lagna_sign, d30_placements, "D30 Chart")

        # Convert SVGs to PNGs
        d1_png_path = os.path.join(temp_dir, "d1.png")
        d9_png_path = os.path.join(temp_dir, "d9.png")
        d30_png_path = os.path.join(temp_dir, "d30.png")

        self._svg_to_png(d1_svg, d1_png_path)
        self._svg_to_png(d9_svg, d9_png_path)
        self._svg_to_png(d30_svg, d30_png_path)

        # 3. Assemble JSON Payload for Node.js
        sections_str_keys = {str(k): v for k, v in sections.items()}
        
        moon_sign = "Unknown"
        for sign, planets in d1_placements.items():
            if "Moon" in planets or "Mo" in planets:
                moon_sign = sign
                break
                
        # Assemble formatted timelines
        import re

        def format_dasa_date_window(date_window_str: str) -> str:
            parts = [p.strip() for p in re.split(r'[-–—to]', date_window_str) if p.strip()]
            if len(parts) != 2:
                return date_window_str.replace("-", "to")
                
            formatted_parts = []
            for part in parts:
                # Check if DD/MM/YYYY
                match_slash = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})', part)
                if match_slash:
                    day = int(match_slash.group(1))
                    month = int(match_slash.group(2))
                    year = match_slash.group(3)
                    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                    month_name = months[month - 1] if 1 <= month <= 12 else "Month"
                    
                    if 11 <= day <= 13:
                        suffix = "th"
                    else:
                        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
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

        # Fills details context
        data_payload = {
            "client_name": client_name.title(),
            "client_gender": "Male" if "male" in birth_details.lower() else "Female",
            "client_dob": client_dob,
            "client_tob": client_tob,
            "client_pob": client_pob,
            "lagna_sign": lagna_sign,
            "moon_sign": moon_sign,
            "moon_nakshatra": "Vedic Nakshatra", # Placeholder or derived
            "sections": sections_str_keys,
            "risk_matrix": risk_matrix,
            "dasha_timeline": formatted_dasha_timeline,
            "prayantar_dasha": formatted_prayantar_dasha,
            "layout": layout,
            "d1_png": d1_png_path.replace("\\", "/"),
            "d9_png": d9_png_path.replace("\\", "/"),
            "d30_png": d30_png_path.replace("\\", "/")
        }

        temp_json_path = os.path.join(temp_dir, "payload.json")
        with open(temp_json_path, "w", encoding="utf-8") as f:
            json.dump(data_payload, f, indent=2)

        # 4. Invoke Node.js PDF-lib overlay compiler
        compiler_script = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "report", "compile_report.js")
        )

        cmd = [
            "node",
            compiler_script,
            "--data", temp_json_path,
            "--template", self.template_path,
            "--output", output_path
        ]

        print(f"[PDFService] Spawning Node.js subprocess...")
        res = subprocess.run(cmd, capture_output=True, text=True, shell=True)

        if res.returncode != 0:
            print(f"[PDFService] Subprocess compilation failed with exit code {res.returncode}")
            print(f"STDOUT:\n{res.stdout}")
            print(f"STDERR:\n{res.stderr}")
            raise RuntimeError(f"Subprocess compilation failed: {res.stderr}")

        print("[PDFService] PDF overlay compilation completed successfully!")

        # 5. Clean up temporary files
        try:
            os.remove(d1_png_path)
            os.remove(d9_png_path)
            os.remove(d30_png_path)
            os.remove(temp_json_path)
            os.rmdir(temp_dir)
            print("[PDFService] Temporary files cleaned up.")
        except Exception as ex:
            print(f"[PDFService] Error cleaning up temporary files: {ex}")
