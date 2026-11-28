#!/usr/bin/env python3
"""Zwei Karten für geschichte/erster-weltkrieg/luftkrieg/luftschiffe/index.html.

Karte „England“ (Luftschiffangriffe 1915–1918) zwischen <!-- karte-england:anfang/ende -->,
Karte „Afrika-Fahrt“ (L 59, November 1917) zwischen <!-- karte-afrika:anfang/ende -->.
Grundlage: Natural Earth ne_50m_land (gemeinfrei, GeoJSON aus nvkelso/natural-earth-vector).
Aufruf:  pip install shapely && python3 luftschiffe_karte.py <geo-ordner>/   (mit land.json)

Alle Fahrtwege sind schematisch: Die Quellen nennen Start, Ziele und Absturzorte, keine Kurse.
Kartenklasse und SVG-Aufbau wie ../../uebersee/werkzeuge/luckner_karte.py.
"""
import json, math, sys, re, pathlib, warnings
warnings.filterwarnings("ignore")
from shapely.geometry import shape, box
from shapely.ops import unary_union, transform
from shapely.affinity import translate
from shapely.validation import make_valid

G = sys.argv[1] if len(sys.argv) > 1 else "./"
SEITE = pathlib.Path(__file__).resolve().parent.parent / "luftschiffe" / "index.html"
LAND = [make_valid(shape(f["geometry"])) for f in json.load(open(G + "land.json"))["features"]]


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
    c = math.cos(math.radians(breite))
    return lambda lon, lat: (lon * c, lat)


def land_in(K, ausschnitte):
    """Land in einem oder mehreren Ausschnitten; ein Ausschnitt ist (Kasten, Verschiebung in Grad Länge)."""
    teile = []
    for kasten, dx in ausschnitte:
        for g in LAND:
            if g.intersects(kasten): teile.append(translate(g.intersection(kasten), dx, 0))
    return transform(K.proj, unary_union(teile)).intersection(K.RECT).simplify(0.02)


