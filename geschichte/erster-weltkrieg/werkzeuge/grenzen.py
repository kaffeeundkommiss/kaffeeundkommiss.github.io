#!/usr/bin/env python3
"""Erzeugt grenzen.svg (Europa 1914 und 1920 zum Umschalten) für geschichte/erster-weltkrieg/.

Grundlage: aourednik/historical-basemaps, geojson/world_1914.geojson und world_1920.geojson (GPL-3.0),
https://github.com/aourednik/historical-basemaps . Die Grenzen sind laut Projekt teils Näherungen.
Aufruf: python3 werkzeuge/grenzen.py PFAD/world_1914.geojson PFAD/world_1920.geojson
Benötigt: shapely (pip install shapely). Projektion wie karte.py (Equal Earth, 15° Ost).

Klassen: g-reich (Kaiserreiche 1914), g-neu (neue oder neu gebildete Staaten 1920),
g-de (Deutsches Reich 1920). Alle übrigen Flächen bleiben neutral.
"""
import json, sys, pathlib
from shapely.geometry import shape, box
from karte import proj, geom_d

HIER = pathlib.Path(__file__).resolve().parent.parent
LON0, LON1, LAT0, LAT1 = -10.5, 44, 35, 66   # Ausschnitt, Startwert
CLIP = box(LON0 - 8, LAT0 - 8, LON1 + 8, LAT1 + 6)

KLASSE = {
  1914: {'German Empire': 'g-reich', 'Austro-Hungarian Empire': 'g-reich', 'Russian Empire': 'g-reich',
         'Grand Duchy of Finland': 'g-reich', 'Armenia': 'g-reich', 'Azerbaijan': 'g-reich', 'Georgia': 'g-reich',
         'Ottoman Empire': 'g-reich'},
  1920: {'Germany': 'g-de', 'East Prussia': 'g-de',
         'Poland': 'g-neu', 'Czechoslovakia': 'g-neu', 'Austria': 'g-neu', 'Hungary': 'g-neu', 'Yugoslavia': 'g-neu',
         'Estonia': 'g-neu', 'Latvia': 'g-neu', 'Lithuania': 'g-neu', 'Finland': 'g-neu'},
}
# Beschriftungen: (Text, Länge, Breite)
NAMEN = {
  1914: [('Deutsches Reich', 10.5, 51.6), ('Österreich-Ungarn', 18.5, 47.3), ('Russisches Reich', 34, 55),
         ('Osmanisches Reich', 33, 39.3), ('Frankreich', 2.4, 46.8), ('Italien', 12.6, 43.2),
         ('Serbien', 21, 43.6), ('Rumänien', 25.2, 45.6), ('Bulgarien', 25.4, 42.6)],
  1920: [('Deutsches Reich', 10.2, 51.2), ('Polen', 20.5, 52.3), ('Tschecho-slowakei', 16.4, 50.1),
         ('Österreich', 14.2, 47.3), ('Ungarn', 19.3, 47), ('Königreich SHS', 18.8, 44.2),
         ('Rumänien', 25.2, 46), ('Litauen', 24, 55.4), ('Lettland', 25.5, 56.9), ('Estland', 25.8, 58.7),
         ('Finnland', 26.5, 63), ('Frankreich', 2.4, 46.8), ('Italien', 12.6, 43.2),
         ('Osmanisches Reich', 33, 39.3), ('Sowjet-russland', 38, 56)],
}

# Auf schmalen Bildschirmen ausgeblendet (zu eng)
KLEIN = {'Österreich', 'Ungarn', 'Tschecho-slowakei', 'Estland', 'Lettland', 'Litauen', 'Serbien', 'Bulgarien', 'Königreich SHS'}

def schicht(src, jahr):
    teile = []
    for f in json.load(open(src))['features']:
        if not f['geometry']:
            continue
        name = f['properties'].get('NAME')
        g = shape(f['geometry']).buffer(0)
        if not g.intersects(CLIP):
            continue
        g = g.intersection(CLIP).simplify(0.04, preserve_topology=True)
        if g.is_empty or g.geom_type not in ('Polygon', 'MultiPolygon'):
            if g.geom_type == 'GeometryCollection':
                from shapely.geometry import MultiPolygon
                g = MultiPolygon([p for p in g.geoms if p.geom_type == 'Polygon'])
            else:
                continue
        d = geom_d(g)
        if not d:
            continue
        k = KLASSE[jahr].get(name, '')
        teile.append((1 if k else 0, f'<path{f" class=\"{k}\"" if k else ""} d="{d}"/>'))
    teile.sort(key=lambda t: t[0])
    txt = []
    for t, lon, lat in NAMEN[jahr]:
        x, y = proj(lon, lat)
        zeilen = t.split('-') if t.endswith(('slowakei', 'russland')) else [t]
        if len(zeilen) == 2:
            zeilen = [zeilen[0] + '-', zeilen[1]]
        tsp = ''.join(f'<tspan x="{x:.1f}" dy="{0 if i == 0 else 1.1}em">{z}</tspan>' for i, z in enumerate(zeilen))
        kl = ' class="klein"' if t in KLEIN else ''
        txt.append(f'<text{kl} x="{x:.1f}" y="{y:.1f}">{tsp}</text>')
    return ''.join(t[1] for t in teile) + '<g class="g-namen" aria-hidden="true">' + ''.join(txt) + '</g>'

def main(s14, s20):
    e = [proj(LON0, LAT1), proj(LON1, LAT1), proj(LON0, LAT0), proj(LON1, LAT0)]
    ex = [p[0] for p in e]; ey = [p[1] for p in e]
    vb = f'{min(ex):.0f} {min(ey):.0f} {max(ex)-min(ex):.0f} {max(ey)-min(ey):.0f}'
    svg = (f'<svg id="grenz-karte" viewBox="{vb}" role="img" aria-labelledby="grenz-karte-titel" xmlns="http://www.w3.org/2000/svg">'
           f'<title id="grenz-karte-titel">Europakarte mit den Grenzen von 1914 oder 1920, je nach gewähltem Jahr</title>'
           f'<rect class="meer" x="{min(ex)-50:.0f}" y="{min(ey)-50:.0f}" width="{max(ex)-min(ex)+100:.0f}" height="{max(ey)-min(ey)+100:.0f}"/>'
           f'<g data-jahr="1914">{schicht(s14, 1914)}</g>'
           f'<g data-jahr="1920" hidden>{schicht(s20, 1920)}</g></svg>')
    (HIER / 'grenzen.svg').write_text(svg)
    print('grenzen.svg', len(svg) // 1024, 'KB')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
