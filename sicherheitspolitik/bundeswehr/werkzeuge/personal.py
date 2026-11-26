"""Erzeugt das interaktive Liniendiagramm „Truppenstärke seit 1955“ als Inline-SVG
plus Ereignisliste und Datentabelle und setzt alles zwischen <!-- PERSONAL-START -->
und <!-- PERSONAL-ENDE --> in index.html.
Aufruf im Ordner sicherheitspolitik/bundeswehr: python3 werkzeuge/personal.py
Daten: werkzeuge/personal.json (Herkunft dort unter _hinweis)."""
import json, re, pathlib
hier = pathlib.Path(__file__).resolve().parent
d = json.loads((hier / "personal.json").read_text())
WB = {int(k): v for k, v in d["wb"].items()}
COW = {int(k): v for k, v in d["cow"].items() if int(k) >= 1959}
IISS = {int(k): v for k, v in d["iiss"].items()}
AKT = d["aktuell"]

W, H = 720, 380
X0 = 1955
def de(v): return f"{v:,}".replace(",", ".")
def q(*n): return '<span class="q">' + ",".join(f'<a href="#q{i}">{i}</a>' for i in n) + "</span>"

# Ereignisse: Nummer, Jahr (Position), Jahr (Trefferfläche), Kurztext, Belege
EREIGNISSE = [
    (1, 1957.25, 1957, "1. April 1957: Die ersten Wehrpflichtigen rücken ein.", (104, 105)),
    (2, 1990.75, 1990, "3. Oktober 1990: Deutsche Einheit. Die Bundeswehr übernimmt Soldaten der Nationalen Volksarmee (NVA), der Armee der DDR.", (9, 107)),
    (3, 2011.5, 2011, "1. Juli 2011: Die allgemeine Wehrpflicht wird ausgesetzt.", (10, 12)),
    (4, 2026.0, 2026, "1. Januar 2026: Das Wehrdienst-Modernisierungsgesetz gilt, der Dienst bleibt freiwillig.", (41, 42)),
]
EKURZ = {1957: "Erste Wehrpflichtige (1.4.)", 1990: "Deutsche Einheit (3.10.)", 2011: "Wehrpflicht ausgesetzt (1.7.)", 2026: "Neuer Wehrdienst (1.1.)"}

