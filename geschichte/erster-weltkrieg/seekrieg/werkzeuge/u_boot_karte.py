#!/usr/bin/env python3
"""Karte „U-Boot-Krieg 1914–1918“ für geschichte/erster-weltkrieg/seekrieg/u-boot-krieg/index.html.

Setzt das SVG zwischen <!-- karte:anfang --> und <!-- karte:ende --> ein.
Grundlagen: Natural Earth ne_50m_land (gemeinfrei, GeoJSON aus nvkelso/natural-earth-vector),
aourednik/historical-basemaps world_1914.geojson (GPL-3.0) für die Grenzen von 1914.
Aufruf:  pip install shapely && python3 u_boot_karte.py <geo-ordner>/   (mit land.json und w1914.json)

Sperrgebiet 1917: Nordzone nach den Koordinaten der deutschen Denkschrift vom 31.1.1917 (FRUS 1917, Suppl. 1, Dok. 92),
vereinfacht (ohne den 20-Seemeilen-Streifen vor der niederländischen Küste). Mittelmeer: Sperrgebiet östlich der Linie
Pointe de l'Espiguette – 38°20' N 6° O, ohne die offenen Fahrwege nach Griechenland und entlang Nordafrika.
Kriegsgebiet 1915: „Gewässer rings um Großbritannien und Irland einschließlich des gesamten Kanals“, schematisch als Saum.
"""
import json, math, sys, re, pathlib, warnings
warnings.filterwarnings("ignore")
from shapely.geometry import shape, box, Polygon, Point
from shapely.ops import unary_union, transform
from shapely.validation import make_valid

G = sys.argv[1] if len(sys.argv) > 1 else "./"
SEITE = pathlib.Path(__file__).resolve().parent.parent / "u-boot-krieg" / "index.html"

LON0, LAT0, LON1, LAT1 = -24, 31, 32, 64
p1, p2, l0, f0 = math.radians(40), math.radians(58), math.radians(4), math.radians(48)
n = math.log(math.cos(p1) / math.cos(p2)) / math.log(math.tan(math.pi/4 + p2/2) / math.tan(math.pi/4 + p1/2))
F = math.cos(p1) * math.tan(math.pi/4 + p1/2) ** n / n
r0 = F / math.tan(math.pi/4 + f0/2) ** n
def P(lon, lat):
    r = F / math.tan(math.pi/4 + math.radians(lat)/2) ** n; t = n * (math.radians(lon) - l0)
    return r * math.sin(t), r0 - r * math.cos(t)
def proj(x, y, z=None):
    o = [P(a, b) for a, b in zip(x, y)]; return [a for a, _ in o], [b for _, b in o]

# Ausschnitt in Projektionskoordinaten
minx = P(-23.5, 46)[0]; maxx = P(29.5, 40)[0]; miny = P(4, 33.2)[1]; maxy = P(4, 63.3)[1]
W = 1000; s = W / (maxx - minx); H = round((maxy - miny) * s)
def xy(lon, lat):
    x, y = P(lon, lat); return round((x - minx) * s, 1), round((maxy - y) * s, 1)
RECT = box(minx, miny, maxx, maxy)

def pfad(g):
    if g.is_empty: return ""
    polys = [g] if g.geom_type == "Polygon" else [q for q in getattr(g, "geoms", []) if q.geom_type == "Polygon"]
    out = []
    for q in polys:
        for ring in [q.exterior] + list(q.interiors):
            pts = [(round((x - minx) * s, 1), round((maxy - y) * s, 1)) for x, y in ring.coords]
            if len(pts) < 4: continue
            out.append("M" + "L".join(f"{a},{b}" for a, b in pts[:-1]) + "Z")
    return "".join(out)

B = box(LON0, LAT0, LON1, LAT1)
land = unary_union([make_valid(shape(f["geometry"])).intersection(B) for f in json.load(open(G + "land.json"))["features"]
                    if shape(f["geometry"]).intersects(B)])
landp = transform(proj, land).intersection(RECT).simplify(0.0014)
h = json.load(open(G + "w1914.json"))
def staat(*names):
    gs = [make_valid(shape(f["geometry"])).intersection(B) for f in h["features"] if f["properties"].get("NAME") in names]
    return transform(proj, unary_union(gs)).intersection(landp.buffer(0.0004)).intersection(RECT).simplify(0.0014)
mittel = staat("German Empire", "Austro-Hungarian Empire")
gb = staat("United Kingdom of Great Britain and Ireland")
grenzen = unary_union([transform(proj, make_valid(shape(f["geometry"])).intersection(B)).boundary for f in h["features"]
                       if shape(f["geometry"]).intersects(B)]).intersection(landp.buffer(-0.0003)).simplify(0.0014)
