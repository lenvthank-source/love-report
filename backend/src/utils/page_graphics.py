"""
page_graphics.py  — Watermarks + romantic bottom scene illustrations
"""
import math

# ─────────────────────────────────────────────────────────────────────────────
# SMALL CORNER WATERMARKS  (120×120, transparent, opacity applied in CSS)
# ─────────────────────────────────────────────────────────────────────────────

def _wm(content: str, size: int = 120) -> str:
    return (
        f'<svg viewBox="0 0 {size} {size}" width="{size}" height="{size}" '
        f'xmlns="http://www.w3.org/2000/svg">{content}</svg>'
    )


_WM_MANDALA = lambda: _wm(
    "".join([
        f'<ellipse cx="{60 + 28*math.cos(math.radians(i*30)):.1f}" '
        f'cy="{60 + 28*math.sin(math.radians(i*30)):.1f}" '
        f'rx="10" ry="18" '
        f'transform="rotate({i*30} {60 + 28*math.cos(math.radians(i*30)):.1f} {60 + 28*math.sin(math.radians(i*30)):.1f})" '
        f'fill="none" stroke="#8E6E5E" stroke-width="0.9"/>'
        for i in range(12)
    ]) +
    '<circle cx="60" cy="60" r="8" fill="none" stroke="#C9967B" stroke-width="1"/>'
    '<circle cx="60" cy="60" r="20" fill="none" stroke="#8E6E5E" stroke-width="0.6"/>'
)

_WM_MOON = lambda: _wm(
    '<circle cx="60" cy="60" r="36" fill="none" stroke="#8E6E5E" stroke-width="1"/>'
    '<circle cx="74" cy="54" r="30" fill="white" opacity="0.95"/>'
    + "".join([f'<circle cx="{x}" cy="{y}" r="1.2" fill="#8E6E5E"/>'
               for x, y in [(25,30),(35,18),(48,22),(18,50),(22,70)]])
)

_WM_STARS = lambda: _wm(
    "".join([
        f'<circle cx="{x}" cy="{y}" r="{r}" fill="#8E6E5E"/>'
        for x, y, r in [(20,40,2),(50,20,2.5),(90,30,1.5),(70,60,2),(40,80,2),(100,70,1.5),(110,40,2),(80,90,1.5)]
    ]) +
    '<line x1="20" y1="40" x2="50" y2="20" stroke="#8E6E5E" stroke-width="0.6" opacity="0.7"/>'
    '<line x1="50" y1="20" x2="90" y2="30" stroke="#8E6E5E" stroke-width="0.6" opacity="0.7"/>'
    '<line x1="70" y1="60" x2="100" y2="70" stroke="#8E6E5E" stroke-width="0.6" opacity="0.7"/>'
)

_WM_COMPASS = lambda: _wm(
    '<circle cx="60" cy="60" r="48" fill="none" stroke="#8E6E5E" stroke-width="0.8"/>'
    '<circle cx="60" cy="60" r="36" fill="none" stroke="#D4A68C" stroke-width="0.5"/>'
    '<polygon points="60,14 56,52 60,44 64,52" fill="#8E6E5E"/>'
    '<polygon points="60,106 64,68 60,76 56,68" fill="#C9967B"/>'
    '<circle cx="60" cy="60" r="4" fill="#C9967B"/>'
)

_WM_HEART = lambda: _wm(
    '<path d="M 60,90 C 60,90 22,66 22,44 C 22,30 32,22 44,26 C 52,28 60,36 60,36 '
    'C 60,36 68,28 76,26 C 88,22 98,30 98,44 C 98,66 60,90 60,90 Z" '
    'fill="none" stroke="#C9967B" stroke-width="1.3"/>'
    '<path d="M 22,44 C 5,38 0,20 14,16" fill="none" stroke="#D4A68C" stroke-width="0.8"/>'
    '<path d="M 98,44 C 115,38 120,20 106,16" fill="none" stroke="#D4A68C" stroke-width="0.8"/>'
)

_WM_HOURGLASS = lambda: _wm(
    '<path d="M 30,10 L 90,10 L 60,60 L 90,110 L 30,110 L 60,60 Z" fill="none" stroke="#8E6E5E" stroke-width="1.2"/>'
    '<line x1="30" y1="10" x2="90" y2="10" stroke="#C9967B" stroke-width="2"/>'
    '<line x1="30" y1="110" x2="90" y2="110" stroke="#C9967B" stroke-width="2"/>'
)