def bau(W, H, schmal):
    L, R, T, B = (40, 10, 46, 34) if schmal else (50, 16, 46, 40)
    X0, X1, YMAX = 1955, 2027, 600000
    def x(j): return L + (j - X0) / (X1 - X0) * (W - L - R)
    def y(v): return T + (1 - v / YMAX) * (H - T - B)
    def pfad(r): return "M" + " L".join(f"{x(j):.1f},{y(v):.1f}" for j, v in sorted(r.items()))
    kl = " pz-schmal" if schmal else " pz-breit"
    sf = "-s" if schmal else ""
    s = []
    s.append(f'<svg class="pz-svg{kl}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="pz-titel{sf} pz-desc{sf}">')
    s.append(f'<title id="pz-titel{sf}">Aktive Soldatinnen und Soldaten der Bundeswehr, Jahresdurchschnitt 1959 bis 2025</title>')
    s.append(f'<desc id="pz-desc{sf}">Laut Wehrbeauftragtem {de(WB[1959])} im Jahr 1959, Höchststand {de(WB[1983])} im Jahr 1983, {de(WB[1989])} 1989, {de(WB[1991])} 1991, {de(WB[2010])} 2010, {de(WB[2011])} 2011, Tiefstwert {de(WB[2016])} 2016, {de(WB[2025])} 2025. Monatswert Ende Oktober 2026: rund {de(AKT["wert"])}. Für 1955 bis 1958 keine Jahreswerte.</desc>')
    s.append(f'<defs><pattern id="pz-schraffur{sf}" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="8" class="pz-schraffur-linie"/></pattern></defs>')
    # Phasenbänder
    s.append(f'<rect class="pz-phase pz-phase-pflicht" x="{x(1957.25):.1f}" y="{T}" width="{x(2011.5)-x(1957.25):.1f}" height="{H-T-B}"/>')
    s.append(f'<text class="pz-phasen-name" x="{(x(1957.25)+x(1990.75))/2:.1f}" y="16" text-anchor="middle">Wehrpflicht</text>')
    s.append(f'<text class="pz-phasen-name" x="{(x(2011.5)+x(2026))/2:.1f}" y="16" text-anchor="middle">Freiwillige</text>')
    # Lücke 1955–1958
    s.append(f'<rect class="pz-luecke" x="{x(1955):.1f}" y="{T}" width="{x(1959)-x(1955):.1f}" height="{H-T-B}" fill="url(#pz-schraffur{sf})"/>')
    if not schmal: s.append(f'<text class="pz-notiz" x="{x(1957):.1f}" y="{y(330000):.1f}" text-anchor="middle" transform="rotate(-90 {x(1957):.1f} {y(330000):.1f})">keine Jahreswerte</text>')
    # Gitter
    for v in range(0, YMAX + 1, 100000):
        s.append(f'<line class="pz-gitter" x1="{L}" x2="{W-R}" y1="{y(v):.1f}" y2="{y(v):.1f}"/>')
        s.append(f'<text class="pz-ach" x="{L-8}" y="{y(v)+6:.1f}" text-anchor="end">{v//1000}</text>')
    s.append(f'<text class="pz-ach pz-einheit" x="{L-8}" y="{T-8}" text-anchor="end">Tsd.</text>')
    for j in range(1960, 2030, 20 if schmal else 10):
        s.append(f'<text class="pz-ach" x="{x(j):.1f}" y="{H-12}" text-anchor="middle">{j}</text>')
    # Bruchlinien mit Nummern
    for n, pos, _, _, _ in EREIGNISSE:
        s.append(f'<line class="pz-bruch" x1="{x(pos):.1f}" x2="{x(pos):.1f}" y1="{T}" y2="{H-B}"/>')
        s.append(f'<g class="pz-nr" data-nr="{n}"><circle cx="{x(pos):.1f}" cy="{T-14}" r="11"/><text x="{x(pos):.1f}" y="{T-9}" text-anchor="middle">{n}</text></g>')
    # Vergleichsreihe COW
    s.append(f'<path class="pz-cow" d="{pfad(COW)}"/>')
    # Hauptreihe
    s.append(f'<path class="pz-wb" d="{pfad(WB)}"/>')
    # Stichtag 3.10.1990: Spanne 570.000 bis knapp 600.000
    sx = x(1990.75)
    s.append(f'<line class="pz-spanne" x1="{sx:.1f}" x2="{sx:.1f}" y1="{y(600000):.1f}" y2="{y(570000):.1f}"/>')
    if not schmal: s.append(f'<text class="pz-wert" x="{sx-10:.1f}" y="{y(585000)+6:.1f}" text-anchor="end">3.10.1990: 570–600 Tsd.</text>')
    # Monatswert Oktober 2026
    ax = x(2026 + 10 / 12)
    s.append(f'<circle class="pz-akt" cx="{ax:.1f}" cy="{y(AKT["wert"]):.1f}" r="5"/>')
    s.append(f'<text class="pz-wert" x="{ax-4:.1f}" y="{y(AKT["wert"])-(14 if schmal else 28):.1f}" text-anchor="end">{de(AKT["wert"])}</text>')
    if not schmal: s.append(f'<text class="pz-notiz" x="{ax-4:.1f}" y="{y(AKT["wert"])-10:.1f}" text-anchor="end">Okt. 2026</text>')
    # Beschriftung Extremwerte
    s.append(f'<text class="pz-wert" x="{x(1976 if schmal else 1983):.1f}" y="{y(WB[1983])+(-14 if schmal else 24):.1f}" text-anchor="middle">{de(WB[1983])} (1983)</text>')
    s.append(f'<text class="pz-wert" x="{x(2016):.1f}" y="{y(WB[2016])+26:.1f}" text-anchor="middle">{de(WB[2016])} (2016)</text>')
    # Trefferflächen
    w = (W - L - R) / (X1 - X0)
    for j in range(X0, 2027):
        attr = f'data-j="{j}"'
        if j in WB: attr += f' data-w="{de(WB[j])}"'
        if j in COW: attr += f' data-c="{de(COW[j])}"'
        if j in EKURZ: attr += f' data-e="{EKURZ[j]}"'
        if j == 1990: attr += ' data-s="rund 570.000 bis knapp 600.000"'
        if j == 2026: attr += f' data-m="{de(AKT["wert"])} (31.10.)"'
        s.append(f'<rect class="pz-hit" x="{x(j)-w/2:.1f}" y="{T}" width="{w:.1f}" height="{H-T-B}" {attr}/>')
    s.append(f'<line class="pz-kreuz" x1="0" x2="0" y1="{T}" y2="{H-B}" hidden/>')
    s.append('</svg>')
    return "\n".join(s)

