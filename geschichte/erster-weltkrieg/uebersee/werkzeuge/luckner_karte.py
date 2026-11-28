#!/usr/bin/env python3
"""Zwei Karten für geschichte/erster-weltkrieg/uebersee/luckner/index.html.

Karte „Kaperfahrt“ (Weser bis Mopelia, Dezember 1916 bis August 1917) zwischen <!-- karte-fahrt:anfang/ende -->,
Karte „Südsee“ (nach dem Schiffbruch, August bis Dezember 1917) zwischen <!-- karte-suedsee:anfang/ende -->.
Grundlage: Natural Earth ne_50m_land (gemeinfrei, GeoJSON aus nvkelso/natural-earth-vector).
Aufruf:  pip install shapely && python3 luckner_karte.py <geo-ordner>/   (mit land.json)

Alle Kurse sind schematisch: Die Quellen nennen Daten und Orte, aber kaum Positionen auf See.
Die Südseekarte reicht über die Datumsgrenze; östliche Längen werden dort um 360 Grad verschoben.
Kartenklasse und SVG-Aufbau wie kolonien_karte.py.
"""
import json, math, sys, re, pathlib, warnings
warnings.filterwarnings("ignore")
from shapely.geometry import shape, box
from shapely.ops import unary_union, transform
from shapely.affinity import translate
from shapely.validation import make_valid

