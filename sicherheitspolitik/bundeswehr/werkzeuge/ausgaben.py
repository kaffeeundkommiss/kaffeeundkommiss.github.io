"""Erzeugt das Liniendiagramm „Verteidigungsausgaben in Prozent des BIP“ als Inline-SVG
plus Datentabelle und setzt beides zwischen <!-- AUSGABEN-START --> und <!-- AUSGABEN-ENDE --> in index.html.
Aufruf im Ordner sicherheitspolitik/bundeswehr: python3 werkzeuge/ausgaben.py"""
import json, re, pathlib
hier = pathlib.Path(__file__).resolve().parent
d = json.loads((hier / "ausgaben.json").read_text())
S = {int(k): v for k, v in d["sipri"].items()}
N = {int(k): v for k, v in d["nato"].items()}
W, H = 720, 340
L, R, T, B = 46, 18, 34, 40
X0, X1, YMAX = 1953, 2025, 5.0
def x(j): return L + (j - X0) / (X1 - X0) * (W - L - R)
def y(v): return T + (1 - v / YMAX) * (H - T - B)
def de(v): return f"{v:.2f}".replace(".", ",")
def pfad(r): return "M" + " L".join(f"{x(j):.1f},{y(v):.1f}" for j, v in sorted(r.items()))
s = []
s.append(f'<svg class="ag-svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="ag-titel ag-desc">')
s.append('<title id="ag-titel">Militärausgaben Deutschlands in Prozent des BIP, 1953 bis 2025</title>')
s.append(f'<desc id="ag-desc">SIPRI-Reihe: {de(S[1955])} % 1955, Höchstwert {de(max(S.values()))} % 1963, {de(S[1990])} % 1990, {de(S[1991])} % 1991, Tiefstwert {de(min(S.values()))} % 2015, {de(S[2025])} % 2025. NATO-Reihe 2014 bis 2024: {de(N[2014])} % bis {de(N[2024])} %.</desc>')
for v in range(0, 6):
    s.append(f'<line class="ag-gitter" x1="{L}" x2="{W-R}" y1="{y(v):.1f}" y2="{y(v):.1f}"/>')
    s.append(f'<text class="ag-ach" x="{L-8}" y="{y(v)+6:.1f}" text-anchor="end">{v}</text>')
for j in range(1960, 2030, 10):
    s.append(f'<text class="ag-ach" x="{x(j):.1f}" y="{H-12}" text-anchor="middle">{j}</text>')
# Bruch Einheit
bx = x(1990.5)
s.append(f'<line class="ag-bruch" x1="{bx:.1f}" x2="{bx:.1f}" y1="{T}" y2="{H-B}"/>')
s.append(f'<text class="ag-notiz" x="{bx+6:.1f}" y="{T+16}">ab 1991 gesamtdeutsch</text>')
s.append(f'<path class="ag-sipri" d="{pfad(S)}"/>')
s.append(f'<path class="ag-nato" d="{pfad(N)}"/>')
for j, v in N.items():
    s.append(f'<circle class="ag-nato-pkt" cx="{x(j):.1f}" cy="{y(v):.1f}" r="4"/>')
# direkte Beschriftungen, sparsam
s.append(f'<text class="ag-wert" x="{x(1963):.1f}" y="{y(S[1963])-10:.1f}" text-anchor="middle">{f'{S[1963]:.1f}'.replace('.',',')} % (1963)</text>')
s.append(f'<text class="ag-wert" x="{x(2025)-4:.1f}" y="{y(S[2025])-12:.1f}" text-anchor="end">{f'{S[2025]:.1f}'.replace('.',',')} % (2025)</text>')
s.append(f'<text class="ag-name ag-name-sipri" x="{x(1970):.1f}" y="{y(S[1970])+26:.1f}">SIPRI</text>')
s.append(f'<text class="ag-name ag-name-nato" x="{x(2012)-6:.1f}" y="{y(1.75):.1f}" text-anchor="end">NATO</text>')
# Trefferflächen für Hover
for j in range(X0, X1 + 1):
    w = (W - L - R) / (X1 - X0)
    attr = f'data-j="{j}" data-s="{de(S[j])}"' + (f' data-n="{de(N[j])}"' if j in N else "")
    s.append(f'<rect class="ag-hit" x="{x(j)-w/2:.1f}" y="{T}" width="{w:.1f}" height="{H-T-B}" {attr}/>')
s.append(f'<line class="ag-kreuz" x1="0" x2="0" y1="{T}" y2="{H-B}" hidden/>')
s.append('</svg>')
svg = "\n".join(s)
zeilen = "\n".join(f'<tr><td class="jahr">{j}</td><td>{de(S[j])}</td><td>{de(N[j]) if j in N else ""}</td></tr>' for j in sorted(S))
html = f'''<figure class="ausgaben" id="ausgaben-diagramm">
  <div class="ag-legende"><span class="ag-l-sipri">SIPRI, Anteil am BIP in %</span><span class="ag-l-nato">NATO-Definition, Anteil am realen BIP in %</span></div>
  <div class="ag-flaeche">
{svg}
  <div class="ag-tip" role="status" hidden></div>
  </div>
  <figcaption>Militärausgaben Deutschlands in Prozent des Bruttoinlandsprodukts. SIPRI-Werte 1953–2025, NATO-Werte 2014–2024 (2024 Schätzung).<span class="q"><a href="#q87">87</a>,<a href="#q89">89</a></span> Die beiden Reihen beruhen auf unterschiedlichen Abgrenzungen und sind nicht deckungsgleich.</figcaption>
  <details class="belege"><summary>Werte als Tabelle</summary>
  <div class="tab"><table class="ag-tab"><thead><tr><th>Jahr</th><th>SIPRI (%)</th><th>NATO (%)</th></tr></thead>
  <tbody>
{zeilen}
  </tbody></table></div></details>
</figure>'''
p = hier.parent / "index.html"
t = p.read_text()
neu, n = re.subn(r"<!-- AUSGABEN-START -->.*?<!-- AUSGABEN-ENDE -->", "<!-- AUSGABEN-START -->\n" + html + "\n<!-- AUSGABEN-ENDE -->", t, flags=re.S)
assert n == 1, "Marker fehlen"
p.write_text(neu)
print("ok")
