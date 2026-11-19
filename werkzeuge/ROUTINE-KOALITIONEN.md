# Routine: Koalitionsrechner wöchentlich aktualisieren

Repo: `kaffeeundkommiss/kaffeeundkommiss.github.io`, Seite `politik/koalitionen/`.
Die Seite holt beim Aufruf live die neuesten Umfragen von dawum.de. Diese Routine sichert den
Stand in `data.json` (Rückfall, falls dawum nicht antwortet) und pflegt die Angaben, die sich
nicht automatisch ergeben: Wahltermine, letzte Wahl und bisherige Regierungen.

## Schritte

1. **Umfragen übernehmen.** Im Repo-Root:
   ```
   python3 werkzeuge/koalitionen_update.py
   ```
   Ist `api.dawum.de` aus der Umgebung nicht erreichbar, die Datei
   `https://api.dawum.de/newest_surveys.json` anders abrufen (z. B. per Firecrawl, rawHtml, Inhalt
   des `<pre>`-Elements), lokal speichern und `--datei <pfad>` anhängen.
   Meldung „Keine neuen Umfragen“ ist kein Fehler.

2. **Neue Regierungen eintragen.** Prüfe per Web-Suche mit zwei unabhängigen Quellen
   (z. B. Landesregierung/Staatskanzlei und tagesschau/dpa), ob seit `historie_stand` irgendwo eine
   neue Landesregierung oder Bundesregierung vereidigt wurde. Falls ja, die Parteienkombination
   (dawum-Kürzel, z. B. `["SPD", "Linke", "Grüne"]`) an `historie` des Parlaments anhängen, wenn sie
   dort noch nicht steht. Laufende Koalitionsverhandlungen zählen nicht, erst die vereidigte
   Regierung. Danach `historie_stand` auf das heutige Datum setzen.
   Offene Fälle Stand 19.11.2026: Berlin (Linke, Grüne, SPD verhandeln seit November),
   Sachsen-Anhalt (Regierung offen, Wahl des Ministerpräsidenten für Mitte Dezember geplant).
   Mecklenburg-Vorpommern (SPD, Linke, Grüne) ist seit 19.11.2026 eingetragen.

3. **Gelaufene Wahl.** Liegt der Termin eines Parlaments in der Vergangenheit und steht das
   amtliche Ergebnis fest: `letzte_wahl` auf den Wahltag setzen (alte Umfragen fallen damit
   automatisch heraus), `wahltermin` und `sortierung` auf die nächste Wahl stellen
   (z. B. `"voraussichtlich Frühjahr 2032"`, `"2032-03"`). Quellen: Bundesrat (Termine der
   Landtagswahlen) und Bundeswahlleiterin (Künftige Wahltermine).

4. **Neue Termine.** Wird ein Wahltermin offiziell festgelegt (oder eine Neuwahl angesetzt),
   `wahltermin` und `sortierung` (`JJJJ-MM-TT`) anpassen, mit zwei Quellen geprüft.

5. **Prüfen:** `node --test werkzeuge/tests/*.test.js` muss grün sein.

6. **Committen nur bei Änderungen:** `git status --porcelain politik/koalitionen/data.json`.
   Gibt es eine Zeile: `git add politik/koalitionen/data.json && git commit -m "Koalitionsrechner: Update KW <ww>" && git push`.
   Sonst nichts committen.

7. **Melden:** ob dawum erreichbar war, welche Parlamente neue Umfragen haben, ob eine neue
   Regierung oder ein neuer Termin eingetragen wurde, und ob committet wurde.