def linie(g):
    ls = [g] if g.geom_type == "LineString" else [q for q in getattr(g, "geoms", []) if q.geom_type == "LineString"]
    out = []
    for q in ls:
        pts = [(round((x - minx) * s, 1), round((maxy - y) * s, 1)) for x, y in q.coords]
        if len(pts) > 1: out.append("M" + "L".join(f"{a},{b}" for a, b in pts))
    return "".join(out)

meer = lambda poly: transform(proj, poly.intersection(B)).difference(landp.buffer(0.0008)).intersection(RECT)
# Kriegsgebiet 1915 (schematisch): Saum von rund 150 km um Großbritannien und Irland, mit dem ganzen Kanal
gbll = unary_union([make_valid(shape(f["geometry"])) for f in h["features"] if f["properties"].get("NAME") == "United Kingdom of Great Britain and Ireland"])
zone15 = meer(unary_union([gbll.buffer(2.0), box(-6, 48.4, 2.6, 51.2)]).intersection(box(-16, 47.6, 6, 62)))
# Sperrgebiet Nord 1917 nach der Denkschrift vom 31.1.1917 (Landteile werden abgezogen)
nord = Polygon([(4.7, 53.2), (5.0, 53.45), (5.0, 59.3), (5.0, 62), (-5, 62), (-6.7, 61.35), (-10, 62), (-15, 61), (-20, 57),
                (-20, 47), (-15, 43), (-9.6, 43), (-8.3, 43.65), (-1.8, 43.45), (2, 45), (6, 48), (6, 51.5), (4.7, 53.2)])
zone17n = meer(nord)
# Sperrgebiet Mittelmeer 1917, vereinfacht: östlich der Linie Pointe de l'Espiguette – 38°20' N 6° O
mm = Polygon([(4.13, 43.3), (6, 38.33), (6, 36.0), (11, 33), (32, 30.5), (32, 47), (4.13, 47)])
zone17m = meer(mm.difference(box(26.2, 40.25, 33, 48)))  # ohne Marmarameer und Schwarzes Meer

ORTE = [  # (Name, lon, lat, Ausrichtung)
    ("Wilhelmshaven", 8.12, 53.52, "start"), ("Helgoland", 7.89, 54.18, "end"), ("Brügge", 3.22, 51.21, "start"),
    ("Pola", 13.85, 44.87, "end"), ("Cattaro", 18.77, 42.42, "start"), ("Liverpool", -2.99, 53.4, "start"),
]
STUETZ = {"Wilhelmshaven", "Helgoland", "Brügge", "Pola", "Cattaro"}
EREIGNISSE = [  # (Nummer wie im Verlauf, lon, lat, Schritt, Klasse)
    (1, 3.75, 52.4, "1", "versenkung"),      # 22.9.1914 U 9, vor der niederländischen Küste
    (2, -8.55, 51.42, "2", "versenkung"),    # 7.5.1915 Lusitania, vor Old Head of Kinsale
    (3, 1.0, 50.45, "3", "versenkung"),      # 24.3.1916 Sussex im Kanal
    (4, -4.0, 57.5, "4", "beginn"),          # 1.2.1917 Sperrgebiete (Marke im Nordgebiet)
    (5, 2.9, 51.45, "5", "beginn"),          # 23.4.1918 Angriff auf Zeebrugge und Ostende
]
GELEIT = [  # Geleitzüge, schematisch: (Schritt, Punkte)
    ("5", [(-21, 47.5), (-12, 49.5), (-6.5, 50.6)]),
    ("5", [(-21, 55.5), (-12, 55.6), (-6.5, 54.6), (-4.2, 53.7)]),
]
def kurve(pts):
    return "M" + "L".join("%s,%s" % xy(a, b) for a, b in pts)

t = []
t.append(f'<svg class="kk-karte ub-karte" viewBox="0 0 {W} {H}" role="img" aria-labelledby="karte-titel karte-beschr">'
         '<title id="karte-titel">U-Boot-Krieg 1914–1918: Kriegsgebiet 1915 und Sperrgebiete 1917</title>'
         '<desc id="karte-beschr">Karte von Nordatlantik, Nordsee und Mittelmeer mit dem deutschen Kriegsgebiet um Großbritannien und Irland '
         'von 1915, den Sperrgebieten vom 1. Februar 1917, den Stützpunkten der U-Boote und den Orten wichtiger Versenkungen.</desc>')
