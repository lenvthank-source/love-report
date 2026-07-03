"""
chart_drawer.py  — Redesigned North Indian Kundali chart
Key improvements:
  - Removed center circle label
  - 2-letter planet abbreviations to prevent overlaps
  - 3 planet slots per house (some have 4 for corner houses)
  - Cleaner grid lines using rose-gold palette
  - Rounded outer border
  - Subtle alternate-house tint
  - House number shown in elegant small italic
"""
from typing import Dict, List


SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

SIGN_ABBR = ["Ar","Ta","Ge","Ca","Le","Vi","Li","Sc","Sa","Cp","Aq","Pi"]

PLANET_ABBR = {
    "Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me",
    "Jupiter": "Ju", "Venus": "Ve", "Saturn": "Sa", "Rahu": "Ra", "Ketu": "Ke",
    "Ascendant": "As", "Lagna": "La",
}

# Viewbox size
W = 270
C = 135  # centre point


def get_sign_index(sign_name: str) -> int:
    """Returns 0-indexed position of sign from Aries to Pisces."""
    try:
        return SIGNS.index(sign_name.strip().capitalize())
    except ValueError:
        return 0


# For each house: sign label position (x,y), then planet slots (x,y) stacked
# Designed so NO text lands on a grid line.
# Grid lines pass through: corners (0,0),(270,0),(270,270),(0,270)
# Midpoints (135,0),(270,135),(135,270),(0,135)
# Diagonal intersections with inner diamond: (67,67),(202,67),(67,202),(202,202)
HOUSE_CONFIG = {
    # House: (sign_x, sign_y, [(planet_x, planet_y), ...])
    # Bottom-centre triangle (house 1 / Lagna — largest, most important)
    1:  (C,   248, [(C, 232),(C, 218),(C, 204),(C, 190)]),
    # Bottom-left corner box
    2:  (80,  252, [(55, 238),(55, 226),(80, 252)]),
    # Left side outer triangle
    3:  (22,  202, [(38, 192),(38, 180),(38, 168)]),
    # Left-centre inner triangle
    4:  (72,  C,   [(96, C),(96, C-14),(96, C-28)]),
    # Top-left outer triangle
    5:  (22,  68,  [(38, 78),(38, 90),(38, 102)]),
    # Top-left corner box
    6:  (80,  18,  [(55, 30),(55, 42),(80, 18)]),
    # Top-centre triangle (house 7, opposite lagna)
    7:  (C,   22,  [(C, 36),(C, 50),(C, 64),(C, 78)]),
    # Top-right corner box
    8:  (190, 18,  [(214, 30),(214, 42),(190, 18)]),
    # Right side outer triangle
    9:  (248, 68,  [(232, 78),(232, 90),(232, 102)]),
    # Right-centre inner triangle
    10: (198, C,   [(174, C),(174, C-14),(174, C-28)]),
    # Bottom-right outer triangle
    11: (248, 202, [(232, 192),(232, 180),(232, 168)]),
    # Bottom-right corner box
    12: (190, 252, [(214, 238),(214, 226),(190, 252)]),
}

# Subtle fill colours for house regions (alternating tint)
HOUSE_FILLS = {
    # corner boxes get a very light fill
    2:  "rgba(212,166,140,0.07)",
    6:  "rgba(212,166,140,0.07)",
    8:  "rgba(212,166,140,0.07)",
    12: "rgba(212,166,140,0.07)",
}


