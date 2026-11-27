#!/usr/bin/env python3
"""Draw the library's icons: write them into the Modelica files, or preview them as SVG.

    python3 scripts/write_icons.py                  # write the icons
    python3 scripts/write_icons.py --preview DIR    # write DIR/icons.html, every icon as SVG, and change nothing

The pictures are defined here as Modelica graphics primitives (Rectangle, Ellipse, Polygon, Line, Text) and
written into the classes' `Icon` annotations:

- the package `Kommunekonomi.Icons`, with the icons that packages inherit: `Package`, `Municipality`,
  `DataPackage` and `ExamplesPackage`, as the standard library does with `Modelica.Icons`;
- a picture for each part of `Continuous.Economy` (people for the demography, a school for the services, coins for
  the operating accounts, a crane for the capital, banknotes for the payments, a bank for the finance) and for the
  packages `Units`, `Components`, `Continuous` and `Municipalities`;
- `extends Kommunekonomi.Icons.Municipality;` (and `DataPackage`, `ExamplesPackage`) in each municipality's package,
  its `Data` and its `Examples`, with their own icons removed. scripts/prepare_municipality.py writes the same lines.

Placements and connections are not touched, so the diagrams mocoal laid out stay as they are. Run it again after
changing a picture; it replaces what it wrote before.
"""
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / 'modelica/Kommunekonomi/package.mo'
MUNICIPALITIES = ROOT / 'modelica/Kommunekonomi/Municipalities'

# Colours, as in the library already: blue for people and the library, green for services and operations,
# brown for capital and finance, grey for data and scenario.
BLUE, BLUE_L, BLUE_M = (40, 95, 140), (235, 245, 252), (170, 200, 228)
GREEN, GREEN_L, GREEN_M = (35, 115, 85), (230, 245, 238), (150, 205, 180)
BROWN, BROWN_L, BROWN_M = (155, 95, 35), (255, 246, 230), (230, 190, 140)
GREY, GREY_L, GREY_M = (90, 110, 130), (245, 248, 250), (200, 210, 220)
DARK = (35, 50, 65)
GOLD, GOLD_L = (175, 130, 30), (245, 215, 120)
WHITE = (255, 255, 255)


def rect(x1, y1, x2, y2, line, fill=None, radius=0, thick=None):
    return ('Rectangle', dict(extent=((x1, y1), (x2, y2)), line=line, fill=fill, radius=radius, thick=thick))


def ellipse(x1, y1, x2, y2, line, fill=None, thick=None):
    return ('Ellipse', dict(extent=((x1, y1), (x2, y2)), line=line, fill=fill, thick=thick))


def poly(points, line, fill=None, thick=None):
    return ('Polygon', dict(points=points, line=line, fill=fill, thick=thick))


def line(points, color, thick=0.5, arrow=None):
    return ('Line', dict(points=points, color=color, thick=thick, arrow=arrow))


def text(x1, y1, x2, y2, s, color=DARK, size=0):
    return ('Text', dict(extent=((x1, y1), (x2, y2)), s=s, color=color, size=size))


# --- building blocks -------------------------------------------------------------------------------------------------

def person(cx, base, height, line_c, fill):
    """A person: head and a body with round shoulders; `height` from the feet to the top of the head."""
    head = height * 0.27
    body_top = base + height - head * 1.05
    w = height * 0.36
    return [rect(cx - w / 2, base, cx + w / 2, body_top, line_c, fill, radius=w * 0.45),
            ellipse(cx - head / 2, body_top + head * 0.08, cx + head / 2, body_top + head * 1.08, line_c, fill)]


def coin_stack(cx, base, n, w, h, line_c, fill):
    out = []
    for i in range(n):
        y = base + i * h * 0.55
        out.append(ellipse(cx - w / 2, y, cx + w / 2, y + h, line_c, fill))
    return out