_WM_CHAKRA = lambda: _wm(
    "".join([
        f'<circle cx="60" cy="{y}" r="5" fill="none" stroke="{c}" stroke-width="1.2"/>'
        for y, c in [(100,"#C0392B"),(88,"#E67E22"),(76,"#F1C40F"),
                     (64,"#27AE60"),(52,"#2980B9"),(40,"#6C3483"),(28,"#8E44AD")]
    ]) +
    '<line x1="60" y1="20" x2="60" y2="108" stroke="#D4A68C" stroke-width="0.6" opacity="0.5"/>'
)

_WM_GEMS = lambda: _wm(
    "".join([
        f'<polygon points="{gx},{gy-16} {gx+14},{gy} {gx},{gy+10} {gx-14},{gy}" '
        f'fill="none" stroke="{gc}" stroke-width="1"/>'
        for gx, gy, gc in [(38,55,"#7FB3D3"),(60,38,"#D4A68C"),(82,55,"#9B59B6")]
    ]) +
    '<ellipse cx="60" cy="90" rx="35" ry="8" fill="none" stroke="#C9967B" stroke-width="1"/>'
)

_WM_SHIELD = lambda: _wm(
    '<path d="M 60,10 L 100,28 L 100,68 Q 100,100 60,112 Q 20,100 20,68 L 20,28 Z" '
    'fill="none" stroke="#8E6E5E" stroke-width="1.2"/>'
    '<path d="M 60,35 L 70,55 L 58,68 L 72,88" fill="none" stroke="#C9967B" stroke-width="1.5" stroke-linecap="round"/>'
)

_WM_BARS = lambda: _wm(
    "".join([
        f'<rect x="{x}" y="{90-h}" width="14" height="{h}" rx="2" fill="none" stroke="#C9967B" stroke-width="1"/>'
        for x, h in [(12,50),(30,35),(48,60),(66,28),(84,45),(102,22)]
    ]) +
    '<line x1="10" y1="92" x2="118" y2="92" stroke="#8E6E5E" stroke-width="0.8"/>'
)

_WM_CALENDAR = lambda: _wm(
    "".join([
        f'<rect x="{10+c*28}" y="{20+r*28}" width="24" height="22" rx="2" '
        f'fill="{"#C9967B" if (r*4+c) in [1,5,9] else "none"}" '
        f'stroke="#C9967B" stroke-width="0.8" opacity="0.8"/>'
        for r in range(3) for c in range(4)
    ])
)

_WM_REGISTRY = {
    2:_WM_COMPASS, 3:_WM_MANDALA, 4:_WM_HEART, 5:_WM_COMPASS,
    6:_WM_STARS, 7:_WM_MOON, 8:_WM_MOON, 9:_WM_HEART, 10:_WM_HEART,
    11:_WM_STARS, 12:_WM_HEART, 13:_WM_HEART, 14:_WM_STARS,
    15:_WM_MANDALA, 16:_WM_SHIELD, 17:_WM_HOURGLASS, 18:_WM_SHIELD, 19:_WM_BARS,
    20:_WM_BARS, 21:_WM_HOURGLASS, 22:_WM_CALENDAR, 23:_WM_CHAKRA,
    24:_WM_CHAKRA, 25:_WM_GEMS, 26:_WM_HEART,
}

def get_page_watermark(page_num: int) -> str:
    fn = _WM_REGISTRY.get(page_num)
    return fn() if fn else ""


# ─────────────────────────────────────────────────────────────────────────────
# BOTTOM SCENE ILLUSTRATIONS  (595 × 115, visible, romantic/celestial)
# These are placed in the lower portion of each content page.
# ─────────────────────────────────────────────────────────────────────────────

C_ROSE   = "#C9967B"
C_DARK   = "#6E4F40"
C_LIGHT  = "#E8C9B6"
C_SUBTLE = "#D4A68C"
C_GOLD   = "#C9967B"
STR      = "#8E6E5E"  # stroke colour


def _scene(content: str, w: int = 595, h: int = 115) -> str:
    return (
        f'<svg viewBox="0 0 {w} {h}" width="100%" height="{h}px" '
        f'preserveAspectRatio="xMidYMid meet" '
        f'xmlns="http://www.w3.org/2000/svg">'
        f'{content}</svg>'
    )


