#!/usr/bin/env python3
"""Karte für geschichte/erster-weltkrieg/kaiserreich/kaiser/index.html.

Karte „Großes Hauptquartier 1914–1918“ zwischen <!-- karte-hauptquartier:anfang/ende -->.
Orte und Zeiträume nach dem Bundesarchiv (Themenbeitrag „Das Große Hauptquartier S.M. des Kaisers und Königs“).
Grundlagen: Natural Earth ne_50m_land und ne_50m_lakes (gemeinfrei, GeoJSON aus nvkelso/natural-earth-vector),
aourednik/historical-basemaps world_1914.geojson (GPL-3.0) für die Grenzen von 1914 (laut Projekt teils Näherungen).
Aufruf:  pip install shapely && python3 kaiser_karte.py <geo-ordner>/   (mit land.json, lakes.json und w1914.json)

Die Pfeile verbinden nur die Orte, sie zeigen keine Reisewege. Aufbau und Kartenklasse wie
../../uebersee/werkzeuge/kolonien_karte.py.
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



# ---------- Karte: Stationen des Großen Hauptquartiers 1914–1918 ----------
K = Karte(plattkarte(51), [(1.0, 54.4), (20.2, 47.4)])
A = box(-2, 44, 24, 57)
land, seen, land_roh = flaechen(K, A, [])
REICH = kolonie(K, "German Empire", land_roh, 0.0)
BERLIN, KOBLENZ, LUX, CHARLEV = (13.40, 52.52), (7.59, 50.36), (6.13, 49.61), (4.72, 49.77)
PLESS, KREUZN, SPA, AVESNES = (18.95, 49.98), (7.87, 49.84), (5.86, 50.49), (3.93, 50.12)
EYSDEN, AMERONGEN, DOORN = (5.72, 50.78), (5.46, 52.00), (5.35, 52.03)
pfeile = [  # (Schritt, Seite, Punkte, Text, Textort, gestrichelt)
    ("1", "de", [(BERLIN[0] - 0.25, BERLIN[1] - 0.1), (10.6, 51.4), (KOBLENZ[0] + 0.25, KOBLENZ[1] + 0.05)], "17. August", (10.0, 51.75), False),
    ("1", "de", [(KOBLENZ[0] - 0.1, KOBLENZ[1] - 0.15), (6.8, 49.95), (LUX[0] + 0.15, LUX[1] + 0.1)], "", None, False),
    ("2", "de", [(LUX[0] - 0.2, LUX[1] + 0.03), (5.4, 49.75), (CHARLEV[0] + 0.2, CHARLEV[1])], "25. September 1914", (3.1, 49.25), False),
    ("3", "de", [(CHARLEV[0] + 0.2, CHARLEV[1] + 0.12), (11.5, 51.3), (PLESS[0] - 0.25, PLESS[1] + 0.05)], "September 1916", (12.6, 51.55), False),
    ("4", "de", [(PLESS[0] - 0.25, PLESS[1] - 0.05), (13.5, 49.4), (KREUZN[0] + 0.25, KREUZN[1] - 0.03)], "Februar 1917", (12.6, 49.0), False),
    ("5", "de", [(KREUZN[0] - 0.2, KREUZN[1] + 0.1), (6.9, 50.3), (SPA[0] + 0.2, SPA[1])], "März 1918", (7.1, 50.75), False),
    ("6", "gb", [(SPA[0] - 0.05, SPA[1] + 0.12), (EYSDEN[0] + 0.05, EYSDEN[1] - 0.05)], "", None, True),
    ("6", "gb", [(EYSDEN[0] - 0.05, EYSDEN[1] + 0.12), (5.3, 51.4), (AMERONGEN[0] - 0.02, AMERONGEN[1] - 0.1)], "ins Exil", (3.6, 51.55), True),
]
beschr = [("Nordsee", 3.6, 54.0, "meer"), ("Ostsee", 15.6, 54.5, "meer"),
          ("Deutsches Reich", 10.4, 52.9, "gross"), ("Frankreich", 4.4, 48.35, "gross"), ("Österreich-Ungarn", 15.6, 48.2, "gross"),
          ("Niederlande", 4.6, 52.75, "klein"), ("Belgien", 4.0, 50.75, "klein"),
          ("Russisches Reich", 19.0, 52.3, "klein"), ("Schweiz", 7.5, 47.55, "klein")]
orte = [("Berlin", *BERLIN, "start"), ("Koblenz", *KOBLENZ, "start"), ("Luxemburg", *LUX, "start"),
        ("Charleville-Mézières", *CHARLEV, "end"), ("Pleß", *PLESS, "end"), ("Bad Kreuznach", *KREUZN, "start"),
        ("Spa", *SPA, "end"), ("Avesnes", *AVESNES, "end"), ("Eysden", *EYSDEN, "start"), ("Amerongen", *AMERONGEN, "start"),
        ("Doorn", *DOORN, "end")]
ereig = [(1, "e1", 8.3, 50.85, "1", "beginn"), (2, "e2", 4.35, 49.3, "2", "beginn"), (3, "e3", 18.4, 50.55, "3", "gefecht"),
         (4, "e4", 8.6, 49.45, "4", "gefecht"), (5, "e5", 4.75, 50.42, "5", "gefecht"), (6, "e6", 6.25, 52.5, "6", "beginn")]
svg = svg_karte(K, "ka-k1", "Das Große Hauptquartier 1914–1918",
                "Karte Mitteleuropas mit den Grenzen von 1914: die Stationen des Großen Hauptquartiers von Berlin über Koblenz und "
                "Luxemburg nach Charleville-Mézières 1914, Schloss Pleß in Schlesien 1916, Bad Kreuznach 1917 und Spa in Belgien 1918, "
                "dazu der Weg des Kaisers ins Exil über Eysden nach Amerongen und Doorn in den Niederlanden im November 1918.",
                land, seen, [("ka-dr", REICH)], [], grenzen(K, A, land_roh), pfeile, beschr, orte, ereig,
                ((1.6, 47.75), 100, 48))

html = SEITE.read_text(encoding="utf-8")
k = "karte-hauptquartier"
html, z = re.subn(rf"<!-- {k}:anfang -->.*?<!-- {k}:ende -->", lambda m: f"<!-- {k}:anfang -->\n" + svg + f"\n<!-- {k}:ende -->", html, flags=re.S)
if z != 1: raise SystemExit(f"Marken <!-- {k}:anfang/ende --> fehlen")
SEITE.write_text(html, encoding="utf-8")
print("Karte eingesetzt:", K.W, "x", K.H, len(svg) // 1024, "KB")
