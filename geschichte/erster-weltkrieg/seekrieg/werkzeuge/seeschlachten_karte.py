#!/usr/bin/env python3
"""Zwei Karten für geschichte/erster-weltkrieg/seekrieg/seeschlachten/index.html.

Karte „Übersee“ (Coronel und Falklandinseln 1914) zwischen <!-- karte-uebersee:anfang/ende -->,
Karte „Nordsee“ (Doggerbank 1915, Skagerrak 1916) zwischen <!-- karte-nordsee:anfang/ende -->.
Grundlagen: Natural Earth ne_50m_land (gemeinfrei, GeoJSON aus nvkelso/natural-earth-vector),
aourednik/historical-basemaps world_1914.geojson (GPL-3.0) für die Grenzen von 1914.
Aufruf:  pip install shapely && python3 seeschlachten_karte.py <geo-ordner>/   (mit land.json und w1914.json)

Alle Wege sind schematisch und folgen nur den in den Quellen genannten Stationen.
"""
import json, math, sys, re, pathlib, warnings
warnings.filterwarnings("ignore")
from shapely.geometry import shape, box
from shapely.ops import unary_union, transform
from shapely.affinity import translate
from shapely.validation import make_valid

G = sys.argv[1] if len(sys.argv) > 1 else "./"
SEITE = pathlib.Path(__file__).resolve().parent.parent / "seeschlachten" / "index.html"
LAND = [make_valid(shape(f["geometry"])) for f in json.load(open(G + "land.json"))["features"]]
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


def svg_karte(K, kennung, titel, beschr, land, staaten, grenzen, gebiete, pfeile, beschriftung, orte, ereignisse, massstab):
    t = [f'<svg class="kk-karte ss-karte" viewBox="0 0 {K.W} {K.H}" role="img" aria-labelledby="{kennung}-titel {kennung}-beschr">'
         f'<title id="{kennung}-titel">{titel}</title><desc id="{kennung}-beschr">{beschr}</desc>',
         f'<rect class="ss-meer" x="0" y="0" width="{K.W}" height="{K.H}"/>',
         f'<path class="ss-land" d="{K.pfad(land)}"/>']
    for kl, g in staaten: t.append(f'<path class="{kl}" d="{K.pfad(g)}"/>')
    if grenzen is not None: t.append(f'<path class="ss-grenzen" d="{K.linie(grenzen)}"/>')
    t.append('<g class="ss-gebiete">' + "".join(f'<path class="ss-gebiet" data-s="{st}" d="{K.kurve(p)}Z"/>' for st, p in gebiete) + '</g>')
    t.append(f'<defs><marker id="{kennung}-sp-ge" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="4" markerHeight="4" orient="auto">'
             f'<path class="sp-ge" d="M0,0L10,5L0,10z"/></marker><marker id="{kennung}-sp-pr" viewBox="0 0 10 10" refX="7" refY="5" '
             f'markerWidth="4" markerHeight="4" orient="auto"><path class="sp-pr" d="M0,0L10,5L0,10z"/></marker></defs>')
    pf = []
    for st, seite, pts, text, tpos, strich in pfeile:
        kl = "ge" if seite == "de" else "pr"
        da = ' stroke-dasharray="6 5"' if strich else ''
        pf.append(f'<g data-s="{st}"><path class="pf-{kl}" d="{K.kurve(pts)}" pathLength="1"{"" if strich else f" marker-end=\"url(#{kennung}-sp-{kl})\""}{da}/>'
                  + (f'<text class="tx-{kl}" x="%s" y="%s">{text}</text>' % K.xy(*tpos) if text else '') + '</g>')
    t.append('<g class="kk-pfeile">' + "".join(pf) + '</g>')
    t.append('<g class="kk-landschaft">' + "".join(
        '<text class="%s" x="%s" y="%s">%s</text>' % (k, *K.xy(a, b), name) for name, a, b, k in beschriftung if k.startswith("meer")) + '</g>')
    t.append('<g class="ek-namen">' + "".join(
        '<text class="%s" x="%s" y="%s">%s</text>' % (k, *K.xy(a, b), name) for name, a, b, k in beschriftung if not k.startswith("meer")) + '</g>')
    o = []
    for nm, a, b, al, stuetz in orte:
        x, y = K.xy(a, b); dx = 7 if al == "start" else -7
        form = (f'<rect class="stuetz" x="{x-4}" y="{y-4}" width="8" height="8"/>' if stuetz else f'<circle cx="{x}" cy="{y}" r="3.2"/>')
        o.append(f'{form}<text class="klein" x="{x+dx}" y="{y+4}" text-anchor="{al}">{nm}</text>')
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


