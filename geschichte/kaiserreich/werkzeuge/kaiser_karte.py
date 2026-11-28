#!/usr/bin/env python3
"""Karte für geschichte/kaiserreich/kaiser/index.html.

Karte „Orte der drei Kaiser 1871–1914“ zwischen <!-- karte-orte:anfang/ende -->.
Orte und Daten nach den Quellen der Seite (Deutsches Historisches Museum/LeMO, Neue Deutsche Biographie,
Bundeszentrale für politische Bildung, 1914-1918-online).
Grundlagen: Natural Earth ne_50m_land (gemeinfrei, GeoJSON aus nvkelso/natural-earth-vector),
aourednik/historical-basemaps world_1914.geojson (GPL-3.0) für die Grenzen von 1914 (laut Projekt teils Näherungen).
Aufruf:  pip install shapely && python3 kaiser_karte.py <geo-ordner>/   (mit land.json, lakes.json und w1914.json)

Der Pfeil zeigt nur eine Richtung, keinen genauen Reiseweg. Aufbau und Kartenklasse wie
geschichte/erster-weltkrieg/kaiserreich/werkzeuge/rev_karte.py.
"""
import json, math, sys, re, pathlib, warnings
warnings.filterwarnings("ignore")
from shapely.geometry import shape, box
from shapely.ops import unary_union, transform
from shapely.validation import make_valid

G = sys.argv[1] if len(sys.argv) > 1 else "./"
SEITE = pathlib.Path(__file__).resolve().parent.parent / "kaiser" / "index.html"
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





# ---------- Karte: Orte der drei Kaiser 1871–1914 ----------
K = Karte(plattkarte(44.0), [(-11.5, 56.2), (21.5, 29.2)])
A = box(-16, 25, 27, 60)
land, seen, land_roh = flaechen(K, A, [])
REICH = kolonie(K, "German Empire", land_roh, 0.0)
VERSAILLES, BERLIN, SANREMO = (2.13, 48.80), (13.40, 52.52), (7.78, 43.82)
LONDON, TANGER, AGADIR = (-0.13, 51.51), (-5.80, 35.77), (-9.60, 30.43)
pfeile = [  # (Schritt, Seite, Punkte, Text, Textort, gestrichelt) – "de": Weg des Kaisers
    ("3", "de", [(SANREMO[0] + 0.3, SANREMO[1] + 0.4), (10.2, 48.6), (BERLIN[0] - 0.4, BERLIN[1] - 0.4)], "März 1888", (10.9, 47.6), False),
]
beschr = [("Nordsee", 3.2, 55.3, "meer"), ("Ostsee", 17.2, 55.6, "meer"), ("Atlantik", -7.4, 46.6, "meer"),
          ("Mittelmeer", 5.2, 39.0, "meer"),
          ("Deutsches Reich", 9.2, 51.3, "gross"), ("Frankreich", 2.4, 46.6, "gross"), ("Spanien", -4.2, 40.0, "gross"),
          ("Großbritannien", -3.2, 53.6, "gross"), ("Italien", 13.2, 42.4, "gross"), ("Österreich-Ungarn", 17.0, 47.6, "gross"),
          ("Marokko", -6.3, 32.2, "gross")]
orte = [("Versailles", *VERSAILLES, "end"), ("Berlin", *BERLIN, "start"), ("San Remo", *SANREMO, "start"),
        ("London", *LONDON, "end"), ("Tanger", *TANGER, "start"), ("Agadir", *AGADIR, "start")]
ereig = [(1, "e1", 0.6, 49.9, "1", "beginn"), (2, "e2", 12.4, 53.6, "2", "gefecht"), (3, "e3", 8.6, 42.6, "3", "beginn"),
         (4, "e4", 14.6, 53.6, "4", "beginn"), (5, "e5", -4.0, 36.9, "5", "beginn"), (6, "e6", -1.4, 52.7, "6", "beginn"),
         (7, "e7", -7.9, 31.5, "7", "beginn")]
svg = svg_karte(K, "kai-k1", "Orte der drei Kaiser 1871–1914",
                "Karte Europas und Nordwestafrikas mit dem Deutschen Reich in den Grenzen von 1914: Kaiserproklamation in "
                "Versailles am 18. Januar 1871, Attentate auf Wilhelm I. in Berlin 1878, Friedrich III. in San Remo und seine "
                "Rückkehr nach Berlin im März 1888, Bismarcks Entlassung in Berlin 1890, der Besuch Wilhelms II. in Tanger 1905, "
                "das Interview im Londoner Daily Telegraph 1908 und das Kanonenboot Panther vor Agadir 1911.",
                land, seen, [("ka-dr", REICH)], [], grenzen(K, A, land_roh), pfeile, beschr, orte, ereig,
                ((15.0, 30.6), 500, 44))

html = SEITE.read_text(encoding="utf-8")
k = "karte-orte"
html, z = re.subn(rf"<!-- {k}:anfang -->.*?<!-- {k}:ende -->", lambda m: f"<!-- {k}:anfang -->\n" + svg + f"\n<!-- {k}:ende -->", html, flags=re.S)
if z != 1: raise SystemExit(f"Marken <!-- {k}:anfang/ende --> fehlen")
SEITE.write_text(html, encoding="utf-8")
print("Karte eingesetzt:", K.W, "x", K.H, len(svg) // 1024, "KB")
