#!/usr/bin/env python3
"""Karte für geschichte/erster-weltkrieg/kaiserreich/ludendorff-hindenburg/index.html.

Karte „Hindenburg und Ludendorff 1914–1919“ zwischen <!-- karte-wege:anfang/ende -->.
Orte und Daten nach den Quellen der Seite (Deutsches Historisches Museum/LeMO, Bundesarchiv, 1914-1918-online).
Grundlagen: Natural Earth ne_50m_land (gemeinfrei, GeoJSON aus nvkelso/natural-earth-vector),
aourednik/historical-basemaps world_1914.geojson (GPL-3.0) für die Grenzen von 1914 (laut Projekt teils Näherungen).
Aufruf:  pip install shapely && python3 lh_karte.py <geo-ordner>/   (mit land.json, lakes.json und w1914.json)

Die Pfeile zeigen Richtungen und Umzüge, keine genauen Wege oder Frontverläufe. Die Lage der drei Verwaltungsgebiete
von Ober Ost ist nur ungefähr beschriftet. Aufbau und Kartenklasse wie kaiser_karte.py.
"""
import json, math, sys, re, pathlib, warnings
warnings.filterwarnings("ignore")
from shapely.geometry import shape, box
from shapely.ops import unary_union, transform
from shapely.validation import make_valid

G = sys.argv[1] if len(sys.argv) > 1 else "./"
SEITE = pathlib.Path(__file__).resolve().parent.parent / "ludendorff-hindenburg" / "index.html"
LAND = [make_valid(shape(f["geometry"])) for f in json.load(open(G + "land.json"))["features"]]
SEEN = {f["properties"].get("name"): make_valid(shape(f["geometry"])) for f in json.load(open(G + "lakes.json"))["features"]}
H14 = json.load(open(G + "w1914.json"))["features"]


class Karte:
    """Projektion, Bildmaße und SVG-Hilfen für eine Karte."""
    def __init__(self, P, ecken, W=1000):
        self.P = P
        xs, ys = zip(*[P(a, b) for a, b in ecken])
        self.minx, self.maxx, self.miny, self.maxy = min(xs), max(xs), min(ys), max(ys)
        self.W = W; self.s = W / (self.maxx - self.minx); self.H = round((self.maxy - self.miny) * self.s)
        self.RECT = box(self.minx, self.miny, self.maxx, self.maxy)
    def proj(self, x, y, z=None):
        o = [self.P(a, b) for a, b in zip(x, y)]; return [a for a, _ in o], [b for _, b in o]
    def xy(self, lon, lat):
        x, y = self.P(lon, lat); return round((x - self.minx) * self.s, 1), round((self.maxy - y) * self.s, 1)
    def _pt(self, x, y):
        return round((x - self.minx) * self.s, 1), round((self.maxy - y) * self.s, 1)
    def pfad(self, g):
        if g.is_empty: return ""
        polys = [g] if g.geom_type == "Polygon" else [q for q in getattr(g, "geoms", []) if q.geom_type == "Polygon"]
        out = []
        for q in polys:
            for ring in [q.exterior] + list(q.interiors):
                pts = [self._pt(x, y) for x, y in ring.coords]
                if len(pts) < 4: continue
                out.append("M" + "L".join(f"{a},{b}" for a, b in pts[:-1]) + "Z")
        return "".join(out)
    def linie(self, g):
        ls = [g] if g.geom_type == "LineString" else [q for q in getattr(g, "geoms", []) if q.geom_type == "LineString"]
        out = []
        for q in ls:
            pts = [self._pt(x, y) for x, y in q.coords]
            if len(pts) > 1: out.append("M" + "L".join(f"{a},{b}" for a, b in pts))
        return "".join(out)
    def kurve(self, pts):
        """Glatte Linie durch die Punkte (Catmull-Rom als kubische Bézierkurven)."""
        p = [self.xy(a, b) for a, b in pts]
        if len(p) == 2: return "M%s,%sL%s,%s" % (*p[0], *p[1])
        d = "M%s,%s" % p[0]
        for i in range(len(p) - 1):
            p0 = p[i - 1] if i else p[i]; p1, p2 = p[i], p[i + 1]; p3 = p[i + 2] if i + 2 < len(p) else p2
            c1 = (round(p1[0] + (p2[0] - p0[0]) / 6, 1), round(p1[1] + (p2[1] - p0[1]) / 6, 1))
            c2 = (round(p2[0] - (p3[0] - p1[0]) / 6, 1), round(p2[1] - (p3[1] - p1[1]) / 6, 1))
            d += "C%s,%s %s,%s %s,%s" % (*c1, *c2, *p2)
        return d