def _heart_path(cx: float, cy: float, s: float = 1.0, color: str = C_ROSE, op: float = 0.8) -> str:
    """Centered heart at (cx,cy) scaled by s."""
    r = 12 * s
    return (
        f'<path d="M {cx},{cy + 0.6*r} '
        f'C {cx},{cy + 0.6*r} {cx - r},{cy + 0.1*r} {cx - r},{cy - 0.3*r} '
        f'C {cx - r},{cy - 0.7*r} {cx - 0.6*r},{cy - r} {cx},{cy - 0.55*r} '
        f'C {cx + 0.6*r},{cy - r} {cx + r},{cy - 0.7*r} {cx + r},{cy - 0.3*r} '
        f'C {cx + r},{cy + 0.1*r} {cx},{cy + 0.6*r} {cx},{cy + 0.6*r} Z" '
        f'fill="{color}" opacity="{op}"/>'
    )


def _star(cx: float, cy: float, r: float = 3, color: str = C_SUBTLE, op: float = 0.7) -> str:
    return (
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" opacity="{op}"/>'
    )


def _sparkle(cx: float, cy: float, s: float = 8, color: str = C_SUBTLE, op: float = 0.6) -> str:
    return (
        f'<line x1="{cx}" y1="{cy-s}" x2="{cx}" y2="{cy+s}" stroke="{color}" stroke-width="1.2" opacity="{op}"/>'
        f'<line x1="{cx-s}" y1="{cy}" x2="{cx+s}" y2="{cy}" stroke="{color}" stroke-width="1.2" opacity="{op}"/>'
        f'<line x1="{cx-s*0.7:.1f}" y1="{cy-s*0.7:.1f}" x2="{cx+s*0.7:.1f}" y2="{cy+s*0.7:.1f}" stroke="{color}" stroke-width="0.7" opacity="{op*0.7:.1f}"/>'
        f'<line x1="{cx+s*0.7:.1f}" y1="{cy-s*0.7:.1f}" x2="{cx-s*0.7:.1f}" y2="{cy+s*0.7:.1f}" stroke="{color}" stroke-width="0.7" opacity="{op*0.7:.1f}"/>'
    )


