# Baut die drei Kriegsseiten ../1864/, ../1866/, ../1870-71/ aus kriege_daten.py.
# Aufruf: GEO=<ordner-mit-geodaten> python3 kriegsseiten.py   (Geodaten siehe README.md)
import html, os, re, sys
from shapely.geometry import box, shape
from shapely.ops import unary_union
from shapely.validation import make_valid
import kriegskarten as KK
from kriege_daten import KRIEGE, Q, BILDER, ABRUF, KOK_BELEG

HIER = os.path.dirname(os.path.abspath(__file__))
EK = os.path.dirname(HIER)
BASIS = "https://kaffeeundkommiss.github.io/geschichte/einigungskriege/"


class Belege:
    """Nummeriert die Quellen einer Seite in der Reihenfolge der ersten Nennung."""
    def __init__(self):
        self.nr = {}

    def __call__(self, text):
        def ersetze(m):
            inhalt = m.group(1)
            if inhalt == "eine":
                return '<span class="eine">eine Quelle</span>'
            if inhalt.startswith("eine:"):
                return f'<span class="eine">{html.escape(inhalt[5:])}</span>'
            teile = []
            for k in inhalt.split(","):
                k = k.strip()
                if k not in Q: sys.exit(f"Unbekannte Quelle {k}")
                if k not in self.nr: self.nr[k] = len(self.nr) + 1
                teile.append(f'<a href="#q{self.nr[k]}">{self.nr[k]}</a>')
            return '<span class="q">' + ",".join(teile) + "</span>"
        return re.sub(r"\{\{([^}]+)\}\}", ersetze, text)


def kopf(k, pfad_bild):
    t = f'{k["seitentitel"]} · Kaffee und Kommiss'
    url = BASIS + k["ordner"] + "/"
    b = html.escape(k["beschreibung"])
    # Vorschaubild-Block (werkzeuge/vorschau.js im Repo-Wurzelordner) aus der vorhandenen Seite übernehmen
    alt = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", k["ordner"], "index.html")
    m = re.search(r"<!-- Vorschau für Linkvorschauen, erzeugt mit werkzeuge/vorschau\.js -->\n(?:<meta [^>]*>\n)*", open(alt).read()) if os.path.exists(alt) else None
    vorschau = m.group(0) if m else ""
    pfad = ('<nav class="kk-pfad" aria-label="Pfad"><div class="kk-in"><a href="https://kaffeeundkommiss.github.io/geschichte/">Geschichte</a> › '
            '<a href="https://kaffeeundkommiss.github.io/geschichte/einigungskriege-kaiserreich/">Einigungskriege und Kaiserreich</a> › '
            f'<a href="../">Einigungskriege 1864–1871</a> › <span aria-current="page">{html.escape(k["titel"])}</span></div></nav>\n')
    return f'''<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t}</title>
<meta name="description" content="{b}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:locale" content="de_DE">
<meta property="og:site_name" content="Kaffee und Kommiss">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{b}">
<meta property="og:url" content="{url}">
{vorschau}<link rel="icon" href="../../../icons/einigungskriege.svg" type="image/svg+xml">
<link rel="icon" href="../../../favicon-32.png" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" sizes="180x180" href="../../../apple-touch-icon.png?v=2">
<meta name="theme-color" content="#23211C">
<link rel="stylesheet" href="https://kaffeeundkommiss.github.io/schriften/schriften.css">
<link rel="stylesheet" href="../../../basis.css">
<link rel="stylesheet" href="../../../style.css">
<link rel="stylesheet" href="../einigungskriege.css">
<link rel="stylesheet" href="../kriege.css">
<link rel="stylesheet" href="../../reiter.css">
</head>
<body class="kk-b-gesch kk-einigung kk-breit">
<!-- Erzeugt mit werkzeuge/kriegsseiten.py aus werkzeuge/kriege_daten.py, nicht von Hand ändern. -->
<div class="kk-leiste"><div class="kk-in">
  <a class="kk-haus" href="https://kaffeeundkommiss.github.io/"><img src="../../../kk-tasse.svg" alt="" width="22" height="22"><span>Kaffee und Kommiss</span></a>
  <nav class="kk-bereiche" aria-label="Bereiche"><a href="https://kaffeeundkommiss.github.io/geschichte/" aria-current="true">Geschichte</a><a href="https://kaffeeundkommiss.github.io/sicherheitspolitik/"><span class="kk-lang">Sicherheitspolitik</span><span class="kk-kurz">Sicherheit</span></a><a href="https://kaffeeundkommiss.github.io/politik/">Politik</a></nav>
</div></div>
{pfad}<header class="kk-kopf">
  <div class="wrap">
    <a class="kk-schild" href="../">
      <img class="logo" src="../../../icons/einigungskriege.svg" alt="" width="44" height="44">
      <div>
        <div class="kk-name">Einigungskriege 1864–1871</div>
        <div class="kk-unter">{html.escape(k["titel"])}</div>
      </div>
    </a>
  </div>
</header>
'''