def plattkarte(breite):
    """Plattkarte, längentreu am Breitenkreis `breite`."""
    c = math.cos(math.radians(breite))
    return lambda lon, lat: (lon * c, lat)


def flaechen(K, ausschnitt, seen):
    land = unary_union([g.intersection(ausschnitt) for g in LAND if g.intersects(ausschnitt)])
    wasser = unary_union([SEEN[s] for s in seen])
    land = transform(K.proj, land).intersection(K.RECT)
    return land.simplify(0.02), transform(K.proj, wasser).intersection(K.RECT).simplify(0.02), land


def kolonie(K, name, land, puffer=0.15, ohne=()):
    """Fläche einer Kolonie von 1914, leicht erweitert und auf die Küste von Natural Earth beschnitten."""
    g = unary_union([make_valid(shape(f["geometry"])) for f in H14 if f["properties"].get("NAME") == name]).buffer(puffer)
    for nb in ohne:
        g = g.difference(unary_union([make_valid(shape(f["geometry"])) for f in H14 if f["properties"].get("NAME") == nb]))
    return transform(K.proj, g).intersection(land).intersection(K.RECT).simplify(0.02)


def grenzen(K, ausschnitt, land):
    return unary_union([transform(K.proj, make_valid(shape(f["geometry"])).intersection(ausschnitt)).boundary for f in H14
                        if shape(f["geometry"]).intersects(ausschnitt)]).intersection(land.buffer(-0.02)).simplify(0.02)


def svg_karte(K, kennung, titel, beschr, land, seen, kolonien, besetzt, grenzlinien, pfeile, beschriftung, orte, ereignisse, massstab):
    t = [f'<svg class="kk-karte ka-karte" viewBox="0 0 {K.W} {K.H}" role="img" aria-labelledby="{kennung}-titel {kennung}-beschr">'
         f'<title id="{kennung}-titel">{titel}</title><desc id="{kennung}-beschr">{beschr}</desc>',
         f'<rect class="ka-meer" x="0" y="0" width="{K.W}" height="{K.H}"/>',
         f'<path class="ka-land" d="{K.pfad(land)}"/>']
    for kl, g in kolonien: t.append(f'<path class="{kl}" d="{K.pfad(g)}"/>')
    t.append('<g class="ka-besetzt">' + "".join(f'<path data-s="{st}" d="{K.pfad(g)}"/>' for st, g in besetzt) + '</g>')
    t.append(f'<path class="ka-grenzen" d="{K.linie(grenzlinien)}"/>')
    t.append(f'<path class="ka-see" d="{K.pfad(seen)}"/>')
    t.append(f'<defs><marker id="{kennung}-sp-ge" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="4" markerHeight="4" orient="auto">'
             f'<path class="sp-ge" d="M0,0L10,5L0,10z"/></marker><marker id="{kennung}-sp-pr" viewBox="0 0 10 10" refX="7" refY="5" '
             f'markerWidth="4" markerHeight="4" orient="auto"><path class="sp-pr" d="M0,0L10,5L0,10z"/></marker></defs>')
    pf = []
    for st, seite, pts, text, tpos, strich in pfeile:
        kl = "ge" if seite == "de" else "pr"
        da = ' stroke-dasharray="6 5"' if strich else ''
        pf.append(f'<g data-s="{st}"><path class="pf-{kl}{' luft' if strich else ''}" d="{K.kurve(pts)}" pathLength="1" marker-end="url(#{kennung}-sp-{kl})"{da}/>'
                  + (f'<text class="tx-{kl}" x="%s" y="%s">{text}</text>' % K.xy(*tpos) if text else '') + '</g>')
    t.append('<g class="kk-pfeile">' + "".join(pf) + '</g>')
    t.append('<g class="kk-landschaft">' + "".join(
        '<text class="%s" x="%s" y="%s">%s</text>' % (k, *K.xy(a, b), name) for name, a, b, k in beschriftung if k.startswith("meer")) + '</g>')
    t.append('<g class="ek-namen">' + "".join(
        '<text class="%s" x="%s" y="%s">%s</text>' % (k, *K.xy(a, b), name) for name, a, b, k in beschriftung if not k.startswith("meer")) + '</g>')
    o = []
    for nm, a, b, al in orte:
        x, y = K.xy(a, b); dx = 7 if al == "start" else -7
        o.append(f'<circle cx="{x}" cy="{y}" r="3.2"/><text class="klein" x="{x+dx}" y="{y+4}" text-anchor="{al}">{nm}</text>')
    t.append('<g class="ek-orte">' + "".join(o) + '</g>')
    e = []
    for nr, ziel, a, b, st, kl in ereignisse:
        x, y = K.xy(a, b)
        e.append(f'<a href="#{ziel}" data-s="{st}"><g class="kk-marke {kl}" transform="translate({x},{y})"><g class="kk-inhalt">'
                 f'<circle r="12"/><text y="4.5">{nr}</text></g></g></a>')
    t.append('<g class="kk-ereignisse">' + "".join(e) + '</g>')
    (la, lb), km, breite = massstab
    xa, ya = K.xy(la, lb)
    grad = km / (111.32 * math.cos(math.radians(breite)))
    xb = xa + abs(K.xy(la + grad, breite)[0] - K.xy(la, breite)[0])
    t.append(f'<g class="kk-massstab"><path d="M{xa},{ya}h{round(xb-xa,1)}M{xa},{ya-5}v5M{round(xb,1)},{ya-5}v5"/>'
             f'<text x="{xa}" y="{ya-9}">' + f'{km:,}'.replace(",", ".") + ' km</text></g>')
    t.append('</svg>')
    return "".join(t)





