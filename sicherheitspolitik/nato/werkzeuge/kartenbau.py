#!/usr/bin/env python3
"""Erzeugt karte-daten.js (window.KARTE) für die Karte der NATO-Erweiterungen auf sicherheitspolitik/nato/.

Grundlage: aourednik/historical-basemaps (GPL-3.0), https://github.com/aourednik/historical-basemaps
  - world_1960.geojson für die Schritte 1949–1982 (Bundesrepublik und DDR getrennt)
  - world_2010.geojson für die Schritte ab 1990 (Grenzen von 2010, Kosovo nicht getrennt von Serbien)
Aufruf: python3 werkzeuge/kartenbau.py PFAD/world_1960.geojson PFAD/world_2010.geojson
Benötigt: shapely. Projektion Equal Earth, Mittelmeridian 15° Ost (wie geschichte/kaiserreich/werkzeuge/kartenbau.py).
"""
import json, sys, math, pathlib
import shapely
from shapely.geometry import shape, box, Polygon
from shapely.ops import unary_union

HIER = pathlib.Path(__file__).resolve().parent.parent
LON0, LON1, LAT0, LAT1 = -25, 45, 34, 71   # Ausschnitt, Startwert
CLIP = box(LON0 - 8, LAT0 - 6, LON1 + 8, LAT1 + 6)
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
RAHMEN = box(0, 0, W, H)
MIN_PX2 = 12  # kleinere Inseln weglassen (Fläche in Pixel², Startwert)

# Name in historical-basemaps -> Kürzel. Alles andere wird einzeln als Nichtmitglied gezeichnet.
KUERZEL = {
  'Belgium': 'BE', 'Denmark': 'DK', 'France': 'FR', 'Iceland': 'IS', 'Italy': 'IT', 'Luxembourg': 'LU',
  'Netherlands': 'NL', 'Norway': 'NO', 'Portugal': 'PT', 'United Kingdom': 'GB', 'Greece': 'GR', 'Turkey': 'TR',
  'West Germany': 'DE', 'Germany': 'DE', 'East Germany': 'DDR', 'Spain': 'ES', 'Poland': 'PL',
  'Czech Republic': 'CZ', 'Hungary': 'HU', 'Bulgaria': 'BG', 'Estonia': 'EE', 'Latvia': 'LV', 'Lithuania': 'LT',
  'Romania': 'RO', 'Slovakia': 'SK', 'Slovenia': 'SI', 'Albania': 'AL', 'Croatia': 'HR', 'Montenegro': 'ME',
  'Macedonia': 'MK', 'Finland': 'FI', 'Sweden': 'SE',
}
LAB = {  # Beschriftungspunkte (Länge, Breite), Startwerte
  'IS': (-18.5, 64.9), 'NO': (9.5, 61.5), 'SE': (15.5, 63.0), 'FI': (26.5, 63.5), 'GB': (-1.8, 53.0),
  'FR': (2.4, 46.8), 'ES': (-3.6, 40.0), 'PT': (-8.2, 39.6), 'IT': (12.6, 42.6), 'DE': (10.2, 51.0),
  'PL': (19.3, 52.1), 'TR': (34.0, 39.0), 'GR': (22.0, 39.5), 'RO': (25.0, 45.9),
}
NAMEN = {'IS': 'Island', 'NO': 'Norwegen', 'SE': 'Schweden', 'FI': 'Finnland', 'GB': 'Großbritannien',
         'FR': 'Frankreich', 'ES': 'Spanien', 'PT': 'Portugal', 'IT': 'Italien', 'DE': 'Deutschland',
         'PL': 'Polen', 'TR': 'Türkei', 'GR': 'Griechenland', 'RO': 'Rumänien'}

def polygone(g):
    if g.is_empty: return []
    if g.geom_type == 'Polygon': return [g]
    if hasattr(g, 'geoms'): return [p for t in g.geoms for p in polygone(t)]
    return []

def d_von(g):
    g = shapely.transform(g, lambda a: [proj(x, y) for x, y in a]).buffer(0).intersection(RAHMEN)
    out = []
    for p in polygone(g):
        if p.area < MIN_PX2: continue
        for r in [p.exterior, *(i for i in p.interiors if Polygon(i).area >= MIN_PX2)]:
            out.append('M' + 'L'.join(f'{x:.1f},{y:.1f}' for x, y in r.coords) + 'Z')
    return ''.join(out)

def karte(src):
    teile, rest = {}, []
    for f in json.loads(pathlib.Path(src).read_text(encoding='utf-8'))['features']:
        if not f['geometry']: continue
        g = shape(f['geometry']).buffer(0)
        if not g.intersects(CLIP): continue
        g = g.intersection(CLIP)
        k = KUERZEL.get(f['properties'].get('NAME'))
        if k: teile.setdefault(k, []).append(g)
        else: rest.append(g)
    units = {k: d_von(unary_union(gs).simplify(0.04, preserve_topology=True)) for k, gs in teile.items()}
    units['REST'] = ''.join(d_von(x.simplify(0.04, preserve_topology=True)) for x in rest)
    return {k: v for k, v in units.items() if v}

def main(a, b):
    daten = {'W': W, 'H': H, 'karten': {'a': karte(a), 'b': karte(b)},
             'lab': {k: [round(v, 1) for v in proj(*p)] for k, p in LAB.items()}, 'namen': NAMEN}
    js = ('// Erzeugt mit werkzeuge/kartenbau.py, nicht von Hand ändern.\n'
          '// Grenzen: aourednik/historical-basemaps world_1960 (Schritte bis 1982) und world_2010 (ab 1990), GPL-3.0.\n'
          'window.KARTE=' + json.dumps(daten, separators=(',', ':'), ensure_ascii=False) + ';\n')
    (HIER / 'karte-daten.js').write_text(js, encoding='utf-8')
    print('karte-daten.js', len(js) // 1024, 'KB', 'H', H, sorted(daten['karten']['a']), sorted(daten['karten']['b']))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
