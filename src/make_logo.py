"""Build the UNIQUE Biological & Chemicals logo as pure-path SVGs (no font dependency)."""
import os
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
OUT = os.path.join(HERE, "..", "logo")
os.makedirs(OUT, exist_ok=True)

OLIVE = "#5E6E25"
OLIVE_DK = "#46531A"
OLIVE_LT = "#A9BC4A"
LIME = "#CFE07A"
GRAY = "#3A3A38"
STRIPE = "#B9B9B4"

_fonts = {}


def font(name):
    if name not in _fonts:
        _fonts[name] = TTFont(os.path.join(FONTS, name))
    return _fonts[name]


def text_path(txt, fname, size, x, y, tracking=0.0, skip=()):
    """Return (svg path d, end_x, glyph boxes) for txt set at baseline y."""
    f = font(fname)
    upm = f["head"].unitsPerEm
    cmap = f.getBestCmap()
    gs = f.getGlyphSet()
    s = size / upm
    pen = SVGPathPen(gs)
    boxes = []
    cx = x
    for i, ch in enumerate(txt):
        gname = cmap[ord(ch)]
        adv = f["hmtx"][gname][0] * s
        if i not in skip:
            tp = TransformPen(pen, (s, 0, 0, -s, cx, y))
            gs[gname].draw(tp)
        boxes.append((cx, adv))
        cx += adv + tracking * size
    return pen.getCommands(), cx - tracking * size, boxes


def width(txt, fname, size, tracking=0.0):
    return text_path(txt, fname, size, 0, 0, tracking)[1]


def wordmark(x, baseline, size, color=OLIVE):
    """'UNIQUE' in Poppins Black with the card's signature Q (an O with a stem)."""
    word = "UNIQUE"
    fn = "poppins-latin-900-normal.woff2"
    d, end, boxes = text_path(word, fn, size, x, baseline, tracking=0.02, skip=(3,))
    # draw the Q as an O plus a vertical stem through its bottom
    qx, qadv = boxes[3]
    od, _, _ = text_path("O", fn, size, qx, baseline)
    # Poppins O spans the cap height; stem centred, dropping below baseline
    stem_w = size * 0.155
    cxq = qx + qadv / 2
    stem = (f"M{cxq - stem_w/2:.1f},{baseline - size*0.26:.1f}"
            f"h{stem_w:.1f}v{size*0.42:.1f}h{-stem_w:.1f}z")
    return f'<path fill="{color}" d="{d} {od} {stem}"/>', end


def emblem(cx, cy, r):
    """Round mark: an Erlenmeyer flask with a sprouting leaf (biology + chemistry)."""
    k = r / 100.0  # design on a 200x200 box centred at 0,0

    def P(*pts):
        return " ".join(f"{cx + a*k:.1f},{cy + b*k:.1f}" for a, b in pts)

    flask = (f"M{P((-13,-52))} L{P((-13,-22))} L{P((-46,40))} "
             f"Q{P((-52,54))} {P((-38,58))} L{P((38,58))} Q{P((52,54))} {P((46,40))} "
             f"L{P((13,-22))} L{P((13,-52))} Z")
    lip = f"M{P((-20,-58))} L{P((20,-58))} L{P((20,-50))} L{P((-20,-50))} Z"
    liquid = (f"M{P((-35,20))} Q{P((-18,12))} {P((0,20))} T{P((35,20))} "
              f"L{P((48,44))} Q{P((54,62))} {P((38,62))} L{P((-38,62))} "
              f"Q{P((-54,62))} {P((-48,44))} Z")
    stem = f"M{P((0,-50))} C{P((0,-62))} {P((-2,-70))} {P((-4,-78))}"
    leaf_r = (f"M{P((-2,-66))} C{P((10,-86))} {P((34,-88))} {P((44,-80))} "
              f"C{P((34,-62))} {P((12,-56))} {P((-2,-66))} Z")
    leaf_l = (f"M{P((-4,-76))} C{P((-14,-92))} {P((-34,-94))} {P((-42,-86))} "
              f"C{P((-32,-72))} {P((-16,-68))} {P((-4,-76))} Z")
    vein_r = f"M{P((0,-66))} Q{P((20,-74))} {P((40,-80))}"
    sw = 7 * k
    return f'''
  <defs>
    <radialGradient id="embg" cx="38%" cy="30%" r="80%">
      <stop offset="0" stop-color="#7C8E34"/>
      <stop offset="1" stop-color="{OLIVE_DK}"/>
    </radialGradient>
    <clipPath id="flaskclip"><path d="{flask}"/></clipPath>
  </defs>
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#embg)"/>
  <circle cx="{cx}" cy="{cy}" r="{r*0.9:.1f}" fill="none" stroke="{OLIVE_LT}" stroke-opacity=".55" stroke-width="{2.2*k:.1f}"/>
  <path d="{liquid}" fill="{LIME}" clip-path="url(#flaskclip)"/>
  <circle cx="{cx - 12*k:.1f}" cy="{cy + 36*k:.1f}" r="{5*k:.1f}" fill="#fff" fill-opacity=".85"/>
  <circle cx="{cx + 10*k:.1f}" cy="{cy + 28*k:.1f}" r="{3.4*k:.1f}" fill="#fff" fill-opacity=".85"/>
  <circle cx="{cx + 2*k:.1f}" cy="{cy + 2*k:.1f}" r="{3*k:.1f}" fill="#fff" fill-opacity=".7"/>
  <circle cx="{cx - 5*k:.1f}" cy="{cy - 14*k:.1f}" r="{2.2*k:.1f}" fill="#fff" fill-opacity=".6"/>
  <path d="{flask}" fill="none" stroke="#fff" stroke-width="{sw:.1f}" stroke-linejoin="round"/>
  <path d="{lip}" fill="#fff" stroke="#fff" stroke-width="{2*k:.1f}" stroke-linejoin="round"/>
  <path d="{stem}" fill="none" stroke="{LIME}" stroke-width="{4*k:.1f}" stroke-linecap="round"/>
  <path d="{leaf_r}" fill="{LIME}"/>
  <path d="{leaf_l}" fill="#E6F0B0"/>
  <path d="{vein_r}" fill="none" stroke="{OLIVE}" stroke-width="{1.8*k:.1f}" stroke-linecap="round"/>'''


