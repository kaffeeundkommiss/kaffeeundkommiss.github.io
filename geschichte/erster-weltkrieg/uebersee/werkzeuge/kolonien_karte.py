#!/usr/bin/env python3
"""Zwei Karten für geschichte/erster-weltkrieg/uebersee/kolonien/index.html.

Karte „Afrika“ (Togo, Kamerun, Deutsch-Südwestafrika 1914–1916) zwischen <!-- karte-afrika:anfang/ende -->,
Karte „Ostafrika“ (Deutsch-Ostafrika 1914–1918) zwischen <!-- karte-ostafrika:anfang/ende -->.
Grundlagen: Natural Earth ne_50m_land und ne_50m_lakes (gemeinfrei, GeoJSON aus nvkelso/natural-earth-vector),
aourednik/historical-basemaps world_1914.geojson (GPL-3.0) für die Grenzen von 1914 (laut Projekt teils Näherungen).
Aufruf:  pip install shapely && python3 kolonien_karte.py <geo-ordner>/   (mit land.json, lakes.json und w1914.json)

Alle Wege sind schematisch und folgen nur den in den Quellen genannten Orten. Aufbau wie
../../seekrieg/werkzeuge/seeschlachten_karte.py; die Kartenklasse ist von dort übernommen.
"""
import json, math, sys, re, pathlib, warnings
warnings.filterwarnings("ignore")
from shapely.geometry import shape, box
from shapely.ops import unary_union, transform
from shapely.validation import make_valid

G = sys.argv[1] if len(sys.argv) > 1 else "./"
SEITE = pathlib.Path(__file__).resolve().parent.parent / "kolonien" / "index.html"
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
    t = [f'<svg class="kk-karte ko-karte" viewBox="0 0 {K.W} {K.H}" role="img" aria-labelledby="{kennung}-titel {kennung}-beschr">'
         f'<title id="{kennung}-titel">{titel}</title><desc id="{kennung}-beschr">{beschr}</desc>',
         f'<rect class="ko-meer" x="0" y="0" width="{K.W}" height="{K.H}"/>',
         f'<path class="ko-land" d="{K.pfad(land)}"/>']
    for kl, g in kolonien: t.append(f'<path class="{kl}" d="{K.pfad(g)}"/>')
    t.append('<g class="ko-besetzt">' + "".join(f'<path data-s="{st}" d="{K.pfad(g)}"/>' for st, g in besetzt) + '</g>')
    t.append(f'<path class="ko-grenzen" d="{K.linie(grenzlinien)}"/>')
    t.append(f'<path class="ko-see" d="{K.pfad(seen)}"/>')
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


AB = lambda s: " ".join(str(i) for i in range(int(s), 6))  # ab Schritt s bis zum letzten Schritt 5