def town_hall(cx, base, s, line_c, fill, accent):
    """A town hall: two wings, a central block and a tower with a clock. `s` scales; width about 1.6 s."""
    g = []
    # wings
    g.append(rect(cx - 0.8 * s, base, cx - 0.3 * s, base + 0.55 * s, line_c, fill))
    g.append(rect(cx + 0.3 * s, base, cx + 0.8 * s, base + 0.55 * s, line_c, fill))
    g.append(poly([(cx - 0.85 * s, base + 0.55 * s), (cx - 0.55 * s, base + 0.75 * s), (cx - 0.3 * s, base + 0.55 * s)], line_c, accent))
    g.append(poly([(cx + 0.3 * s, base + 0.55 * s), (cx + 0.55 * s, base + 0.75 * s), (cx + 0.85 * s, base + 0.55 * s)], line_c, accent))
    # tower
    g.append(rect(cx - 0.3 * s, base, cx + 0.3 * s, base + 1.05 * s, line_c, fill))
    g.append(poly([(cx - 0.36 * s, base + 1.05 * s), (cx, base + 1.45 * s), (cx + 0.36 * s, base + 1.05 * s)], line_c, accent))
    g.append(ellipse(cx - 0.15 * s, base + 0.7 * s, cx + 0.15 * s, base + 1.0 * s, line_c, WHITE))
    g.append(line([(cx, base + 0.85 * s), (cx, base + 0.95 * s)], line_c, 0.5))
    g.append(line([(cx, base + 0.85 * s), (cx + 0.08 * s, base + 0.85 * s)], line_c, 0.5))
    # door and windows
    g.append(rect(cx - 0.12 * s, base, cx + 0.12 * s, base + 0.32 * s, line_c, accent, radius=0))
    for x in (-0.68, -0.48, 0.42, 0.62):
        g.append(rect(cx + x * s, base + 0.2 * s, cx + (x + 0.12) * s, base + 0.38 * s, line_c, WHITE))
    return g


def package_frame(line_c=GREY, fill=GREY_L):
    return [rect(-100, -100, 100, 100, line_c, fill, radius=25)]


def component_frame(line_c, fill):
    """Frame and name for a component that is placed in a diagram."""
    return [rect(-100, -80, 100, 60, line_c, fill, radius=10), text(-100, 64, 100, 98, '%name', line_c)]


# --- icons -----------------------------------------------------------------------------------------------------------

def icon_package():
    return package_frame()


def icon_municipality():
    return package_frame(BLUE, BLUE_L) + town_hall(0, -68, 85, BLUE, WHITE, BLUE_M) + [line([(-80, -68), (80, -68)], BLUE, 1)]


def icon_municipalities():
    g = package_frame(BLUE, BLUE_L)
    g += town_hall(-45, -62, 42, BLUE, WHITE, BLUE_M) + town_hall(45, -62, 42, BLUE, WHITE, BLUE_M)
    g += town_hall(0, -30, 50, BLUE, WHITE, BLUE_M)
    return g + [line([(-85, -62), (85, -62)], BLUE, 1)]


def icon_data():
    g = package_frame()
    x1, x2, y1, y2, rows, cols = -70, 70, -65, 60, 5, 3
    g.append(rect(x1, y1, x2, y2, GREY, WHITE))
    h = (y2 - y1) / rows
    g.append(rect(x1, y2 - h, x2, y2, GREY, GREY_M))
    for r in range(1, rows):
        g.append(line([(x1, y2 - r * h), (x2, y2 - r * h)], GREY))
    for c in range(1, cols):
        x = x1 + c * (x2 - x1) / cols
        g.append(line([(x, y1), (x, y2)], GREY))
    return g


def icon_examples():
    return package_frame() + [ellipse(-65, -65, 65, 65, GREY, WHITE),
                              poly([(-25, -40), (45, 0), (-25, 40)], GREEN, GREEN_M)]


def icon_units():
    g = package_frame()
    g.append(rect(-80, -25, 80, 25, BROWN, BROWN_L))
    for i in range(9):
        x = -70 + i * 17.5
        g.append(line([(x, 25), (x, 25 - (22 if i % 2 == 0 else 12))], BROWN))
    g.append(text(-90, -85, 90, -40, 'mnkr · år', DARK))
    return g