# ---------- Karte 1: Übersee (Pazifik und Südamerika), Längen östlich von 180° als 180–360 ----------
def P1(lon, lat):  # Plattkarte, Breitenkreis 25° längentreu
    return lon * math.cos(math.radians(25)), lat
K1 = Karte(P1, [(112, 38), (322, -61)])
B1a, B1b = box(112, -62, 180, 39), box(-180, -62, -37, 39)
land1 = unary_union([g.intersection(B1a) for g in LAND if g.intersects(B1a)] +
                    [translate(g.intersection(B1b), 360) for g in LAND if g.intersects(B1b)])
land1 = transform(K1.proj, land1).intersection(K1.RECT).simplify(0.12)
L = lambda lon: lon + 360 if lon < 0 else lon  # westliche Längen weiterzählen
PAGAN, SAMOA, TAHITI, OSTER = (145.8, 18.1), (L(-171.8), -13.8), (L(-149.6), -17.6), (L(-109.4), -27.1)
JUANF, CORON, VALPO, HORN, STANLEY = (L(-80.8), -33.8), (L(-73.2), -37.0), (L(-71.6), -33.0), (L(-67.3), -56.0), (L(-57.85), -51.7)
pfeile1 = [  # (Schritt, Seite, Punkte, Text, Textort, gestrichelt)
    ("1", "de", [PAGAN, (136, 13), (127, 8)], "Emden", (128.5, 5.6), False),
    ("2", "de", [PAGAN, (166, 9), SAMOA, TAHITI, (232, -24), OSTER, (266, -31), JUANF], "Spee", (196, -6.5), False),
    ("2", "gb", [STANLEY, (L(-62), -55.2), (L(-68.5), -56.8), (L(-76.5), -50), (L(-75.5), -43)], "Cradock", (L(-84), -47.5), False),
    ("3", "de", [JUANF, (L(-76.5), -35.6), (L(-74.4), -36.8)], "", None, False),
    ("3", "gb", [(L(-75.5), -43), (L(-74.6), -39.5), (L(-74.0), -37.6)], "", None, False),
    ("4", "de", [VALPO, (L(-76), -40), (L(-77), -50), (L(-69.5), -57.0), (L(-63), -55.3), (L(-59.2), -53.1)], "Spee", (L(-84.5), -46), False),
    ("4", "gb", [(L(-48), -12), (L(-44.5), -30), (L(-52), -46), (L(-57.2), -51.0)], "Sturdee", (L(-54), -22.5), False),
    ("5", "gb", [STANLEY, (L(-56), -52.8), (L(-56.4), -54)], "", None, False),
    ("5", "de", [(L(-58.5), -53.6), (L(-64), -56.4), (L(-72), -55.5)], "Dresden", (L(-70), -58.6), False),
]
beschr1 = [("Pazifischer Ozean", 205, 2, "meer"), ("Atlantik", L(-49), -57.5, "meer"),
           ("China", 117.5, 27.5, "gross"), ("Japan", 139, 39.5, ""), ("Australien", 134, -24, "gross"),
           ("Südamerika", L(-62), -12, "gross"), ("Chile", L(-69.2), -27, "")]
orte1 = [("Tsingtau", 120.3, 36.1, "start", True), ("Pagan", *PAGAN, "start", False), ("Samoa", *SAMOA, "end", False),
         ("Tahiti", *TAHITI, "start", False), ("Osterinsel", *OSTER, "end", False), ("Juan Fernández", *JUANF, "end", False),
         ("Valparaíso", *VALPO, "start", False), ("Kap Horn", *HORN, "end", False), ("Port Stanley", *STANLEY, "start", True)]
