#!/usr/bin/env python3
"""Gliederung des Bereichs Geschichte (27.11.2026): eine Quelle für alle Bereichskacheln.

Erzeugt die reinen Bereichsseiten
  geschichte/index.html                                  Geschichte: zwei Bereiche
  geschichte/einigungskriege-kaiserreich/index.html      Einigungskriege und Kaiserreich: zwei Bereiche
  geschichte/erster-weltkrieg/<bereich>/index.html       Landkrieg, Luftkrieg, Seekrieg, Übersee, Kaiserreich 1914–1918
und setzt die Kachelreihe zwischen <!-- bereiche:anfang --> und <!-- bereiche:ende --> in die vorhandenen Übersichten
  geschichte/einigungskriege/index.html                  drei Kriege und Luchmann
  geschichte/kaiserreich/index.html                      Kaiser, Gesellschaft, Politik
  geschichte/erster-weltkrieg/werkzeuge/vorlage.html     fünf Bereiche (danach werkzeuge/bau.py dort ausführen)

Eine Kachel ohne "href" erscheint als „In Vorbereitung“: nur Titel, kein Inhalt. Inhalte kommen erst auf die
Website, wenn sie mit zwei voneinander unabhängigen Quellen belegt sind. Ist eine Seite fertig, "href" und "text"
eintragen und das Skript neu ausführen. Bereichsseiten, auf denen noch keine Seite fertig ist, tragen noindex.

Aufruf im Repo-Wurzelverzeichnis:
  python3 geschichte/werkzeuge/gliederung.py && python3 geschichte/erster-weltkrieg/werkzeuge/bau.py
"""
import html
import os
import re

WURZEL = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SITE = "https://kaffeeundkommiss.github.io/"
G = SITE + "geschichte/"
WK = G + "erster-weltkrieg/"
EUK = G + "einigungskriege-kaiserreich/"

VORSCHAU = {  # vorhandene Vorschaubilder (werkzeuge/vorschau.js); neue Bereichsseiten nutzen das ihres Oberbereichs
    "geschichte": ("geschichte.jpg?v=0f378e6e", "Kriege 1864 bis 1918: Kaffee und Kommiss"),
    "einigungskriege": ("einigungskriege.jpg?v=0e8a6dc7", "Einigungskriege 1864–1871: Kaffee und Kommiss"),
    "erster-weltkrieg": ("erster-weltkrieg.jpg?v=4285885d", "Der Erste Weltkrieg 1914–1918: drei KI-generierte Illustrationen (Soldat im Schützengraben, Flieger vor einem roten Doppeldecker, Marineoffizier an Deck), keine historischen Fotos. Kaffee und Kommiss"),
}

# ---------------------------------------------------------------------------------------------------------------
# Kacheln. Texte zu fertigen Seiten stammen aus deren eigenen, belegten Inhalten.
JUENGER = dict(titel="Ernst Jünger an der Westfront 1914–1918", href=SITE + "Stahlgewitter/", icon="juenger",
               text="Jünger wurde mit seinem Kriegsbuch „In Stahlgewittern“ bekannt. Eine Karte zeigt seinen Weg als "
                    "Infanterist mit sieben Verwundungen; dazu ein Vergleich zwischen Tagebuch und Buch.",
               hinweis="Mit Karte und Textvergleich")
BULLECOURT = dict(titel="Bullecourt 1917: ein Panzerangriff in Nordfrankreich", href=SITE + "bullecourt/", icon="bullecourt",
                  text="Australische und britische Truppen griffen 1917 bei Bullecourt eine deutsche Verteidigungsstellung "
                       "an. Beim ersten Angriff sollten zwölf Panzer die fehlende Artillerie ersetzen; er scheiterte.",
                  hinweis="Mit Karte und Kartenablauf")