def icon_components():
    g = package_frame()
    g += [rect(-75, 10, -15, 60, GREEN, GREEN_L, 6), rect(15, 10, 75, 60, BROWN, BROWN_L, 6),
          rect(-30, -65, 30, -15, BLUE, BLUE_L, 6),
          line([(-15, 35), (15, 35)], GREY, 1), line([(-45, 10), (-15, -40)], GREY, 1), line([(45, 10), (15, -40)], GREY, 1)]
    return g


def icon_continuous():
    """A stock with a flow in and a flow out: the package of stocks and flows."""
    g = package_frame()
    g += [rect(-30, -60, 30, 50, BROWN, WHITE), rect(-30, -60, 30, -5, BROWN, BROWN_M),
          line([(-90, 20), (-32, 20)], GREEN, 1.5, 'end'), line([(32, -30), (90, -30)], (170, 60, 50), 1.5, 'end')]
    return g


def icon_demography():
    g = component_frame(BLUE, BLUE_L)
    g += person(-50, -65, 100, BLUE, BLUE_M) + person(52, -65, 88, BLUE, BLUE_M) + person(2, -65, 58, BLUE, WHITE)
    return g


def icon_cohort():
    """A population pyramid: men left, women right."""
    g = component_frame(BLUE, BLUE_L)
    widths = [62, 66, 64, 60, 58, 52, 44, 32, 18]
    h = 13
    for i, w in enumerate(widths):
        y = -68 + i * h
        g.append(rect(-w, y, 0, y + h - 2, BLUE, BLUE_M))
        g.append(rect(0, y, w * 1.04 if i > 5 else w, y + h - 2, BLUE, WHITE))
    g.append(line([(0, -70), (0, 52)], BLUE, 0.5))
    return g


def icon_services():
    """A public building, such as a school, and a road."""
    g = component_frame(GREEN, GREEN_L)
    g.append(rect(-70, -50, 40, 10, GREEN, WHITE))
    g.append(poly([(-80, 10), (-15, 48), (50, 10)], GREEN, GREEN_M))
    g.append(rect(-22, -50, -4, -22, GREEN, GREEN_M))
    for x in (-60, -40, 6, 22):
        g.append(rect(x, -12, x + 12, 2, GREEN, GREEN_L))
    g.append(ellipse(-23, 18, -7, 34, GREEN, WHITE))
    # a road with a dashed centre line
    g.append(poly([(50, -72), (95, -72), (75, 20), (62, 20)], GREY, GREY_M))
    g += [line([(71.5, y), (70.5, y + 10)], WHITE, 1) for y in (-65, -42, -19, 4)]
    g.append(line([(-80, -50), (55, -50)], GREEN, 1))
    return g


def icon_operating():
    """Coins in stacks of different heights: costs and revenues that grow with wages and prices."""
    g = component_frame(GREEN, GREEN_L)
    g += coin_stack(-45, -68, 4, 46, 18, GOLD, GOLD_L)
    g += coin_stack(5, -68, 7, 46, 18, GOLD, GOLD_L)
    g += coin_stack(55, -68, 10, 46, 18, GOLD, GOLD_L)
    return g


def icon_capital():
    """A building under construction with a crane."""
    g = component_frame(BROWN, BROWN_L)
    g.append(rect(-15, -68, 75, -10, BROWN, WHITE))
    g.append(rect(-15, -10, 40, 18, BROWN, WHITE))
    for x in (-5, 20, 45):
        g.append(rect(x, -52, x + 14, -32, BROWN, BROWN_M))
    g.append(line([(40, 18), (75, 18), (75, -10)], BROWN, 0.5))
    # crane
    g.append(line([(-60, -68), (-60, 42)], DARK, 1.5))
    g.append(line([(-80, 42), (35, 42)], DARK, 1.5))
    g.append(line([(-60, 52), (-80, 42)], DARK, 0.5))
    g.append(line([(-60, 52), (35, 42)], DARK, 0.5))
    g.append(line([(20, 42), (20, 28)], DARK, 0.5))
    g.append(rect(13, 22, 27, 28, DARK, BROWN_M))
    g.append(rect(-82, 36, -70, 46, DARK, DARK))
    g.append(line([(-80, -68), (85, -68)], BROWN, 1))
    return g