# ---------- Karte 1: Afrika (Togo, Kamerun, Südwestafrika) ----------
K1 = Karte(plattkarte(10), [(-18, 17), (52, -36)])
A1 = box(-25, -40, 60, 20)
land1, seen1, land1_roh = flaechen(K1, A1, ["Lake Victoria", "Lake Tanganyika", "Lake Malawi"])
TOGO = kolonie(K1, "Togoland", land1_roh)
KAM = kolonie(K1, "Kamerun", land1_roh, ohne=("Equatorial Guinea", "Nigeria", "French Equatorial Africa"))
DSWA = kolonie(K1, "German South-West Africa", land1_roh)
DOA = kolonie(K1, "German E. Africa (Tanganyika)", land1_roh)
RIOMUNI = kolonie(K1, "Equatorial Guinea", land1_roh, 0.05)
KAMINA, LOME, DUALA, JAUNDE, MORA, KHORAB = (1.13, 7.53), (1.22, 6.13), (9.7, 4.05), (11.52, 3.87), (14.14, 11.05), (17.65, -19.62)
pfeile1 = [  # (Schritt, Seite, Punkte, Text, Textort, gestrichelt)
    ("1", "gb", [(-1.6, 5.6), (0.0, 6.0), (0.95, 7.2)], "Briten", (-7.2, 4.4), False),
    ("1", "gb", [(2.6, 6.6), (2.1, 7.2), (1.45, 7.55)], "Franzosen", (3.0, 8.7), False),
    ("2", "gb", [(7.0, 8.2), (8.9, 7.4), (10.2, 6.8)], "", None, False),
    ("2", "gb", [(4.6, 2.0), (7.6, 3.2), (9.35, 3.95)], "von See", (2.6, 1.0), False),
    ("2", "gb", [(12.2, -0.6), (12.0, 0.9), (11.9, 2.0)], "", None, False),
    ("2", "gb", [(18.6, 3.0), (17.0, 3.6), (15.6, 4.0)], "Franzosen", (19.0, 1.9), False),
    ("3", "gb", [(19.6, -31.0), (18.6, -29.6), (17.9, -27.8)], "Südafrikaner", (21.0, -31.5), False),
    ("4", "gb", [(17.9, -27.0), (17.6, -24.0), (17.6, -21.0)], "", None, False),
    ("4", "gb", [(15.0, -23.5), (16.2, -21.6), (17.3, -20.2)], "", None, False),
    ("5", "de", [JAUNDE, (11.0, 2.6), (10.7, 1.9)], "Übertritt", (12.2, 1.6), False),
]
beschr1 = [("Atlantischer Ozean", -4.0, -14, "meer"), ("Indischer Ozean", 44.5, -24, "meer"),
           ("Togo", 0.2, 11.8, ""), ("Kamerun", 13.4, 8.2, ""), ("Deutsch-Südwestafrika", 15.0, -15.3, ""),
           ("Deutsch-Ostafrika", 30.0, -1.6, ""), ("Rio Muni", 6.6, -0.4, "klein"),
           ("Nigeria", 6.0, 11.5, "klein"), ("Goldküste", -4.0, 9.5, "klein"), ("Südafrikanische Union", 25.0, -29.2, "klein"),
           ("Belgisch-Kongo", 21.0, -2.5, "klein")]
orte1 = [("Kamina", *KAMINA, "start"), ("Lomé", *LOME, "end"), ("Duala", *DUALA, "end"), ("Jaunde", *JAUNDE, "start"),
         ("Mora", *MORA, "end"), ("Khorab", *KHORAB, "start")]
ereig1 = [(1, "a1", 2.4, 9.3, "1", "gefecht"), (2, "a2", 8.2, 2.4, "2", "gefecht"),
          (3, "a3", 19.6, -18.2, "4", "beginn"), (4, "a4", 12.9, 0.4, "5", "beginn"), (5, "a5", 16.4, 11.0, "5", "gefecht")]
svg1 = svg_karte(K1, "ko-k1", "Die deutschen Kolonien in Afrika 1914–1916",
                 "Karte Afrikas südlich der Sahara mit den deutschen Kolonien Togo, Kamerun, Deutsch-Südwestafrika und Deutsch-Ostafrika, "
                 "den schematischen Vorstößen der Alliierten 1914 und 1915, der Kapitulation bei Khorab am 9. Juli 1915 und dem "
                 "Übertritt der Schutztruppe Kameruns nach Rio Muni 1916.",
                 land1, seen1, [("ko-dr", g) for g in (TOGO, KAM, DSWA, DOA)] + [("ko-neutral", RIOMUNI)],
                 [(AB(1), TOGO), (AB(4), DSWA), ("5", KAM)], grenzen(K1, A1, land1_roh), pfeile1, beschr1, orte1, ereig1,
                 ((-15, -33), 1000, -10))

