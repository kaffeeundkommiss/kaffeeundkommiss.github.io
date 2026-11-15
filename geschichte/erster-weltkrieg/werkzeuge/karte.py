#!/usr/bin/env python3
"""Erzeugt karte.svg (Weltkarte mit Grenzen von 1914) für geschichte/erster-weltkrieg/.

Grundlage: aourednik/historical-basemaps, geojson/world_1914.geojson (GPL-3.0),
https://github.com/aourednik/historical-basemaps . Die Grenzen sind laut Projekt teils Näherungen.
Aufruf: python3 werkzeuge/karte.py PFAD/world_1914.geojson
Benötigt: shapely (pip install shapely).

Jede Fläche erhält data-k (Kürzel des Staates, dem sie 1914 zugeordnet ist) und bei Kolonien,
Dominions und abhängigen Gebieten die Klasse "kol". Die Farben je Datum setzt seite.js.
"""
import json, math, sys, pathlib
from shapely.geometry import shape, mapping
from shapely.ops import transform

HIER = pathlib.Path(__file__).resolve().parent.parent

# Zuordnung NAME (Datensatz) -> (Kürzel, Kolonie?). Nicht aufgeführte Flächen gelten als nicht beteiligt.
# Korrekturen gegenüber dem Datensatz sind mit "Korr." markiert.
Z = {
  'German Empire': ('DE', 0),
  'German E. Africa (Tanganyika)': ('DE', 1), 'German South-West Africa': ('DE', 1),
  'Kamerun': ('DE', 1), 'Togoland': ('DE', 1), 'Samoa': ('DE', 1),
  'Austro-Hungarian Empire': ('AH', 0),
  'Ottoman Empire': ('OS', 0),
  'Bulgaria': ('BG', 0),
  'Serbia': ('RS', 0), 'Montenegro': ('ME', 0),
  'Russian Empire': ('RU', 0), 'Grand Duchy of Finland': ('RU', 0), 'Sakhalin (RU)': ('RU', 0),
  'Armenia': ('RU', 0), 'Azerbaijan': ('RU', 0), 'Georgia': ('RU', 0),   # Korr.: 1914 Teil des Russischen Reichs
  'France': ('FR', 0),
  'Algeria': ('FR', 1), 'Djibouti': ('FR', 1), 'French Equatorial Africa': ('FR', 1), 'French West Africa': ('FR', 1),
  'French Indochina': ('FR', 1), 'Madagascar (France)': ('FR', 1), 'French Guiana': ('FR', 1),
  'Guadeloupe': ('FR', 1), 'Martinique': ('FR', 1), 'Wallis and Futuna Islands': ('FR', 1),
  'Saint Barthelemy': ('FR', 1), 'Saint Martin': ('FR', 1),
  'Morocco': ('FR', 1), 'Tunisia': ('FR', 1),   # Korr.: französische Protektorate (1912 bzw. 1881)
  'Belgium': ('BE', 0), 'Belgian Congo': ('BE', 1),
  'United Kingdom of Great Britain and Ireland': ('GB', 0),
  'Canada': ('GB', 1), 'Australia': ('GB', 1), 'New Zealand': ('GB', 1), 'South Africa': ('GB', 1),
  'British Raj': ('GB', 1), 'Anglo-Egyptian Sudan': ('GB', 1), 'Botswana': ('GB', 1),
  'British East Africa': ('GB', 1), 'British Protectorate': ('GB', 1), 'British Somaliland': ('GB', 1),
  'Egypt': ('GB', 1), 'Gold Coast': ('GB', 1), 'Malawi': ('GB', 1), 'Nigeria': ('GB', 1),
  'Rhodesia': ('GB', 1), 'Hong Kong': ('GB', 1),
  # Korr.: britische Kolonien, Protektorate oder Dominions, im Datensatz als eigene Einheit geführt
  'Uganda': ('GB', 1), 'Ceylon': ('GB', 1), 'Malaya': ('GB', 1), 'Malta': ('GB', 1),
  'Gambia, The': ('GB', 1), 'Sierra Leone': ('GB', 1), 'Belize': ('GB', 1), 'Guyana': ('GB', 1),
  'Fiji': ('GB', 1), 'Brunei': ('GB', 1), 'Swaziland': ('GB', 1), 'Lesotho': ('GB', 1),
  'Anguilla': ('GB', 1), 'Antigua and Barbuda': ('GB', 1), 'Barbados': ('GB', 1), 'Dominica': ('GB', 1),
  'Grenada': ('GB', 1), 'Montserrat': ('GB', 1), 'Saint Kitts and Nevis': ('GB', 1), 'Saint Lucia': ('GB', 1),
  'Saint Vincent and the Grenadines': ('GB', 1), 'Niue': ('GB', 1), 'Tonga': ('GB', 1), 'Kuwait': ('GB', 1),
  'Papua New Guinea': ('GB', 1),   # vereinfacht: Nordosten war bis 1914 deutsch (Kaiser-Wilhelmsland)
  'Empire of Japan': ('JP', 0),
  'Kingdom of Italy': ('IT', 0), 'Libya': ('IT', 1), 'Eritrea': ('IT', 1), 'Italian Somaliland': ('IT', 1),
  'Portugal': ('PT', 0), 'Angola': ('PT', 1), 'Mozambique': ('PT', 1), 'Portuguese Guinea': ('PT', 1),
  'Romania': ('RO', 0),
  'United States': ('US', 0), 'Philippines': ('US', 1), 'Puerto Rico': ('US', 1), 'American Samoa': ('US', 1),
  'Greece': ('GR', 0),
  'Manchu Empire': ('CN', 0), 'Xinjiang': ('CN', 0),   # Korr.: seit 1912 Republik China
  'Brazil': ('BR', 0), 'Rattanakosin Kingdom': ('SI', 0), 'Liberia': ('LR', 0),
  'Cuba': ('CU', 0), 'Panama': ('PA', 0), 'Guatemala': ('GT', 0), 'Nicaragua': ('NI', 0),
  'Costa Rica': ('CR', 0), 'Haiti': ('HT', 0), 'Honduras': ('HN', 0),
}