def banknote(x1, y1, x2, y2, line_c, fill):
    cx, cy, r = (x1 + x2) / 2, (y1 + y2) / 2, (y2 - y1) * 0.28
    return [rect(x1, y1, x2, y2, line_c, fill, radius=3), ellipse(cx - r, cy - r, cx + r, cy + r, line_c, WHITE)]


def icon_payments():
    """Banknotes moving between accounts: the cash and what is owed either way."""
    g = component_frame(GREEN, GREEN_L)
    g += banknote(-80, 0, 10, 45, GREEN, GREEN_M)
    g += banknote(-10, -65, 80, -20, GREEN, GREEN_M)
    g.append(line([(25, 25), (55, 25), (55, -12)], DARK, 1, 'end'))
    g.append(line([(-25, -45), (-55, -45), (-55, -8)], DARK, 1, 'end'))
    return g


def icon_finance():
    """A bank: pediment, columns and steps."""
    g = component_frame(BROWN, BROWN_L)
    g.append(poly([(-75, 18), (0, 50), (75, 18)], BROWN, BROWN_M))
    g.append(rect(-70, 10, 70, 18, BROWN, WHITE))
    for x in (-58, -28, 2, 32):
        g.append(rect(x + 4, -52, x + 22, 10, BROWN, WHITE))
    g.append(rect(-72, -60, 72, -52, BROWN, WHITE))
    g.append(rect(-80, -68, 80, -60, BROWN, BROWN_M))
    g.append(ellipse(-8, 24, 8, 40, BROWN, GOLD_L))
    return g


def icon_economy():
    """The whole economy: the town hall with money in and out."""
    g = [rect(-100, -100, 100, 100, BLUE, WHITE, radius=10), text(-96, 62, 96, 94, '%name', BLUE)]
    g += town_hall(0, -60, 72, BLUE, WHITE, BLUE_M)
    g += [line([(-95, -60), (95, -60)], BLUE, 1)]
    g += coin_stack(-75, -88, 3, 28, 11, GOLD, GOLD_L) + coin_stack(75, -88, 3, 28, 11, GOLD, GOLD_L)
    g += [line([(-90, 10), (-62, 10)], GREEN, 1.5, 'end'), line([(62, 10), (90, 10)], (170, 60, 50), 1.5, 'end')]
    return g


def icon_scenario():
    """Wide: sliders and the label. Coordinate system {{-300, -25}, {300, 25}}."""
    g = [rect(-300, -25, 300, 25, GREY, GREY_L, radius=8)]
    for i, (y, k) in enumerate(((13, -250), (0, -215), (-13, -265))):
        g.append(line([(-285, y), (-195, y)], GREY, 1))
        g.append(ellipse(k - 5, y - 5, k + 5, y + 5, GREY, (BLUE_M, GREEN_M, BROWN_M)[i]))
    g.append(text(-185, -20, 290, 20, 'Scenario: årets antaganden', DARK, 16))
    return g


def icon_calendar():
    """Coordinate system {{-100, -60}, {100, 60}}: a calendar page and the start year."""
    g = [rect(-100, -60, 100, 60, GREY, GREY_L, radius=8)]
    g.append(rect(-88, -48, -22, 38, GREY, WHITE, radius=3))
    g.append(rect(-88, 20, -22, 38, (170, 60, 50), (220, 110, 100), radius=3))
    g += [line([(x, 30), (x, 46)], DARK, 1) for x in (-72, -38)]
    for r in range(3):
        for c in range(4):
            x, y = -82 + c * 15, 4 - r * 16
            g.append(rect(x, y, x + 10, y + 9, GREY, GREY_M if (r, c) != (2, 3) else (220, 110, 100)))
    g.append(text(-15, 8, 95, 48, 'Kalender', DARK))
    g.append(text(-15, -45, 95, -5, 'Start: bokslut %baseYear', GREY))
    return g


