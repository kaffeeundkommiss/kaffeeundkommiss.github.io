# Topografische Karten für die Kriegsseiten 1864, 1866 und 1870/71.
# Aufruf über kriegsseiten.py; erzeugt je Krieg ein Reliefbild (JPG) und liefert das SVG der Karte als Text.
#
# Eingaben (Ordner GEO, siehe README.md):
#   Höhen: Terrain Tiles (Terrarium-PNG) von s3.amazonaws.com/elevation-tiles-prod, werden im Ordner GEO/tiles zwischengespeichert.
#   Grenzen: aourednik/historical-basemaps world_1815.geojson (GPL-3.0) als w1815.json.
#   Gewässer und Land: Natural Earth 10m (gemeinfrei): ne_10m_land, ne_10m_lakes, ne_10m_rivers_europe, ne_10m_rivers_lake_centerlines,
#   ne_10m_admin_1_states_provinces (nur für den Umriss des 1871 abgetretenen Gebiets).
import io, json, math, os, urllib.request, warnings
warnings.filterwarnings("ignore")
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from shapely.geometry import shape, box, mapping
from shapely.ops import unary_union
from shapely.validation import make_valid

GEO = os.environ.get("GEO", "geo")
_cache = {}


def lade(name):
    if name not in _cache:
        _cache[name] = json.load(open(os.path.join(GEO, name)))
    return _cache[name]


# ---------- Höhenmodell ----------
def kachel(z, x, y):
    d = os.path.join(GEO, "tiles", str(z)); os.makedirs(d, exist_ok=True)
    f = os.path.join(d, f"{x}_{y}.png")
    if not os.path.exists(f):
        url = f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
        with urllib.request.urlopen(url, timeout=60) as r:
            open(f, "wb").write(r.read())
    a = np.asarray(Image.open(f).convert("RGB")).astype(np.float32)
    return a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768


def merc(lon, lat, z):
    n = 256 * 2 ** z
    x = (lon + 180) / 360 * n
    lr = np.radians(lat)
    y = (1 - np.log(np.tan(lr) + 1 / np.cos(lr)) / math.pi) / 2 * n
    return x, y