RICHTHOFEN = dict(titel="Der „Rote Baron“ und sein Jagdgeschwader 1916–1918", href=SITE + "erster-Weltkrieg/", icon="richthofen",
                  text="Manfred von Richthofen gilt als erfolgreichster Jagdflieger des Krieges. Eine Karte zeigt, wo seine "
                       "Einheit an der Westfront lag; dazu Seiten zu einzelnen Ereignissen bis zu seinem Tod 1918.",
                  hinweis="Mit Karte und Ereignisseiten")

UBOOT = dict(titel="Der U-Boot-Krieg 1914–1918", href="u-boot-krieg/", icon="erster-weltkrieg",
             text="Deutsche U-Boote versenkten Tausende Handelsschiffe. Der uneingeschränkte U-Boot-Krieg ab Februar 1917 "
                  "führte zum Kriegseintritt der USA; Geleitzüge nahmen ihm die Wirkung.",
             hinweis="Mit Karte der Sperrgebiete und Lesarten")
SEESCHLACHTEN = dict(titel="Seeschlachten 1914–1916", href="seeschlachten/", icon="erster-weltkrieg",
                     text="Coronel und die Falklandinseln 1914, die Doggerbank 1915 und der Skagerrak 1916, die einzige "
                          "Schlacht der beiden Hauptflotten.",
                     hinweis="Mit zwei Karten und Lesarten")
KOLONIEN = dict(titel="Die Kolonien 1914–1918", href="kolonien/", icon="erster-weltkrieg",
                text="Togo, Kamerun, Südwestafrika, die Südsee und Tsingtau gingen schnell verloren; in Ostafrika "
                     "kämpfte Lettow-Vorbeck bis November 1918.",
                hinweis="Mit zwei Karten und Lesarten")

# "bild": (Datei in geschichte/erster-weltkrieg/bilder/bereiche/, Bildausschnitt als object-position). Bereiche ohne
# "bild" zeigen im Bildband das Muster; ein neues Bild dort ablegen, hier eintragen, Skripte neu ausführen.
# Alle Bilder im Bildband sind KI-generiert und tragen deshalb das Schild „KI-Bild“ (siehe KI_HINWEIS).
KI_HINWEIS = ("KI-generierte Illustrationen (erstellt mit Gemini und ChatGPT), keine historischen Fotos. Uniformen, "
              "Flugzeug und Schiff sind nicht quellengeprüft und zeigen keine bestimmte Person.")

WK_BEREICHE = [
    dict(ordner="landkrieg", bild=("landkrieg.jpg", "50% 14%"), titel="Landkrieg", rubrik="Bereich 1 von 5",
         einleitung="Zwei Seiten zum Krieg an Land: der Weg des Infanteristen Ernst Jünger an der Westfront und ein "
                    "Panzerangriff bei Bullecourt 1917.",
         kurz="Ernst Jünger an der Westfront · Bullecourt 1917", kacheln=[JUENGER, BULLECOURT]),
    dict(ordner="luftkrieg", bild=("luftkrieg.jpg", "58% 24%"), titel="Luftkrieg", rubrik="Bereich 2 von 5",
         einleitung="Der Krieg in der Luft: das Jagdgeschwader Richthofen an der Westfront. Eine Seite zu den Luftschiffen "
                    "ist in Vorbereitung.",
         kurz="Jagdgeschwader Richthofen · Luftschiffe (in Vorbereitung)",
         kacheln=[RICHTHOFEN, dict(titel="Luftschiffe")]),
    dict(ordner="seekrieg", bild=("seekrieg.jpg", "50% 12%"), titel="Seekrieg", rubrik="Bereich 3 von 5",
         einleitung="Der Krieg auf See: der deutsche U-Boot-Krieg gegen den Handel von 1914 bis 1918 und die großen "
                    "Seeschlachten von Coronel bis zum Skagerrak.",
         kurz="U-Boot-Krieg · Seeschlachten",
         kacheln=[UBOOT, SEESCHLACHTEN]),
    dict(ordner="uebersee", titel="Krieg in Übersee", rubrik="Bereich 4 von 5",
         einleitung="Der Krieg außerhalb Europas: wie das Reich seine Kolonien verlor. Eine Seite zu Felix Graf von "
                    "Luckner ist in Vorbereitung.",
         kurz="Kolonien · Felix Graf von Luckner (in Vorbereitung)",
         kacheln=[KOLONIEN, dict(titel="Felix Graf von Luckner")]),
    dict(ordner="kaiserreich", titel="Kaiserreich 1914–1918", rubrik="Bereich 5 von 5",
         einleitung="Das Deutsche Reich im Krieg. Alle drei Seiten dieses Bereichs sind in Vorbereitung.",
         kurz="Kaiser · Ludendorff und Hindenburg · Revolution (in Vorbereitung)",
         kacheln=[dict(titel="Der Kaiser"), dict(titel="Ludendorff und Hindenburg"), dict(titel="Revolution")]),
]