t.append(f'<rect class="ub-meer" x="0" y="0" width="{W}" height="{H}"/>')
t.append('<g class="uz">'
         f'<path class="uz-15" data-s="2 3" d="{pfad(zone15)}"/>'
         f'<path class="uz-17" data-s="4 5" d="{pfad(zone17n)}"/>'
         f'<path class="uz-17" data-s="4 5" d="{pfad(zone17m)}"/></g>')
t.append(f'<path class="ub-land" d="{pfad(landp)}"/>')
t.append(f'<path class="ub-mittel" d="{pfad(mittel)}"/><path class="ub-gb" d="{pfad(gb)}"/>')
t.append(f'<path class="ub-grenzen" d="{linie(grenzen)}"/>')
t.append('<defs><marker id="ub-spitze" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="4" markerHeight="4" orient="auto">'
         '<path class="sp-pr" d="M0,0L10,5L0,10z"/></marker></defs>')
t.append('<g class="kk-pfeile">' + "".join(
    f'<g data-s="{st}"><path class="pf-pr" d="{kurve(p)}" pathLength="1" marker-end="url(#ub-spitze)"/></g>' for st, p in GELEIT)
    + '<g data-s="5"><text class="tx-pr" x="%s" y="%s">Geleitzüge</text></g></g>' % xy(-16.5, 52.3))
lab = [("Nordsee", 3.2, 56.2, "meer"), ("Atlantik", -14.5, 41.5, "meer"), ("Mittelmeer", 17.5, 34.6, "meer"),
       ("Ärmelkanal", -3.2, 49.55, "meer klein"), ("Adria", 15.6, 42.9, "meer klein")]
t.append('<g class="kk-landschaft">' + "".join(
    '<text class="%s" x="%s" y="%s">%s</text>' % (k, *xy(a, b), name) for name, a, b, k in lab) + '</g>')
namen = [("Großbritannien", -2.0, 54.8, "gross"), ("Irland", -8.0, 53.1, ""), ("Frankreich", 2.4, 46.8, "gross"),
         ("Deutsches Reich", 10.3, 51.2, "gross"), ("Österreich-Ungarn", 18.5, 47.6, ""), ("Italien", 13.0, 41.9, ""),
         ("Spanien", -3.8, 40.0, ""), ("Norwegen", 9.0, 61.5, "")]
t.append('<g class="ek-namen">' + "".join(
    '<text class="%s" x="%s" y="%s">%s</text>' % (k, *xy(a, b), nm) for nm, a, b, k in namen) + '</g>')
o = []
for nm, a, b, al in ORTE:
    x, y = xy(a, b); dx = 7 if al == "start" else -7
    kl = "stuetz" if nm in STUETZ else ""
    form = (f'<rect class="{kl}" x="{x-4}" y="{y-4}" width="8" height="8"/>' if kl else f'<circle cx="{x}" cy="{y}" r="3.2"/>')
    o.append(f'{form}<text class="klein" x="{x+dx}" y="{y+4}" text-anchor="{al}">{nm}</text>')
t.append('<g class="ek-orte">' + "".join(o) + '</g>')
e = []
for nr, a, b, st, kl in EREIGNISSE:
    x, y = xy(a, b)
    e.append(f'<a href="#e{nr}" data-s="{st}"><g class="kk-marke {kl}" transform="translate({x},{y})"><g class="kk-inhalt">'
             f'<circle r="12"/><text y="4.5">{nr}</text></g></g></a>')
t.append('<g class="kk-ereignisse">' + "".join(e) + '</g>')
# Maßstab 500 km am 50. Breitengrad
xa, ya = xy(-17, 35.5); km = 500
xb = xa + (P(-20 + km / (111.32 * math.cos(math.radians(50))), 50)[0] - P(-20, 50)[0]) * s
t.append(f'<g class="kk-massstab"><path d="M{xa},{ya}h{round(xb-xa,1)}M{xa},{ya-5}v5M{round(xb,1)},{ya-5}v5"/>'
         f'<text x="{xa}" y="{ya-9}">500 km</text></g>')
t.append('</svg>')
svg = "".join(t)

html = SEITE.read_text(encoding="utf-8")
neu, k = re.subn(r"<!-- karte:anfang -->.*?<!-- karte:ende -->", lambda m: "<!-- karte:anfang -->\n" + svg + "\n<!-- karte:ende -->", html, flags=re.S)
if k != 1: raise SystemExit("Marken <!-- karte:anfang/ende --> fehlen")
SEITE.write_text(neu, encoding="utf-8")
print("Karte eingesetzt:", W, "x", H, len(svg) // 1024, "KB")
