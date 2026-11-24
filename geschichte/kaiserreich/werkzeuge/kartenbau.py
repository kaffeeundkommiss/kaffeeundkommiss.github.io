#!/usr/bin/env python3
"""Erzeugt karte-daten.js (window.KARTE) für die Bündniskarte 1871–1907 auf geschichte/kaiserreich/.

Grundlage: aourednik/historical-basemaps, geojson/world_1880.geojson (GPL-3.0),
https://github.com/aourednik/historical-basemaps . Grenzen von 1880 gelten für alle Schritte (vereinfacht).
world_1880 rechnet den größten Teil Elsass-Lothringens (Metz, Colmar, Mülhausen, Zabern) Frankreich zu.
Deshalb wird die Fläche aus elsass-lothringen.geojson (Départements 57, 67, 68 = Reichsland 1871–1918,
IGN Admin Express über gregoiredavid/france-geojson, Licence Ouverte) allen anderen Ländern abgezogen
und dem Reich zugeschlagen.
Aufruf: python3 werkzeuge/kartenbau.py PFAD/world_1880.geojson
Benötigt: shapely. Projektion Equal Earth, Mittelmeridian 15° Ost (wie erster-weltkrieg/werkzeuge/karte.py).
"""
import json, sys, math, pathlib
import shapely
from shapely.geometry import shape, box, Polygon
from shapely.ops import unary_union

HIER = pathlib.Path(__file__).resolve().parent.parent
LON0, LON1, LAT0, LAT1 = -11, 42, 35, 62   # Ausschnitt, Startwert
# Grober Vorfilter in Grad; der eigentliche Zuschnitt erfolgt nach der Projektion auf den Bildrahmen,
# sonst ragen Landflächen über das Meer-Rechteck hinaus (sichtbar im Vorschaubild).
CLIP = box(LON0 - 6, LAT0 - 6, LON1 + 6, LAT1 + 6)
W = 1000

A1, A2, A3, A4 = 1.340264, -0.081106, 0.000893, 0.003796
M = math.sqrt(3) / 2
def eq(lon, lat):
    lon = lon - 15.0
    l, p = math.radians(lon), math.radians(lat)
    t = math.asin(M * math.sin(p)); t2 = t * t; t6 = t2 * t2 * t2
    x = 2 * math.sqrt(3) * l * math.cos(t) / (3 * (9 * A4 * t6 * t2 + 7 * A3 * t6 + 3 * A2 * t2 + A1))
    y = t * (A4 * t6 * t2 + A3 * t6 + A2 * t2 + A1)
    return x, -y

ecken = [eq(LON0, LAT1), eq(LON1, LAT1), eq(LON0, LAT0), eq(LON1, LAT0), eq(15, LAT1), eq(15, LAT0)]
X0 = min(e[0] for e in ecken); X1 = max(e[0] for e in ecken)
Y0 = min(e[1] for e in ecken); Y1 = max(e[1] for e in ecken)
SK = W / (X1 - X0); H = round((Y1 - Y0) * SK)
def proj(lon, lat):
    x, y = eq(lon, lat)
    return (x - X0) * SK, (y - Y0) * SK

ZUORDNUNG = {
  'Germany': 'DE', 'Austria Hungary': 'AH', 'Russian Empire': 'RU', 'Italy': 'IT', 'France': 'FR',
  'United Kingdom of Great Britain and Ireland': 'GB', 'Ottoman Empire': 'OT', 'Spain': 'ES',
}
LAB = {  # Beschriftungspunkte (Länge, Breite), Startwerte
  'DE': (10.3, 51.3), 'AH': (19.6, 46.6), 'RU': (32, 55), 'IT': (12.8, 42.8), 'FR': (2.4, 46.9),
  'GB': (-2.2, 53.2), 'OT': (31, 39.6), 'ES': (-3.8, 40.2),
}
ORTE = {'Berlin': (13.4, 52.52), 'Wien': (16.37, 48.21), 'St. Petersburg': (30.31, 59.94), 'Rom': (12.5, 41.9),
        'Paris': (2.35, 48.86), 'London': (-0.13, 51.51)}

RAHMEN = None  # box(0, 0, W, H), gesetzt nach Berechnung von H
MIN_PX2 = 15     # kleinere Inseln weglassen (Fläche in Pixel², Startwert)

def polygone(g):
    """Alle Polygone einer Geometrie, auch aus verschachtelten Sammlungen."""
    if g.is_empty:
        return []
    if g.geom_type == 'Polygon':
        return [g]
    if hasattr(g, 'geoms'):
        return [p for t in g.geoms for p in polygone(t)]
    return []  # Linien und Punkte aus dem Zuschnitt

def d_von(g):
    """Grad-Geometrie projizieren, auf den Bildrahmen zuschneiden, als SVG-Pfad ausgeben."""
    g = shapely.transform(g, lambda a: [proj(x, y) for x, y in a]).buffer(0).intersection(RAHMEN)
    out = []
    for p in polygone(g):
        if p.area < MIN_PX2:
            continue
        # Löcher unter der Mindestfläche sind Nahtreste zwischen den beiden Datenquellen
        for r in [p.exterior, *(i for i in p.interiors if Polygon(i).area >= MIN_PX2)]:
            out.append('M' + 'L'.join(f'{x:.1f},{y:.1f}' for x, y in r.coords) + 'Z')
    return ''.join(out)

def main(src):
    global RAHMEN
    RAHMEN = box(0, 0, W, H)
    el = unary_union([shape(f['geometry']) for f in
                      json.loads((HIER / 'werkzeuge' / 'elsass-lothringen.geojson').read_text(encoding='utf-8'))['features']])
    teile = {'DE': [el]}
    for f in json.loads(pathlib.Path(src).read_text(encoding='utf-8'))['features']:
        if not f['geometry']:
            continue
        g = shape(f['geometry']).buffer(0)
        if not g.intersects(CLIP):
            continue
        g = g.intersection(CLIP)
        k = ZUORDNUNG.get(f['properties'].get('NAME'), 'REST')
        if k != 'DE':
            g = g.difference(el)
            if g.is_empty:
                continue
        teile.setdefault(k, []).append(g)
    units = {}
    for k, gs in teile.items():
        g = unary_union(gs).simplify(0.05, preserve_topology=True)
        if k == 'REST':
            # Restflächen einzeln lassen, damit Grenzen sichtbar bleiben
            units[k] = ''.join(d_von(x.simplify(0.05, preserve_topology=True)) for x in gs)
        else:
            units[k] = d_von(g)
    lab = {k: [round(v, 1) for v in proj(*p)] for k, p in LAB.items()}
    orte = {k: [round(v, 1) for v in proj(*p)] for k, p in ORTE.items()}
    js = ('// Erzeugt mit werkzeuge/kartenbau.py, nicht von Hand ändern.\n'
          '// Grenzen: aourednik/historical-basemaps world_1880 (GPL-3.0), für alle Schritte gleich (vereinfacht);\n'
          '// Elsass-Lothringen aus elsass-lothringen.geojson (IGN Admin Express, Licence Ouverte) dem Reich zugeordnet.\n'
          'window.KARTE=' + json.dumps({'W': W, 'H': H, 'units': units, 'lab': lab, 'orte': orte}, separators=(',', ':')) + ';\n')
    (HIER / 'karte-daten.js').write_text(js, encoding='utf-8')
    print('karte-daten.js', len(js) // 1024, 'KB', 'H', H)

if __name__ == '__main__':
    main(sys.argv[1])
