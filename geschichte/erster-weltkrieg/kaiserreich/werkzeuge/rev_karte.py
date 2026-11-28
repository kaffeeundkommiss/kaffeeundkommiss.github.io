#!/usr/bin/env python3
"""Karte für geschichte/erster-weltkrieg/kaiserreich/revolution/index.html.

Karte „Die Revolution 1918/19“ zwischen <!-- karte-orte:anfang/ende -->.
Orte und Daten nach den Quellen der Seite (Deutsches Historisches Museum/LeMO, Bundeszentrale für politische Bildung,
1914-1918-online, Deutscher Bundestag).
Grundlagen: Natural Earth ne_50m_land (gemeinfrei, GeoJSON aus nvkelso/natural-earth-vector),
aourednik/historical-basemaps world_1914.geojson (GPL-3.0) für die Grenzen von 1914 (laut Projekt teils Näherungen).
Aufruf:  pip install shapely && python3 rev_karte.py <geo-ordner>/   (mit land.json, lakes.json und w1914.json)

Die Pfeile zeigen Richtungen und Umzüge, keine genauen Wege oder Frontverläufe. Aufbau und Kartenklasse wie kaiser_karte.py.
"""
import json, math, sys, re, pathlib, warnings
warnings.filterwarnings("ignore")
from shapely.geometry import shape, box
from shapely.ops import unary_union, transform
from shapely.validation import make_valid

G = sys.argv[1] if len(sys.argv) > 1 else "./"
SEITE = pathlib.Path(__file__).resolve().parent.parent / "revolution" / "index.html"
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





# ---------- Karte: Die Revolution 1918/19 ----------
K = Karte(plattkarte(51.5), [(2.0, 55.9), (17.4, 47.1)])
A = box(-2, 44, 21, 58)
land, seen, land_roh = flaechen(K, A, [])
REICH = kolonie(K, "German Empire", land_roh, 0.0)
WHV, KIEL, HAMBURG, BREMEN, BERLIN = (8.11, 53.53), (10.13, 54.32), (9.99, 53.55), (8.80, 53.08), (13.40, 52.52)
MUENCHEN, WEIMAR, BAMBERG, SPA, COMPIEGNE = (11.58, 48.14), (11.33, 50.98), (10.89, 49.89), (5.86, 50.49), (2.83, 49.42)
AMERONGEN = (5.46, 52.00)
pfeile = [  # (Schritt, Seite, Punkte, Text, Textort, gestrichelt) – "gb": Aufständische, "de": Regierung, Militär, Kaiser
    ("1", "gb", [(8.25, 53.8), (9.0, 54.25), (KIEL[0] - 0.3, KIEL[1] + 0.02)], "Teile der Flotte nach Kiel", (6.55, 54.55), False),
    ("3", "gb", [(KIEL[0] - 0.05, KIEL[1] - 0.12), (10.2, 53.95), (HAMBURG[0] + 0.12, HAMBURG[1] + 0.14)], "6. November", (10.35, 53.3), False),
    ("3", "gb", [(KIEL[0] - 0.25, KIEL[1] - 0.08), (9.0, 53.95), (WHV[0] + 0.25, WHV[1] + 0.07)], "", None, False),
    ("4", "de", [(SPA[0] + 0.05, SPA[1] + 0.2), (5.55, 51.3), (AMERONGEN[0] + 0.02, AMERONGEN[1] - 0.18)], "Kaiser ins Exil", (5.95, 51.25), True),
    ("6", "de", [(BERLIN[0] - 0.2, BERLIN[1] - 0.15), (12.4, 51.9), (WEIMAR[0] + 0.22, WEIMAR[1] + 0.12)], "Nationalversammlung", (12.6, 51.55), False),
    ("7", "de", [(MUENCHEN[0] - 0.08, MUENCHEN[1] + 0.22), (11.0, 49.1), (BAMBERG[0] + 0.05, BAMBERG[1] - 0.17)], "Regierung Hoffmann", (11.35, 49.5), True),
    ("7", "de", [(9.4, 49.2), (10.4, 48.55), (MUENCHEN[0] - 0.3, MUENCHEN[1] + 0.02)], "Freikorps, 1. Mai", (8.15, 48.5), False),
]
beschr = [("Nordsee", 5.2, 54.9, "meer"), ("Ostsee", 14.6, 55.2, "meer"),
          ("Deutsches Reich", 9.4, 51.9, "gross"), ("Frankreich", 3.3, 48.2, "gross"), ("Österreich-Ungarn", 15.2, 48.0, "gross"),
          ("Belgien", 4.2, 50.7, "klein"), ("Niederlande", 4.3, 52.75, "klein"), ("Dänemark", 9.1, 55.6, "klein"),
          ("Schweiz", 7.8, 47.25, "klein"), ("Bayern", 12.1, 49.0, "ob")]
orte = [("Wilhelmshaven", *WHV, "end"), ("Kiel", *KIEL, "start"), ("Hamburg", *HAMBURG, "end"), ("Bremen", *BREMEN, "end"),
        ("Berlin", *BERLIN, "start"), ("München", *MUENCHEN, "start"), ("Weimar", *WEIMAR, "end"), ("Bamberg", *BAMBERG, "end"),
        ("Spa", *SPA, "end"), ("Compiègne", *COMPIEGNE, "start"), ("Amerongen", *AMERONGEN, "start")]
ereig = [(1, "e1", 7.3, 53.95, "1", "gefecht"), (2, "e2", 10.9, 54.75, "2", "gefecht"), (3, "e3", 12.6, 48.6, "3", "beginn"),
         (4, "e4", 14.2, 52.95, "4", "beginn"), (5, "e5", 14.3, 52.1, "5", "gefecht"), (6, "e6", 10.6, 51.4, "6", "beginn"),
         (7, "e7", 12.6, 47.75, "7", "gefecht"), (5, "e5", 8.1, 52.75, "5", "gefecht")]
svg = svg_karte(K, "rev-k1", "Die Revolution 1918/19",
                "Karte des Deutschen Reichs mit den Grenzen von 1914: die Meuterei vor Wilhelmshaven Ende Oktober 1918, der Aufstand "
                "in Kiel am 3. und 4. November, die Ausbreitung nach Hamburg und Wilhelmshaven am 6. November und die Republik in "
                "München am 7. November, die Ausrufung der Republik in Berlin am 9. November und der Weg des Kaisers von Spa in die "
                "Niederlande, die Kämpfe in Berlin und die Räterepublik in Bremen im Winter 1918/19, die Nationalversammlung in "
                "Weimar ab 6. Februar 1919 sowie die Münchner Räterepublik und ihr Ende im Frühjahr 1919.",
                land, seen, [("ka-dr", REICH)], [], grenzen(K, A, land_roh), pfeile, beschr, orte, ereig,
                ((14.6, 47.55), 100, 48))

html = SEITE.read_text(encoding="utf-8")
k = "karte-orte"
html, z = re.subn(rf"<!-- {k}:anfang -->.*?<!-- {k}:ende -->", lambda m: f"<!-- {k}:anfang -->\n" + svg + f"\n<!-- {k}:ende -->", html, flags=re.S)
if z != 1: raise SystemExit(f"Marken <!-- {k}:anfang/ende --> fehlen")
SEITE.write_text(html, encoding="utf-8")
print("Karte eingesetzt:", K.W, "x", K.H, len(svg) // 1024, "KB")