def hoehen(bb, z, lon, lat):
    """Höhe in Metern für Gitter lon/lat (2D) aus Kacheln der Zoomstufe z."""
    x, y = merc(lon, lat, z)
    tx0, tx1 = int(x.min() // 256), int(x.max() // 256)
    ty0, ty1 = int(y.min() // 256), int(y.max() // 256)
    M = np.zeros(((ty1 - ty0 + 1) * 256, (tx1 - tx0 + 1) * 256), np.float32)
    for ty in range(ty0, ty1 + 1):
        for tx in range(tx0, tx1 + 1):
            M[(ty - ty0) * 256:(ty - ty0 + 1) * 256, (tx - tx0) * 256:(tx - tx0 + 1) * 256] = kachel(z, tx, ty)
    px = x - tx0 * 256; py = y - ty0 * 256
    # bilinear
    x0 = np.clip(np.floor(px).astype(int), 0, M.shape[1] - 2); y0 = np.clip(np.floor(py).astype(int), 0, M.shape[0] - 2)
    fx = px - x0; fy = py - y0
    return (M[y0, x0] * (1 - fx) * (1 - fy) + M[y0, x0 + 1] * fx * (1 - fy) + M[y0 + 1, x0] * (1 - fx) * fy + M[y0 + 1, x0 + 1] * fx * fy)


# ---------- Projektion ----------
class Proj:
    def __init__(self, bb, W):
        self.lon0, self.lat0, self.lon1, self.lat1 = bb
        self.k = math.cos(math.radians((self.lat0 + self.lat1) / 2))
        self.W = W
        self.s = W / ((self.lon1 - self.lon0) * self.k)
        self.H = round((self.lat1 - self.lat0) * self.s)

    def xy(self, lon, lat):
        return (lon - self.lon0) * self.k * self.s, (self.lat1 - lat) * self.s

    def km_px(self):
        return self.s / 111.32  # Pixel je Kilometer (Nord-Süd)


def polys(g):
    if g.is_empty: return []
    if g.geom_type == "Polygon": return [g]
    return [q for q in getattr(g, "geoms", []) if q.geom_type == "Polygon"]


def lines(g):
    if g.is_empty: return []
    if g.geom_type == "LineString": return [g]
    if g.geom_type == "MultiLineString": return list(g.geoms)
    return [q for q in getattr(g, "geoms", []) if q.geom_type == "LineString"]


# ---------- Relief ----------
STUFEN = [  # Höhe m, Farbe (gedämpfte Höhenschichten)
    (0, (226, 228, 210)), (100, (222, 223, 200)), (250, (214, 210, 182)), (500, (204, 192, 160)),
    (900, (190, 172, 138)), (1500, (176, 160, 134)), (2200, (205, 200, 192)), (3200, (240, 238, 234))]
MEER = (210, 223, 230)


def relief(p, bb, z, datei, ueberhoehung=2.2):
    W, H = p.W, p.H
    xs = np.linspace(bb[0], bb[2], W); ys = np.linspace(bb[3], bb[1], H)
    lon, lat = np.meshgrid(xs, ys)
    e = hoehen(bb, z, lon, lat)
    e = (e + np.roll(e, 1, 0) + np.roll(e, -1, 0) + np.roll(e, 1, 1) + np.roll(e, -1, 1)) / 5  # leicht glätten
    # Land/Wasser aus Natural Earth
    mask = Image.new("L", (W, H), 0); d = ImageDraw.Draw(mask)
    B = box(*bb).buffer(0.5)
    for f in lade("ne_10m_land.json")["features"]:
        g = make_valid(shape(f["geometry"])).intersection(B)
        for q in polys(g):
            d.polygon([p.xy(*c) for c in q.exterior.coords], fill=255)
            for r in q.interiors: d.polygon([p.xy(*c) for c in r.coords], fill=0)
    for f in lade("ne_10m_lakes.json")["features"]:
        g = make_valid(shape(f["geometry"])).intersection(B)
        for q in polys(g): d.polygon([p.xy(*c) for c in q.exterior.coords], fill=0)
    land = np.asarray(mask) > 127
    # Schummerung (Licht aus Nordwest)
    mpp = 1000 / p.km_px()
    gy, gx = np.gradient(e * ueberhoehung, mpp)   # gy: Zeilen nach Süden
    dzdx, dzdn = gx, -gy
    az, alt = math.radians(315), math.radians(42)
    lx, ly, lz = math.cos(alt) * math.sin(az), math.cos(alt) * math.cos(az), math.sin(alt)
    sh = (-dzdx * lx - dzdn * ly + lz) / np.sqrt(dzdx ** 2 + dzdn ** 2 + 1)
    sh = np.clip(sh, 0, 1)
    flach = math.sin(alt)
    licht = np.clip(1 + (sh - flach) * 1.15, 0.45, 1.25)
    hs = np.array([s[0] for s in STUFEN], np.float32); cs = np.array([s[1] for s in STUFEN], np.float32)
    ec = np.clip(e, 0, hs[-1])
    farbe = np.stack([np.interp(ec, hs, cs[:, i]) for i in range(3)], -1)
    rgb = np.clip(farbe * licht[..., None], 0, 255)
    rgb[~land] = MEER
    Image.fromarray(rgb.astype(np.uint8)).save(datei, quality=84, optimize=True, progressive=True)


# ---------- SVG ----------
def pfad(p, g, B, tol=0.004):
    g = g.intersection(B).simplify(tol)
    out = []
    for q in polys(g):
        for ring in [q.exterior, *q.interiors]:
            pts = [p.xy(*c) for c in ring.coords]
            out.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z")
    return "".join(out)


def linie(p, g, B, tol=0.003):
    g = g.intersection(B).simplify(tol)
    out = []
    for l in lines(g):
        pts = [p.xy(*c) for c in l.coords]
        if len(pts) < 2: continue
        out.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts))
    return "".join(out)


def hb(*names):
    gs = [make_valid(shape(f["geometry"])) for f in lade("w1815.json")["features"] if f["properties"].get("NAME") in names]
    return unary_union(gs)


def ne1(*names):
    return unary_union([make_valid(shape(f["geometry"])) for f in lade("ne_10m_admin_1_states_provinces.json")["features"]
                        if f["properties"]["adm0_a3"] == "FRA" and f["properties"]["name"] in names])


def ne0(*codes):
    a0 = lade("ne_10m_admin_0_countries.json") if os.path.exists(os.path.join(GEO, "ne_10m_admin_0_countries.json")) else None
    return unary_union([make_valid(shape(f["geometry"])) for f in a0["features"] if f["properties"]["ADM0_A3"] in codes])


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;")