# ── Scene A: COUPLE HOLDING HANDS ────────────────────────────────────────────
def scene_couple_hands() -> str:
    W, H = 595, 115
    ground = H - 12

    # Female figure  (left, centre ~215)
    # Male figure  (right, centre ~380)
    FX, MX = 215, 380
    head_y = 20

    female = (
        # head
        f'<ellipse cx="{FX}" cy="{head_y}" rx="13" ry="15" fill="{C_LIGHT}" opacity="0.9"/>'
        # hair (3 wavy strands)
        f'<path d="M {FX-13},{head_y-5} Q {FX-17},{head_y-18} {FX-7},{head_y-16} Q {FX},{head_y-20} {FX+7},{head_y-16}" '
        f'stroke="{C_DARK}" stroke-width="5" fill="none" stroke-linecap="round" opacity="0.75"/>'
        # dress body
        f'<path d="M {FX-12},{head_y+15} C {FX-15},{head_y+35} {FX-22},{ground-20} {FX-26},{ground} '
        f'L {FX+26},{ground} C {FX+22},{ground-20} {FX+15},{head_y+35} {FX+12},{head_y+15} Z" '
        f'fill="{C_ROSE}" opacity="0.7"/>'
        # neck
        f'<rect x="{FX-4}" y="{head_y+14}" width="8" height="10" rx="3" fill="{C_LIGHT}" opacity="0.85"/>'
        # right arm extending to centre
        f'<path d="M {FX+12},{head_y+26} Q {FX+30},{head_y+38} {FX+58},{head_y+45}" '
        f'stroke="{C_LIGHT}" stroke-width="7" fill="none" stroke-linecap="round" opacity="0.8"/>'
    )

    male = (
        # head
        f'<ellipse cx="{MX}" cy="{head_y}" rx="13" ry="14" fill="{C_SUBTLE}" opacity="0.9"/>'
        # hair (short, thick top)
        f'<path d="M {MX-13},{head_y-4} Q {MX-12},{head_y-16} {MX},{head_y-18} Q {MX+12},{head_y-16} {MX+13},{head_y-4}" '
        f'fill="{C_DARK}" opacity="0.6"/>'
        # body (jacket)
        f'<path d="M {MX-14},{head_y+14} L {MX-16},{ground} L {MX+16},{ground} L {MX+14},{head_y+14} Z" '
        f'fill="{STR}" opacity="0.65"/>'
        # neck
        f'<rect x="{MX-4}" y="{head_y+13}" width="8" height="10" rx="3" fill="{C_SUBTLE}" opacity="0.85"/>'
        # left arm extending to centre
        f'<path d="M {MX-12},{head_y+26} Q {MX-30},{head_y+38} {MX-58},{head_y+45}" '
        f'stroke="{C_SUBTLE}" stroke-width="7" fill="none" stroke-linecap="round" opacity="0.8"/>'
    )

    # Joined hands
    mid_x = (FX + MX) // 2
    hands = (
        f'<ellipse cx="{mid_x}" cy="{head_y+48}" rx="22" ry="12" fill="{C_ROSE}" opacity="0.55"/>'
        f'<ellipse cx="{mid_x}" cy="{head_y+46}" rx="14" ry="7" fill="{C_LIGHT}" opacity="0.5"/>'
    )

    # Floating hearts
    hearts = (
        _heart_path(FX - 35, head_y + 5, 0.7, C_ROSE, 0.6)
        + _heart_path(mid_x, head_y - 15, 0.9, C_ROSE, 0.7)
        + _heart_path(MX + 38, head_y + 8, 0.6, C_SUBTLE, 0.6)
        + _heart_path(mid_x - 40, head_y - 25, 0.5, C_LIGHT, 0.5)
        + _heart_path(mid_x + 50, head_y - 20, 0.55, C_LIGHT, 0.5)
    )

    # Sparkles
    sparks = (
        _sparkle(120, 35) + _sparkle(475, 28) + _sparkle(297, 8)
        + _sparkle(160, 65, 5) + _sparkle(435, 58, 5)
    )

    # Ground line
    ground_line = (
        f'<line x1="80" y1="{ground}" x2="{W-80}" y2="{ground}" stroke="{C_SUBTLE}" stroke-width="0.8" opacity="0.4"/>'
        + "".join([_star(x, ground - 3, 2, C_ROSE, 0.3) for x in range(90, W-80, 30)])
    )

    return _scene(female + male + hands + hearts + sparks + ground_line, W, H)