def icon_revenue():
    """Coordinate system {{-100, -75}, {100, 75}}: tax and grants, a percent sign and coins."""
    g = [rect(-100, -75, 100, 75, GREEN, GREEN_L, radius=10), text(-95, 45, 95, 70, '%name', GREEN)]
    g.append(ellipse(-80, -45, -10, 25, GREEN, WHITE))
    g.append(line([(-60, -30), (-30, 10)], GREEN, 1.5))
    g.append(ellipse(-66, -2, -54, 10, GREEN, GREEN_M))
    g.append(ellipse(-36, -28, -24, -16, GREEN, GREEN_M))
    g += coin_stack(25, -60, 5, 40, 15, GOLD, GOLD_L) + coin_stack(65, -60, 3, 40, 15, GOLD, GOLD_L)
    g.append(text(-95, -72, 95, -50, 'Skatt / bidrag', DARK))
    return g


# Class -> (icon function, coordinate system)
UNIT = ((-100, -100), (100, 100))
ICONS = {
    'Icons.Package': (icon_package, UNIT),
    'Icons.Municipality': (icon_municipality, UNIT),
    'Municipalities': (icon_municipalities, UNIT),
    'Icons.DataPackage': (icon_data, UNIT),
    'Icons.ExamplesPackage': (icon_examples, UNIT),
    'Units': (icon_units, UNIT),
    'Components': (icon_components, UNIT),
    'Continuous': (icon_continuous, UNIT),
    'Continuous.Demography': (icon_demography, UNIT),
    'Continuous.CohortDemography': (icon_cohort, UNIT),
    'Continuous.Services': (icon_services, UNIT),
    'Continuous.OperatingAccounts': (icon_operating, UNIT),
    'Continuous.Capital': (icon_capital, UNIT),
    'Continuous.Payments': (icon_payments, UNIT),
    'Continuous.Finance': (icon_finance, UNIT),
    'Continuous.Economy': (icon_economy, UNIT),
    'Components.Scenario': (icon_scenario, ((-300, -25), (300, 25))),
    'Components.Calendar': (icon_calendar, ((-100, -60), (100, 60))),
    'Components.Revenue': (icon_revenue, ((-100, -75), (100, 75))),
}


# --- emitters --------------------------------------------------------------------------------------------------------

def n(v):
    v = round(v, 1)
    return str(int(v)) if v == int(v) else str(v)


def pt(p):
    return '{' + n(p[0]) + ', ' + n(p[1]) + '}'


def col(c):
    return '{' + ', '.join(str(x) for x in c) + '}'


def to_modelica(prims):
    out = []
    for kind, a in prims:
        if kind in ('Rectangle', 'Ellipse', 'Polygon'):
            parts = []
            if kind == 'Polygon':
                pts = list(a['points']) + [a['points'][0]]
                parts.append('points = {' + ', '.join(pt(p) for p in pts) + '}')
            else:
                parts.append('extent = {' + pt(a['extent'][0]) + ', ' + pt(a['extent'][1]) + '}')
            parts.append('lineColor = ' + col(a['line']))
            if a['fill'] is not None:
                parts += ['fillColor = ' + col(a['fill']), 'fillPattern = FillPattern.Solid']
            if a.get('thick'):
                parts.append('lineThickness = ' + n(a['thick']))
            if kind == 'Rectangle' and a['radius']:
                parts.append('radius = ' + n(a['radius']))
            out.append(f'{kind}(' + ', '.join(parts) + ')')
        elif kind == 'Line':
            parts = ['points = {' + ', '.join(pt(p) for p in a['points']) + '}', 'color = ' + col(a['color'])]
            if a['thick'] and a['thick'] != 0.25:
                parts.append('thickness = ' + n(a['thick']))
            if a['arrow'] == 'end':
                parts += ['arrow = {Arrow.None, Arrow.Filled}', 'arrowSize = 8']
            out.append('Line(' + ', '.join(parts) + ')')
        elif kind == 'Text':
            parts = ['extent = {' + pt(a['extent'][0]) + ', ' + pt(a['extent'][1]) + '}', f'textString = "{a["s"]}"',
                     'textColor = ' + col(a['color'])]
            if a['size']:
                parts.append('fontSize = ' + n(a['size']))
            out.append('Text(' + ', '.join(parts) + ')')
    return '{' + ', '.join(out) + '}'