def karte(k, ordner, relief_name):
    """k: Kartendefinition aus kriege_daten.py. Gibt SVG-Text zurück und schreibt das Reliefbild."""
    bb = k["bb"]; p = Proj(bb, k.get("W", 1000)); B = box(*bb)
    relief(p, bb, k["zoom"], os.path.join(ordner, relief_name), k.get("ueberhoehung", 2.2))
    o = [f'<svg class="kk-karte" viewBox="0 0 {p.W} {p.H}" role="img" aria-labelledby="karte-titel karte-beschr">']
    o.append(f'<title id="karte-titel">{esc(k["titel"])}</title><desc id="karte-beschr">{esc(k["beschreibung"])}</desc>')
    o.append(f'<image class="kk-relief" href="{relief_name}" x="0" y="0" width="{p.W}" height="{p.H}" preserveAspectRatio="none"/>')
    # Flächen der Kriegsparteien (durchscheinend über dem Relief)
    land = unary_union([make_valid(shape(f["geometry"])) for f in lade("ne_10m_land.json")["features"]
                        if shape(f["geometry"]).intersects(B)])
    o.append('<g class="kk-flaechen">')
    for rolle, g in k["flaechen"]:
        d = pfad(p, g.intersection(land), B)
        if d: o.append(f'<path class="kf r-{rolle}" d="{d}"/>')
    o.append('</g>')
    # Gewässer
    flr = []
    for name in ("ne_10m_rivers_europe.json", "ne_10m_rivers_lake_centerlines.json"):
        for f in lade(name)["features"]:
            sr = f["properties"].get("scalerank", 9)
            if sr is not None and sr > k.get("fluss_rang", 12): continue
            g = shape(f["geometry"])
            if not g.intersects(B): continue
            d = linie(p, g, B)
            if d: flr.append(d)
    o.append(f'<path class="kk-fluss" d="{"".join(flr)}"/>')
    # Grenzen
    o.append('<g class="kk-grenzen">')
    for g in k.get("grenzen", []):
        d = pfad(p, g, B)
        if d: o.append(f'<path d="{d}"/>')
    o.append('</g>')
    for klasse, g in k.get("umrisse", []):
        d = pfad(p, g, B)
        if d: o.append(f'<path class="{klasse}" d="{d}"/>')
    # Bewegungen (schematisch)
    if k.get("pfeile"):
        o.append('<defs>' + ''.join(f'<marker id="kk-spitze-{r}" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="4" markerHeight="4" orient="auto"><path class="sp-{r}" d="M0,0L10,5L0,10z"/></marker>' for r in sorted({x[0] for x in k["pfeile"]})) + '</defs>')
        o.append('<g class="kk-pfeile">')
        for rolle, pts, beschr in k["pfeile"]:
            xy = [p.xy(*c) for c in pts]
            d = "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in xy)
            o.append(f'<path class="pf-{rolle}" d="{d}" marker-end="url(#kk-spitze-{rolle})"/>')
            if beschr:
                x, y = xy[0]
                o.append(f'<text x="{x:.0f}" y="{y-8:.0f}">{esc(beschr)}</text>')
        o.append('</g>')
    # Landschafts- und Flussnamen
    o.append('<g class="kk-landschaft">')
    for t, lon, lat, *rest in k.get("landschaft", []):
        x, y = p.xy(lon, lat); cls = rest[0] if rest else ""
        o.append(f'<text class="{cls}" x="{x:.0f}" y="{y:.0f}">{esc(t)}</text>')
    o.append('</g>')
    # Staatennamen
    o.append('<g class="ek-namen">')
    for t, lon, lat, *rest in k.get("staaten", []):
        x, y = p.xy(lon, lat); cls = rest[0] if rest else ""
        o.append(f'<text class="{cls}" x="{x:.0f}" y="{y:.0f}">{esc(t)}</text>')
    o.append('</g>')
    # Orte
    o.append('<g class="ek-orte">')
    for t, lon, lat, *rest in k.get("orte", []):
        x, y = p.xy(lon, lat); anker = rest[0] if rest else "r"; cls = rest[1] if len(rest) > 1 else ""
        dx, ta = (7, "start") if anker == "r" else (-7, "end")
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.2"/><text class="{cls}" x="{x+dx:.0f}" y="{y+4:.0f}" text-anchor="{ta}">{esc(t)}</text>')
    o.append('</g>')
    # Ereignisse (nummeriert, Liste daneben)
    o.append('<g class="kk-ereignisse">')
    for i, e in enumerate(k["ereignisse"], 1):
        x, y = p.xy(e["lon"], e["lat"])
        dx, dy = e.get("versatz", (0, 0))
        if dx or dy:
            o.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x+dx:.1f}" y2="{y+dy:.1f}"/>')
        o.append(f'<a href="#e{i}"><g class="kk-marke {e.get("art","schlacht")}" transform="translate({x+dx:.1f},{y+dy:.1f})">'
                 f'<circle r="11"/><text y="4.5">{i}</text></g></a>')
    o.append('</g>')
    # Maßstab
    km = k.get("massstab", 50); L = km * p.km_px(); x0, y0 = 16, p.H - 18
    o.append(f'<g class="kk-massstab"><path d="M{x0},{y0}h{L:.1f}M{x0},{y0-5}v5M{x0+L:.1f},{y0-5}v5"/><text x="{x0}" y="{y0-9}">{km} km</text></g>')
    o.append('</svg>')
    return "".join(o)