G = sys.argv[1] if len(sys.argv) > 1 else "./"
SEITE = pathlib.Path(__file__).resolve().parent.parent / "luckner" / "index.html"
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
    t = [f'<svg class="kk-karte lu-karte" viewBox="0 0 {K.W} {K.H}" role="img" aria-labelledby="{kennung}-titel {kennung}-beschr">'
         f'<title id="{kennung}-titel">{titel}</title><desc id="{kennung}-beschr">{beschr}</desc>',
         f'<rect class="lu-meer" x="0" y="0" width="{K.W}" height="{K.H}"/>',
         f'<path class="lu-land" d="{K.pfad(land)}"/>',
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


# ---------- Karte 1: die Kaperfahrt, Dezember 1916 bis August 1917 ----------
K1 = Karte(plattkarte(15), [(-168, 68), (22, -62)])
land1 = land_in(K1, [(box(-180, -70, 30, 75), 0)])
WESER, ISLAND_SO, RIO, KAP_HOORN, MOPELIA = (8.3, 53.7), (-9.0, 61.0), (-43.2, -22.9), (-67.3, -55.98), (-153.9, -16.8)
pfeile1 = [  # (Schritt, Seite, Punkte, Text, Textort, gestrichelt)
    ("1", "de", [WESER, (5.0, 57.5), (1.0, 61.5), (-6.0, 62.3), (-14.0, 59.5), (-22.0, 52.0), (-26.0, 42.0)],
     "Durchbruch der Blockade", (-32.0, 60.0), False),
    ("2", "de", [(-26.0, 42.0), (-27.0, 30.0), (-29.0, 15.0), (-30.0, 3.0), (-29.0, -8.0), (-27.0, -18.0)],
     "Kaperkrieg im Atlantik", (-24.0, 22.0), False),
    ("2", "gb", [(-27.0, -18.0), (-34.0, -21.0), (-41.5, -22.6)], "Cambronne", (-35.0, -27.5), True),
    ("3", "de", [(-27.0, -18.0), (-36.0, -38.0), (-52.0, -54.0), (-67.0, -59.5), (-80.0, -55.0), (-82.0, -42.0)],
     "um Kap Hoorn", (-64.0, -51.0), False),
    ("4", "de", [(-82.0, -42.0), (-86.0, -26.0), (-98.0, -8.0), (-120.0, 1.0), (-140.0, 2.0)],
     "", None, False),
    ("5", "de", [(-140.0, 2.0), (-150.0, -4.0), (-153.0, -12.0), (-153.7, -15.8)], "nach Mopelia", (-149.0, -9.5), False),
]
beschr1 = [("Atlantischer Ozean", -42.0, 30.0, "meer"), ("Pazifischer Ozean", -128.0, -30.0, "meer"),
           ("Europa", 12.0, 48.0, "gross"), ("Afrika", 12.0, 8.0, "gross"), ("Nordamerika", -104.0, 45.0, "gross"),
           ("Südamerika", -64.0, -12.0, "gross")]
orte1 = [("Weser", *WESER, "start"), ("Rio de Janeiro", *RIO, "end"), ("Kap Hoorn", *KAP_HOORN, "start"),
         ("Mopelia", *MOPELIA, "end")]
ereig1 = [(1, "f1", -12.0, 57.0, "1", "gefecht"), (2, "f2", -33.0, 8.0, "2", "gefecht"), (3, "f3", -29.0, -24.0, "2", "beginn"),
          (4, "f4", -73.0, -60.0, "3", "beginn"), (5, "f5", -118.0, 6.0, "4", "gefecht"), (6, "f6", -158.0, -20.0, "5", "beginn")]
svg1 = svg_karte(K1, "lu-k1", "Die Kaperfahrt der Seeadler 1916 und 1917",
                 "Karte des Atlantiks und des Ostpazifiks mit dem schematischen Kurs der Seeadler: von der Weser im Dezember 1916 "
                 "nördlich um Schottland und südöstlich an Island vorbei in den Atlantik, Kaperungen im Mittelatlantik von Januar bis "
                 "März 1917, Freilassung der Gefangenen auf der Cambronne, um Kap Hoorn in den Pazifik, drei amerikanische Segler im "
                 "Juni und Juli 1917 und der Schiffbruch vor dem Atoll Mopelia am 2. August 1917.",
                 land1, pfeile1, beschr1, orte1, ereig1, ((-160.0, -55.0), 2000, -40))

# ---------- Karte 2: nach dem Schiffbruch, August bis Dezember 1917 ----------
O = lambda lon: lon - 360 if lon > 0 else lon      # östliche Längen hinter die Datumsgrenze schieben
K2 = Karte(plattkarte(24), [(O(164.0), -9.0), (-104.0, -42.5)])
land2 = land_in(K2, [(box(160, -50, 180, 0), -360), (box(-180, -50, -95, 0), 0)])
ATIU, RAROTONGA, WAKAYA = (-158.1, -20.0), (-159.78, -21.23), (O(179.0), -17.65)
AUCKLAND, MERCURY, CURTIS, PAGO, OSTER = (O(174.95), -36.81), (O(175.93), -36.63), (-178.56, -30.54), (-170.7, -14.28), (-109.35, -27.12)
pfeile2 = [
    ("2", "de", [(-154.4, -17.2), (-156.4, -18.8), (ATIU[0] + 0.3, ATIU[1] + 0.2)], "Kronprinzessin Cecilie", (-160.0, -24.2), False),
    ("2", "de", [ATIU, (RAROTONGA[0] + 0.2, RAROTONGA[1] + 0.3), (-166.0, -20.6), (-174.0, -19.6), (WAKAYA[0] + 0.6, WAKAYA[1] - 0.1)],
     "", None, False),
    ("3", "de", [(-153.2, -17.4), (-140.0, -22.0), (-124.0, -25.6), (OSTER[0] - 0.8, OSTER[1])], "Fortuna", (-132.0, -21.0), False),
    ("3", "gb", [(-154.6, -16.4), (-162.0, -15.2), (PAGO[0] + 0.6, PAGO[1])], "Kapitän Smith", (-163.0, -12.2), False),
    ("4", "gb", [(WAKAYA[0], WAKAYA[1] - 0.6), (O(178.5), -26.0), (O(175.4), -35.6)], "als Gefangene", (O(168.6), -27.0), True),
    ("5", "de", [(AUCKLAND[0] + 0.4, AUCKLAND[1]), MERCURY, (O(178.5), -34.0), (-179.0, -31.0)], "Moa", (-177.0, -34.3), False),
    ("5", "gb", [(-178.0, -30.2), (O(179.5), -33.0), (O(176.0), -36.2)], "zurück", (O(174.6), -31.8), True),
]
beschr2 = [("Pazifischer Ozean", -135.0, -34.0, "meer"), ("Cookinseln", -159.0, -18.0, "klein"), ("Fidschi", O(178.2), -15.2, "klein"),
           ("Neuseeland", O(176.5), -41.4, "klein"), ("Kermadecinseln", -177.6, -29.0, "klein"), ("Gesellschaftsinseln", -150.5, -14.0, "klein")]
orte2 = [("Mopelia", -153.9, -16.8, "start"), ("Atiu", *ATIU, "start"), ("Rarotonga", *RAROTONGA, "end"), ("Wakaya", *WAKAYA, "end"),
         ("Motuihe", *AUCKLAND, "end"), ("Curtis-Insel", *CURTIS, "start"), ("Pago Pago", *PAGO, "start"), ("Osterinsel", *OSTER, "end")]
ereig2 = [(1, "s1", -151.6, -18.4, "1", "gefecht"), (2, "s2", O(177.4), -18.6, "2", "beginn"), (3, "s3", -111.6, -29.4, "3", "beginn"),
          (4, "s4", O(171.4), -34.6, "4", "beginn"), (5, "s5", -176.6, -31.6, "5", "gefecht")]
svg2 = svg_karte(K2, "lu-k2", "Nach dem Schiffbruch: Südsee 1917",
                 "Karte des Südpazifiks von Neuseeland und Fidschi bis zur Osterinsel: das Atoll Mopelia, die Fahrt Luckners im offenen "
                 "Boot über die Cookinseln nach Wakaya in Fidschi, die Fahrt der übrigen Besatzung auf der Fortuna zur Osterinsel, "
                 "Kapitän Smiths Bootsfahrt nach Pago Pago, die Gefangenschaft auf Motuihe bei Auckland und die Flucht mit der Moa zu den "
                 "Kermadecinseln im Dezember 1917.",
                 land2, pfeile2, beschr2, orte2, ereig2, ((-125.0, -39.0), 1000, -38))

html = SEITE.read_text(encoding="utf-8")
for k, svg in (("karte-fahrt", svg1), ("karte-suedsee", svg2)):
    html, z = re.subn(rf"<!-- {k}:anfang -->.*?<!-- {k}:ende -->", lambda m: f"<!-- {k}:anfang -->\n" + svg + f"\n<!-- {k}:ende -->", html, flags=re.S)
    if z != 1: raise SystemExit(f"Marken <!-- {k}:anfang/ende --> fehlen")
SEITE.write_text(html, encoding="utf-8")
print("Karten eingesetzt:", K1.W, "x", K1.H, len(svg1) // 1024, "KB;", K2.W, "x", K2.H, len(svg2) // 1024, "KB")
