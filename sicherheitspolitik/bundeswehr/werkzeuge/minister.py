#!/usr/bin/env python3
"""Baut die Zeitleiste der Bundesminister der Verteidigung in ../index.html neu.

Daten stehen in MINISTER unten. Der Block zwischen <!-- minister:start --> und <!-- minister:end -->
wird ersetzt. Liegt ein Porträt unter bilder/<schluessel>.jpg, wird es eingebunden, sonst erscheinen
die Initialen. Bildnachweise stehen in BILDER (Schlüssel -> Text mit Urheber, Jahr, Lizenz, Commons-Datei).
Aufruf im Ordner sicherheitspolitik/bundeswehr/:  python3 werkzeuge/minister.py
"""
import html
import re
from datetime import date
from pathlib import Path

ORDNER = Path(__file__).resolve().parent.parent
SEITE = ORDNER / "index.html"
BEGINN, ENDE = date(1955, 6, 7), date(2026, 11, 15)  # Ende = Stand der Seite

# Schlüssel, Name, Partei, Beginn, Ende (None = amtierend), Kanzler, Ereignisse [(Text, Quellen)]
# Daten der Amtszeit: BMVg [12] (Jahre) und Wikipedia-Abgleich [13] (Tage).
MINISTER = [
    ("blank", "Theodor Blank", "CDU", "1955-06-07", "1956-10-16", "Konrad Adenauer", [
        ("5. Mai 1955: Beitritt der Bundesrepublik zur NATO", "1,2"),
        ("12. November 1955: Die ersten 101 Freiwilligen erhalten ihre Ernennungsurkunden", "1,2"),
        ("20. Januar 1956: Adenauer besucht die ersten Soldaten in Andernach", "2")]),
    ("strauss", "Franz Josef Strauß", "CSU", "1956-10-16", "1963-01-09", "Konrad Adenauer", [
        ("Februar 1962: Sturmflut, Großeinsatz der Bundeswehr in Hamburg", "15,16,17"),
        ("1962: Spiegel-Affäre", "12,2")]),
    ("hassel", "Kai-Uwe von Hassel", "CDU", "1963-01-09", "1966-12-01", "Adenauer, Ludwig Erhard", []),
    ("schroeder", "Gerhard Schröder", "CDU", "1966-12-01", "1969-10-21", "Kurt Georg Kiesinger", [
        ("1968: Notstandsgesetze, Hilfe der Streitkräfte bei Katastrophen im Grundgesetz geregelt (Art. 35 Abs. 2)", "15,16")]),
    ("schmidt", "Helmut Schmidt", "SPD", "1969-10-22", "1972-07-07", "Willy Brandt", [
        ("Reformen, unter anderem Hochschulen der Bundeswehr (laut BMVg)", "12")]),
    ("leber", "Georg Leber", "SPD", "1972-07-07", "1978-02-16", "Brandt, Helmut Schmidt", []),
    ("apel", "Hans Apel", "SPD", "1978-02-17", "1982-10-01", "Helmut Schmidt", [
        ("Winter 1978/79: Schneekatastrophe in Norddeutschland, Hilfe mit Panzern und Hubschraubern", "15")]),
    ("woerner", "Manfred Wörner", "CDU", "1982-10-04", "1988-05-18", "Helmut Kohl", [
        ("Umsetzung des NATO-Doppelbeschlusses (laut BMVg)", "12")]),
    ("scholz", "Rupert Scholz", "CDU", "1988-05-18", "1989-04-21", "Helmut Kohl", []),
    ("stoltenberg", "Gerhard Stoltenberg", "CDU", "1989-04-21", "1992-03-31", "Helmut Kohl", [
        ("3. Oktober 1990: Die NVA wird aufgelöst, die Bundeswehr wird „Armee der Einheit“", "9,12"),
        ("1991: Golfkrieg, Jagdbomber und Flugabwehr in der Türkei, Minenabwehr im Mittelmeer", "3,4")]),
    ("ruehe", "Volker Rühe", "CDU", "1992-04-01", "1998-10-26", "Helmut Kohl", [
        ("Mai 1992 bis November 1993: Feldlazarett in Kambodscha, erster Blauhelm-Einsatz", "3,4"),
        ("1993/94: UNOSOM II in Somalia", "3,4"),
        ("12. Juli 1994: Urteil des Bundesverfassungsgerichts zu Auslandseinsätzen", "3,7"),
        ("1997: Oderhochwasser, mehr als 30.000 Soldaten", "15,33")]),
    ("scharping", "Rudolf Scharping", "SPD", "1998-10-27", "2002-07-19", "Gerhard Schröder", [
        ("März 1999: Luftkrieg gegen Jugoslawien, erster Kampfauftrag", "3,19"),
        ("Seit 12. Juni 1999: KFOR im Kosovo", "5,3"),
        ("Seit Februar 2002: ISAF in Afghanistan", "3,12")]),
    ("struck", "Peter Struck", "SPD", "2002-07-19", "2005-11-22", "Gerhard Schröder", [
        ("2002: „Die Sicherheit Deutschlands wird auch am Hindukusch verteidigt.“", "4,12"),
        ("August 2002: Elbehochwasser, mehr als 45.000 Soldaten", "32"),
        ("2005: Parlamentsbeteiligungsgesetz tritt in Kraft", "3,37")]),
    ("jung", "Franz Josef Jung", "CDU", "2005-11-22", "2009-10-28", "Angela Merkel", [
        ("13. August 2008: Ehrenkreuz der Bundeswehr für Tapferkeit gestiftet", "24,27"),
        ("6. Juli 2009: erste Verleihung an vier Soldaten", "25,27"),
        ("8. September 2009: Einweihung des Ehrenmals der Bundeswehr", "20,21")]),
    ("guttenberg", "Karl-Theodor zu Guttenberg", "CSU", "2009-10-28", "2011-03-03", "Angela Merkel", [
        ("9. November 2010: Einsatzmedaille Gefecht gestiftet", "26,27")]),
    ("demaiziere", "Thomas de Maizière", "CDU", "2011-03-03", "2013-12-17", "Angela Merkel", [
        ("1. Juli 2011: Die allgemeine Wehrpflicht wird ausgesetzt", "10,12"),
        ("2013: Beginn der Einsätze in Mali", "3,5")]),
    ("leyen", "Ursula von der Leyen", "CDU", "2013-12-17", "2019-07-17", "Angela Merkel", [
        ("2014: Annexion der Krim, Bündnisverteidigung rückt wieder in den Mittelpunkt", "3,12"),
        ("15. November 2014: Einweihung des Waldes der Erinnerung", "22,23")]),
    ("akk", "Annegret Kramp-Karrenbauer", "CDU", "2019-07-17", "2021-12-08", "Angela Merkel", [
        ("2020 bis 2022: Corona-Amtshilfe, längster Hilfseinsatz im Inland", "15"),
        ("30. Juni 2021: Abzug aus Afghanistan, im August Evakuierung aus Kabul", "3"),
        ("Juli 2021: Flutkatastrophe im Ahrtal", "15")]),
    ("lambrecht", "Christine Lambrecht", "SPD", "2021-12-08", "2023-01-19", "Olaf Scholz", [
        ("27. Februar 2022: Regierungserklärung zur „Zeitenwende“, Sondervermögen von 100 Milliarden Euro", "11,12")]),
    ("pistorius", "Boris Pistorius", "SPD", "2023-01-19", None, "Olaf Scholz, Friedrich Merz", [
        ("Dezember 2023: Ende des Mali-Einsatzes", "3"),
        ("25. April 2024: Bundestag beschließt den Nationalen Veteranentag", "28,29"),
        ("18./21. März 2025: Grundgesetzänderung, Verteidigungsausgaben über 1 Prozent des BIP von der Schuldenbremse ausgenommen", "38,39"),
        ("15. Juni 2025: erster Nationaler Veteranentag", "29,30"),
        ("5. Dezember 2025: Bundestag beschließt das Wehrdienst-Modernisierungsgesetz", "41,42")]),
]

