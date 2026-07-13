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
    # 1: Top-centre diamond
    1:  (C,   17,  [(C, 41), (C, 58), (C, 75), (C, 92)]),
    # 2: Top-left corner box
    2:  (65,  18,  [(45, 34), (85, 34), (65, 48)]),
    # 3: Left-top outer triangle
    3:  (20,  65,  [(42, 52), (42, 84), (58, 68)]),
    # 4: Left-centre diamond
    4:  (35,  135, [(72, 139), (92, 139), (112, 139), (92, 122)]),
    # 5: Left-bottom outer triangle
    5:  (20,  205, [(42, 186), (42, 218), (58, 202)]),
    # 6: Bottom-left corner box
    6:  (65,  252, [(45, 236), (85, 236), (65, 222)]),
    # 7: Bottom-centre diamond
    7:  (C,   253, [(C, 229), (C, 212), (C, 195), (C, 178)]),
    # 8: Bottom-right corner box
    8:  (205, 252, [(225, 236), (185, 236), (205, 222)]),
    # 9: Right-bottom outer triangle
    9:  (250, 205, [(228, 186), (228, 218), (212, 202)]),
    # 10: Right-centre diamond
    10: (235, 135, [(198, 139), (178, 139), (158, 139), (178, 122)]),
    # 11: Right-top outer triangle
    11: (250, 65,  [(228, 52), (228, 84), (212, 68)]),
    # 12: Top-right corner box
    12: (205, 18,  [(225, 34), (185, 34), (205, 48)]),
}

# Subtle fill colours for house regions (alternating tint)
HOUSE_FILLS = {
    # corner boxes get a very light fill using standard SVG attributes
    2:  'fill="#D4A68C" fill-opacity="0.07"',
    6:  'fill="#D4A68C" fill-opacity="0.07"',
    8:  'fill="#D4A68C" fill-opacity="0.07"',
    12: 'fill="#D4A68C" fill-opacity="0.07"',
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

    LINE_COLOR  = "#2C1A11"
    OUTER_W     = "3.2"
    INNER_W     = "2.0"
    FONT_STACK  = "'Cormorant Garamond', 'Playfair Display', Georgia, serif"

    svg_parts = [
        f'<svg viewBox="0 0 {W} {W}" width="{W}" height="{W}" xmlns="http://www.w3.org/2000/svg">',
        # ── Background ──
        f'<rect x="0" y="0" width="{W}" height="{W}" fill="#FDFAF6"/>',
        # ── Rounded outer border ──
        f'<rect x="1" y="1" width="{W-2}" height="{W-2}" fill="none" stroke="{LINE_COLOR}" '
        f'stroke-width="{OUTER_W}" rx="5" ry="5"/>',
    ]

    # ── Corner-box fills (subtle) ──
    # Top-left box
    svg_parts += [
        f'<polygon points="1,1 {C},1 {C},{C} 1,{C}" {HOUSE_FILLS.get(2, "fill=\'none\'")}/>',
        f'<polygon points="{C},1 {W-1},1 {W-1},{C} {C},{C}" {HOUSE_FILLS.get(12, "fill=\'none\'")}/>',
        f'<polygon points="1,{C} {C},{C} {C},{W-1} 1,{W-1}" {HOUSE_FILLS.get(6, "fill=\'none\'")}/>',
        f'<polygon points="{C},{C} {W-1},{C} {W-1},{W-1} {C},{W-1}" {HOUSE_FILLS.get(8, "fill=\'none\'")}/>',
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
            f'<text x="{sx}" y="{sy + 4}" text-anchor="middle" '
            f'font-family="Calibri, sans-serif" font-weight="bold" font-size="16" '
            f'fill="#1E120F">{sign_num}</text>'
        )

        # Planets in this sign
        planets_here = planet_placements.get(sign_name, [])
        for idx, planet in enumerate(planets_here):
            if idx >= len(planet_slots):
                if idx == len(planet_slots):
                    lx, ly = planet_slots[-1]
                    svg_parts.append(
                        f'<text x="{lx}" y="{ly + 14}" text-anchor="middle" '
                        f'font-family="{FONT_STACK}" font-weight="700" font-size="11" fill="#2C1A11">+{len(planets_here)-len(planet_slots)}</text>'
                    )
                break
            abbr = PLANET_ABBR.get(planet, planet[:2])
            px, py = planet_slots[idx]
            is_lagna = (planet in ("Ascendant", "Lagna")) or (house_num == 1 and idx == 0)
            is_lagna = (planet in ("Ascendant", "Lagna")) or (house_num == 1 and idx == 0)
            color = "#8D2208" if is_lagna else "#000000"
            weight = "700"
            svg_parts.append(
                f'<text x="{px}" y="{py}" text-anchor="middle" '
                f'font-family="{FONT_STACK}" font-weight="{weight}" font-size="14" '
                f'fill="{color}">{abbr}</text>'
            )

    svg_parts.append('</svg>')
    return "\n".join(svg_parts)