# ---------- Karte: Hindenburg und Ludendorff 1914–1919 ----------
K = Karte(plattkarte(53), [(-0.6, 58.0), (27.4, 48.4)])
A = box(-4, 45, 30, 60)
land, seen, land_roh = flaechen(K, A, [])
REICH = kolonie(K, "German Empire", land_roh, 0.0)
TANNENBERG, KOWNO, PLESS, KREUZN = (20.09, 53.50), (23.90, 54.90), (18.95, 49.98), (7.87, 49.84)
SPA, AVESNES, KASSEL, KOLBERG, BERLIN = (5.86, 50.49), (3.93, 50.12), (9.42, 51.31), (15.58, 54.18), (13.40, 52.52)
ARRAS, STQ, LAFERE, SOISSONS, AMIENS = (2.78, 50.29), (3.29, 49.85), (3.37, 49.66), (3.32, 49.38), (2.30, 49.89)
ARMENT = (2.88, 50.69)
pfeile = [  # (Schritt, Seite, Punkte, Text, Textort, gestrichelt)
    ("1", "gb", [(20.9, 52.35), (20.55, 52.9), (20.25, 53.3)], "2. russische Armee", (20.75, 52.15), False),
    ("1", "gb", [(23.3, 54.45), (22.6, 54.5), (22.0, 54.5)], "1. russische Armee", (22.05, 54.95), False),
    ("2", "de", [(21.6, 54.7), (22.8, 55.0), (23.65, 54.95)], "1915", (21.9, 55.85), False),
    ("2", "de", [(21.2, 55.6), (22.0, 56.2), (22.8, 56.5)], "", None, False),
    ("2", "de", [(21.2, 53.4), (22.3, 53.2), (23.1, 53.15)], "", None, False),
    ("3", "de", [(23.6, 54.55), (21.8, 52.4), (PLESS[0] + 0.3, PLESS[1] + 0.12)], "September 1916", (21.95, 51.4), False),
    ("4", "de", [(PLESS[0] - 0.3, PLESS[1] - 0.05), (13.5, 49.3), (KREUZN[0] + 0.3, KREUZN[1] - 0.03)], "Februar 1917", (12.9, 49.95), False),
    ("5", "de", [(KREUZN[0] - 0.25, KREUZN[1] + 0.1), (6.9, 50.3), (SPA[0] + 0.25, SPA[1])], "März 1918", (6.5, 50.95), False),
    ("5", "de", [(STQ[0] - 0.15, STQ[1] + 0.02), (2.9, 49.9), (AMIENS[0] + 0.2, AMIENS[1] + 0.01)], "Michael", (2.15, 49.55), False),
    ("5", "de", [(ARMENT[0] + 0.05, ARMENT[1] + 0.05), (2.7, 50.75), (2.45, 50.72)], "Georgette", (1.15, 51.0), False),
    ("6", "gb", [(AMIENS[0] + 0.15, AMIENS[1] - 0.05), (2.75, 49.8), (3.15, 49.72)], "8. August", (2.1, 49.4), False),
    ("7", "de", [(SPA[0] + 0.25, SPA[1] + 0.08), (7.6, 51.1), (KASSEL[0] - 0.25, KASSEL[1])], "OHL nach Kassel", (6.4, 51.65), False),
    ("7", "de", [(KASSEL[0] + 0.2, KASSEL[1] + 0.15), (12.0, 53.2), (KOLBERG[0] - 0.25, KOLBERG[1] - 0.05)], "Februar 1919", (10.4, 53.65), True),
    ("7", "gb", [(BERLIN[0] + 0.1, BERLIN[1] + 0.15), (13.3, 54.2), (13.4, 55.55)], "Ludendorff nach Schweden", (13.75, 55.0), True),
]
# Siegfriedstellung (nur schematisch: Arras – St. Quentin – Soissons)
SIEGFRIED = [(ARRAS[0] + 0.05, ARRAS[1]), (3.05, 50.05), (STQ[0] + 0.03, STQ[1]), (3.36, 49.62), (SOISSONS[0] + 0.02, SOISSONS[1])]
beschr = [("Nordsee", 3.8, 55.2, "meer"), ("Ostsee", 17.7, 55.6, "meer"),
          ("Deutsches Reich", 10.6, 52.4, "gross"), ("Russisches Reich", 23.9, 51.0, "gross"),
          ("Österreich-Ungarn", 16.6, 48.75, "gross"), ("Frankreich", 1.8, 48.95, "gross"),
          ("Belgien", 3.75, 50.8, "klein"), ("Niederlande", 5.2, 52.9, "klein"), ("Dänemark", 9.0, 56.2, "klein"),
          ("Schweden", 14.4, 57.3, "klein"), ("Kurland", 22.2, 57.1, "ob"), ("Litauen", 24.9, 55.45, "ob"),
          ("Bialystok-Grodno", 23.4, 53.55, "ob"), ("Ostpreußen", 21.3, 54.0, "klein")]