EK_KACHELN = [
    dict(rubrik="Krieg 1 von 3", titel="Deutsch-Dänischer Krieg 1864", href="1864/", icon="einigungskriege", muster=True,
         text="Preußen und Österreich gegen Dänemark, im Streit um das Herzogtum Schleswig.", hinweis="Mit Reliefkarte und Personen"),
    dict(rubrik="Krieg 2 von 3", titel="Deutscher Krieg 1866", href="1866/", icon="einigungskriege", muster=True,
         text="Preußen und Italien gegen Österreich und dessen Verbündete.", hinweis="Mit Reliefkarte und Personen"),
    dict(rubrik="Krieg 3 von 3", titel="Deutsch-Französischer Krieg 1870/71", href="1870-71/", icon="einigungskriege", muster=True,
         text="Frankreich gegen die deutschen Staaten unter preußischer Führung.", hinweis="Mit Reliefkarte und Personen"),
    dict(rubrik="Ein Soldat in zwei Kriegen", titel="Feldwebel Luchmann 1866 und 1870/71", href=SITE + "luchmann187071/",
         icon="luchmann", muster=True,
         text="Ein Soldat aus Brandenburg schrieb seine Erlebnisse später in einem Heft nieder; Karten folgen seinem Text.",
         hinweis="Mit Karten und Quellenabgleich"),
]

KR_KACHELN = [
    dict(titel="Der Kaiser", icon="kaiserreich", muster=True),
    dict(titel="Gesellschaft", icon="kaiserreich", muster=True),
    dict(rubrik="Auf dieser Seite", titel="Politik", href="#verfassung", icon="kaiserreich", muster=True,
         text="Reichsverfassung, Militär und Bismarcks Bündnissystem, dazu die Bündniskarte 1871–1907.",
         hinweis="Weiter unten auf dieser Seite"),
]


# ---------------------------------------------------------------------------------------------------------------
def e(s):
    return html.escape(s, quote=True)


def kachel(k, pre, gross=False):
    """Eine Kachel im Stil der Bereichsübersichten. pre: relativer Weg zum Repo-Wurzelordner."""
    klassen = "projekt kk-b-gesch" + (" kk-einigung" if k.get("muster") else "") + (" gross" if gross else "")
    icon = k.get("icon", "erster-weltkrieg")
    band = f'<span class="band"><img src="{pre}icons/{icon}.svg" alt="" width="40" height="40"></span>'
    if not k.get("href"):
        return (f'      <div class="{klassen} vorbereitung">\n        {band}\n'
                f'        <span class="rubrik">In Vorbereitung</span>\n'
                f'        <span class="titel">{e(k["titel"])}</span>\n'
                f'        <span class="hinweis">Seite folgt</span>\n      </div>')
    return (f'      <a class="{klassen}" href="{e(k["href"])}">\n        {band}\n'
            f'        <span class="rubrik">{e(k.get("rubrik", "Seite"))}</span>\n'
            f'        <span class="titel">{e(k["titel"])}</span>\n'
            f'        <span class="text">{e(k["text"])}</span>\n'
            f'        <span class="hinweis">{e(k["hinweis"])}</span>\n      </a>')


