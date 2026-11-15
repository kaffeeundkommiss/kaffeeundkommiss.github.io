#!/usr/bin/env python3
"""Koalitionsrechner (politik/koalitionen/): Umfragen von dawum.de in data.json übernehmen.

Aufruf im Repo-Root:
    python3 werkzeuge/koalitionen_update.py                # holt https://api.dawum.de/newest_surveys.json
    python3 werkzeuge/koalitionen_update.py --datei x.json # nutzt eine gespeicherte dawum-Datei

Das Skript ändert nur die Felder "umfragen" je Parlament sowie "umfragen_stand" und "erstellt".
Wahltermine, letzte Wahl, Sperrklausel-Ausnahmen und die Liste bisheriger Regierungen
("historie") pflegt die wöchentliche Routine von Hand mit Beleg (siehe ROUTINE-KOALITIONEN.md).
Daten: dawum.de, Lizenz ODC-ODbL.
"""
import argparse, json, os, sys, urllib.request
from datetime import datetime, timezone, timedelta

PFAD = os.path.join(os.path.dirname(__file__), '..', 'politik', 'koalitionen', 'data.json')
DAWUM = 'https://api.dawum.de/newest_surveys.json'
MAX_JE_PARLAMENT = 40  # Startwert: so viele Umfragen je Parlament werden gespeichert


def lade_dawum(datei=None):
    if datei:
        with open(datei, encoding='utf-8') as f:
            return json.load(f)
    req = urllib.request.Request(DAWUM, headers={'User-Agent': 'kaffeeundkommiss-koalitionen/1.0'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def umfragen_je_parlament(db):
    """{Parlaments-Kürzel bei dawum: [{institut, datum, befragte, werte}]} neueste zuerst."""
    parl = {k: v['Shortcut'] for k, v in db['Parliaments'].items()}
    inst = {k: v['Name'] for k, v in db['Institutes'].items()}
    part = {k: v['Shortcut'] for k, v in db['Parties'].items()}
    out = {}
    for u in db['Surveys'].values():
        werte = {part[p]: float(w) for p, w in u['Results'].items()}
        out.setdefault(parl[u['Parliament_ID']], []).append({
            'institut': inst[u['Institute_ID']],
            'datum': u['Date'],
            'befragte': int(u['Surveyed_Persons']) if str(u.get('Surveyed_Persons', '')).isdigit() else None,
            'werte': werte,
        })
    for liste in out.values():
        liste.sort(key=lambda x: (x['datum'], x['institut']), reverse=True)
    return out


def uebernehmen(d, db):
    je = umfragen_je_parlament(db)
    geaendert = []
    for p in d['parlamente']:
        neu = [u for u in je.get(p['dawum'], []) if u['datum'] > p['letzte_wahl']][:MAX_JE_PARLAMENT]
        if neu != p.get('umfragen'):
            geaendert.append(p['id'])
            p['umfragen'] = neu
    return geaendert


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--datei', help='gespeicherte dawum-Datei statt Live-Abruf')
    a = ap.parse_args()
    with open(PFAD, encoding='utf-8') as f:
        d = json.load(f)
    try:
        db = lade_dawum(a.datei)
    except Exception as e:  # dawum nicht erreichbar: alte Werte bleiben stehen
        print(f'! dawum nicht erreichbar ({e}); data.json bleibt unverändert')
        return 0
    geaendert = uebernehmen(d, db)
    if not geaendert:
        print('Keine neuen Umfragen – data.json bleibt unverändert.')
        return 0
    d['umfragen_stand'] = db['Database']['Last_Update']
    d['erstellt'] = datetime.now(timezone(timedelta(hours=1))).strftime('%Y-%m-%dT%H:%M%z')
    with open(PFAD, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('data.json geschrieben, neue Umfragen für: ' + ', '.join(geaendert))
    return 0


if __name__ == '__main__':
    sys.exit(main())