def svg_karte(K, kennung, titel, beschr, land, pfeile, beschriftung, orte, ereignisse, massstab):
    t = [f'<svg class="kk-karte ls-karte" viewBox="0 0 {K.W} {K.H}" role="img" aria-labelledby="{kennung}-titel {kennung}-beschr">'
         f'<title id="{kennung}-titel">{titel}</title><desc id="{kennung}-beschr">{beschr}</desc>',
         f'<rect class="ls-meer" x="0" y="0" width="{K.W}" height="{K.H}"/>',
         f'<path class="ls-land" d="{K.pfad(land)}"/>',
         f'<defs><marker id="{kennung}-sp-ge" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="4" markerHeight="4" orient="auto">'
         f'<path class="sp-ge" d="M0,0L10,5L0,10z"/></marker><marker id="{kennung}-sp-pr" viewBox="0 0 10 10" refX="7" refY="5" '
         f'markerWidth="4" markerHeight="4" orient="auto"><path class="sp-pr" d="M0,0L10,5L0,10z"/></marker></defs>']
    pf = []
    for st, seite, pts, text, tpos, strich in pfeile:
        kl = "ge" if seite == "de" else "pr"
        da = ' stroke-dasharray="6 5"' if strich else ''
        pf.append(f'<g data-s="{st}"><path class="pf-{kl}{" luft" if strich else ""}" d="{K.kurve(pts)}" pathLength="1" marker-end="url(#{kennung}-sp-{kl})"{da}/>'
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


# ---------- Karte 1: Angriffe auf England 1915–1918 ----------
K1 = Karte(plattkarte(52), [(-4.6, 56.0), (10.6, 47.4)])
land1 = land_in(K1, [(box(-12, 44, 16, 60), 0)])
NORDHOLZ, HAGE, AHLHORN, TONDERN, FUHLS = (8.65, 53.77), (7.28, 53.6), (8.23, 52.9), (8.87, 54.93), (10.0, 53.63)
YARMOUTH, LYNN, LONDON, WALSALL = (1.73, 52.61), (0.40, 52.75), (-0.12, 51.51), (-1.98, 52.59)
CUFFLEY, POTTERS, WELLS, LUNEVILLE, BOURBONNE = (-0.11, 51.71), (-0.18, 51.69), (0.85, 52.96), (6.50, 48.59), (5.75, 47.95)
pfeile1 = [  # (Schritt, Seite, Punkte, Text, Textort, gestrichelt)
    ("1", "de", [(FUHLS[0] - 0.3, FUHLS[1]), (5.0, 53.6), (2.6, 52.9), (1.9, 52.7)], "Januar 1915", (4.6, 54.1), False),
    ("2", "de", [(HAGE[0] - 0.2, HAGE[1] - 0.1), (4.0, 52.6), (1.6, 51.8), (0.1, 51.55)], "nach London", (3.6, 52.15), False),
    ("3", "de", [(NORDHOLZ[0] - 0.2, NORDHOLZ[1]), (4.5, 54.0), (0.6, 53.2), (-1.8, 52.65)], "Ziel Liverpool", (2.0, 53.65), False),
    ("4", "de", [(NORDHOLZ[0] - 0.2, NORDHOLZ[1] - 0.1), (4.0, 53.0), (1.0, 52.2), (-0.1, 51.78)], "", None, False),
    ("5", "de", [(AHLHORN[0] - 0.2, AHLHORN[1]), (3.5, 53.4), (0.0, 53.2), (-1.4, 52.4)], "nach Mittelengland", (1.3, 53.75), False),
    ("5", "de", [(-0.6, 51.8), (1.6, 50.6), (4.0, 49.4), (BOURBONNE[0] - 0.1, BOURBONNE[1] + 0.15)], "vom Wind abgetrieben", (1.5, 49.6), True),
    ("6", "de", [(AHLHORN[0] - 0.2, AHLHORN[1] + 0.1), (4.5, 53.3), (1.4, 53.1)], "L 70", (4.4, 53.6), False),
    ("6", "gb", [(1.3, 52.5), (1.05, 52.8), (WELLS[0] + 0.25, WELLS[1] + 0.12)], "D.H.4", (1.95, 52.35), False),
]
beschr1 = [("Nordsee", 3.2, 55.2, "meer"), ("Ärmelkanal", -2.4, 50.2, "meer klein"),
           ("England", -2.2, 53.6, "gross"), ("Frankreich", 2.6, 48.4, "gross"), ("Deutsches Reich", 8.6, 51.6, "gross"),
           ("Niederlande", 5.8, 52.4, "klein"), ("Belgien", 4.6, 50.7, "klein")]
orte1 = [("Nordholz", *NORDHOLZ, "start"), ("Hage", *HAGE, "end"), ("Ahlhorn", *AHLHORN, "start"), ("Tondern", *TONDERN, "start"),
         ("Hamburg", *FUHLS, "end"), ("Great Yarmouth", *YARMOUTH, "start"), ("King’s Lynn", *LYNN, "end"), ("London", *LONDON, "end"),
         ("Walsall", *WALSALL, "end"), ("Cuffley", *CUFFLEY, "start"), ("Wells", *WELLS, "end"),
         ("Bourbonne-les-Bains", *BOURBONNE, "end")]
ereig1 = [(1, "e1", 2.4, 52.35, "1", "gefecht"), (2, "e2", 0.55, 51.2, "2", "gefecht"), (3, "e3", -2.6, 52.2, "3", "gefecht"),
          (4, "e4", -0.75, 51.95, "4", "beginn"), (5, "e5", 5.2, 48.2, "5", "beginn"), (6, "e6", 1.5, 53.25, "6", "beginn")]
svg1 = svg_karte(K1, "ls-k1", "Luftschiffangriffe auf England 1915–1918",
                 "Karte der Nordsee mit Ostengland, den Niederlanden, Belgien, Nordfrankreich und Norddeutschland: die Luftschiffhäfen "
                 "an der deutschen Nordseeküste, schematische Anflüge auf Norfolk im Januar 1915, auf London 1915 und auf Mittelengland "
                 "1916, die Abschüsse bei Cuffley und Potters Bar im Herbst 1916, die Abtrift nach Frankreich im Oktober 1917 und der "
                 "Abschuss von L 70 vor Norfolk im August 1918.",
                 land1, pfeile1, beschr1, orte1, ereig1, ((-4.0, 47.9), 100, 48))

# ---------- Karte 2: die Afrika-Fahrt von L 59, November 1917 ----------
K2 = Karte(plattkarte(26), [(10.0, 45.0), (50.0, 7.0)])
land2 = land_in(K2, [(box(0, 0, 60, 50), 0)])
JAMBOL, KHARTUM, MALTA, KRETA = (26.5, 42.48), (32.53, 15.5), (14.4, 35.9), (24.9, 35.2)
pfeile2 = [
    ("1", "de", [(JAMBOL[0] - 0.2, JAMBOL[1] - 0.4), (26.4, 40.3), (27.2, 37.2), (26.2, 35.4)], "21.11.1917", (29.6, 40.2), False),
    ("2", "de", [(26.2, 35.4), (26.6, 33.2), (27.6, 31.0), (28.6, 26.0), (30.0, 20.0)], "über Ägypten", (24.5, 27.0), False),
    ("3", "de", [(30.0, 20.0), (30.6, 16.8), (30.8, 15.9)], "", None, False),
    ("3", "de", [(31.2, 14.8), (34.0, 10.6), (36.0, 7.4)], "Ziel Ostafrika", (37.8, 11.2), True),
    ("4", "de", [(31.4, 16.4), (31.6, 20.5), (30.2, 27.0), (28.6, 32.0), (27.8, 37.0), (JAMBOL[0] + 0.3, JAMBOL[1] - 0.5)], "Rückfahrt", (33.6, 25.0), False),
    ("5", "de", [(JAMBOL[0] - 0.5, JAMBOL[1] - 0.3), (22.0, 40.0), (17.5, 37.4), (MALTA[0] + 0.7, MALTA[1] + 0.1)], "Richtung Malta", (17.4, 39.6), False),
]
beschr2 = [("Mittelmeer", 19.0, 34.0, "meer"), ("Schwarzes Meer", 34.6, 43.4, "meer klein"), ("Rotes Meer", 38.4, 20.4, "meer klein"),
           ("Bulgarien", 25.0, 43.6, "klein"), ("Osmanisches Reich", 33.0, 39.0, ""), ("Ägypten", 29.0, 24.5, "gross"),
           ("Sudan", 30.0, 12.4, "gross"), ("Libyen", 17.5, 27.0, "gross")]
orte2 = [("Jambol", *JAMBOL, "start"), ("Khartum", *KHARTUM, "start"), ("Malta", *MALTA, "end"), ("Kreta", *KRETA, "end")]
ereig2 = [(1, "f1", 28.4, 43.6, "1", "beginn"), (2, "f2", 31.4, 31.2, "2", "beginn"), (3, "f3", 28.4, 15.2, "3", "gefecht"),
          (4, "f4", 24.0, 41.6, "4", "beginn"), (5, "f5", 13.0, 34.6, "5", "gefecht")]
svg2 = svg_karte(K2, "ls-k2", "Die Afrika-Fahrt von L 59 im November 1917",
                 "Karte des östlichen Mittelmeers und Nordostafrikas: schematischer Weg des Marineluftschiffs L 59 vom Luftschiffhafen "
                 "Jambol in Bulgarien über die Ägäis, Kreta und Ägypten bis in den Sudan westlich von Khartum, die Umkehr am 23. November "
                 "1917 und die Rückkehr nach Jambol am 25. November sowie die letzte Fahrt Richtung Malta im April 1918.",
                 land2, pfeile2, beschr2, orte2, ereig2, ((40.0, 8.4), 500, 10))

html = SEITE.read_text(encoding="utf-8")
for k, svg in (("karte-england", svg1), ("karte-afrika", svg2)):
    html, z = re.subn(rf"<!-- {k}:anfang -->.*?<!-- {k}:ende -->", lambda m: f"<!-- {k}:anfang -->\n" + svg + f"\n<!-- {k}:ende -->", html, flags=re.S)
    if z != 1: raise SystemExit(f"Marken <!-- {k}:anfang/ende --> fehlen")
SEITE.write_text(html, encoding="utf-8")
print("Karten eingesetzt:", K1.W, "x", K1.H, len(svg1) // 1024, "KB;", K2.W, "x", K2.H, len(svg2) // 1024, "KB")