def icon_annotation(name):
    f, ((x1, y1), (x2, y2)) = ICONS[name]
    return f'Icon(coordinateSystem(extent = {{{{{n(x1)}, {n(y1)}}}, {{{n(x2)}, {n(y2)}}}}}), graphics = {to_modelica(f())})'


def to_svg(prims, cs, px=160, label=None):
    (x1, y1), (x2, y2) = cs
    w, h = x2 - x1, y2 - y1
    scale = px / max(w, h)
    W, H = w * scale, h * scale
    X = lambda x: (x - x1) * scale
    Y = lambda y: (y2 - y) * scale
    rgb = lambda c: f'rgb{tuple(c)}'
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H + (18 if label else 0):.0f}">']
    for kind, a in prims:
        sw = max(1, (a.get('thick') or 0.25) * 4 * scale)
        if kind == 'Rectangle':
            (ax, ay), (bx, by) = a['extent']
            r = a['radius'] * scale
            s.append(f'<rect x="{X(min(ax, bx)):.1f}" y="{Y(max(ay, by)):.1f}" width="{abs(bx - ax) * scale:.1f}" height="{abs(by - ay) * scale:.1f}" rx="{r:.1f}" '
                     f'fill="{rgb(a["fill"]) if a["fill"] else "none"}" stroke="{rgb(a["line"])}" stroke-width="{sw:.1f}"/>')
        elif kind == 'Ellipse':
            (ax, ay), (bx, by) = a['extent']
            s.append(f'<ellipse cx="{X((ax + bx) / 2):.1f}" cy="{Y((ay + by) / 2):.1f}" rx="{abs(bx - ax) / 2 * scale:.1f}" ry="{abs(by - ay) / 2 * scale:.1f}" '
                     f'fill="{rgb(a["fill"]) if a["fill"] else "none"}" stroke="{rgb(a["line"])}" stroke-width="{sw:.1f}"/>')
        elif kind == 'Polygon':
            pts = ' '.join(f'{X(x):.1f},{Y(y):.1f}' for x, y in a['points'])
            s.append(f'<polygon points="{pts}" fill="{rgb(a["fill"]) if a["fill"] else "none"}" stroke="{rgb(a["line"])}" stroke-width="{sw:.1f}"/>')
        elif kind == 'Line':
            pts = ' '.join(f'{X(x):.1f},{Y(y):.1f}' for x, y in a['points'])
            sw = max(1, a['thick'] * 4 * scale)
            s.append(f'<polyline points="{pts}" fill="none" stroke="{rgb(a["color"])}" stroke-width="{sw:.1f}"/>')
            if a['arrow'] == 'end':
                (px1, py1), (px2, py2) = a['points'][-2], a['points'][-1]
                ang = math.atan2(Y(py2) - Y(py1), X(px2) - X(px1)); L = 8 * scale * 1.6
                tip = (X(px2), Y(py2))
                p1 = (tip[0] - L * math.cos(ang - 0.4), tip[1] - L * math.sin(ang - 0.4))
                p2 = (tip[0] - L * math.cos(ang + 0.4), tip[1] - L * math.sin(ang + 0.4))
                s.append(f'<polygon points="{tip[0]:.1f},{tip[1]:.1f} {p1[0]:.1f},{p1[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}" fill="{rgb(a["color"])}"/>')
        elif kind == 'Text':
            (ax, ay), (bx, by) = a['extent']
            hh = abs(by - ay) * scale
            fs = a['size'] * scale * 2.2 if a['size'] else min(hh * 0.8, abs(bx - ax) * scale / max(1, len(a['s'])) * 1.8)
            st = a['s'].replace('%name', 'name').replace('%baseYear', '2025')
            s.append(f'<text x="{X((ax + bx) / 2):.1f}" y="{Y((ay + by) / 2) + fs * 0.35:.1f}" font-size="{fs:.1f}" text-anchor="middle" fill="{rgb(a["color"])}" font-family="sans-serif">{st}</text>')
    if label:
        s.append(f'<text x="{W / 2:.0f}" y="{H + 14:.0f}" font-size="11" text-anchor="middle" font-family="sans-serif">{label}</text>')
    s.append('</svg>')
    return '\n'.join(s)