svg = bau(720, 380, False) + "\n" + bau(400, 420, True)


ereignisse = "\n".join(
    f'    <li><button type="button" class="pz-ereignis" data-j="{hj}" aria-describedby="pz-titel"><span class="pz-enr">{n}</span>{text}</button>{q(*b)}</li>'
    for n, _, hj, text, b in EREIGNISSE)
zeilen = "\n".join(
    f'<tr><td class="jahr">{j}</td><td>{de(WB[j])}</td><td>{de(COW[j]) if j in COW else ""}</td><td>{de(IISS[j]) if j in IISS else ""}</td></tr>'
    for j in sorted(WB))

html = f'''<figure class="personal" id="personal-diagramm">
  <div class="pz-kopf">
    <div class="pz-legende"><span class="pz-l-wb">Jahresdurchschnitt laut Wehrbeauftragtem</span><span class="pz-l-cow">Vergleich: Forschungsdatensatz COW</span><span class="pz-l-akt">Monatswert</span></div>
    <button type="button" class="pz-schalter" aria-pressed="true" aria-controls="personal-diagramm">Vergleichsreihe ausblenden</button>
  </div>
  <div class="pz-flaeche">
{svg}
  <div class="pz-tip" role="status" hidden></div>
  </div>
  <ol class="pz-ereignisse" aria-label="Brüche in der Zeitreihe">
{ereignisse}
  </ol>
  <figcaption>Aktive Soldatinnen und Soldaten der Bundeswehr, Jahresdurchschnitt 1959–2025, Einheit: Personen.{q(95)} Vergleichsreihe: Correlates of War (COW), Variable „military personnel“, Stichtag jeweils 1. Januar, 1959–2022.{q(97)} Monatswert: Stichtag 31.10.2026, gerundet.{q(102, 103)} Nicht enthalten: Zivilpersonal und Reservisten. Für 1955 bis 1958 gibt es keine Jahresdurchschnittswerte. Antippen oder Überfahren zeigt die Werte je Jahr.</figcaption>
  <details class="belege"><summary>Werte als Tabelle</summary>
  <div class="tab"><table class="pz-tab"><thead><tr><th>Jahr</th><th>Wehrbeauftragter (Jahresdurchschnitt)</th><th>COW (1. Januar)</th><th>IISS über Weltbank</th></tr></thead>
  <tbody>
{zeilen}
  </tbody></table></div>
  <p class="pz-tabnotiz">Quellen der Spalten: Wehrbeauftragter{q(95)}, COW{q(97)}, IISS (International Institute for Strategic Studies) über den Weltbank-Indikator „Armed forces personnel, total“{q(98)}. Die COW-Reihe stützt sich ab etwa 1990 auf ähnliche Grundlagen wie die IISS-Reihe; beide gelten hier zusammen als eine Vergleichsquelle. Zum Wert für 2024 siehe{q(96)}.</p>
  </details>
</figure>'''

p = hier.parent / "index.html"
t = p.read_text()
neu, n = re.subn(r"<!-- PERSONAL-START -->.*?<!-- PERSONAL-ENDE -->", "<!-- PERSONAL-START -->\n" + html + "\n<!-- PERSONAL-ENDE -->", t, flags=re.S)
assert n == 1, "Marker fehlen"
p.write_text(neu)
print("ok")