orte = [("Tannenberg", *TANNENBERG, "end"), ("Kowno", *KOWNO, "start"), ("Pleß", *PLESS, "end"),
        ("Bad Kreuznach", *KREUZN, "start"), ("Spa", *SPA, "start"), ("Avesnes", *AVESNES, "start"),
        ("Kassel", *KASSEL, "start"), ("Kolberg", *KOLBERG, "start"), ("Berlin", *BERLIN, "start"),
        ("Arras", *ARRAS, "end"), ("St. Quentin", *STQ, "start"), ("Amiens", *AMIENS, "end")]
ereig = [(1, "e1", 19.25, 54.2, "1", "gefecht"), (2, "e2", 25.4, 56.5, "2", "beginn"), (3, "e3", 18.25, 50.55, "3", "beginn"),
         (4, "e4", 5.35, 49.15, "4", "beginn"), (5, "e5", 1.5, 50.35, "5", "gefecht"), (6, "e6", 5.0, 50.95, "6", "gefecht"),
         (7, "e7", 11.6, 51.9, "7", "beginn")]
svg = svg_karte(K, "lh-k1", "Hindenburg und Ludendorff 1914–1919",
                "Karte Mittel- und Osteuropas mit den Grenzen von 1914: die Schlacht bei Tannenberg in Ostpreußen im August 1914, "
                "der Vormarsch 1915 in die späteren Verwaltungsgebiete von Ober Ost (Kurland, Litauen, Bialystok-Grodno), der "
                "Wechsel in die Oberste Heeresleitung nach Pleß im August 1916, Bad Kreuznach und die Siegfriedstellung 1917, "
                "die Frühjahrsoffensive 1918 bei St. Quentin und Armentières, der alliierte Angriff bei Amiens am 8. August 1918, "
                "die Verlegung der Obersten Heeresleitung von Spa nach Kassel und Kolberg sowie Ludendorffs Weg nach Schweden.",
                land, seen, [("ka-dr", REICH)], [], grenzen(K, A, land_roh), pfeile, beschr, orte, ereig,
                ((22.0, 48.75), 200, 49))
linie = ('<g class="lh-linien"><g data-s="4 5 6"><path class="lh-siegfried" d="%s"/><text class="tx-ge" x="%s" y="%s">'
         'Siegfriedstellung</text></g></g>') % (K.kurve(SIEGFRIED), *K.xy(4.35, 49.3))
svg = svg.replace('<g class="kk-pfeile">', linie + '<g class="kk-pfeile">', 1)

html = SEITE.read_text(encoding="utf-8")
k = "karte-wege"
html, z = re.subn(rf"<!-- {k}:anfang -->.*?<!-- {k}:ende -->", lambda m: f"<!-- {k}:anfang -->\n" + svg + f"\n<!-- {k}:ende -->", html, flags=re.S)
if z != 1: raise SystemExit(f"Marken <!-- {k}:anfang/ende --> fehlen")
SEITE.write_text(html, encoding="utf-8")
print("Karte eingesetzt:", K.W, "x", K.H, len(svg) // 1024, "KB")