def draw_north_indian_chart(
    lagna_sign: str,
    planet_placements: Dict[str, List[str]],
    title: str = "D1 Chart",
) -> str:
    """
    Returns a fully self-contained SVG string of a North Indian Kundali.
    Planets are rendered with 2-letter abbreviations to prevent overlaps.
    The centre is clear of any label or circle.
    """
    lagna_idx = get_sign_index(lagna_sign)

    LINE_COLOR  = "#6B4C3B"
    OUTER_W     = "3.2"
    INNER_W     = "2.0"
    FONT_STACK  = "'Cormorant Garamond', 'Playfair Display', Georgia, serif"

    svg_parts = [
        f'<svg viewBox="0 0 {W} {W}" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">',
        # ── Background ──
        f'<rect x="0" y="0" width="{W}" height="{W}" fill="#FDFAF6"/>',
        # ── Rounded outer border ──
        f'<rect x="1" y="1" width="{W-2}" height="{W-2}" fill="none" stroke="{LINE_COLOR}" '
        f'stroke-width="{OUTER_W}" rx="5" ry="5"/>',
    ]

    # ── Corner-box fills (subtle) ──
    # Top-left box
    svg_parts += [
        f'<polygon points="1,1 {C},1 {C},{C} 1,{C}" fill="{HOUSE_FILLS.get(6, "none")}"/>',
        f'<polygon points="{C},1 {W-1},1 {W-1},{C} {C},{C}" fill="{HOUSE_FILLS.get(8, "none")}"/>',
        f'<polygon points="1,{C} {C},{C} {C},{W-1} 1,{W-1}" fill="{HOUSE_FILLS.get(2, "none")}"/>',
        f'<polygon points="{C},{C} {W-1},{C} {W-1},{W-1} {C},{W-1}" fill="{HOUSE_FILLS.get(12, "none")}"/>',
    ]

    # ── Inner diamond ──
    svg_parts += [
        # Top‑left diamond side
        f'<line x1="{C}" y1="1" x2="1" y2="{C}" stroke="{LINE_COLOR}" stroke-width="{INNER_W}"/>',
        # Top‑right diamond side
        f'<line x1="{C}" y1="1" x2="{W-1}" y2="{C}" stroke="{LINE_COLOR}" stroke-width="{INNER_W}"/>',
        # Bottom‑left diamond side
        f'<line x1="1" y1="{C}" x2="{C}" y2="{W-1}" stroke="{LINE_COLOR}" stroke-width="{INNER_W}"/>',
        # Bottom‑right diamond side
        f'<line x1="{W-1}" y1="{C}" x2="{C}" y2="{W-1}" stroke="{LINE_COLOR}" stroke-width="{INNER_W}"/>',
    ]

    # ── Full diagonals (create the 12-house geometry) ──
    svg_parts += [
        f'<line x1="1" y1="1" x2="{W-1}" y2="{W-1}" stroke="{LINE_COLOR}" stroke-width="{INNER_W}"/>',
        f'<line x1="{W-1}" y1="1" x2="1" y2="{W-1}" stroke="{LINE_COLOR}" stroke-width="{INNER_W}"/>',
    ]

    # ── House signs and planets ──
    for house_num in range(1, 13):
        sign_idx   = (lagna_idx + house_num - 1) % 12
        sign_name  = SIGNS[sign_idx]
        sign_abbr  = SIGN_ABBR[sign_idx]
        sign_num   = str(sign_idx + 1)

        sx, sy, planet_slots = (
            HOUSE_CONFIG[house_num][0],
            HOUSE_CONFIG[house_num][1],
            HOUSE_CONFIG[house_num][2],
        )

        # Sign number — visible, bold
        svg_parts.append(
            f'<text x="{sx}" y="{sy}" text-anchor="middle" '
            f'font-family="{FONT_STACK}" font-weight="700" font-size="13" '
            f'fill="#8E5A40">{sign_num}</text>'
        )

        # Planets in this sign
        planets_here = planet_placements.get(sign_name, [])
        for idx, planet in enumerate(planets_here):
            if idx >= len(planet_slots):
                if idx == len(planet_slots):
                    lx, ly = planet_slots[-1]
                    svg_parts.append(
                        f'<text x="{lx}" y="{ly + 14}" text-anchor="middle" '
                        f'font-family="{FONT_STACK}" font-weight="700" font-size="11" fill="#8E5A40">+{len(planets_here)-len(planet_slots)}</text>'
                    )
                break
            abbr = PLANET_ABBR.get(planet, planet[:2])
            px, py = planet_slots[idx]
            is_lagna = (planet in ("Ascendant", "Lagna")) or (house_num == 1 and idx == 0)
            color = "#7B3F2A" if is_lagna else "#1A1210"
            weight = "700"
            svg_parts.append(
                f'<text x="{px}" y="{py}" text-anchor="middle" '
                f'font-family="{FONT_STACK}" font-weight="{weight}" font-size="14" '
                f'fill="{color}">{abbr}</text>'
            )

    svg_parts.append('</svg>')
    return "\n".join(svg_parts)
