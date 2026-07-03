"""
pdf_service.py
Loads the static HTML template, injects dynamic data into {{PLACEHOLDER}} tokens,
writes the filled HTML, then compiles it to PDF via Playwright (sync API called
from a background thread via asyncio.to_thread).
"""
import os
from typing import Dict, List
from playwright.sync_api import sync_playwright

from src.utils.chart_drawer import draw_north_indian_chart
from src.utils.markdown_parser import parse_markdown_to_html, strip_thinking_tags


class PDFService:
    def __init__(self):
        self.template_path = os.path.join(
            os.path.dirname(__file__), "..", "templates", "report_template.html"
        )

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
        """Injects dynamic data into the static template and compiles to PDF."""
        # Parse birth_details fallback if individual params are empty
        if not client_dob and " at " in birth_details:
            parts = birth_details.split(" at ", 1)
            client_dob = parts[0].strip()
            rest = parts[1].split(" in ", 1)
            client_tob = rest[0].strip()
            client_pob = rest[1].strip() if len(rest) > 1 else ""

        html_content = self._inject_data(
            sections=sections,
            d1_placements=d1_placements,
            d9_placements=d9_placements,
            d30_placements=d30_placements,
            risk_matrix=risk_matrix,
            dasha_timeline=dasha_timeline,
            client_name=client_name,
            client_dob=client_dob,
            client_tob=client_tob,
            client_pob=client_pob,
            lagna_sign=lagna_sign,
            navamsa_lagna_sign=navamsa_lagna_sign,
            trimsamsha_lagna_sign=trimsamsha_lagna_sign,
        )

        # Write temp HTML alongside the PDF
        html_path = output_path.replace(".pdf", ".html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # Compile to PDF
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            file_url = f"file:///{os.path.abspath(html_path)}".replace("\\", "/")
            page.goto(file_url, wait_until="networkidle")
            page.pdf(
                path=output_path,
                format="A4",
                print_background=True,
                margin={"top": "0mm", "right": "0mm", "bottom": "0mm", "left": "0mm"},
            )
            browser.close()

    # ------------------------------------------------------------------
    # Template injection
    # ------------------------------------------------------------------
    def _inject_data(
        self,
        sections: Dict[int, str],
        d1_placements: Dict[str, List[str]],
        d9_placements: Dict[str, List[str]],
        d30_placements: Dict[str, List[str]],
        risk_matrix: List[List[str]],
        dasha_timeline: List[List[str]],
        client_name: str,
        client_dob: str,
        client_tob: str,
        client_pob: str,
        lagna_sign: str,
        navamsa_lagna_sign: str,
        trimsamsha_lagna_sign: str,
    ) -> str:
        with open(self.template_path, encoding="utf-8") as f:
            html = f.read()

        # ── 1. Client identity ──
        html = html.replace("{{CLIENT_FULL_NAME}}", client_name.title())
        html = html.replace("{{CLIENT_DOB}}",      client_dob)
        html = html.replace("{{CLIENT_TOB}}",      client_tob)
        html = html.replace("{{CLIENT_POB}}",      client_pob)

        client_intro = (
            f"This Personalised Cosmic Love &amp; Marriage Report has been carefully prepared for "
            f"<strong>{client_name.title()}</strong>, based on the exact planetary positions at the "
            f"moment of birth in <em>{client_pob}</em>. The insights within these pages are drawn "
            f"from the ancient wisdom of Vedic Astrology, offering a deeply personal guide to "
            f"understanding your emotional nature, relationship patterns, and the beautiful cosmic "
            f"timing of your love journey."
        )
        html = html.replace("{{CLIENT_INTRO}}", client_intro)

        # ── 2. SVG Astrological Charts ──
        d1_svg  = draw_north_indian_chart(lagna_sign,            d1_placements,  "D1 Chart")
        d9_svg  = draw_north_indian_chart(navamsa_lagna_sign,    d9_placements,  "D9 Navamsa")
        d30_svg = draw_north_indian_chart(trimsamsha_lagna_sign, d30_placements, "D30 Chart")

        html = html.replace("{{D1_CHART_SVG}}",  d1_svg)
        html = html.replace("{{D9_CHART_SVG}}",  d9_svg)
        html = html.replace("{{D30_CHART_SVG}}", d30_svg)

        # ── 3. Chart sign labels ──
        html = html.replace("{{LAGNA_SIGN}}",      lagna_sign)
        html = html.replace("{{NAVAMSA_SIGN}}",    navamsa_lagna_sign)
        html = html.replace("{{TRIMSAMSHA_SIGN}}", trimsamsha_lagna_sign)

        # ── 4. Risk Matrix rows ──
        rm_rows = "".join(
            "<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>"
            for row in risk_matrix
        )
        html = html.replace("{{RISK_MATRIX_ROWS}}", rm_rows)

        # ── 5. Dasha Timeline rows ──
        dt_rows = "".join(
            "<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>"
            for row in dasha_timeline
        )
        html = html.replace("{{DASHA_TIMELINE_ROWS}}", dt_rows)

        # ── 6. AI section text ──
        # Template placeholders use ORIGINAL section numbers (2, 6-25 as before).
        for section_key in list(sections.keys()):
            placeholder = f"{{{{SECTION_{section_key}}}}}"
            if placeholder not in html:
                continue
            raw = sections.get(section_key, "")
            # Strip any thinking tags before rendering
            raw = strip_thinking_tags(raw)
            html_text = parse_markdown_to_html(raw) if raw else (
                '<p style="color:#C9967B;font-style:italic;">'
                'Astrological analysis for this section is being prepared&hellip;</p>'
            )
            html = html.replace(placeholder, html_text)

        # Clean up any remaining unreplaced placeholders
        import re
        html = re.sub(r'\{\{[A-Z_0-9]+\}\}', '', html)

        return html