# --- writing into the Modelica files ---------------------------------------------------------------------------------

HEADER = re.compile(r'^(\s*)(?:(?:partial|encapsulated|replaceable|final)\s+)*(?:model|block|connector|package|record|function|class)\s+(\w+)\b(?!\s*=)')


def classes(lines):
    """Path -> (header line, end line, indentation) for every long class definition in the file."""
    found, stack = {}, []
    for i, l in enumerate(lines):
        m = HEADER.match(l)
        if m and not l.lstrip().startswith('end '):
            stack.append((m.group(2), i, m.group(1)))
            continue
        e = re.match(r'^\s*end (\w+);', l)
        if e and stack and stack[-1][0] == e.group(1):
            name, start, indent = stack.pop()
            found['.'.join([s[0] for s in stack] + [name])] = (start, i, indent)
    return found


def balanced(text, start):
    """Index after the parenthesis that closes the one opened at text[start]; strings are skipped."""
    depth, i, quoted = 0, start, False
    while i < len(text):
        c = text[i]
        if quoted:
            if c == '\\':
                i += 1
            elif c == '"':
                quoted = False
        elif c == '"':
            quoted = True
        elif c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise ValueError('unbalanced')


def own_annotation(lines, cls):
    """Line index of the class's own annotation: the last line at the class's indentation + 2 that starts with
    `annotation(` before its end, or None."""
    start, end, indent = cls
    for i in range(end - 1, start, -1):
        if lines[i].startswith(indent + '  annotation('):
            return i
    return None


def set_icon(text, path, icon):
    """Give the class at `path` this Icon annotation: replace its own, or add one."""
    lines = text.split('\n')
    cls = classes(lines)[path]
    i = own_annotation(lines, cls)
    if i is None:
        lines.insert(cls[1], cls[2] + f'  annotation({icon});')
        return '\n'.join(lines)
    offset = sum(len(l) + 1 for l in lines[:i])
    a = offset + lines[i].index('annotation(')
    close = balanced(text, a + len('annotation'))
    k = text.find('Icon(', a, close)
    if k < 0:
        return text[:a + len('annotation(')] + icon + ', ' + text[a + len('annotation('):]
    return text[:k] + icon + text[balanced(text, k + 4):]


def drop_icon(text, path):
    """Remove the class's own Icon annotation (it inherits one instead)."""
    lines = text.split('\n')
    cls = classes(lines)[path]
    i = own_annotation(lines, cls)
    if i is None:
        return text
    offset = sum(len(l) + 1 for l in lines[:i])
    a = offset + lines[i].index('annotation(')
    close = balanced(text, a + len('annotation'))
    k = text.find('Icon(', a, close)
    if k < 0:
        return text
    e = balanced(text, k + 4)
    rest = text[e:close - 1]
    if text[a + len('annotation('):k].strip() == '' and rest.strip() == '':
        # The annotation was only the icon: remove the whole line.
        line_end = text.index('\n', close)
        return text[:offset] + text[line_end + 1:]
    m = re.match(r',\s*', rest)
    if m:
        return text[:k] + text[e + m.end():]
    return text[:text.rindex(',', a, k)] + text[e:]