# Bildnachweise, nur befüllen, wenn die Lizenz auf der Commons-Dateiseite geprüft ist.
BILDER = {}

e = html.escape


def d(s):
    return date.fromisoformat(s) if s else None


def fmt(x):
    return f"{x.day}.{x.month}.{x.year}"


def quellen(s):
    return '<span class="q">' + ",".join(f'<a href="#q{n}">{n}</a>' for n in s.split(",")) + "</span>"


def initialen(name):
    teile = [t for t in name.replace("-", " ").split() if t[0].isupper()]
    return (teile[0][0] + teile[-1][0]) if len(teile) > 1 else teile[0][0]


def bauen():
    gesamt = (ENDE - BEGINN).days
    band, karten = [], []
    for i, (k, name, partei, b, en, kanzler, ereignisse) in enumerate(MINISTER, 1):
        b, en = d(b), d(en)
        bis = en or ENDE
        links = (b - BEGINN).days / gesamt * 100
        breite = max((bis - b).days / gesamt * 100, 0.6)
        band.append(f'<a class="mz-seg" href="#m-{k}" style="left:{links:.2f}%;width:{breite:.2f}%" '
                    f'title="{e(name)}, {b.year}–{bis.year if en else "heute"}"><span>{i}</span></a>')
        bild = ORDNER / "bilder" / f"{k}.jpg"
        if bild.exists():
            foto = f'<img src="bilder/{k}.jpg" alt="{e(name)}" loading="lazy" width="120" height="150">'
        else:
            foto = f'<span class="leer" aria-hidden="true">{e(initialen(name))}</span>'
        nachweis = f'<p class="bild">{e(BILDER[k])} <a href="#b-{k}">Bildnachweis</a></p>' if k in BILDER else ""
        zeit = f'{fmt(b)} – {fmt(en)}' if en else f'seit {fmt(b)}'
        liste = "".join(f"<li>{e(t)}{quellen(q)}</li>" for t, q in ereignisse)
        liste = f'<ul class="mz-ereig">{liste}</ul>' if liste else '<p class="mz-ohne">Keine Ereignisse aus den übrigen Kapiteln dieser Seite.</p>'
        karten.append(f'''    <li class="mz-karte" id="m-{k}">
      <div class="mz-foto">{foto}</div>
      <div class="mz-txt">
        <div class="mz-nr">{i}. Minister{"in" if k in ("leyen", "akk", "lambrecht") else ""} · {e(partei)}</div>
        <h3>{e(name)}</h3>
        <p class="mz-zeit">{zeit}{quellen("12,13")}</p>
        <p class="mz-kanzler">Kabinett: {e(kanzler)}</p>
        {liste}
        {nachweis}
      </div>
    </li>''')
    jahre = "".join(f'<span style="left:{(date(j,1,1)-BEGINN).days/gesamt*100:.2f}%">{j}</span>'
                    for j in range(1960, 2030, 10))
    return ("<!-- minister:start -->\n"
            '  <div class="mz-band" aria-hidden="true">\n    <div class="mz-spur">' + "".join(band) + "</div>\n"
            '    <div class="mz-jahre">' + jahre + "</div>\n  </div>\n"
            '  <ol class="mz-liste">\n' + "\n".join(karten) + "\n  </ol>\n  <!-- minister:end -->")


text = SEITE.read_text(encoding="utf-8")
neu = re.sub(r"<!-- minister:start -->.*?<!-- minister:end -->", lambda m: bauen(), text, flags=re.S)
SEITE.write_text(neu, encoding="utf-8")
print("Zeitleiste geschrieben:", len(MINISTER), "Minister")