ereig1 = [(1, "u1", *PAGAN, "1", "beginn"), (2, "u2", TAHITI[0], TAHITI[1] - 3.6, "2", "beginn"),
          (3, "u3", L(-76.2), -38.2, "3", "gefecht"), (4, "u4", L(-55.0), -53.9, "5", "gefecht")]
svg1 = svg_karte(K1, "ss-k1", "Das deutsche Kreuzergeschwader 1914: von Pagan über Coronel zu den Falklandinseln",
                 "Karte von Pazifik und Südamerika mit dem schematischen Weg des deutschen Kreuzergeschwaders unter Graf Spee "
                 "von den Marianen über Tahiti und die Osterinsel nach Chile, den Gefechten bei Coronel am 1. November und bei den "
                 "Falklandinseln am 8. Dezember 1914 und den Fahrten der britischen Geschwader.",
                 land1, [], None, [], pfeile1, beschr1, orte1, ereig1, ((122, -52), 2000, -40))

# ---------- Karte 2: Nordsee (Lambert, längentreu bei 52° und 58° N) ----------
p1, p2, l0, f0 = math.radians(52), math.radians(58), math.radians(4), math.radians(55)
n = math.log(math.cos(p1) / math.cos(p2)) / math.log(math.tan(math.pi/4 + p2/2) / math.tan(math.pi/4 + p1/2))
F = math.cos(p1) * math.tan(math.pi/4 + p1/2) ** n / n
r0 = F / math.tan(math.pi/4 + f0/2) ** n
def P2(lon, lat):
    r = F / math.tan(math.pi/4 + math.radians(lat)/2) ** n; t = n * (math.radians(lon) - l0)
    return r * math.sin(t), r0 - r * math.cos(t)
K2 = Karte(P2, [(-4.2, 51.0), (-4.2, 61.0), (12.6, 51.0), (12.6, 61.0), (4, 61.4)])
B2 = box(-12, 47, 20, 64)
land2 = transform(K2.proj, unary_union([g.intersection(B2) for g in LAND if g.intersects(B2)])).intersection(K2.RECT).simplify(0.0009)
def staat(name, puffer, ohne=(), plus=None):
    """Fläche eines Staates von 1914, um `puffer` Grad erweitert und auf die Küste von Natural Earth beschnitten,
    damit die gröberen historischen Umrisse die Küstenlinie ganz füllen; Nachbarn in `ohne` werden abgezogen."""
    g = unary_union([make_valid(shape(f["geometry"])) for f in H14 if f["properties"].get("NAME") == name]).buffer(puffer)
    if plus is not None: g = g.union(plus)  # Inseln, die world_1914 keinem Staat zuordnet
    for nb in ohne:
        g = g.difference(unary_union([make_valid(shape(f["geometry"])) for f in H14 if f["properties"].get("NAME") == nb]))
    return transform(K2.proj, g.intersection(B2)).intersection(land2).intersection(K2.RECT)
grenzen2 = unary_union([transform(K2.proj, make_valid(shape(f["geometry"])).intersection(B2)).boundary for f in H14
                        if shape(f["geometry"]).intersects(B2)]).intersection(land2.buffer(-0.0002)).simplify(0.0009)
