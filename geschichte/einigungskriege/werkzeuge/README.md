# Übersicht Einigungskriege: Werkzeuge

- `kartenbau.py` erzeugt `../karte-daten.js` (SVG-Pfade je Staat, Beschriftungspunkte, Orte).
  Eingaben: `world_1815.geojson` aus [aourednik/historical-basemaps](https://github.com/aourednik/historical-basemaps) (GPL-3.0, lokal als `w1815.json`),
  `ne_10m_admin_0_countries` und `ne_10m_admin_1_states_provinces` von Natural Earth (gemeinfrei, GeoJSON aus nvkelso/natural-earth-vector).
  Aufruf: `pip install shapely && python3 kartenbau.py <geo-ordner>/ ../karte-daten.js`
- Zuordnung der Staaten zu den Zeitschritten und die Legenden stehen in `../karte.js` (Konstante `SCHRITTE`).
- Nachgebaute Änderungen gegenüber 1815: Belgien/Niederlande/Luxemburg (heutige Grenzen), Savoyen an Frankreich (1860),
  Lombardei, Parma, Modena, Toskana, Kirchenstaat-Norden an Italien, Elsass-Lothringen (heutige Départements Bas-Rhin, Haut-Rhin, Moselle).
- Vorschaubild: Eintrag in `werkzeuge/vorschau.json` im Repo-Wurzelordner.

## Kriegsseiten 1864, 1866, 1870/71

- Inhalte (Texte, Belege, Personen, Kartenangaben) stehen in `kriege_daten.py`, die Seiten erzeugt `kriegsseiten.py`
  nach `../1864/`, `../1866/`, `../1870-71/` (je `index.html` und `relief.jpg`). Aussehen in `../kriege.css`.
- Karten: `kriegskarten.py`. Relief aus Terrain Tiles (Terrarium-PNG, s3.amazonaws.com/elevation-tiles-prod; Namensnennung siehe
  tilezen/joerd docs/attribution.md), Grenzen aus `w1815.json`, Land/Seen/Flüsse aus Natural Earth 10m
  (`ne_10m_land`, `ne_10m_lakes`, `ne_10m_rivers_europe`, `ne_10m_rivers_lake_centerlines`, `ne_10m_admin_0_countries`,
  `ne_10m_admin_1_states_provinces`, GeoJSON aus nvkelso/natural-earth-vector).
- Aufruf: `pip install shapely numpy pillow && GEO=<geo-ordner> python3 kriegsseiten.py` (Kacheln werden in `<geo-ordner>/tiles` zwischengespeichert).
- Porträts: fehlt `bild`, zeigt die Seite Initialen. Neue Bilder als `../bilder/<name>.jpg` ablegen und in `BILDER` sowie beim Eintrag eintragen.