def bildwahl(bereiche, pre):
    """Bildband der fünf Weltkriegs-Bereiche (Vorschlag B, 28.11.2026). pre: relativer Weg zum Repo-Wurzelordner."""
    teile = []
    for b in bereiche:
        if b.get("bild"):
            datei, pos = b["bild"]
            bild = (f'<img src="bilder/bereiche/{e(datei)}" alt="" style="object-position:{e(pos)}" loading="lazy">'
                    '<span class="ki">KI-Bild</span>')
            klasse = "bw mit-foto"
        else:
            bild = (f'<span class="bw-muster"><img src="{pre}icons/erster-weltkrieg.svg" alt="" width="48" '
                    'height="48"></span>')
            klasse = "bw ohne-foto"
        teile.append(f'      <a class="{klasse}" href="{e(b["ordner"])}/">{bild}<span class="bw-text">'
                     f'<span class="bw-rubrik">{e(b["rubrik"])}</span><span class="bw-titel">{e(b["titel"])}</span>'
                     f'<span class="bw-kurz">{e(b["kurz"])}</span></span></a>')
    hinweis = f'    <p class="ki-hinweis"><span class="ki">KI-Bild</span> {e(KI_HINWEIS)}'
    if any(not b.get("bild") for b in bereiche):
        hinweis += " Bereiche ohne Bild erhalten ihres später."
    return '    <div class="bildwahl">\n' + "\n".join(teile) + "\n    </div>\n" + hinweis + "</p>"


def raster(kacheln, pre, klasse="bereiche-raster", gross=False):
    return f'    <div class="{klasse}">\n' + "\n".join(kachel(k, pre, gross) for k in kacheln) + "\n    </div>"


def seite(*, pfad, titel, beschreibung, kicker, h1, einleitung, name, unter, icon, vorschau, pfadleiste, inhalt,
          noindex=False, muster=False):
    tiefe = pfad.count("/")
    pre = "../" * tiefe
    url = SITE + pfad
    bild, alt = VORSCHAU[vorschau]
    robots = '<meta name="robots" content="noindex">\n' if noindex else ""
    kopf = ""
    if pfadleiste:
        teile = [f'<a href="{e(h)}">{e(t)}</a>' for t, h in pfadleiste]
        kopf = ('<nav class="kk-pfad" aria-label="Pfad"><div class="kk-in">' + " › ".join(teile)
                + f' › <span aria-current="page">{e(name)}</span></div></nav>\n')
    schild_href = pfadleiste[-1][1] if pfadleiste else SITE
    return f'''<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<!-- Erzeugt mit geschichte/werkzeuge/gliederung.py, dort ändern -->
<title>{e(titel)} · Kaffee und Kommiss</title>
<meta name="description" content="{e(beschreibung)}">
{robots}<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:locale" content="de_DE">
<meta property="og:site_name" content="Kaffee und Kommiss">
<meta property="og:title" content="{e(titel)} · Kaffee und Kommiss">
<meta property="og:description" content="{e(beschreibung)}">
<meta property="og:url" content="{url}">
<!-- Vorschau für Linkvorschauen, erzeugt mit werkzeuge/vorschau.js -->
<meta property="og:image" content="{SITE}vorschau/{bild}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{e(alt)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{SITE}vorschau/{bild}">
<link rel="icon" href="{pre}icons/{icon}.svg" type="image/svg+xml">
<link rel="icon" href="{pre}favicon-32.png" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" sizes="180x180" href="{pre}apple-touch-icon.png?v=2">
<meta name="theme-color" content="#23211C">
<link rel="stylesheet" href="{SITE}schriften/schriften.css">
<link rel="stylesheet" href="{pre}basis.css">
<link rel="stylesheet" href="{pre}style.css">
</head>
<body class="kk-b-gesch kk-breit{' kk-einigung' if muster else ''}">
<div class="kk-leiste"><div class="kk-in">
  <a class="kk-haus" href="{SITE}"><img src="{pre}kk-tasse.svg" alt="" width="22" height="22"><span>Kaffee und Kommiss</span></a>
  <nav class="kk-bereiche" aria-label="Bereiche"><a href="{G}" aria-current="true">Geschichte</a><a href="{SITE}sicherheitspolitik/"><span class="kk-lang">Sicherheitspolitik</span><span class="kk-kurz">Sicherheit</span></a><a href="{SITE}politik/">Politik</a></nav>
</div></div>
{kopf}<header class="kk-kopf">
  <div class="wrap">
    <a class="kk-schild" href="{e(schild_href)}">
      <img class="logo" src="{pre}icons/{icon}.svg" alt="" width="44" height="44">
      <div>
        <div class="kk-name">{e(name)}</div>
        <div class="kk-unter">{e(unter)}</div>
      </div>
    </a>
  </div>
</header>

<main>
  <section class="einleitung mittig">
    <div class="kicker">{e(kicker)}</div>
    <h1>{e(h1)}</h1>
    <p>{e(einleitung)}</p>
  </section>

{inhalt}
</main>

<footer class="kk-fuss"><div class="kk-in">
  <p><a href="{SITE}">Kaffee und Kommiss</a>: Geschichte, Sicherheitspolitik und Politik mit Quellen. Private, nichtkommerzielle Zusammenstellung. Fehler gefunden? <a href="{SITE}kontakt/">Bitte mit Quelle melden</a>. <a href="{SITE}kontakt/#impressum">Impressum</a> · <a href="{SITE}kontakt/#datenschutz">Datenschutz</a></p>
</div></footer>
</body>
</html>
'''