# ── Scene B: COUPLE WATCHING THE MOON ────────────────────────────────────────
def scene_couple_moon() -> str:
    W, H = 595, 115
    ground = H - 10

    # Large crescent moon (upper centre)
    moon = (
        f'<circle cx="297" cy="32" r="42" fill="#FDF3E3" opacity="0.85"/>'
        f'<circle cx="318" cy="24" r="35" fill="#FAF8F5" opacity="0.97"/>'
        # moon glow ring
        f'<circle cx="297" cy="32" r="50" fill="none" stroke="#F5DFB6" stroke-width="2" opacity="0.35"/>'
    )

    # Stars around moon
    star_pos = [(180,18),(220,8),(370,12),(420,22),(145,35),(460,38),(200,55),(395,50)]
    stars = "".join([_star(x, y, 2.5, C_GOLD, 0.6) for x, y in star_pos])
    stars += _sparkle(155, 22, 6) + _sparkle(448, 15, 5) + _sparkle(340, 5, 7)

    # Seated female (left) – compact sitting pose
    FX, FY_base = 210, ground - 5
    female_sit = (
        f'<ellipse cx="{FX}" cy="{FY_base-52}" rx="11" ry="13" fill="{C_LIGHT}" opacity="0.9"/>'
        # hair
        f'<path d="M {FX-11},{FY_base-57} Q {FX-15},{FY_base-70} {FX-4},{FY_base-69} Q {FX+3},{FY_base-72} {FX+7},{FY_base-64}" '
        f'stroke="{C_DARK}" stroke-width="5" fill="none" stroke-linecap="round" opacity="0.7"/>'
        # dress (sitting, spread)
        f'<ellipse cx="{FX}" cy="{FY_base-20}" rx="22" ry="14" fill="{C_ROSE}" opacity="0.65"/>'
        # torso
        f'<path d="M {FX-10},{FY_base-39} L {FX-12},{FY_base-22} L {FX+12},{FY_base-22} L {FX+10},{FY_base-39} Z" '
        f'fill="{C_ROSE}" opacity="0.7"/>'
        # leaning arm
        f'<path d="M {FX+10},{FY_base-34} Q {FX+22},{FY_base-30} {FX+28},{FY_base-28}" '
        f'stroke="{C_LIGHT}" stroke-width="6" fill="none" stroke-linecap="round" opacity="0.75"/>'
    )

    # Seated male (right)
    MX, MY_base = 388, ground - 5
    male_sit = (
        f'<ellipse cx="{MX}" cy="{MY_base-52}" rx="12" ry="13" fill="{C_SUBTLE}" opacity="0.9"/>'
        # hair
        f'<path d="M {MX-12},{MY_base-56} Q {MX-11},{MY_base-68} {MX},{MY_base-70} Q {MX+11},{MY_base-68} {MX+12},{MY_base-56}" '
        f'fill="{C_DARK}" opacity="0.5"/>'
        # body
        f'<rect x="{MX-12}" y="{MY_base-39}" width="24" height="22" rx="4" fill="{STR}" opacity="0.6"/>'
        # legs sitting
        f'<ellipse cx="{MX}" cy="{MY_base-14}" rx="18" ry="10" fill="{C_DARK}" opacity="0.5"/>'
        # arm
        f'<path d="M {MX-12},{MY_base-34} Q {MX-24},{MY_base-30} {MX-30},{MY_base-28}" '
        f'stroke="{C_SUBTLE}" stroke-width="6" fill="none" stroke-linecap="round" opacity="0.7"/>'
    )

    # Arms almost touching in centre
    join_x = 297
    touch = (
        f'<path d="M {FX+28},{FY_base-28} Q {join_x},{FY_base-22} {MX-30},{MY_base-28}" '
        f'stroke="{C_ROSE}" stroke-width="4" fill="none" stroke-linecap="round" opacity="0.5"/>'
        + _heart_path(join_x, FY_base - 38, 0.7, C_ROSE, 0.55)
    )

    # Moon reflection on ground
    reflect = (
        f'<ellipse cx="297" cy="{ground}" rx="30" ry="4" fill="#FDF3E3" opacity="0.3"/>'
        f'<line x1="60" y1="{ground}" x2="{W-60}" y2="{ground}" stroke="{C_SUBTLE}" stroke-width="0.8" opacity="0.35"/>'
    )

    return _scene(moon + stars + female_sit + male_sit + touch + reflect, W, H)


