#!/usr/bin/env python3
"""Erzeugt sitemap.xml für alle Seiten unter https://kaffeeundkommiss.github.io/.

Die Seiten liegen in 16 Repos, deren GitHub-Pages-Seiten alle unter diesem Host erscheinen.
Das Skript folgt deshalb den Links der Live-Seiten (nur dieser Host, nur HTML), statt Repos zu lesen.

- Adresse: <link rel="canonical">, sonst die abgerufene Adresse.
- Ausgelassen: Seiten mit <meta name="robots" content="noindex">, Fehlerseiten, Nicht-HTML.
- lastmod: Last-Modified-Header von GitHub Pages (Zeitpunkt der letzten Veröffentlichung des Repos,
  nicht der einzelnen Seite).

Aufruf im Repo-Wurzelverzeichnis:  python3 werkzeuge/sitemap.py
Danach sitemap.xml prüfen und committen. Neu erzeugen, wenn Seiten hinzukommen oder wegfallen.
"""
import re
import sys
import urllib.parse
import urllib.request
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser

START = "https://kaffeeundkommiss.github.io/"
HOST = urllib.parse.urlsplit(START).netloc
AUSLASSEN = re.compile(r"/(werkzeuge|tests|vorlage|schriften|node_modules)/|\.vorlage\.html$", re.I)
GRENZE = 500  # Startwert: Sicherung gegen Endlosschleifen


class Leser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.canonical, self.noindex = [], None, False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
        elif tag == "link" and (a.get("rel") or "").lower() == "canonical" and a.get("href"):
            self.canonical = a["href"]
        elif tag == "meta" and (a.get("name") or "").lower() == "robots" and "noindex" in (a.get("content") or "").lower():
            self.noindex = True


def normal(url):
    teile = urllib.parse.urlsplit(url)
    pfad = teile.path or "/"
    if pfad.endswith("/index.html"):
        pfad = pfad[: -len("index.html")]
    return urllib.parse.urlunsplit(("https", teile.netloc.lower(), pfad, "", ""))


def holen(url):
    anfrage = urllib.request.Request(url, headers={"User-Agent": "sitemap-skript"})
    with urllib.request.urlopen(anfrage, timeout=30) as antwort:
        if "text/html" not in antwort.headers.get("Content-Type", ""):
            return None, None, antwort.geturl()
        return antwort.read().decode("utf-8", "replace"), antwort.headers.get("Last-Modified"), antwort.geturl()


def main():
    offen, gesehen, eintraege = [START], {START}, {}
    while offen and len(gesehen) <= GRENZE:
        url = offen.pop(0)
        try:
            text, geaendert, endadresse = holen(url)
        except Exception as fehler:  # 404 u. a.: nicht aufnehmen
            print("übersprungen:", url, fehler, file=sys.stderr)
            continue
        if text is None:
            continue
        leser = Leser()
        leser.feed(text)
        for href in leser.links:
            ziel = normal(urllib.parse.urljoin(endadresse, href))
            if urllib.parse.urlsplit(ziel).netloc != HOST or AUSLASSEN.search(ziel):
                continue
            if not (ziel.endswith("/") or ziel.endswith(".html")):
                continue
            if ziel not in gesehen:
                gesehen.add(ziel)
                offen.append(ziel)
        if leser.noindex:
            continue
        adresse = normal(urllib.parse.urljoin(endadresse, leser.canonical)) if leser.canonical else normal(endadresse)
        if urllib.parse.urlsplit(adresse).netloc != HOST:
            continue
        datum = parsedate_to_datetime(geaendert).date().isoformat() if geaendert else None
        eintraege[adresse] = datum

    zeilen = ['<?xml version="1.0" encoding="UTF-8"?>',
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for adresse in sorted(eintraege):
        zeilen.append("  <url><loc>%s</loc>%s</url>" % (
            adresse.replace("&", "&amp;"),
            "<lastmod>%s</lastmod>" % eintraege[adresse] if eintraege[adresse] else ""))
    zeilen.append("</urlset>")
    with open("sitemap.xml", "w", encoding="utf-8") as datei:
        datei.write("\n".join(zeilen) + "\n")
    print(len(eintraege), "Seiten in sitemap.xml")


if __name__ == "__main__":
    main()