NACHBARN_DR = ("Denmark", "Netherlands", "Belgium", "Russian Empire", "Austro-Hungarian Empire", "France", "Switzerland", "Luxembourg")
WHV, SCAPA, ROSYTH, HORNS = (8.12, 53.52), (-3.1, 58.88), (-3.4, 56.03), (7.55, 55.5)
pfeile2 = [
    ("1", "gb", [(-1.2, 60.4), (2.0, 60.55), (4.7, 60.7)], "Sperrlinie", (1.6, 60.15), True),
    ("1", "gb", [(1.3, 51.15), (1.75, 50.95)], "", None, True),
    ("2", "de", [(7.9, 53.85), (6.4, 54.45), (4.3, 54.85)], "Hipper", (6.0, 54.95), False),
    ("2", "gb", [(-1.6, 56.0), (0.8, 55.5), (2.7, 55.0)], "Beatty", (0.4, 55.95), False),
    ("2", "de", [(3.9, 54.55), (5.6, 54.25), (7.6, 54.0)], "", None, False),
    ("3", "de", [(7.95, 53.85), (7.5, 55.0), (6.6, 56.4)], "Hochseeflotte", (8.9, 56.3), False),
    ("3", "gb", [(-2.6, 58.7), (1.2, 58.2), (4.3, 57.6)], "Jellicoe", (1.0, 58.6), False),
    ("3", "gb", [(-2.4, 56.1), (1.4, 56.5), (4.6, 56.75)], "Beatty", (1.2, 56.15), False),
    ("4", "gb", [(3.9, 57.8), (5.0, 57.45), (5.9, 57.3)], "Grand Fleet", (3.2, 57.9), False),
    ("4", "de", [(6.9, 57.15), (6.5, 56.75), (5.8, 56.55)], "Kehrtwendung", (7.1, 56.45), False),
    ("5", "de", [(5.9, 56.6), (7.0, 56.0), HORNS, (7.95, 54.6), (8.05, 53.85)], "Hochseeflotte", (7.0, 54.45), False),
    ("5", "gb", [(5.2, 57.0), (5.4, 56.1), (5.6, 55.3)], "Grand Fleet", (4.1, 55.6), False),
]
beschr2 = [("Nordsee", 2.2, 57.0, "meer"), ("Skagerrak", 9.3, 58.0, "meer klein"), ("Doggerbank", 1.6, 54.45, "meer klein"),
           ("Großbritannien", -2.6, 54.4, "gross"), ("Deutsches Reich", 10.6, 52.6, "gross"), ("Dänemark", 9.3, 56.2, ""),
           ("Norwegen", 8.2, 59.9, ""), ("Niederlande", 5.9, 52.4, "")]
orte2 = [("Scapa Flow", *SCAPA, "end", True), ("Rosyth", *ROSYTH, "end", True), ("Wilhelmshaven", *WHV, "start", True),
         ("Horns Riff", *HORNS, "end", False)]
ereig2 = [(1, "n1", 3.4, 54.75, "2", "gefecht"), (2, "n2", 5.5, 56.75, "3", "gefecht"),
          (3, "n3", 6.25, 57.1, "4", "gefecht"), (4, "n4", 6.75, 55.95, "5", "beginn")]
svg2 = svg_karte(K2, "ss-k2", "Doggerbank 1915 und Skagerrak 1916", "Karte der Nordsee mit den Stützpunkten Scapa Flow, Rosyth und "
                 "Wilhelmshaven, den britischen Sperrlinien, dem Gefecht auf der Doggerbank am 24. Januar 1915 und dem Verlauf der "
                 "Skagerrakschlacht am 31. Mai und 1. Juni 1916, alle Wege schematisch.",
                 land2, [("ss-dr", staat("German Empire", 0.12, NACHBARN_DR)), ("ss-uk", staat("United Kingdom of Great Britain and Ireland", 0.8, ("France", "Belgium", "Netherlands", "Norway"), box(-3.6, 58.6, -0.4, 61)))],  # mit Orkney und Shetland
                 grenzen2, [], pfeile2, beschr2, orte2, ereig2, ((-3.6, 51.6), 200, 52))

html = SEITE.read_text(encoding="utf-8")
for k, svg in (("karte-uebersee", svg1), ("karte-nordsee", svg2)):
    html, z = re.subn(rf"<!-- {k}:anfang -->.*?<!-- {k}:ende -->", lambda m: f"<!-- {k}:anfang -->\n" + svg + f"\n<!-- {k}:ende -->", html, flags=re.S)
    if z != 1: raise SystemExit(f"Marken <!-- {k}:anfang/ende --> fehlen")
SEITE.write_text(html, encoding="utf-8")
print("Karten eingesetzt:", K1.W, "x", K1.H, len(svg1) // 1024, "KB;", K2.W, "x", K2.H, len(svg2) // 1024, "KB")