def stripes(x0, x1, y, n=5, gap=11, h=3.2, color=STRIPE):
    return "".join(f'<rect x="{x0:.1f}" y="{y + i*gap:.1f}" width="{x1-x0:.1f}" height="{h}" fill="{color}"/>'
                   for i in range(n))


def svg(w, h, body, bg=None):
    bgrect = f'<rect width="{w}" height="{h}" fill="{bg}"/>' if bg else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
            f'<title>Unique Biological &amp; Chemicals</title>{bgrect}{body}</svg>\n')


def horizontal(text_color=GRAY, word_color=OLIVE, bg=None, stripe_color=STRIPE):
    W, H = 1700, 540
    body = emblem(255, 270, 205)
    size = 250
    x = 520
    wm, end = wordmark(x, 305, size, word_color)
    body += wm
    tag = "BIOLOGICAL & CHEMICALS"
    tfn = "poppins-latin-600-normal.woff2"
    tsize = 58
    tw = width(tag, tfn, tsize, tracking=0.12)
    # stretch tagline to span the wordmark exactly
    span = end - x
    tracking = 0.12 + (span - tw) / (tsize * (len(tag) - 1))
    td, _, _ = text_path(tag, tfn, tsize, x, 470, tracking=tracking)
    body += f'<path fill="{text_color}" d="{td}"/>'
    body += stripes(x, end, 375, n=3, gap=10, h=3, color=stripe_color)
    return svg(W, H, body, bg)


def stacked(bg=None):
    W, H = 1400, 1150
    body = emblem(700, 250, 200)
    size = 270
    word_w = width("UNIQUE", "poppins-latin-900-normal.woff2", size, tracking=0.02)
    x = (W - word_w) / 2
    wm, end = wordmark(x, 760, size)
    body += wm
    # card-style stripes on either side of the wordmark
    sy = 760 - size * 0.62
    body += stripes(40, x - 40, sy, n=6, gap=14, h=4)
    body += stripes(end + 40, W - 40, sy, n=6, gap=14, h=4)
    tag = "BIOLOGICAL & CHEMICALS"
    tfn = "poppins-latin-700-normal.woff2"
    tsize = 64
    tw = width(tag, tfn, tsize, tracking=0.1)
    td, _, _ = text_path(tag, tfn, tsize, (W - tw) / 2, 930, tracking=0.1)
    body += f'<path fill="{GRAY}" d="{td}"/>'
    sub = "KOLHAPUR"
    sfn = "poppins-latin-500-normal.woff2"
    ssize = 40
    sw_ = width(sub, sfn, ssize, tracking=0.5)
    sd, _, _ = text_path(sub, sfn, ssize, (W - sw_) / 2, 1030, tracking=0.5)
    body += f'<path fill="{OLIVE}" d="{sd}"/>'
    return svg(W, H, body, bg)


def icon(bg=None):
    return svg(600, 600, emblem(300, 300, 280), bg)


files = {
    "unique-logo-horizontal.svg": horizontal(),
    "unique-logo-horizontal-white.svg": horizontal(text_color="#FFFFFF", word_color="#FFFFFF",
                                                  stripe_color="#FFFFFF66"),
    "unique-logo-stacked.svg": stacked(),
    "unique-logo-icon.svg": icon(),
}
for name, content in files.items():
    with open(os.path.join(OUT, name), "w") as fh:
        fh.write(content)
    print("wrote", name, len(content))