# ── Scene C: COUPLE TYING HANDS / CEREMONY ───────────────────────────────────
def scene_couple_ceremony() -> str:
    W, H = 595, 115
    ground = H - 12

    # Two large hands coming from left and right, overlapping in centre
    # Left hand (hers, delicate)
    left_hand = (
        f'<path d="M 150,{ground} L 155,{ground-55} Q 157,{ground-65} 165,{ground-65} '
        f'Q 175,{ground-65} 175,{ground-55} L 175,{ground-40} '
        f'Q 185,{ground-48} 185,{ground-60} Q 185,{ground-70} 192,{ground-70} '
        f'Q 200,{ground-70} 200,{ground-60} L 200,{ground-40} '
        f'Q 208,{ground-48} 208,{ground-58} Q 208,{ground-68} 215,{ground-68} '
        f'Q 222,{ground-68} 222,{ground-58} L 222,{ground-42} '
        f'Q 230,{ground-48} 230,{ground-56} Q 230,{ground-64} 236,{ground-64} '
        f'Q 242,{ground-64} 242,{ground-50} L 244,{ground-30} '
        f'Q 250,{ground-10} 265,{ground} Z" '
        f'fill="{C_LIGHT}" stroke="{C_ROSE}" stroke-width="1.2" opacity="0.85"/>'
    )

    # Right hand (his, broader)
    right_hand = (
        f'<path d="M 445,{ground} L 440,{ground-52} Q 438,{ground-62} 430,{ground-62} '
        f'Q 420,{ground-62} 420,{ground-52} L 420,{ground-38} '
        f'Q 412,{ground-46} 412,{ground-58} Q 412,{ground-68} 405,{ground-68} '
        f'Q 397,{ground-68} 397,{ground-58} L 397,{ground-38} '
        f'Q 390,{ground-46} 390,{ground-56} Q 390,{ground-66} 383,{ground-66} '
        f'Q 376,{ground-66} 376,{ground-56} L 376,{ground-40} '
        f'Q 368,{ground-46} 368,{ground-54} Q 368,{ground-62} 362,{ground-62} '
        f'Q 354,{ground-62} 354,{ground-48} L 352,{ground-28} '
        f'Q 346,{ground-8} 332,{ground} Z" '
        f'fill="{C_SUBTLE}" stroke="{STR}" stroke-width="1.2" opacity="0.82"/>'
    )

    # Flowing thread/cloth binding the hands
    thread = (
        f'<path d="M 265,{ground-25} Q 297,{ground-50} 332,{ground-25}" '
        f'stroke="{C_GOLD}" stroke-width="2.5" fill="none" stroke-dasharray="6,4" opacity="0.7"/>'
        f'<path d="M 270,{ground-18} Q 297,{ground-42} 325,{ground-18}" '
        f'stroke="{C_ROSE}" stroke-width="1.5" fill="none" opacity="0.5"/>'
        # knot in centre
        f'<ellipse cx="297" cy="{ground-35}" rx="12" ry="8" fill="{C_GOLD}" opacity="0.6"/>'
        + _heart_path(297, ground - 60, 0.9, C_ROSE, 0.75)
    )

    # Small flower accents
    flowers = "".join([
        f'<circle cx="{x}" cy="{y}" r="5" fill="{C_ROSE}" opacity="0.4"/>'
        f'<circle cx="{x}" cy="{y}" r="2" fill="{C_LIGHT}" opacity="0.7"/>'
        for x, y in [(200, ground-72), (250, ground-78), (345, ground-76), (397, ground-70)]
    ])

    # Stars
    sparks = _sparkle(100, 35) + _sparkle(500, 28) + _sparkle(297, 12) + _sparkle(180, 20, 5)

    ground_line = (
        f'<line x1="80" y1="{ground}" x2="{W-80}" y2="{ground}" stroke="{C_SUBTLE}" stroke-width="0.8" opacity="0.35"/>'
    )

    return _scene(left_hand + right_hand + thread + flowers + sparks + ground_line, W, H)


# ── Scene D: HEARTS & BLOOMS ─────────────────────────────────────────────────
def scene_hearts_blooms() -> str:
    W, H = 595, 115

    # Rose stems
    stems = "".join([
        f'<path d="M {x},{H-5} Q {x+wx},{H//2} {x+tx},{ty}" '
        f'stroke="{STR}" stroke-width="1.5" fill="none" opacity="0.55"/>'
        for x, wx, tx, ty in [
            (120, -10, -5, 30), (180, 8, 5, 20), (250, -5, -8, 25),
            (330, 6, 4, 22), (400, -8, -3, 28), (460, 10, 6, 18), (520, -5, -4, 35),
        ]
    ])

    # Rose heads (stylised)
    roses = "".join([
        f'<ellipse cx="{x}" cy="{y}" rx="14" ry="11" fill="{C_ROSE}" opacity="0.6"/>'
        f'<ellipse cx="{x}" cy="{y}" rx="9" ry="7" fill="{C_LIGHT}" opacity="0.5"/>'
        f'<ellipse cx="{x}" cy="{y}" rx="4" ry="3" fill="{C_DARK}" opacity="0.25"/>'
        for x, y in [(115,30),(185,20),(245,25),(335,22),(405,28),(465,18),(515,35)]
    ])

    # Floating hearts of different sizes
    hearts = (
        _heart_path(297, 28, 1.4, C_ROSE, 0.75)
        + _heart_path(160, 50, 0.85, C_SUBTLE, 0.6)
        + _heart_path(430, 45, 0.9, C_ROSE, 0.55)
        + _heart_path(70, 40, 0.7, C_LIGHT, 0.5)
        + _heart_path(530, 55, 0.7, C_LIGHT, 0.5)
        + _heart_path(225, 70, 0.6, C_ROSE, 0.4)
        + _heart_path(370, 72, 0.6, C_ROSE, 0.4)
    )

    # Sparkles
    sparks = "".join([_sparkle(x, y, s, C_GOLD, 0.55) for x, y, s in
                      [(100, 22, 7), (200, 12, 6), (297, 8, 9), (395, 14, 6), (500, 20, 7)]])

    # Ground petal scatter
    petals = "".join([
        f'<ellipse cx="{x}" cy="{H-7}" rx="5" ry="3" fill="{C_ROSE}" opacity="0.35" '
        f'transform="rotate({a} {x} {H-7})"/>'
        for x, a in [(90, 20), (170, -15), (260, 30), (330, -10), (410, 25), (490, -20), (550, 15)]
    ])

    return _scene(stems + roses + hearts + sparks + petals, W, H)