def abschnitt(gid, titel, koerper):
    return (f'  <section class="themen" aria-labelledby="{gid}">\n    <h2 class="gruppe" id="{gid}">{e(titel)}</h2>\n'
            f'{koerper}\n  </section>\n')


def bezuege(gid, titel, eintraege):
    a = "\n".join(f'      <a href="{e(h)}"><b>{e(t)}</b><span>{e(s)}</span></a>' for t, h, s in eintraege)
    return (f'  <section class="bezuege" aria-labelledby="{gid}">\n    <h2 class="gruppe" id="{gid}">{e(titel)}</h2>\n'
            f'    <div class="bezug-liste">\n{a}\n    </div>\n  </section>\n')


def schreiben(rel, text):
    ziel = os.path.join(WURZEL, rel)
    os.makedirs(os.path.dirname(ziel), exist_ok=True)
    with open(ziel, "w", encoding="utf-8") as f:
        f.write(text)
    print("geschrieben:", rel)


def einsetzen(rel, block):
    ziel = os.path.join(WURZEL, rel)
    s = open(ziel, encoding="utf-8").read()
    neu, n = re.subn(r"<!-- bereiche:anfang -->.*?<!-- bereiche:ende -->",
                     lambda m: "<!-- bereiche:anfang -->\n" + block + "\n  <!-- bereiche:ende -->", s, flags=re.S)
    if n != 1:
        raise SystemExit(f"{rel}: Marken <!-- bereiche:anfang/ende --> fehlen")
    if neu != s:
        open(ziel, "w", encoding="utf-8").write(neu)
        print("aktualisiert:", rel)