# Equal-Earth-Projektion (Šavrič, Patterson, Jenny 2018), Mittelmeridian 15° Ost
A1, A2, A3, A4 = 1.340264, -0.081106, 0.000893, 0.003796
M = math.sqrt(3) / 2
L0 = 15.0
S = 160.0  # Pixel je Einheit

def proj(lon, lat):
    lon = (lon - L0 + 180) % 360 - 180
    l, p = math.radians(lon), math.radians(lat)
    t = math.asin(M * math.sin(p)); t2 = t * t; t6 = t2 * t2 * t2
    x = 2 * math.sqrt(3) * l * math.cos(t) / (3 * (9 * A4 * t6 * t2 + 7 * A3 * t6 + 3 * A2 * t2 + A1))
    y = t * (A4 * t6 * t2 + A3 * t6 + A2 * t2 + A1)
    return x * S, -y * S

def ring_d(coords):
    pts = [proj(x, y) for x, y in coords]
    out, last = [], None
    for i, (x, y) in enumerate(pts):
        if last is not None and abs(x - last[0]) > 300:  # Datumsgrenze: Ring auftrennen
            out.append('M')
        last = (x, y)
        out.append(f'{x:.1f},{y:.1f}')
    s = 'M' + ' '.join(out).replace(' M ', 'M')
    s = s.replace('MM', 'M')
    return s + 'Z'

def geom_d(g):
    polys = [g] if g.geom_type == 'Polygon' else list(g.geoms)
    parts = []
    for p in polys:
        if p.area < 0.02:   # Kleinstinseln (Quadratgrad) weglassen, Startwert
            continue
        for r in [p.exterior, *p.interiors]:
            parts.append(ring_d(list(r.coords)))
    return ''.join(parts)

def main(src):
    d = json.load(open(src))
    rows, unbekannt = [], set()
    for f in d['features']:
        if not f['geometry']:
            continue
        name = f['properties'].get('NAME')
        g = shape(f['geometry']).buffer(0)
        g = g.simplify(0.06, preserve_topology=True)
        if g.is_empty:
            continue
        dd = geom_d(g)
        if not dd:
            continue
        k, kol = Z.get(name, ('', 0))
        if name and name not in Z:
            unbekannt.add(name)
        attr = f' data-k="{k}"' if k else ''
        cls = ' class="kol"' if kol else ''
        title = f'<title>{name}</title>' if name else ''
        rows.append((0 if not k else (1 if kol else 2), f'<path{attr}{cls} d="{dd}">{title}</path>'))
    rows.sort(key=lambda r: r[0])
    # Rahmen der ganzen Welt (Kartenrand)
    rand = []
    for lat in range(-90, 91, 5): rand.append(proj(L0 - 180 + 1e-9, lat))
    for lat in range(90, -91, -5): rand.append(proj(L0 + 180 - 1e-9, lat))
    rand_d = 'M' + ' '.join(f'{x:.1f},{y:.1f}' for x, y in rand) + 'Z'
    xs = [p[0] for p in rand]; ys = [p[1] for p in rand]
    y0, y1 = proj(L0, 84)[1], proj(L0, -57)[1]   # Ausschnitt 84° N bis 57° S (ohne Antarktis)
    vb = f'{min(xs):.0f} {y0:.0f} {max(xs)-min(xs):.0f} {y1-y0:.0f}'
    e = [proj(-11, 64), proj(50, 64), proj(-11, 30), proj(50, 30)]   # Ausschnitt Europa
    ex = [p[0] for p in e]; ey = [p[1] for p in e]
    eu = f'{min(ex):.0f} {min(ey):.0f} {max(ex)-min(ex):.0f} {max(ey)-min(ey):.0f}'
    svg = (f'<svg id="wk-karte" viewBox="{vb}" data-welt="{vb}" data-europa="{eu}" role="img" aria-labelledby="wk-karte-titel" xmlns="http://www.w3.org/2000/svg">'
           f'<title id="wk-karte-titel">Weltkarte mit den Grenzen von 1914, eingefärbt nach Kriegsbeteiligung zum gewählten Datum</title>'
           f'<path class="meer" d="{rand_d}"/>'
           + ''.join(r[1] for r in rows) + '</svg>')
    (HIER / 'karte.svg').write_text(svg)
    print('karte.svg', len(svg) // 1024, 'KB; ohne Zuordnung:', ', '.join(sorted(unbekannt)))

if __name__ == '__main__':
    main(sys.argv[1])
