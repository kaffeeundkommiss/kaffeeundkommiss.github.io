# Übersicht Einigungskriege: Werkzeuge

- `kartenbau.py` erzeugt `../karte-daten.js` (SVG-Pfade je Staat, Beschriftungspunkte, Orte).
  Eingaben: `world_1815.geojson` aus [aourednik/historical-basemaps](https://github.com/aourednik/historical-basemaps) (GPL-3.0, lokal als `w1815.json`),
  `ne_10m_admin_0_countries` und `ne_10m_admin_1_states_provinces` von Natural Earth (gemeinfrei, GeoJSON aus nvkelso/natural-earth-vector).
  Aufruf: `pip install shapely && python3 kartenbau.py <geo-ordner>/ ../karte-daten.js`
- Zuordnung der Staaten zu den Zeitschritten und die Legenden stehen in `../karte.js` (Konstante `SCHRITTE`).
- Nachgebaute Änderungen gegenüber 1815: Belgien/Niederlande/Luxemburg (heutige Grenzen), Savoyen an Frankreich (1860),
  Lombardei, Parma, Modena, Toskana, Kirchenstaat-Norden an Italien, Elsass-Lothringen (heutige Départements Bas-Rhin, Haut-Rhin, Moselle).
- Vorschaubild: Eintrag in `werkzeuge/vorschau.json` im Repo-Wurzelordner.