def main():
    # 1. Geschichte
    oben = [
        dict(rubrik="Bereich 1 von 2 · 1864–1914", titel="Einigungskriege und Kaiserreich", href="einigungskriege-kaiserreich/",
             icon="einigungskriege", muster=True,
             text="Die drei Kriege von 1864 bis 1871, an deren Ende das Deutsche Kaiserreich stand, die Erlebnisse des "
                  "Feldwebels Luchmann und das Kaiserreich bis 1914.",
             hinweis="Einigungskriege · Kaiserreich 1871–1914"),
        dict(rubrik="Bereich 2 von 2 · 1914–1918", titel="Erster Weltkrieg", href="erster-weltkrieg/", icon="erster-weltkrieg",
             text="Wie es zum Krieg kam und welche Staaten wann beteiligt waren, dazu Seiten zum Krieg an Land, in der Luft, "
                  "auf See, in Übersee und zum Kaiserreich im Krieg.",
             hinweis="Landkrieg · Luftkrieg · Seekrieg · Übersee · Kaiserreich 1914–1918"),
    ]
    inhalt = abschnitt("g-bereiche", "Zwei Bereiche", raster(oben, "../", "bereiche-raster zwei", gross=True))
    inhalt += bezuege("g-bezug", "Bezüge zu den anderen Bereichen", [
        ("Sicherheitspolitik: Die Bundeswehr seit 1955", SITE + "sicherheitspolitik/bundeswehr/",
         "Die Streitkräfte der Bundesrepublik: Gründung 1955, Auftrag im Bündnis und Auslandseinsätze bis heute."),
        ("Sicherheitspolitik und Politik: Parlament und Armee", SITE + "sicherheitspolitik/bundeswehr/#parlament",
         "Heute entscheidet der Bundestag über bewaffnete Auslandseinsätze. Wie es dazu kam und wie ein Mandat entsteht, "
         "zeigt der Abschnitt „Parlamentsarmee“."),
    ])
    besch = ("Geschichte von 1864 bis 1918 in zwei Bereichen: Einigungskriege und Kaiserreich 1864–1914 sowie der Erste "
             "Weltkrieg 1914–1918 mit Landkrieg, Luftkrieg, Seekrieg, Übersee und dem Kaiserreich im Krieg, jede Angabe mit Quelle.")
    schreiben("geschichte/index.html", seite(
        pfad="geschichte/", titel="Geschichte", beschreibung=besch, kicker="Bereich Geschichte", h1="Geschichte 1864–1918",
        einleitung="Zwei Bereiche: die Einigungskriege und das Kaiserreich von 1864 bis 1914 sowie der Erste Weltkrieg "
                   "1914–1918. Jede Aussage auf den Themenseiten trägt Quellen, Widersprüche zwischen ihnen sind ausgewiesen.",
        name="Geschichte", unter="Kriege 1864 bis 1918, mit Karten und Belegen", icon="geschichte", vorschau="geschichte",
        pfadleiste=None, inhalt=inhalt))

    # 2. Einigungskriege und Kaiserreich
    kacheln = [
        dict(rubrik="Bereich 1 von 2", titel="Einigungskriege 1864–1871", href="../einigungskriege/", icon="einigungskriege",
             muster=True,
             text="Drei Kriege in sieben Jahren: 1864 gegen Dänemark, 1866 zwischen Preußen und Österreich, 1870/71 gegen "
                  "Frankreich. Dazu ein Soldat, der in zwei dieser Kriege kämpfte: Feldwebel Luchmann.",
             hinweis="1864 · 1866 · 1870/71 · Feldwebel Luchmann"),
        dict(rubrik="Bereich 2 von 2", titel="Kaiserreich 1871–1914", href="../kaiserreich/", icon="kaiserreich", muster=True,
             text="Das Deutsche Kaiserreich von der Gründung 1871 bis 1914. Fertig ist die Politik: Reichsverfassung, "
                  "Militär und Bismarcks Bündnissystem mit einer Karte der Bündnisse 1871–1907.",
             hinweis="Kaiser · Gesellschaft · Politik"),
    ]
    inhalt = abschnitt("g-bereiche", "Zwei Bereiche", raster(kacheln, "../../", "bereiche-raster zwei", gross=True))
    inhalt += bezuege("g-weiter", "Danach", [
        ("Erster Weltkrieg 1914–1918", WK, "Das Kaiserreich zog 1914 in den Krieg: Ursachen, Julikrise, Verlauf und Kriegsende."),
    ])
    schreiben("geschichte/einigungskriege-kaiserreich/index.html", seite(
        pfad="geschichte/einigungskriege-kaiserreich/", titel="Einigungskriege und Kaiserreich 1864–1914",
        beschreibung="Die Einigungskriege 1864 bis 1871 mit Feldwebel Luchmann und das Deutsche Kaiserreich 1871 bis 1914 "
                     "mit Kaiser, Gesellschaft und Politik, jede Angabe mit Quelle.",
        kicker="Geschichte · 1864–1914", h1="Einigungskriege und Kaiserreich",
        einleitung="Zwei Bereiche: die Einigungskriege von 1864 bis 1871 und das Deutsche Kaiserreich von seiner Gründung "
                   "1871 bis zum Beginn des Ersten Weltkriegs 1914.",
        name="Einigungskriege und Kaiserreich", unter="1864 bis 1914, mit Karten und Belegen", icon="einigungskriege",
        vorschau="einigungskriege", pfadleiste=[("Geschichte", G)], inhalt=inhalt, muster=True))

    # 3. Fünf Bereiche des Ersten Weltkriegs
    for b in WK_BEREICHE:
        fertig = any(k.get("href") for k in b["kacheln"])
        hinweis = ('    <p class="vorbereitung-hinweis">Seiten „in Vorbereitung“ erscheinen erst mit Inhalt, wenn jede '
                   'Aussage mit zwei voneinander unabhängigen Quellen belegt ist.</p>') \
            if any(not k.get("href") for k in b["kacheln"]) else ""
        koerper = raster(b["kacheln"], "../../../") + ("\n" + hinweis if hinweis else "")
        inhalt = abschnitt("g-seiten", "Seiten in diesem Bereich", koerper)
        andere = [(x["titel"], WK + x["ordner"] + "/", x["kurz"]) for x in WK_BEREICHE if x is not b]
        andere.append(("Übersicht Erster Weltkrieg", WK, "Ursachen, Julikrise, Kriegsende, Kriegsschuldfrage, Karte der beteiligten Staaten"))
        inhalt += bezuege("g-andere", "Die anderen Bereiche", andere)
        schreiben(f"geschichte/erster-weltkrieg/{b['ordner']}/index.html", seite(
            pfad=f"geschichte/erster-weltkrieg/{b['ordner']}/", titel=f"{b['titel']} · Erster Weltkrieg",
            beschreibung=f"Erster Weltkrieg, Bereich {b['titel']}: {b['kurz']}.",
            kicker=f"Erster Weltkrieg · {b['rubrik']}", h1=b["titel"], einleitung=b["einleitung"],
            name=b["titel"], unter="Erster Weltkrieg 1914–1918", icon="erster-weltkrieg", vorschau="erster-weltkrieg",
            pfadleiste=[("Geschichte", G), ("Erster Weltkrieg 1914–1918", WK)], inhalt=inhalt, noindex=not fertig))

    # 4. Kachelreihen in den vorhandenen Übersichten
    einsetzen("geschichte/erster-weltkrieg/werkzeuge/vorlage.html",
              '  <section class="themen bereiche" data-reiter="ueberblick" aria-labelledby="h-bereiche">\n'
              '    <h2 class="gruppe" id="h-bereiche">Fünf Bereiche</h2>\n' + bildwahl(WK_BEREICHE, "../../")
              + '\n    <p class="bereiche-auch">Außerdem: <a href="technik/">Technik im Modell</a>, drehbare 3D-Modelle '
                'von Schützengraben, Flugzeug, Panzer und Gewehr.</p>\n  </section>')
    einsetzen("geschichte/einigungskriege/index.html",
              '  <section class="themen bereiche" data-reiter="ueberblick" aria-labelledby="h-bereiche">\n'
              '    <h2 class="gruppe" id="h-bereiche">Drei Kriege und ein Soldat</h2>\n' + raster(EK_KACHELN, "../../", "bereiche-raster vier")
              + '\n  </section>')
    einsetzen("geschichte/kaiserreich/index.html",
              '  <section class="themen bereiche" data-reiter="ueberblick" aria-labelledby="h-bereiche">\n'
              '    <h2 class="gruppe" id="h-bereiche">Drei Bereiche</h2>\n' + raster(KR_KACHELN, "../../", "bereiche-raster drei")
              + '\n    <p class="vorbereitung-hinweis">Seiten „in Vorbereitung“ erscheinen erst mit Inhalt, wenn jede '
                'Aussage mit zwei voneinander unabhängigen Quellen belegt ist.</p>\n  </section>')


if __name__ == "__main__":
    main()