# ── Scene E: CELESTIAL / STARFIELD ────────────────────────────────────────────
def scene_celestial() -> str:
    W, H = 595, 115

    # Crescent moon (smaller, off-centre)
    moon = (
        f'<circle cx="130" cy="48" r="35" fill="#FDF3E3" opacity="0.75"/>'
        f'<circle cx="148" cy="40" r="28" fill="#FAF8F5" opacity="0.96"/>'
        f'<circle cx="130" cy="48" r="42" fill="none" stroke="#F5DFB6" stroke-width="1.5" opacity="0.3"/>'
    )

    # Constellation lines + dots (right half)
    const_pts = [(340,22),(390,40),(360,65),(420,70),(450,38),(500,20),(480,60),(530,45),(560,70)]
    const_lines = [
        (340,22,390,40),(390,40,420,70),(390,40,450,38),(450,38,500,20),(450,38,480,60),(500,20,530,45),
    ]
    constellation = "".join([
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{C_SUBTLE}" stroke-width="0.9" opacity="0.45"/>'
        for x1,y1,x2,y2 in const_lines
    ]) + "".join([
        f'<circle cx="{x}" cy="{y}" r="2.5" fill="{C_GOLD}" opacity="0.7"/>'
        for x, y in const_pts
    ])

    # Scattered stars
    star_field = "".join([_star(x, y, r, C_SUBTLE, op) for x, y, r, op in [
        (220, 18, 1.8, 0.6),(270, 35, 2.2, 0.55),(250, 58, 1.5, 0.5),(310, 12, 2.5, 0.65),
        (200, 75, 1.8, 0.45),(550, 90, 2.0, 0.5),(165, 45, 1.5, 0.4),(580, 30, 2.2, 0.55),
    ]])

    # Sparkles
    sparks = (
        _sparkle(60, 22, 8) + _sparkle(180, 80, 6) + _sparkle(297, 95, 9, C_ROSE)
        + _sparkle(470, 88, 7) + _sparkle(570, 55, 6)
    )

    # Shooting star trace
    shoot = (
        f'<path d="M 580,15 L 495,65" stroke="#FDF3E3" stroke-width="1.5" opacity="0.6" stroke-linecap="round"/>'
        f'<circle cx="580" cy="15" r="3" fill="#FDF3E3" opacity="0.8"/>'
    )

    ground_line = f'<line x1="60" y1="{H-8}" x2="{W-60}" y2="{H-8}" stroke="{C_SUBTLE}" stroke-width="0.6" opacity="0.3"/>'

    return _scene(moon + constellation + star_field + sparks + shoot + ground_line, W, H)