def flaechen(kd, bb):
    B = box(*bb)
    out = []
    for rolle, namen in kd["flaechen_def"]:
        g = KK.hb(*namen)
        if rolle == "ge" and kd.get("abgetreten"):
            pass
        out.append((rolle, g.intersection(B.buffer(0.2))))
    return out


def grenzen(bb, mit_benelux):
    B = box(*bb).buffer(0.2)
    gs = []
    for f in KK.lade("w1815.json")["features"]:
        g = shape(f["geometry"])
        if g.intersects(B): gs.append(make_valid(g))
    if mit_benelux:
        nl = KK.ne0("NLD", "BEL", "LUX")
        gs = [g.difference(nl.buffer(0.01)) for g in gs] + [KK.ne0("NLD"), KK.ne0("BEL"), KK.ne0("LUX")]
    return gs


def seite(k):
    kd = dict(k["karte"]); q = Belege()
    ordner = os.path.join(EK, k["ordner"]); os.makedirs(ordner, exist_ok=True)
    bb = kd["bb"]
    kd["flaechen"] = flaechen(kd, bb)
    benelux = k["ordner"] != "1864"
    if benelux:
        nl = KK.ne0("NLD", "BEL", "LUX")
        kd["flaechen"] = [(r, g.difference(nl)) for r, g in kd["flaechen"]]
    kd["grenzen"] = grenzen(bb, benelux)
    if kd.get("abgetreten"):
        kd["umrisse"] = [("kk-abgetreten", KK.ne1("Bas-Rhin", "Haute-Rhin", "Moselle"))]
    svg = KK.karte(kd, ordner, "relief.jpg")

    o = [kopf(k, ordner), "<main>"]
    o.append('<header class="seitenkopf">')
    o.append(f'<div class="kicker">{html.escape(k["kicker"])}</div>')
    o.append(f'<h1>{html.escape(k["seitentitel"])}</h1>')
    o.append('<nav class="pages" aria-label="Bereiche dieser Seite"><a href="#ueberblick" data-reiter="ueberblick">Überblick</a><a href="#karte" data-reiter="karte">Karte und Verlauf</a><a href="#personen" data-reiter="personen">Personen</a><a href="#quellen" data-reiter="quellen">Quellen</a></nav>')
    o.append("</header>")

    # Überblick
    o.append('<section class="reiter-teil" id="ueberblick" data-reiter="ueberblick">')
    o.append(f'<p class="lead">{q(k["lead"])}</p>')
    o.append('<dl class="steckbrief">')
    for dt, dd in k["steckbrief"]:
        o.append(f"<div><dt>{html.escape(dt)}</dt><dd>{q(dd)}</dd></div>")
    o.append("</dl>")
    for h, absaetze in k["abschnitte"]:
        hid = re.sub(r"[^a-z]+", "-", h.lower()).strip("-")
        o.append(f'<h2 id="{hid}">{html.escape(h)}</h2>')
        if h == "Ergebnis und Folgen":
            o.append('<p class="verweis">Den Verlauf mit allen Gefechten zeigt der Reiter <a href="#karte">Karte und Verlauf</a>.</p>')
        for a in absaetze: o.append(f"<p>{q(a)}</p>")
    o.append('<section class="kasten" aria-labelledby="h-einordnung"><h3 id="h-einordnung"><span class="marke deutung">Einordnung</span>Lesarten</h3>')
    for a in k["einordnung"]: o.append(f"<p>{q(a)}</p>")
    o.append("</section>")
    o.append("</section>")

    # Karte und Verlauf
    o.append('<section class="reiter-teil" data-reiter="karte">')
    o.append(f'<h2 id="karte">{html.escape(kd["titel"])}</h2>')
    schritte = kd.get("schritte", [])
    s_ereignis = {i: n for n, st in enumerate(schritte, 1) for i in st.get("ereignisse", [])}
    s_ohne = {j: n for n, st in enumerate(schritte, 1) for j in st.get("ohne", [])}
    if schritte:
        o.append('<div class="kk-ablauf" hidden><p class="kk-ablauf-titel">Ablauf auf der Karte</p>')
        o.append('<div class="kk-schritte" role="group" aria-label="Zeitpunkt wählen">')
        for n, st in enumerate(schritte, 1):
            o.append(f'<button type="button" data-step="{n}" aria-pressed="false"><span class="d">{html.escape(st["datum"])}</span><span class="t">{html.escape(st["titel"])}</span></button>')
        o.append('</div><p class="kk-abspiel"><button type="button" class="kk-play" aria-pressed="false">Abspielen</button><span>Die Karte zeigt je Schritt die Bewegungen und Ereignisse dieses Abschnitts.</span></p></div>')
    o.append('<div class="kk-kartenblock"><div class="kk-kartenbild">')
    o.append(svg)
    o.append('<ul class="kk-legende" aria-label="Legende">')
    for rolle, text in kd["legende"]:
        o.append(f'<li><span class="feld {"abg" if rolle=="abg" else "r-"+rolle}"></span>{html.escape(text)}</li>')
    o.append('<li><span class="feld fluss"></span>Flüsse und Seen</li>')
    if kd.get("schritte"):
        o.append('<li><span class="feld pfeil"></span>Bewegung, schematisch, Farbe nach Seite</li>')
    o.append('<li><span class="sym saebel-sym"><svg class="saebel" viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path class="kl" d="M6.6 17.4C10 12.4 14.6 7.4 21.2 2.8M17.4 17.4C14 12.4 9.4 7.4 2.8 2.8"/><path class="gr" d="M4 14.6L9.4 20M20 14.6L14.6 20"/><path class="gf" d="M6.4 17.6L3 21M17.6 17.6L21 21"/><circle class="kn" cx="2.6" cy="21.4" r="1.5"/><circle class="kn" cx="21.4" cy="21.4" r="1.5"/></svg></span>Schlacht oder Gefecht, Nummer wie im Verlauf</li>')
    o.append('<li><span class="sym saebel-sym entscheidung"><svg class="saebel" viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path class="kl" d="M6.6 17.4C10 12.4 14.6 7.4 21.2 2.8M17.4 17.4C14 12.4 9.4 7.4 2.8 2.8"/><path class="gr" d="M4 14.6L9.4 20M20 14.6L14.6 20"/><path class="gf" d="M6.4 17.6L3 21M17.6 17.6L21 21"/><circle class="kn" cx="2.6" cy="21.4" r="1.5"/><circle class="kn" cx="21.4" cy="21.4" r="1.5"/></svg></span>Entscheidende Schlacht</li>')
    o.append('<li><span class="sym">1</span>Sonstiges Ereignis</li>')
    o.append('<li><span class="sym frieden">1</span>Friedensschluss oder Proklamation</li>')
    if kd.get("kokarden"):
        for key, (name, ringe) in kd["kokarden"].items():
            rs = [10, 6.8, 3.6]
            c = "".join(f'<circle r="{r}" fill="{f}"/>' for r, f in zip(rs, ringe))
            o.append(f'<li><svg class="kok" viewBox="-11 -11 22 22" aria-hidden="true"><circle r="10.8" fill="#3A352B"/>{c}</svg>{html.escape(name)}</li>')
    o.append("</ul>")
    o.append(f'<p class="ek-hinweis">{html.escape(kd["hinweis"])} Kartengrundlagen: {q("{{KTERR,KHB,KNE}}")}</p>')
    if kd.get("kokarden"):
        teile = [KOK_BELEG[x] for x in ("oesterreich", "sachsen", "frankreich", "preussen", "daenemark") if x in kd["kokarden"]]
        o.append(f'<p class="ek-hinweis">Kokarden vereinfacht als Ringe in den Landesfarben, am Anfang der Bewegungspfeile. {q("; ".join(teile))}. '
                 'Die Kokarde Preußens steht auch für Truppen der mit Preußen verbündeten Staaten.</p>')
    o.append('</div><div class="kk-verlauf"><h3>Verlauf</h3><ol class="kk-chronik">')
    for i, e in enumerate(kd["ereignisse"], 1):
        art = e.get("art", "schlacht")
        ds = f' data-s="{s_ereignis[i]}"' if i in s_ereignis else ""
        o.append(f'<li id="e{i}" class="{art}"{ds}><span class="nr">{i}</span><div><span class="datum">{html.escape(e["datum"])}</span><strong>{html.escape(e["titel"])}</strong><p>{q(e["text"])}</p></div></li>')
    for j, (datum, titel, text) in enumerate(kd.get("ohne_ort", [])):
        ds = f' data-s="{s_ohne[j]}"' if j in s_ohne else ""
        o.append(f'<li class="ohne"{ds}><span class="nr">·</span><div><span class="datum">{html.escape(datum)}</span><strong>{html.escape(titel)}</strong><p>{q(text)}</p></div></li>')
    o.append("</ol></div></div>")
    o.append("</section>")

    # Personen
    o.append('<section class="reiter-teil" data-reiter="personen">')
    o.append('<h2 id="personen">Personen beider Seiten</h2>')
    o.append('<p>Monarchen, Politiker und Befehlshaber, die für den Verlauf des Kriegs eine Rolle spielten, geordnet nach Seite.')
    if any(p["bild"] is None for p in k["personen"]):
        o.append(' Für Personen ohne Bildnis ist noch kein gemeinfreies Porträt eingebunden.')
    o.append("</p>")
    seiten = []
    for p in k["personen"]:
        haupt = p.get("partei", p["seite"])
        if not seiten or seiten[-1][0] != haupt: seiten.append((haupt, []))
        seiten[-1][1].append(p)
    bildnr = {}
    for haupt, ps in seiten:
        o.append(f'<h3 class="seite-titel">{html.escape(haupt)}</h3><div class="personen">')
        for p in ps:
            o.append('<article class="person">')
            if p["bild"]:
                alt, kurz, _, _ = BILDER[p["bild"]]
                bildnr.setdefault(p["bild"], len(bildnr) + 1)
                o.append(f'<div class="foto"><img src="../bilder/{p["bild"]}.jpg" alt="{html.escape(alt)}" loading="lazy"></div>')
            else:
                o.append(f'<div class="foto ohne-bild" aria-hidden="true"><span>{html.escape(p["initialen"])}</span></div>')
            o.append(f'<div class="txt"><div class="staat">{html.escape(p["seite"])}</div><h3>{html.escape(p["name"])}</h3><p class="leben">{html.escape(p["leben"])}</p>')
            for t in p["text"]: o.append(f"<p>{q(t)}</p>")
            o.append("</div>")
            if p["bild"]:
                o.append(f'<p class="bild">{html.escape(BILDER[p["bild"]][1])} <a href="#b{bildnr[p["bild"]]}">Bildnachweis B{bildnr[p["bild"]]}</a></p>')
            o.append("</article>")
        o.append("</div>")
    o.append("</section>")

    # Quellen
    o.append('<section class="reiter-teil" data-reiter="quellen">')
    o.append('<h2 id="quellen">Quellen</h2>')
    o.append(f'<p>Abgerufen am {ABRUF}, sofern nicht anders angegeben. Ziel sind zwei voneinander unabhängige Quellen je Aussage; Seiten derselben Institution (etwa mehrere LeMO-Seiten des Deutschen Historischen Museums oder mehrere Lex-Artikel) gelten dabei als eine Quelle. Aussagen mit nur einer Quelle sind mit <span class="eine">eine Quelle</span> markiert. Wikipedia dient nur dem Datenabgleich. Abweichende Angaben stehen nebeneinander.</p>')
    o.append('<ol class="quellen">')
    for key, n in sorted(q.nr.items(), key=lambda x: x[1]):
        text, url = Q[key]
        host = re.sub(r"^https?://(www\.)?([^/]+).*$", r"\2", url)
        o.append(f'<li id="q{n}">{html.escape(text)} <a href="{html.escape(url)}">{html.escape(host)}</a></li>')
    o.append("</ol>")
    if bildnr:
        o.append('<h3 id="bildnachweis">Bildnachweis</h3><p>Porträts aus Wikimedia Commons, verkleinert. Lizenz und Herkunft stammen aus den Angaben der Commons-Dateiseiten und wurden nicht unabhängig geprüft.</p><ol class="quellen">')
        for b, n in sorted(bildnr.items(), key=lambda x: x[1]):
            _, _, lang, url = BILDER[b]
            o.append(f'<li id="b{n}">{html.escape(lang)} <a href="{html.escape(url)}">commons.wikimedia.org</a></li>')
        o.append("</ol>")
    o.append("</section>")
    # Weiter
    o.append('<nav class="kriegsweiter" aria-label="Weiter">')
    o.append('<a class="zurueck" href="../"><span>Zurück</span>Übersicht Einigungskriege</a>')
    o.append("</nav>")
    o.append("</main>")
    o.append('''<footer class="kk-fuss"><div class="kk-in">
  <p><a href="https://kaffeeundkommiss.github.io/">Kaffee und Kommiss</a>: Geschichte, Sicherheitspolitik und Politik mit Quellen. Private, nichtkommerzielle Zusammenstellung. Fehler gefunden? <a href="https://kaffeeundkommiss.github.io/kontakt/">Bitte mit Quelle melden</a>. <a href="https://kaffeeundkommiss.github.io/kontakt/#impressum">Impressum</a> · <a href="https://kaffeeundkommiss.github.io/kontakt/#datenschutz">Datenschutz</a></p>
</div></footer>
<script src="../ablauf.js"></script>
<script src="../../reiter.js"></script>
</body>
</html>
''')
    open(os.path.join(ordner, "index.html"), "w").write("\n".join(o))
    print(k["ordner"], "Quellen:", len(q.nr))


if __name__ == "__main__":
    for k in KRIEGE:
        seite(k)
