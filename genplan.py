"""Generate the schematic floor plan of the flat (2. OG, Neißstraße 28) as inline SVG.

The outer walls, window axes, stairwell and lift are those of the construction drawing used for
the restaurant plan on gastro-goerlitz.de; the rooms follow the owners' hand sketch.
Units are "u" (~1 cm), portrait orientation: x = left outer wall -> right, y = back outer wall -> street.
The plan is emitted twice: "tall" (street at the bottom) and "wide" (rotated 90 degrees, street on
the left). Labels stay upright in both.

Usage: python3 genplan.py index.html  (replaces the content between <!--plan:wohnung--> markers)
"""
import math
import re
import sys

def fac_out(x): return 2220 - 0.12 * x
def fac_in(x): return 2125 - 0.12 * x

OUTLINE = [(0, 0), (680, 0), (680, 805), (875, 805), (875, fac_out(875)), (0, fac_out(0))]
BALCONY = [(455, -130), (625, -130), (625, 0), (455, 0)]

def rect(x1, y1, x2, y2): return [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
def facade(x1, x2, inset=0):
    return [(x1, fac_out(x1) + inset), (x2, fac_out(x2) + inset), (x2, fac_in(x2) - inset), (x1, fac_in(x1) - inset)]

def door(h, c, o):
    """Door leaf from hinge h to open end o, swing arc from o back to closed end c."""
    r = math.dist(h, c)
    cross = (o[0] - h[0]) * (c[1] - h[1]) - (o[1] - h[1]) * (c[0] - h[0])
    sweep = 1 if cross > 0 else 0
    return f"M{h[0]:g} {h[1]:g}L{o[0]:g} {o[1]:g}A{r:g} {r:g} 0 0 {sweep} {c[0]:g} {c[1]:g}"

def treads(x1, x2, y1, y2, n):
    step = (y2 - y1) / n
    return "".join(f"M{x1:g} {y1 + i * step:g}H{x2:g}" for i in range(n + 1))

def cabin(x1, y1, x2, y2):
    return f"M{x1} {y1}H{x2}V{y2}H{x1}ZM{x1} {y1}L{x2} {y2}M{x2} {y1}L{x1} {y2}"

def box(x1, y1, x2, y2): return f"M{x1:g} {y1:g}H{x2:g}V{y2:g}H{x1:g}Z"

def ellipse(cx, cy, rx, ry):
    return f"M{cx - rx:g} {cy:g}A{rx:g} {ry:g} 0 1 0 {cx + rx:g} {cy:g}A{rx:g} {ry:g} 0 1 0 {cx - rx:g} {cy:g}Z"

def bed(x1, y1, x2, y2, head):
    """Double bed with two pillows at the head end ("left" or "right")."""
    px1, px2 = (x1 + 12, x1 + 52) if head == "left" else (x2 - 52, x2 - 12)
    mid = (y1 + y2) / 2
    return box(x1, y1, x2, y2) + box(px1, y1 + 12, px2, mid - 6) + box(px1, mid + 6, px2, y2 - 12)

FLAT = dict(
    key="wohnung",
    label="Grundriss der Wohnung im 2. Obergeschoss: Zur Neißstraße liegen zwei Schlafzimmer mit je einem Doppelbett, "
          "eines davon mit eigenem Bad mit Badewanne. Hinter den Schlafzimmern führt der Flur an einem Duschbad vorbei "
          "nach hinten in die Wohnküche mit Sofa und Küchenzeile, von dort geht es auf den Balkon zum Hof. "
          "Die Wohnungstür liegt am Treppenhaus mit Aufzug.",
    fills=[
        ("p-guest", [(45, 95), (620, 95), (620, 655), (465, 655), (465, 780), (45, 780)]),  # Wohnküche
        ("p-hall", [(45, 800), (450, 800), (450, 1270), (830, 1270), (830, 1395), (270, 1395), (270, 1030),
                    (45, 1030)]),  # Flur
        ("p-room", rect(45, 1045, 255, 1395)),  # Duschbad
        ("p-hall", rect(465, 845, 830, 1255)),  # Treppenhaus
        ("p-room", rect(50, 1450, 340, 1720)),  # Bad mit Wanne
        ("p-guest", [(355, 1450), (455, 1450), (455, fac_in(455)), (50, fac_in(50)), (50, 1735),
                     (355, 1735)]),  # Schlafzimmer links
        ("p-guest", [(475, 1450), (830, 1450), (830, fac_in(830)), (475, fac_in(475))]),  # Schlafzimmer rechts
        ("p-hall", rect(480, 675, 605, 830)),  # Aufzugskabine
    ],
    openings=[
        ("p-guest", rect(300, 778, 420, 802)),  # Rundbogen Flur/Wohnküche
        ("p-hall", rect(448, 880, 467, 970)),  # Wohnungstür
        ("p-hall", rect(500, 828, 585, 847)),  # Aufzugstür
        ("p-room", rect(253, 1210, 272, 1290)),  # Duschbad
        ("p-guest", rect(365, 1393, 445, 1452)),  # Schlafzimmer links
        ("p-guest", rect(720, 1393, 800, 1452)),  # Schlafzimmer rechts
        ("p-room", rect(180, 1718, 310, 1737)),  # Schiebetür ins Bad
        ("p-guest", rect(494, -2, 586, 97)),  # Balkontür
    ],
    windows=[("front", 135, 260), ("front", 344, 448), ("front", 600, 705),
             ("back", 93, 186), ("back", 340, 432)],
    thin=[
        door((450, 970), (450, 880), (360, 970)),  # Wohnungstür
        door((255, 1290), (255, 1210), (175, 1290)),  # Duschbad
        door((445, 1450), (365, 1450), (445, 1530)),  # Schlafzimmer links
        door((800, 1450), (720, 1450), (800, 1530)),  # Schlafzimmer rechts
        door((494, 95), (540, 95), (494, 141)), door((586, 95), (540, 95), (586, 141)),  # Balkontür, zweiflügelig
        treads(580, 700, 1000, 1240, 9) + treads(715, 825, 960, 1240, 10) + "M707.5 960V1240",  # Haustreppe
        cabin(480, 675, 605, 830),
    ],
    furniture=[
        bed(55, 1845, 255, 2015, "left"),
        bed(630, 1800, 828, 1970, "right"),
        ellipse(195, 1625, 100, 50) + ellipse(195, 1625, 84, 36),  # freistehende Wanne
        box(48, 1292, 150, 1392) + ellipse(99, 1342, 9, 9),  # Dusche
        "M170 200H375V460H290V285H170Z",  # Ecksofa
        box(560, 150, 618, 640),  # Küchenzeile
    ],
    labels=[
        dict(t=["Wohnküche"], x=280, y=615, cls="p-name"),
        dict(t=["Schlafzimmer"], x=352, y=1912, cls="p-name", along=True, sub="mit eigenem Bad"),
        dict(t=["Schlafzimmer"], x=652, y=1625, cls="p-name", sub="mit Sitzecke"),
        dict(t=["Bad"], x=195, y=1520, cls="p-small", sub="Wanne"),
        dict(t=["Bad"], x=150, y=1130, cls="p-small", sub="Dusche"),
        dict(t=["Flur"], x=360, y=1180, cls="p-small", along=True),
        dict(t=["Treppenhaus"], x=520, y=1075, cls="p-small", along=True, halo=True),
        dict(t=["Aufzug"], x=542, y=752, cls="p-small", halo=True, size=30),
        dict(t=["Balkon"], x=540, y=-62, cls="p-small", halo=True, size=32),
        dict(t=["Hof"], x=240, y=-95, cls="p-small p-out"),
    ],
)

SIZES = {"p-name": 46, "p-small": 36}
SUB_SIZE = 34

def pts(poly): return " ".join(f"{x:g},{y:g}" for x, y in poly)

def window_shapes(side, x1, x2):
    if side == "front":
        quad = facade(x1, x2, -2)
        mid = lambda x: (fac_out(x) + fac_in(x)) / 2
        glass = f"M{x1:g} {mid(x1):g}L{x2:g} {mid(x2):g}"
    else:
        quad = rect(x1, -2, x2, 97)
        glass = f"M{x1} 47.5H{x2}"
    return quad, glass

def render(floor, wide):
    k = floor["key"] + ("-w" if wide else "-t")
    T = (lambda x, y: (-y, x)) if wide else (lambda x, y: (x, y))
    out = []
    # bounds from the building plus the balcony and the yard label behind it
    allp = list(OUTLINE) + [(35, -170), (695, -170)]
    xs, ys = zip(*[T(*p) for p in allp])
    pad = 30
    minx, maxx, miny, maxy = min(xs) - pad, max(xs) + pad, min(ys) - pad, max(ys) + pad
    # room outside the façade for the street label
    street_gap = 150
    if wide:
        minx -= street_gap
    else:
        maxy += street_gap
    vb = f"{minx:g} {miny:g} {maxx - minx:g} {maxy - miny:g}"
    out.append(f'<svg class="plan-{"wide" if wide else "tall"}" viewBox="{vb}" role="img" aria-label="{floor["label"]}">')
    g = [f'<pattern id="balkon-{k}" width="24" height="24" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><path class="p-hatch" d="M0 0V24"/></pattern>',
         f'<polygon class="p-yard" points="{pts(BALCONY)}"/>',
         f'<polygon fill="url(#balkon-{k})" points="{pts(BALCONY)}"/>',
         f'<polygon class="p-rail" points="{pts(BALCONY)}"/>',
         f'<polygon class="p-wall" points="{pts(OUTLINE)}"/>']
    for cls, poly in floor["fills"] + floor["openings"]:
        g.append(f'<polygon class="{cls}" points="{pts(poly)}"/>')
    glass = []
    for side, x1, x2 in floor["windows"]:
        quad, gl = window_shapes(side, x1, x2)
        cls = "p-guest"
        g.append(f'<polygon class="{cls}" points="{pts(quad)}"/>')
        glass.append(gl)
    g.append(f'<path class="p-thin" d="{"".join(floor["thin"])}"/>')
    g.append(f'<path class="p-furn" d="{"".join(floor["furniture"])}"/>')
    g.append(f'<path class="p-glass" d="{"".join(glass)}"/>')
    if wide:
        out.append('<g transform="rotate(90)">' + "".join(g) + "</g>")
    else:
        out.append("".join(g))
    # labels
    for lab in floor["labels"]:
        size = lab.get("size", SIZES[lab["cls"].split()[0]])
        lh = size * 1.08
        lx, ly = T(lab["x"], lab["y"])
        rot = -90 if (lab.get("along") and not wide) or (lab.get("across") and wide) else 0
        n = len(lab["t"])
        cls = lab["cls"] + (" p-halo" if lab.get("halo") else "")
        tf = f' transform="rotate({rot} {lx:g} {ly:g})"' if rot else ""
        # optional muted second line below the name, block centred on (x, y)
        sub = lab.get("sub")
        shift = -(SUB_SIZE * 1.25) / 2 if sub else 0
        spans = []
        for i, line in enumerate(lab["t"]):
            by = ly + shift + (i - (n - 1) / 2) * lh + 0.35 * size
            spans.append(f'<tspan x="{lx:g}" y="{by:g}">{line}</tspan>')
        if sub:
            by = ly + shift + (n - 1) / 2 * lh + 0.35 * size + SUB_SIZE * 1.25
            spans.append(f'<tspan class="p-sub" font-size="{SUB_SIZE}" x="{lx:g}" y="{by:g}">{sub}</tspan>')
        out.append(f'<text class="{cls}" font-size="{size}" text-anchor="middle"{tf}>{"".join(spans)}</text>')
    # street label along the façade
    sx = 437.5
    sy = fac_out(sx) + 90
    ang = math.degrees(math.atan2(fac_out(875) - fac_out(0), 875))
    if wide:
        lx, ly = T(sx, sy)
        out.append(f'<text class="p-street" font-size="40" text-anchor="middle" transform="rotate({ang - 90:.2f} {lx:g} {ly:g})" x="{lx:g}" y="{ly + 14:g}">Neißstraße</text>')
    else:
        out.append(f'<text class="p-street" font-size="40" text-anchor="middle" transform="rotate({ang:.2f} {sx:g} {sy:g})" x="{sx:g}" y="{sy + 14:g}">Neißstraße</text>')
    out.append("</svg>")
    return "".join(out)

def build():
    return {FLAT["key"]: render(FLAT, True) + "\n" + render(FLAT, False)}

if __name__ == "__main__":
    target = sys.argv[1]
    src = open(target, encoding="utf-8").read()
    for key, svg in build().items():
        pat = re.compile(rf"(<!--plan:{key}-->)(.*?)(<!--/plan:{key}-->)", re.S)
        if not pat.search(src):
            sys.exit(f"marker plan:{key} missing")
        src = pat.sub(lambda m: m.group(1) + "\n" + svg + "\n" + m.group(3), src)
    open(target, "w", encoding="utf-8").write(src)
    print("ok", {k: len(v) for k, v in build().items()})