# ── Scene F: SILHOUETTE EMBRACE ───────────────────────────────────────────────
def scene_embrace() -> str:
    W, H = 595, 115
    ground = H - 12
    CX = W // 2  # 297

    # Two figures standing close, slightly turned toward each other
    # Female (slightly left of centre)
    FX = CX - 18
    female = (
        f'<ellipse cx="{FX}" cy="{ground-82}" rx="12" ry="14" fill="{C_LIGHT}" opacity="0.9"/>'
        f'<path d="M {FX-12},{ground-80} Q {FX-16},{ground-96} {FX-5},{ground-95} Q {FX+2},{ground-98} {FX+8},{ground-90}" '
        f'stroke="{C_DARK}" stroke-width="5" fill="none" stroke-linecap="round" opacity="0.65"/>'
        # dress
        f'<path d="M {FX-11},{ground-68} C {FX-14},{ground-45} {FX-24},{ground-18} {FX-28},{ground} '
        f'L {FX+14},{ground} C {FX+10},{ground-18} {FX+10},{ground-45} {FX+11},{ground-68} Z" '
        f'fill="{C_ROSE}" opacity="0.7"/>'
        # arm around him
        f'<path d="M {FX+11},{ground-68} Q {FX+22},{ground-72} {FX+32},{ground-76}" '
        f'stroke="{C_LIGHT}" stroke-width="7" fill="none" stroke-linecap="round" opacity="0.75"/>'
    )

    # Male (slightly right of centre)
    MX = CX + 18
    male = (
        f'<ellipse cx="{MX}" cy="{ground-86}" rx="13" ry="14" fill="{C_SUBTLE}" opacity="0.9"/>'
        f'<path d="M {MX-13},{ground-90} Q {MX-12},{ground-103} {MX},{ground-105} Q {MX+12},{ground-103} {MX+13},{ground-90}" '
        f'fill="{C_DARK}" opacity="0.5"/>'
        # body
        f'<path d="M {MX-13},{ground-72} L {MX-14},{ground} L {MX+14},{ground} L {MX+13},{ground-72} Z" '
        f'fill="{STR}" opacity="0.65"/>'
        # arm around her
        f'<path d="M {MX-13},{ground-68} Q {MX-24},{ground-72} {MX-34},{ground-76}" '
        f'stroke="{C_SUBTLE}" stroke-width="8" fill="none" stroke-linecap="round" opacity="0.7"/>'
    )

    # Large heart above them
    big_heart = _heart_path(CX, ground - 115, 1.8, C_ROSE, 0.55)

    # Halo / aura
    aura = (
        f'<circle cx="{CX}" cy="{ground-80}" r="55" fill="none" stroke="{C_ROSE}" stroke-width="0.8" opacity="0.2"/>'
        f'<circle cx="{CX}" cy="{ground-80}" r="68" fill="none" stroke="{C_SUBTLE}" stroke-width="0.5" opacity="0.15"/>'
    )

    # Scattered hearts
    small_hearts = (
        _heart_path(CX - 75, ground - 78, 0.65, C_ROSE, 0.5)
        + _heart_path(CX + 80, ground - 82, 0.6, C_ROSE, 0.45)
        + _heart_path(CX - 110, ground - 60, 0.5, C_LIGHT, 0.4)
        + _heart_path(CX + 115, ground - 55, 0.5, C_LIGHT, 0.4)
    )

    sparks = (
        _sparkle(80, 30) + _sparkle(520, 25) + _sparkle(CX, 5, 10, C_ROSE)
        + _sparkle(160, 60, 5) + _sparkle(440, 55, 5)
    )

    ground_line = (
        f'<line x1="80" y1="{ground}" x2="{W-80}" y2="{ground}" stroke="{C_SUBTLE}" stroke-width="0.8" opacity="0.4"/>'
    )

    return _scene(aura + female + male + big_heart + small_hearts + sparks + ground_line, W, H)


# Registry: page_num → scene generator
_SCENE_REGISTRY = {
    2:  scene_celestial,       # Customer info
    3:  scene_hearts_blooms,   # Disclaimer
    4:  scene_hearts_blooms,   # Author message
    5:  scene_celestial,       # Master Index
    6:  scene_celestial,       # D1 Chart
    7:  scene_couple_moon,     # 1st House
    8:  scene_couple_moon,     # Moon Sign
    9:  scene_couple_hands,    # 5th House romance
    10: scene_hearts_blooms,   # Venus
    11: scene_celestial,       # D9/D30 charts
    12: scene_couple_ceremony, # 7th House
    13: scene_couple_hands,    # Spouse nature
    14: scene_couple_moon,     # D1 vs D9
    15: scene_couple_ceremony, # D9 Navamsa
    16: scene_hearts_blooms,   # D30 Trimsamsha
    17: scene_celestial,       # Recurring patterns
    18: scene_celestial,       # Planetary blockages
    19: scene_hearts_blooms,   # Red flags
    20: scene_hearts_blooms,   # Risk matrix
    21: scene_couple_moon,     # Dasha overview
    22: scene_couple_moon,     # 3-Year forecast
    23: scene_hearts_blooms,   # Sub-minor forecast
    24: scene_hearts_blooms,   # Mantras & healing
    25: scene_hearts_blooms,   # Practical remedies
    26: scene_embrace,         # Final heart synthesis
}


def get_bottom_scene(page_num: int) -> str:
    """Return a 595×115 romantic/celestial SVG scene for the given page."""
    fn = _SCENE_REGISTRY.get(page_num)
    return fn() if fn else ""
