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


def get_house_layout(house_num: int, num_planets: int):
    """
    Returns: (sign_x, sign_y, planet_coords, font_size)
    - sign_x, sign_y: Coordinates for sign number text
    - planet_coords: List of (x, y) coordinates for planet abbreviations
    - font_size: Font size to use for planet text
    """
    # 1. Sign positions (remains stable and spacious)
    sign_positions = {
        1:  (135, 18),
        2:  (67.5, 18),
        3:  (18, 71.5),
        4:  (22, 139),
        5:  (18, 206.5),
        6:  (67.5, 256),
        7:  (135, 256),
        8:  (202.5, 256),
        9:  (252, 206.5),
        10: (248, 139),
        11: (252, 71.5),
        12: (202.5, 18),
    }
    
    sx, sy = sign_positions.get(house_num, (135, 135))
    
    # Determine slots based on house type and number of planets
    coords = []
    
    # Standard font sizes:
    # 1 or 2 planets: 13.5
    # 3 planets: 12.5
    # 4+ planets: 10.5
    if num_planets <= 2:
        font_size = 13.5
    elif num_planets == 3:
        font_size = 12.5
    else:
        font_size = 10.5
        
    # Group houses by geometric type:
    # Diamonds (1, 7)
    if house_num in (1, 7):
        is_h1 = (house_num == 1)
        y_center = 75 if is_h1 else 195
        
        if num_planets == 1:
            coords = [(135, y_center)]
        elif num_planets == 2:
            coords = [(135, y_center - 16), (135, y_center + 16)]
        elif num_planets == 3:
            coords = [(135, y_center - 28), (135, y_center), (135, y_center + 28)]
        elif num_planets == 4:
            coords = [(135, y_center - 36), (135, y_center - 12), (135, y_center + 12), (135, y_center + 36)]
        else: # 5 or more planets
            if num_planets == 5:
                coords = [
                    (135, y_center - 30),
                    (105, y_center), (135, y_center), (165, y_center),
                    (135, y_center + 30)
                ]
            else: # 6 or more
                coords = [
                    (135, y_center - 33),
                    (110, y_center - 12), (160, y_center - 12),
                    (110, y_center + 12), (160, y_center + 12),
                    (135, y_center + 33)
                ]
                
    # Diamonds (4, 10)
    elif house_num in (4, 10):
        is_h4 = (house_num == 4)
        x_center = 75 if is_h4 else 195
        y_center = 139
        
        if num_planets == 1:
            coords = [(x_center, y_center)]
        elif num_planets == 2:
            coords = [(x_center - 18, y_center), (x_center + 18, y_center)]
        elif num_planets == 3:
            coords = [(x_center - 28, y_center), (x_center, y_center), (x_center + 28, y_center)]
        elif num_planets == 4:
            coords = [(x_center - 33, y_center), (x_center - 11, y_center), (x_center + 11, y_center), (x_center + 33, y_center)]
        else: # 5 or more planets
            if num_planets == 5:
                coords = [
                    (x_center - 15, y_center - 15), (x_center + 15, y_center - 15),
                    (x_center - 25, y_center + 15), (x_center, y_center + 15), (x_center + 25, y_center + 15)
                ]
            else: # 6 or more
                coords = [
                    (x_center - 25, y_center - 16), (x_center, y_center - 16), (x_center + 25, y_center - 16),
                    (x_center - 25, y_center + 16), (x_center, y_center + 16), (x_center + 25, y_center + 16)
                ]

    # Flat top/bottom triangles (2, 6, 8, 12)
    elif house_num in (2, 6, 8, 12):
        is_top = house_num in (2, 12)
        is_left = house_num in (2, 6)
        
        cx = 67.5 if is_left else 202.5
        y1 = 33 if is_top else 237  # Row 1
        y2 = 52 if is_top else 218  # Row 2
        y3 = 64 if is_top else 206  # Row 3
        
        if num_planets == 1:
            coords = [(cx, 42 if is_top else 228)]
        elif num_planets == 2:
            coords = [(cx - 17, 36 if is_top else 234), (cx + 17, 36 if is_top else 234)]
        elif num_planets == 3:
            coords = [(cx - 22, y1), (cx + 22, y1), (cx, y2)]
        else: # 4 or more planets
            if num_planets == 4:
                coords = [(cx - 22, y1), (cx, y1), (cx + 22, y1), (cx, y2)]
            elif num_planets == 5:
                coords = [(cx - 22, y1), (cx, y1), (cx + 22, y1), (cx - 12, y2), (cx + 12, y2)]
            else: # 6 or more
                coords = [(cx - 22, y1), (cx, y1), (cx + 22, y1), (cx - 12, y2), (cx + 12, y2), (cx, y3)]

    # Flat left/right side triangles (3, 5, 9, 11)
    else:
        is_left = house_num in (3, 5)
        is_top = house_num in (3, 11)
        
        cy = 71.5 if is_top else 206.5
        x1 = 33 if is_left else 237  # Col 1
        x2 = 52 if is_left else 218  # Col 2
        x3 = 64 if is_left else 206  # Col 3
        
        if num_planets == 1:
            coords = [(42 if is_left else 228, cy)]
        elif num_planets == 2:
            coords = [(36 if is_left else 234, cy - 17), (36 if is_left else 234, cy + 17)]
        elif num_planets == 3:
            coords = [(x1, cy - 22), (x1, cy + 22), (x2, cy)]
        else: # 4 or more planets
            if num_planets == 4:
                coords = [(x1, cy - 22), (x1, cy), (x1, cy + 22), (x2, cy)]
            elif num_planets == 5:
                coords = [(x1, cy - 22), (x1, cy), (x1, cy + 22), (x2, cy - 12), (x2, cy + 12)]
            else: # 6 or more
                coords = [(x1, cy - 22), (x1, cy), (x1, cy + 22), (x2, cy - 12), (x2, cy + 12), (x3, cy)]
                
    return (sx, sy, coords, font_size)


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
    svg_parts += [
        f'<polygon points="1,1 {C},1 {C},{C} 1,{C}" {HOUSE_FILLS.get(2, "fill=\'none\'")}/>',
        f'<polygon points="{C},1 {W-1},1 {W-1},{C} {C},{C}" {HOUSE_FILLS.get(12, "fill=\'none\'")}/>',
        f'<polygon points="1,{C} {C},{C} {C},{W-1} 1,{W-1}" {HOUSE_FILLS.get(6, "fill=\'none\'")}/>',
        f'<polygon points="{C},{C} {W-1},{C} {W-1},{W-1} {C},{W-1}" {HOUSE_FILLS.get(8, "fill=\'none\'")}/>',
    ]

    # ── Inner diamond ──
    svg_parts += [
        f'<line x1="{C}" y1="1" x2="1" y2="{C}" stroke="{LINE_COLOR}" stroke-width="{INNER_W}"/>',
        f'<line x1="{C}" y1="1" x2="{W-1}" y2="{C}" stroke="{LINE_COLOR}" stroke-width="{INNER_W}"/>',
        f'<line x1="1" y1="{C}" x2="{C}" y2="{W-1}" stroke="{LINE_COLOR}" stroke-width="{INNER_W}"/>',
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

        planets_here = planet_placements.get(sign_name, [])
        sx, sy, planet_slots, p_font_size = get_house_layout(house_num, len(planets_here))

        # Sign number — visible, bold
        svg_parts.append(
            f'<text x="{sx}" y="{sy + 4}" text-anchor="middle" '
            f'font-family="Calibri, sans-serif" font-weight="bold" font-size="16" '
            f'fill="#1E120F">{sign_num}</text>'
        )

        # Planets in this sign
        for idx, planet in enumerate(planets_here):
            if idx >= len(planet_slots):
                break
            abbr = PLANET_ABBR.get(planet, planet[:2])
            px, py = planet_slots[idx]
            is_lagna = (planet in ("Ascendant", "Lagna")) or (house_num == 1 and idx == 0)
            color = "#8D2208" if is_lagna else "#000000"
            weight = "700"
            svg_parts.append(
                f'<text x="{px}" y="{py}" text-anchor="middle" '
                f'font-family="{FONT_STACK}" font-weight="{weight}" font-size="{p_font_size}" '
                f'fill="{color}">{abbr}</text>'
            )

    svg_parts.append('</svg>')
    return "\n".join(svg_parts)