def inherit(text, path, icon_class):
    """`extends icon_class;` as the first element of the class at `path`, and no icon of its own."""
    text = drop_icon(text, path)
    lines = text.split('\n')
    start, end, indent = classes(lines)[path]
    statement = f'{indent}  extends {icon_class};'
    if statement not in lines[start + 1:end]:
        lines.insert(start + 1, statement)
    return '\n'.join(lines)


def icons_package():
    doc = {'Package': 'Paket', 'Municipality': 'En kommun', 'DataPackage': 'Data: basår och befolkning',
           'ExamplesPackage': 'Exempel att simulera'}
    out = ['  package Icons "Ikoner som paketen i biblioteket och kommunerna ärver; ritas av scripts/write_icons.py"',
           '    extends Icons.Package;']
    for name in ('Package', 'Municipality', 'DataPackage', 'ExamplesPackage'):
        out += [f'    partial package {name} "{doc[name]}"', f'      annotation({icon_annotation("Icons." + name)});', f'    end {name};']
    out += ['    annotation(Documentation(info = "<html><p>Ikoner att ärva med <code>extends</code>, som '
            '<code>Modelica.Icons</code> i standardbiblioteket. Bilderna ritas av <code>scripts/write_icons.py</code>; '
            'ändra dem där.</p></html>"));', '  end Icons;']
    return '\n'.join(out)


def write_library():
    text = LIBRARY.read_text()
    lines = text.split('\n')
    found = classes(lines)
    block = icons_package()
    if 'Kommunekonomi.Icons' in found:
        start, end, _ = found['Kommunekonomi.Icons']
        lines[start:end + 1] = block.split('\n')
    else:
        top = [i for i, l in enumerate(lines) if l.startswith('  annotation(version')][0]
        lines[top:top] = block.split('\n')
    text = '\n'.join(lines)
    for name in ICONS:
        if not name.startswith('Icons.') and name != 'Municipalities':
            text = set_icon(text, 'Kommunekonomi.' + name, icon_annotation(name))
    text = inherit(text, 'Kommunekonomi.Data', 'Icons.DataPackage')
    LIBRARY.write_text(text)
    order = LIBRARY.parent / 'package.order'
    names = order.read_text().split()
    if 'Icons' not in names:
        order.write_text('\n'.join(names + ['Icons']) + '\n')


def write_municipalities():
    package = MUNICIPALITIES / 'package.mo'
    package.write_text(set_icon(package.read_text(), 'Municipalities', icon_annotation('Municipalities')))
    for f in sorted(MUNICIPALITIES.glob('*.mo')):
        if f.name == 'package.mo':
            continue
        name, text = f.stem, f.read_text()
        text = inherit(text, name, 'Kommunekonomi.Icons.Municipality')
        text = inherit(text, f'{name}.Data', 'Kommunekonomi.Icons.DataPackage')
        text = inherit(text, f'{name}.Examples', 'Kommunekonomi.Icons.ExamplesPackage')
        f.write_text(text)


def preview(directory):
    directory.mkdir(parents=True, exist_ok=True)
    cells = ''.join(f'<div class="c">{to_svg(f(), cs, 170, name)}</div>' for name, (f, cs) in ICONS.items())
    (directory / 'icons.html').write_text('<!doctype html><html><head><meta charset="utf-8"><title>Kommunekonomi icons</title></head>'
                                          '<body style="margin:12px;background:#fafafa"><style>.c{display:inline-block;margin:8px;'
                                          'vertical-align:top}</style>' + cells + '</body></html>\n')
    print(directory / 'icons.html')


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--preview':
        preview(Path(sys.argv[2]))
    elif len(sys.argv) == 1:
        write_library()
        write_municipalities()
    else:
        raise SystemExit(__doc__)