# ---------- Karte 2: Ostafrika 1914–1918 ----------
K2 = Karte(plattkarte(9), [(26.0, 0.6), (44.0, -17.3)])
A2 = box(24, -22, 46, 3)
land2, seen2, land2_roh = flaechen(K2, A2, ["Lake Victoria", "Lake Tanganyika", "Lake Malawi", "Lake Kivu", "Lake Rukwa", "Lake Bangweulu"])
DOA2 = kolonie(K2, "German E. Africa (Tanganyika)", land2_roh, 0.04)
TANGA, MOSHI, DAR, TABORA, LINDI, MAHIWA = (39.1, -5.07), (37.35, -3.35), (39.28, -6.8), (32.8, -5.02), (39.71, -10.0), (39.35, -10.3)
KASAMA, ABERCORN = (31.18, -10.21), (31.37, -8.84)
pfeile2 = [
    ("1", "gb", [(41.6, -6.4), (40.4, -5.6), (39.35, -5.15)], "Briten und Inder", (40.0, -6.6), False),
    ("1", "de", [(37.5, -3.7), (38.3, -4.3), (38.9, -4.9)], "Schutztruppe", (35.6, -4.5), False),
    ("2", "gb", [(37.6, -2.4), (37.9, -4.6), (38.0, -6.4), (38.9, -6.9)], "Smuts", (36.0, -2.0), False),
    ("2", "gb", [(29.4, -2.0), (31.2, -3.6), (32.5, -4.8)], "Belgier", (29.0, -1.2), False),
    ("2", "gb", [(34.0, -11.8), (34.2, -10.6), (34.6, -9.6)], "aus Njassaland", (32.0, -12.6), False),
    ("2", "de", [(37.0, -4.2), (36.9, -6.6), (37.6, -8.4)], "Rückzug", (35.1, -7.6), False),
    ("3", "de", [(38.4, -9.2), (39.1, -10.2), (38.6, -11.3), (37.8, -12.4)], "über den Rovuma", (38.9, -12.6), False),
    ("4", "de", [(37.8, -12.4), (37.9, -14.8), (37.0, -16.2), (35.9, -14.6), (35.6, -11.6), (35.2, -10.6)], "Weg schematisch", (38.3, -16.4), True),
    ("5", "de", [(35.0, -10.4), (33.6, -9.3), (32.3, -9.6), (31.45, -10.05)], "nach Nordrhodesien", (32.6, -8.6), False),
    ("5", "de", [(31.1, -10.0), (31.1, -9.4), (31.3, -9.0)], "", None, False),
]
beschr2 = [("Indischer Ozean", 41.6, -9.0, "meer"), ("Victoriasee", 33.0, -1.0, "meer klein"),
           ("Tanganjikasee", 28.6, -7.4, "meer klein"), ("Njassasee", 33.0, -11.4, "meer klein"),
           ("Deutsch-Ostafrika", 35.0, -6.0, "gross"), ("Britisch-Ostafrika", 37.4, 0.0, ""), ("Belgisch-Kongo", 27.9, -4.6, "gross"),
           ("Nordrhodesien", 28.4, -13.6, ""), ("Portugiesisch-Ostafrika", 39.6, -14.0, ""), ("Rovuma", 37.7, -11.2, "klein")]
orte2 = [("Tanga", *TANGA, "end"), ("Moshi", *MOSHI, "end"), ("Daressalam", *DAR, "start"), ("Tabora", *TABORA, "start"),
         ("Lindi", *LINDI, "start"), ("Kasama", *KASAMA, "end"), ("Abercorn", *ABERCORN, "end")]
ereig2 = [(1, "o1", 39.9, -4.3, "1", "gefecht"), (2, "o2", 40.0, -7.4, "2", "beginn"), (3, "o3", 40.2, -10.9, "3", "gefecht"),
          (4, "o4", 30.4, -10.8, "5", "gefecht"), (5, "o5", 30.6, -8.2, "5", "beginn")]
svg2 = svg_karte(K2, "ko-k2", "Der Feldzug in Ostafrika 1914–1918",
                 "Karte Ostafrikas mit Deutsch-Ostafrika, den Nachbarkolonien und großen Seen: britische Landung bei Tanga 1914, "
                 "alliierte Offensive 1916, Gefecht bei Mahiwa 1917, der schematische Weg der Schutztruppe durch Portugiesisch-Ostafrika "
                 "1917 und 1918 und ihr Zug nach Nordrhodesien bis zur Kapitulation bei Abercorn am 25. November 1918.",
                 land2, seen2, [("ko-dr", DOA2)], [], grenzen(K2, A2, land2_roh), pfeile2, beschr2, orte2, ereig2,
                 ((27.0, -16.6), 200, -16))

html = SEITE.read_text(encoding="utf-8")
for k, svg in (("karte-afrika", svg1), ("karte-ostafrika", svg2)):
    html, z = re.subn(rf"<!-- {k}:anfang -->.*?<!-- {k}:ende -->", lambda m: f"<!-- {k}:anfang -->\n" + svg + f"\n<!-- {k}:ende -->", html, flags=re.S)
    if z != 1: raise SystemExit(f"Marken <!-- {k}:anfang/ende --> fehlen")
SEITE.write_text(html, encoding="utf-8")
print("Karten eingesetzt:", K1.W, "x", K1.H, len(svg1) // 1024, "KB;", K2.W, "x", K2.H, len(svg2) // 1024, "KB")
