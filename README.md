# kaffeeundkommiss.github.io

Startseite der Organisation: https://kaffeeundkommiss.github.io/

Verweist auf die drei Projekte:

- Politik: Übersicht https://kaffeeundkommiss.github.io/politik/ (Ordner `politik/`) mit den Monitoren für CDU/CSU (https://kaffeeundkommiss.github.io/cducsu-monitor/), AfD (https://kaffeeundkommiss.github.io/afd-monitor/), SPD (https://kaffeeundkommiss.github.io/spd-monitor/), Grüne (https://kaffeeundkommiss.github.io/gruene-monitor/), Linke (https://kaffeeundkommiss.github.io/linke-monitor/) und FDP (https://kaffeeundkommiss.github.io/fdp-monitor/) sowie dem Koalitionsrechner (Ordner `politik/koalitionen/`)
- Geschichte: Übersicht https://kaffeeundkommiss.github.io/geschichte/ (Ordner `geschichte/`) mit den Übersichten Einigungskriege 1864–1871 (`geschichte/einigungskriege/`), Kaiserreich 1871–1914 (`geschichte/kaiserreich/`) und Erster Weltkrieg (`geschichte/erster-weltkrieg/`) sowie Feldwebel Luchmann (https://kaffeeundkommiss.github.io/luchmann187071/), Jagdgeschwader Richthofen (https://kaffeeundkommiss.github.io/erster-Weltkrieg/), Ernst Jünger (https://kaffeeundkommiss.github.io/stahlgewitter/) und Bullecourt 1917 (https://kaffeeundkommiss.github.io/bullecourt/)
- Sicherheitspolitik: Übersicht https://kaffeeundkommiss.github.io/sicherheitspolitik/ (Ordner `sicherheitspolitik/`) mit der Übersicht „Die Bundeswehr seit 1955“ (Ordner `sicherheitspolitik/bundeswehr/`, Zeitleiste der Minister wird mit `werkzeuge/minister.py` erzeugt, Symbol `icons/bundeswehr.svg`) sowie Bundeswehr in Afghanistan (https://kaffeeundkommiss.github.io/bundeswehr-Afghanistan-/), in Mali (https://kaffeeundkommiss.github.io/bundeswehr-Mali/) im Kosovo (https://kaffeeundkommiss.github.io/bundeswehr-Kosovo/) in Somalia (https://kaffeeundkommiss.github.io/bundeswehr-somalia/) und die Brigade Litauen (https://kaffeeundkommiss.github.io/bundeswehr-litauen/); Länderumrisse in `icons/afghanistan.svg`, `icons/mali.svg`, `icons/kosovo.svg`, `icons/somalia.svg`, `icons/litauen.svg`

## Aufbau

- `index.html` – die Seite, ohne Skripte
- `style.css` – Farben und Gestaltung wie die Afghanistan-Seite (Tropentarn, heller und dunkler Modus)
- `tarn.svg` – Tarnmuster im Kopf, aus dem Afghanistan-Repo übernommen
- `favicon.svg`, `kk-tasse.svg` – Symbol (schwarze Kaffeetasse auf Weiß); PNG-Fassungen: `favicon-32.png`, `apple-touch-icon.png`, `icons/icon-192.png`, `icons/icon-512.png`
- Startseite in Schwarz-Weiß: Klasse `kk-sw` am `<html>` von `index.html`, Regeln am Ende von `style.css`
