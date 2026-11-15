#!/usr/bin/env python3
"""Baut geschichte/erster-weltkrieg/index.html und daten.js aus den Daten in dieser Datei.
Inhalte nur hier ändern, dann: python3 werkzeuge/bau.py
Die Karte (karte.svg) erzeugt werkzeuge/karte.py; sie wird hier eingebettet.
Alle Quellen abgerufen am 15.11.2026."""
import json, pathlib, html

HIER = pathlib.Path(__file__).resolve().parent.parent
ABRUF = '15.11.2026'

# ---------------------------------------------------------------- Quellen
# id: (Kurztitel mit Institution/Autor, URL, Zusatz)
Q = {
 'L14': ('Deutsches Historisches Museum (DHM), LeMO: Jahreschronik 1914', 'https://www.dhm.de/lemo/jahreschronik/1914', ''),
 'L15': ('DHM, LeMO: Jahreschronik 1915', 'https://www.dhm.de/lemo/jahreschronik/1915', ''),
 'L16': ('DHM, LeMO: Jahreschronik 1916', 'https://www.dhm.de/lemo/jahreschronik/1916', ''),
 'L17': ('DHM, LeMO: Jahreschronik 1917', 'https://www.dhm.de/lemo/jahreschronik/1917', ''),
 'L18': ('DHM, LeMO: Jahreschronik 1918', 'https://www.dhm.de/lemo/jahreschronik/1918', ''),
 'LJK': ('DHM, LeMO: Die Juli-Krise 1914', 'https://www.dhm.de/lemo/kapitel/erster-weltkrieg/kriegsverlauf/juli-krise-1914', ''),
 'LKV': ('DHM, LeMO: Erster Weltkrieg, Kriegsverlauf', 'https://www.dhm.de/lemo/kapitel/erster-weltkrieg/kriegsverlauf', ''),
 'LEW': ('DHM, LeMO: Der Erste Weltkrieg (Kapitelseite)', 'https://www.dhm.de/lemo/kapitel/erster-weltkrieg', ''),
 'LAP': ('DHM, LeMO: Kaiserreich, Außenpolitik', 'https://www.dhm.de/lemo/kapitel/kaiserreich/aussenpolitik', ''),
 'LBB': ('DHM, LeMO: Bismarcks Bündnissystem', 'https://www.dhm.de/lemo/kapitel/kaiserreich/aussenpolitik/bismarcks-buendnissystem', ''),
 'LFB': ('DHM, LeMO: Flottenbau', 'https://www.dhm.de/lemo/kapitel/kaiserreich/aussenpolitik/flottenbau', ''),
 'LM5': ('DHM, LeMO: Marokko-Krise 1905/06', 'https://www.dhm.de/lemo/kapitel/kaiserreich/aussenpolitik/marokko-krise-190506', ''),
 'LM1': ('DHM, LeMO: Marokko-Krise 1911', 'https://www.dhm.de/lemo/kapitel/kaiserreich/aussenpolitik/marokko-krise-1911', ''),
 'WDK': ('Wikipedia (englisch): Declarations of war during World War I', 'https://en.wikipedia.org/wiki/Declarations_of_war_during_World_War_I', 'Die Liste nennt nach eigener Angabe die Daten, ab denen ein Kriegszustand de facto bestand.'),
 'WJK': ('Wikipedia (deutsch): Julikrise', 'https://de.wikipedia.org/wiki/Julikrise', ''),
 'WKS': ('Wikipedia (deutsch): Kriegsschuldfrage', 'https://de.wikipedia.org/wiki/Kriegsschuldfrage', ''),
 'WAS': ('Wikipedia (deutsch): Attentat von Sarajevo', 'https://de.wikipedia.org/wiki/Attentat_von_Sarajevo', ''),
 'WEW': ('Wikipedia (deutsch): Erster Weltkrieg', 'https://de.wikipedia.org/wiki/Erster_Weltkrieg', ''),
 'BWW': ('Encyclopaedia Britannica: World War I (Summary)', 'https://www.britannica.com/summary/World-War-I', ''),
 'BTE': ('Encyclopaedia Britannica: Triple Entente', 'https://www.britannica.com/topic/Triple-Entente', ''),
 'AV8': ('Yale Law School, Avalon Project: Treaty of Versailles, Part VIII (Art. 231)', 'https://avalon.law.yale.edu/imt/partviii.asp', ''),
 'A14': ('Yale Law School, Avalon Project: President Woodrow Wilson’s Fourteen Points', 'https://avalon.law.yale.edu/20th_century/wilson14.asp', ''),
 'SWW': ('U.S. Department of State, Office of the Historian: U.S. Entry into World War I, 1917', 'https://history.state.gov/milestones/1914-1920/wwi', 'Seite laut Hinweis nicht mehr gepflegt.'),
 'S14': ('U.S. Department of State, Office of the Historian: Wilson’s Fourteen Points, 1918', 'https://history.state.gov/milestones/1914-1920/fourteen-points', 'Seite laut Hinweis nicht mehr gepflegt.'),
 'PCL': ('Perlentaucher: Christopher Clark, „Die Schlafwandler“ (DVA 2013), mit Rezensionsnotizen zu FAZ, SZ, ZEIT, NZZ, taz', 'https://www.perlentaucher.de/buch/christopher-clark/die-schlafwandler.html', ''),
 'HGB': ('aourednik: historical-basemaps, world_1914.geojson (GPL-3.0)', 'https://github.com/aourednik/historical-basemaps', 'Grundlage der Kartengrenzen; laut Projekt teils Näherungen.'),
}
# Personen: je Person Wikipedia und, wo erreichbar, Britannica oder LeMO
PQ = {
 'richthofen': [('Wikipedia (deutsch): Manfred von Richthofen', 'https://de.wikipedia.org/wiki/Manfred_von_Richthofen'),
                ('Encyclopaedia Britannica: Manfred, Freiherr von Richthofen', 'https://www.britannica.com/biography/Manfred-Freiherr-von-Richthofen')],
 'franzferdinand': [('Wikipedia (englisch): Archduke Franz Ferdinand of Austria', 'https://en.wikipedia.org/wiki/Archduke_Franz_Ferdinand_of_Austria'),
                ('Encyclopaedia Britannica: Franz Ferdinand, Archduke of Austria-Este', 'https://www.britannica.com/biography/Franz-Ferdinand-Archduke-of-Austria-Este')],
 'kemal': [('Wikipedia (englisch): Mustafa Kemal Atatürk', 'https://en.wikipedia.org/wiki/Mustafa_Kemal_Atat%C3%BCrk'),
           ('Encyclopaedia Britannica: Kemal Atatürk', 'https://www.britannica.com/biography/Kemal-Ataturk')],
 'ferdinand': [('Wikipedia (englisch): Ferdinand I of Bulgaria', 'https://en.wikipedia.org/wiki/Ferdinand_I_of_Bulgaria')],
 'putnik': [('Wikipedia (englisch): Radomir Putnik', 'https://en.wikipedia.org/wiki/Radomir_Putnik'),
            ('Encyclopaedia Britannica: Radomir Putnik', 'https://www.britannica.com/biography/Radomir-Putnik')],
 'nikola': [('Wikipedia (englisch): Nicholas I of Montenegro', 'https://en.wikipedia.org/wiki/Nicholas_I_of_Montenegro'),
            ('Encyclopaedia Britannica: Nicholas I, king of Montenegro', 'https://www.britannica.com/biography/Nicholas-I-king-of-Montenegro')],
 'nikolaus': [('Wikipedia (englisch): Nicholas II of Russia', 'https://en.wikipedia.org/wiki/Nicholas_II_of_Russia'),
              ('Encyclopaedia Britannica: Nicholas II, tsar of Russia', 'https://www.britannica.com/biography/Nicholas-II-tsar-of-Russia')],
 'clemenceau': [('Wikipedia (englisch): Georges Clemenceau', 'https://en.wikipedia.org/wiki/Georges_Clemenceau'),
                ('Encyclopaedia Britannica: Georges Clemenceau', 'https://www.britannica.com/biography/Georges-Clemenceau')],
 'churchill': [('Wikipedia (englisch): Winston Churchill', 'https://en.wikipedia.org/wiki/Winston_Churchill'),
               ('Encyclopaedia Britannica: Winston Churchill', 'https://www.britannica.com/biography/Winston-Churchill')],
 'albert': [('Wikipedia (englisch): Albert I of Belgium', 'https://en.wikipedia.org/wiki/Albert_I_of_Belgium'),
            ('Encyclopaedia Britannica: Albert I, king of Belgium', 'https://www.britannica.com/biography/Albert-I-king-of-Belgium')],
 'okuma': [('Wikipedia (englisch): Ōkuma Shigenobu', 'https://en.wikipedia.org/wiki/%C5%8Ckuma_Shigenobu'),
           ('Encyclopaedia Britannica: Ōkuma Shigenobu', 'https://www.britannica.com/biography/Okuma-Shigenobu')],
 'dannunzio': [('Wikipedia (englisch): Gabriele D’Annunzio', 'https://en.wikipedia.org/wiki/Gabriele_D%27Annunzio'),
               ('Encyclopaedia Britannica: Gabriele D’Annunzio', 'https://www.britannica.com/biography/Gabriele-DAnnunzio')],
 'milhais': [('Wikipedia (englisch): Aníbal Milhais', 'https://en.wikipedia.org/wiki/An%C3%ADbal_Milhais')],
 'marie': [('Wikipedia (englisch): Marie of Romania', 'https://en.wikipedia.org/wiki/Marie_of_Romania')],
 'wilson': [('Wikipedia (englisch): Woodrow Wilson', 'https://en.wikipedia.org/wiki/Woodrow_Wilson'),
            ('Encyclopaedia Britannica: Woodrow Wilson', 'https://www.britannica.com/biography/Woodrow-Wilson')],
 'venizelos': [('Wikipedia (englisch): Eleftherios Venizelos', 'https://en.wikipedia.org/wiki/Eleftherios_Venizelos')],
}

ORDER = []          # Reihenfolge der Quellen nach erstem Auftreten
def q(*ids, einfach=False):
    """Quellenverweis [n, m]; einfach=True setzt den Hinweis 'eine Quelle'."""
    nums = []
    for i in ids:
        if i not in ORDER:
            ORDER.append(i)
        nums.append(ORDER.index(i) + 1)
    links = ', '.join(f'<a href="#q-{i}">{n}</a>' for i, n in zip(ids, nums))
    s = f'<span class="q">[{links}]</span>'
    if einfach:
        s += ' <span class="einfach" title="Nur eine Quelle oder keine zwei voneinander unabhängigen Quellen">einfach belegt</span>'
    return s

# ---------------------------------------------------------------- Staaten und Karte
# p: Perioden [ab Datum, Status]; M Mittelmächte, A Alliierte, X ausgeschieden (Waffenstillstand, Kapitulation, Frieden)
# ein/aus: Text für die Tabelle; qe/qa: Quellen-IDs; einfach: nur eine Quelle
STAATEN = [
 # Kürzel, Name, Lager, Eintritt (Text), Quellen, Austritt (Text), Quellen, Perioden, Hinweis
 ('AH', 'Österreich-Ungarn', 'M', '28.07.1914', 'Kriegserklärung an Serbien', ('L14', 'WDK'), '03.11.1918', 'Waffenstillstand mit den Alliierten', ('L18',), [['1914-07-28', 'M'], ['1918-11-03', 'X']], ''),
 ('RS', 'Serbien', 'A', '28.07.1914', 'Kriegserklärung Österreich-Ungarns', ('L14', 'WDK'), '11.11.1918', 'Ende der Kämpfe', ('L18', 'WEW'), [['1914-07-28', 'A'], ['1918-11-11', 'X']], 'Ende 1915 von den Mittelmächten erobert'),
 ('DE', 'Deutsches Reich', 'M', '01.08.1914', 'Kriegserklärung an Russland', ('L14', 'WDK'), '11.11.1918', 'Waffenstillstand von Compiègne', ('L18', 'WEW'), [['1914-08-01', 'M'], ['1918-11-11', 'X']], ''),
 ('RU', 'Russland', 'A', '01.08.1914', 'Kriegserklärung des Deutschen Reichs', ('L14', 'WDK'), '15.12.1917', 'Waffenstillstand; Frieden von Brest-Litowsk 03.03.1918', ('LKV', 'L18'), [['1914-08-01', 'A'], ['1917-12-15', 'X']], 'LeMO nennt für den Waffenstillstand den 5. und den 15.12.1917'),
 ('FR', 'Frankreich', 'A', '03.08.1914', 'Kriegserklärung des Deutschen Reichs', ('L14', 'WDK'), '11.11.1918', 'Waffenstillstand von Compiègne', ('L18', 'WEW'), [['1914-08-03', 'A'], ['1918-11-11', 'X']], ''),
 ('BE', 'Belgien', 'A', '03./04.08.1914', 'Einmarsch deutscher Truppen', ('L14', 'WJK'), '11.11.1918', 'Waffenstillstand von Compiègne', ('L18',), [['1914-08-04', 'A'], ['1918-11-11', 'X']], 'Einmarsch: LeMO 3.8., Wikipedia 4.8.'),
 ('GB', 'Großbritannien (Britisches Weltreich)', 'A', '04.08.1914', 'Kriegserklärung an das Deutsche Reich', ('L14', 'WDK'), '11.11.1918', 'Waffenstillstand von Compiègne', ('L18', 'WEW'), [['1914-08-04', 'A'], ['1918-11-11', 'X']], 'Dominions und Kolonien ohne eigene Kriegserklärung mit erfasst'),
 ('ME', 'Montenegro', 'A', '05./07.08.1914', 'Kriegserklärung an Österreich-Ungarn', ('WDK', 'L14'), '25.01.1916', 'Kapitulation', ('L16', 'WEW'), [['1914-08-05', 'A'], ['1916-01-25', 'X']], 'Datum der Kriegserklärung: Wikipedia 5.8., LeMO 7.8.'),
 ('JP', 'Japan', 'A', '23.08.1914', 'Kriegserklärung an das Deutsche Reich', ('L14', 'WDK'), '11.11.1918', 'Waffenstillstand von Compiègne', ('L18',), [['1914-08-23', 'A'], ['1918-11-11', 'X']], ''),
 ('OS', 'Osmanisches Reich', 'M', 'Anfang 11.1914', 'Kriegserklärungen der Entente', ('L14', 'WDK'), '30.10.1918', 'Waffenstillstand mit den Alliierten', ('L18',), [['1914-11-02', 'M'], ['1918-10-30', 'X']], 'Wikipedia: Russland 1.11., Frankreich und Großbritannien 5.11.; LeMO: 2.–5.11.'),
 ('IT', 'Italien', 'A', '23./24.05.1915', 'Kriegserklärung an Österreich-Ungarn', ('L15', 'WDK'), '03.11.1918', 'Waffenstillstand mit Österreich-Ungarn; mit dem Deutschen Reich 11.11.', ('L18',), [['1915-05-23', 'A'], ['1918-11-11', 'X']], 'LeMO 23.5., Wikipedia 24.5.; an das Deutsche Reich erst im August 1916'),
 ('BG', 'Bulgarien', 'M', '14.10.1915', 'Kriegserklärung an Serbien', ('L15', 'WDK'), '29.09.1918', 'Waffenstillstand mit den Alliierten', ('L18',), [['1915-10-14', 'M'], ['1918-09-29', 'X']], ''),
 ('PT', 'Portugal', 'A', '09.03.1916', 'Kriegserklärung des Deutschen Reichs', ('L16', 'WDK'), '11.11.1918', 'Waffenstillstand von Compiègne', ('L18',), [['1916-03-09', 'A'], ['1918-11-11', 'X']], ''),
 ('RO', 'Rumänien', 'A', '27./28.08.1916', 'Kriegserklärung an Österreich-Ungarn', ('L16', 'WDK'), '12.1917', 'Waffenstillstand; Frieden von Bukarest 07.05.1918', ('L17', 'L18'), [['1916-08-27', 'A'], ['1917-12-09', 'X']], 'LeMO 27.8., Wikipedia 28.8.; Tag des Waffenstillstands nicht eindeutig belegt'),
 ('US', 'Vereinigte Staaten', 'A', '06.04.1917', 'Kriegserklärung an das Deutsche Reich', ('L17', 'WDK', 'SWW'), '11.11.1918', 'Waffenstillstand von Compiègne', ('L18',), [['1917-04-06', 'A'], ['1918-11-11', 'X']], 'an Österreich-Ungarn am 07.12.1917'),
 ('CU', 'Kuba', 'A', '07.04.1917', 'Kriegserklärung', ('WDK',), '11.11.1918', 'Waffenstillstand', (), [['1917-04-07', 'A'], ['1918-11-11', 'X']], ''),
 ('PA', 'Panama', 'A', '07.04.1917', 'Kriegserklärung', ('WDK',), '11.11.1918', 'Waffenstillstand', (), [['1917-04-07', 'A'], ['1918-11-11', 'X']], ''),
 ('GR', 'Griechenland', 'A', '27.06.1917', 'Kriegseintritt auf alliierter Seite', ('L17', 'WDK'), '11.11.1918', 'Waffenstillstand', (), [['1917-06-27', 'A'], ['1918-11-11', 'X']], ''),
 ('SI', 'Siam (Thailand)', 'A', '22.07.1917', 'Kriegserklärung', ('WDK',), '11.11.1918', 'Waffenstillstand', (), [['1917-07-22', 'A'], ['1918-11-11', 'X']], ''),
 ('LR', 'Liberia', 'A', '04.08.1917', 'Kriegserklärung', ('WDK',), '11.11.1918', 'Waffenstillstand', (), [['1917-08-04', 'A'], ['1918-11-11', 'X']], ''),
 ('CN', 'China', 'A', '14.08.1917', 'Kriegserklärung an Österreich-Ungarn', ('L17', 'WDK'), '11.11.1918', 'Waffenstillstand', (), [['1917-08-14', 'A'], ['1918-11-11', 'X']], 'Wikipedia nennt auch das Deutsche Reich, LeMO nur Österreich-Ungarn'),
 ('BR', 'Brasilien', 'A', '26.10.1917', 'Kriegserklärung', ('WDK',), '11.11.1918', 'Waffenstillstand', (), [['1917-10-26', 'A'], ['1918-11-11', 'X']], ''),
 ('GT', 'Guatemala', 'A', '23.04.1918', 'Kriegserklärung an das Deutsche Reich', ('WDK',), '11.11.1918', 'Waffenstillstand', (), [['1918-04-23', 'A'], ['1918-11-11', 'X']], ''),
 ('NI', 'Nicaragua', 'A', '06.05.1918', 'Kriegserklärung', ('WDK',), '11.11.1918', 'Waffenstillstand', (), [['1918-05-06', 'A'], ['1918-11-11', 'X']], ''),
 ('CR', 'Costa Rica', 'A', '23.05.1918', 'Kriegserklärung', ('WDK',), '11.11.1918', 'Waffenstillstand', (), [['1918-05-23', 'A'], ['1918-11-11', 'X']], ''),
 ('HT', 'Haiti', 'A', '12.07.1918', 'Kriegserklärung', ('WDK',), '11.11.1918', 'Waffenstillstand', (), [['1918-07-12', 'A'], ['1918-11-11', 'X']], ''),
 ('HN', 'Honduras', 'A', '19.07.1918', 'Kriegserklärung', ('WDK',), '11.11.1918', 'Waffenstillstand', (), [['1918-07-19', 'A'], ['1918-11-11', 'X']], ''),
]

SCHRITTE = [
 ('1914-06-28', 'Attentat von Sarajevo: Erzherzog Franz Ferdinand und seine Frau werden ermordet. Noch ist kein Staat im Krieg.', []),
 ('1914-07-28', 'Österreich-Ungarn erklärt Serbien den Krieg.', ['AH', 'RS']),
 ('1914-08-01', 'Das Deutsche Reich erklärt Russland den Krieg.', ['DE', 'RU']),
 ('1914-08-03', 'Das Deutsche Reich erklärt Frankreich den Krieg; deutsche Truppen marschieren in Belgien ein.', ['FR']),
 ('1914-08-04', 'Großbritannien tritt in den Krieg ein, mit ihm das Britische Weltreich. Belgien wird Kriegsschauplatz.', ['GB', 'BE']),
 ('1914-08-05', 'Montenegro erklärt Österreich-Ungarn den Krieg (Datum je nach Quelle 5. oder 7. August).', ['ME']),
 ('1914-08-23', 'Japan erklärt dem Deutschen Reich den Krieg.', ['JP']),
 ('1914-11-02', 'Anfang November: Die Entente erklärt dem Osmanischen Reich den Krieg.', ['OS']),
 ('1915-05-23', 'Italien erklärt Österreich-Ungarn den Krieg.', ['IT']),
 ('1915-10-14', 'Bulgarien tritt auf Seiten der Mittelmächte ein und erklärt Serbien den Krieg.', ['BG']),
 ('1916-01-25', 'Montenegro kapituliert.', ['ME']),
 ('1916-03-09', 'Das Deutsche Reich erklärt Portugal den Krieg.', ['PT']),
 ('1916-08-27', 'Rumänien erklärt Österreich-Ungarn den Krieg.', ['RO']),
 ('1917-04-06', 'Die Vereinigten Staaten erklären dem Deutschen Reich den Krieg; am 7. April folgen Kuba und Panama.', ['US', 'CU', 'PA']),
 ('1917-06-27', 'Griechenland tritt auf alliierter Seite in den Krieg ein.', ['GR']),
 ('1917-07-22', 'Siam erklärt den Mittelmächten den Krieg; am 4. August folgt Liberia.', ['SI', 'LR']),
 ('1917-08-14', 'China erklärt Österreich-Ungarn den Krieg.', ['CN']),
 ('1917-10-26', 'Brasilien erklärt den Krieg.', ['BR']),
 ('1917-12-09', 'Rumänien schließt mit den Mittelmächten einen Waffenstillstand (Dezember 1917).', ['RO']),
 ('1917-12-15', 'Waffenstillstand zwischen dem Deutschen Reich und Russland; Frieden von Brest-Litowsk am 3. März 1918.', ['RU']),
 ('1918-04-23', 'Guatemala erklärt dem Deutschen Reich den Krieg; bis Juli folgen Nicaragua, Costa Rica, Haiti und Honduras.', ['GT']),
 ('1918-07-19', 'Mit Honduras erklärt der letzte Staat in dieser Übersicht den Krieg.', ['NI', 'CR', 'HT', 'HN']),
 ('1918-09-29', 'Bulgarien schließt einen Waffenstillstand mit den Alliierten.', ['BG']),
 ('1918-10-30', 'Waffenstillstand zwischen den Alliierten und dem Osmanischen Reich.', ['OS']),
 ('1918-11-03', 'Waffenstillstand zwischen Österreich-Ungarn und den Alliierten.', ['AH']),
 ('1918-11-11', 'Waffenstillstand von Compiègne: Ende der Kämpfe. Die Friedensverträge folgen 1919 bis 1923.', ['DE']),
]

# ---------------------------------------------------------------- Personen
# Kürzel Staat, Staat, Bildschlüssel, Name, Lebensdaten, Text (HTML), Quellen-Schlüssel, einfach?, Link
PERSONEN = [
 ('DE', 'Deutsches Reich', 'richthofen', 'Manfred von Richthofen', '2.5.1892 Breslau – 21.4.1918 bei Vaux-sur-Somme',
  'Jagdflieger mit 80 anerkannten Luftsiegen, der höchsten Zahl des Krieges. Fiel im April 1918 an der Somme.', 'richthofen', False,
  ('https://kaffeeundkommiss.github.io/erster-Weltkrieg/', 'Zur Seite Jagdgeschwader Richthofen')),
 ('AH', 'Österreich-Ungarn', 'franzferdinand', 'Erzherzog Franz Ferdinand', '18.12.1863 Graz – 28.6.1914 Sarajevo',
  'Thronfolger Österreich-Ungarns. Seine Ermordung in Sarajevo war der unmittelbare Anlass des Krieges.', 'franzferdinand', False, None),
 ('OS', 'Osmanisches Reich', 'kemal', 'Mustafa Kemal (Atatürk)', '1881 Saloniki – 10.11.1938 Istanbul',
  'Befehligte 1915 bei der Schlacht von Gallipoli die 19. Division. Den Namen Atatürk trug er ab 1934.', 'kemal', False, None),
 ('BG', 'Bulgarien', 'ferdinand', 'Zar Ferdinand I.', '26.2.1861 Wien – 10.9.1948 Coburg',
  'Führte Bulgarien 1915 an der Seite der Mittelmächte in den Krieg. Dankte nach dem Waffenstillstand 1918 zugunsten seines Sohnes ab.', 'ferdinand', True, None),
 ('RS', 'Serbien', 'putnik', 'Radomir Putnik', '24.1.1847 Kragujevac – 17.5.1917 Nizza',
  'Chef des serbischen Generalstabs. Schlug im August 1914 am Cer die erste österreichisch-ungarische Offensive zurück.', 'putnik', False, None),
 ('ME', 'Montenegro', 'nikola', 'König Nikola I.', '7.10.1841 Njeguši – 1. oder 2.3.1921 Antibes',
  'König von Montenegro. Nach der Niederlage im Januar 1916 ging er ins Exil, zuerst nach Italien, dann nach Frankreich.', 'nikola', False, None),
 ('RU', 'Russland', 'nikolaus', 'Zar Nikolaus II.', '18.5.1868 Zarskoje Selo – 17.7.1918 Jekaterinburg',
  'Letzter russischer Kaiser. Dankte 1917 ab und wurde 1918 mit seiner Familie in Jekaterinburg ermordet.', 'nikolaus', False, None),
 ('FR', 'Frankreich', 'clemenceau', 'Georges Clemenceau', '28.9.1841 Mouilleron-en-Pareds – 24.11.1929 Paris',
  'Ministerpräsident ab 1917. In Frankreich als „Vater des Sieges“ bekannt.', 'clemenceau', False, None),
 ('GB', 'Großbritannien', 'churchill', 'Winston Churchill', '30.11.1874 Blenheim Palace – 24.1.1965 London',
  'Als Erster Lord der Admiralität verantwortlich für den gescheiterten Angriff auf die Dardanellen 1915. Danach Bataillonskommandeur an der Westfront, ab 1917 Munitionsminister.', 'churchill', True, None),
 ('BE', 'Belgien', 'albert', 'König Albert I.', '8.4.1875 Brüssel – 17.2.1934 Marche-les-Dames',
  'Führte die belgische Armee während des ganzen Krieges. 1918 befehligte er die französisch-belgische Nordgruppe, die Ostende und Brügge einnahm.', 'albert', False, None),
 ('JP', 'Japan', 'okuma', 'Ōkuma Shigenobu', '11.3.1838 Saga – 10.1.1922 Tokio',
  'Premierminister 1914 bis 1916, als Japan auf Seiten der Alliierten in den Krieg eintrat.', 'okuma', False, None),
 ('IT', 'Italien', 'dannunzio', 'Gabriele D’Annunzio', '12.3.1863 Pescara – 1.3.1938 Gardone Riviera',
  'Schriftsteller und Kriegsflieger. Führte am 9. August 1918 den Flug über Wien, bei dem Flugblätter abgeworfen wurden.', 'dannunzio', True, None),
 ('PT', 'Portugal', 'milhais', 'Aníbal Milhais', '9.7.1895 Murça – 3.6.1970 Murça',
  'Soldat am Maschinengewehr in der Schlacht an der Lys am 9. April 1918. In Portugal als „Soldado Milhões“ bekannt.', 'milhais', True, None),
 ('RO', 'Rumänien', 'marie', 'Königin Maria', '29.10.1875 Eastwell (Kent) – 18.7.1938',
  'Königin ab Oktober 1914. Pflegte mit ihren Töchtern Verwundete in Lazaretten.', 'marie', True, None),
 ('US', 'Vereinigte Staaten', 'wilson', 'Woodrow Wilson', '28.12.1856 Staunton – 3.2.1924 Washington',
  'Präsident 1913 bis 1921. Führte die USA 1917 in den Krieg und legte am 8. Januar 1918 seine Vierzehn Punkte vor.', 'wilson', False, None),
 ('GR', 'Griechenland', 'venizelos', 'Eleftherios Venizelos', '23.8.1864 Mournies (Kreta) – 18.3.1936 Paris',
  'Ministerpräsident. Brachte Griechenland 1917 auf die Seite der Alliierten.', 'venizelos', True, None),
]
# Zusätzliche Belege einzelner Personenaussagen aus den allgemeinen Quellen
PERSON_ZUSATZ = {'wilson': ('A14', 'S14')}


# ---------------------------------------------------------------- Bildnachweis
# Schlüssel: (Commons-Dateiname, Urheber, Datum, Lizenz) – alles nur laut Commons-Beschreibung, nicht unabhängig geprüft.
BILDER = {
 'richthofen': ('Manfred von Richthofen.jpg', 'C. J. von Dühren (gest. 1931), Postkarte Willi Sanke Nr. 503', 'um 1917', 'gemeinfrei'),
 'franzferdinand': ('Archduke Franz Ferdinand (48059749968).jpg', 'Carl Pietzner', 'um 1896', 'gemeinfrei'),
 'kemal': ('Mustafa Kemal in Gallipoli.jpg', 'unbekannt (Quelle: türkischer Generalstab)', '1915', 'gemeinfrei'),
 'ferdinand': ('BASA-237K-1-361-1a-Ferdinand I of Bulgaria, 1915.jpg', 'unbekannt (Bulgarische Staatsarchive)', 'vor 1915', 'gemeinfrei'),
 'putnik': ('Général Putnik, généralissime serbe - btv1b69310497.jpg', 'Agence Rol (Bibliothèque nationale de France)', '1914', 'gemeinfrei'),
 'nikola': ('Nicholas I, King of Montenegro, 1841-1921, head and shoulders portrait, facing left LCCN2005680731.tif', 'George Grantham Bain Collection (Library of Congress)', 'ohne Datum', 'gemeinfrei'),
 'nikolaus': ('Nicholas II by E.Lipgart (1914, Russian museum).jpg', 'Ernst von Liphart (Gemälde)', '1914', 'gemeinfrei'),
 'clemenceau': ('CLEMENCEAU, Georges, Nadar, GALLICA.jpg', 'Paul Nadar (Gallica)', 'um 1910', 'CC0'),
 'churchill': ('Churchill Admiralty Uniform 1914.jpg', 'unbekannt', '16.09.1914', 'gemeinfrei'),
 'albert': ('Portrait of Albert I of Belgium (cropped).jpg', 'Richard Speaight', '1917', 'gemeinfrei'),
 'okuma': ('Okuma Shigenobu bust portrait.jpg', 'unbekannt (Diplomatisches Archiv des japanischen Außenministeriums)', 'vor 1922', 'gemeinfrei'),
 'dannunzio': ('Photo of prince d\' annunzio.jpg', 'unbekannt', '1920', 'gemeinfrei'),
 'milhais': ('Anibal Milhais.jpg', 'J. Fernandes (Biblioteca Nacional de Portugal)', '1918', 'gemeinfrei'),
 'marie': ('Queen Marie of Romania wearing the steel crown.jpg', 'Adolf Klingsberg', '1922', 'gemeinfrei'),
 'wilson': ('Thomas Woodrow Wilson, Harris & Ewing bw photo portrait, 1919.jpg', 'Harris & Ewing (Library of Congress)', '1919', 'gemeinfrei'),
 'venizelos': ('Eleftherios Venizelos 1917.jpg', 'Agence Rol (Bibliothèque nationale de France)', '1917', 'gemeinfrei'),
}


def bildnachweis_html():
    from urllib.parse import quote
    out = []
    for k, staat, bild, name, *_ in PERSONEN:
        if not (HIER / 'bilder' / f'{bild}.jpg').exists() or bild not in BILDER:
            continue
        datei, urheber, datum, lizenz = BILDER[bild]
        url = 'https://commons.wikimedia.org/wiki/File:' + quote(datei.replace(' ', '_'))
        out.append(f'<li>{esc(name)}: {esc(urheber)}, {esc(datum)}. {esc(lizenz)}. Wikimedia Commons, <a href="{url}">{esc(datei)}</a>.</li>')
    return '\n'.join(out)


def esc(s):
    return html.escape(s, quote=True)


def personen_html():
    out = []
    bilder = HIER / 'bilder'
    for k, staat, bild, name, leben, text, qk, einfach, link in PERSONEN:
        ids = []
        for i, (t, u) in enumerate(PQ[qk]):
            key = f'P-{qk}-{i}'
            Q[key] = (t, u, '')
            ids.append(key)
        ids += list(PERSON_ZUSATZ.get(qk, ()))
        datei = bilder / f'{bild}.jpg'
        if datei.exists():
            fig = f'<figure><img src="bilder/{bild}.jpg" alt="{esc(name)}" width="84" height="108" loading="lazy"></figure>'
        else:
            gross = [w for w in name.replace('(', '').split() if w[0].isupper() and w not in ('Zar', 'König', 'Königin', 'Erzherzog')]
            ini = gross[0][0] + (gross[-1][0] if len(gross) > 1 else '')
            fig = f'<figure><div class="ohnebild" aria-hidden="true">{ini}</div></figure>'
        mehr = f'<p><a class="mehr" href="{link[0]}">{esc(link[1])}</a></p>' if link else ''
        out.append(f'''<article class="person" id="person-{k.lower()}">{fig}<div>
  <div class="staat">{esc(staat)}</div>
  <h3>{esc(name)}</h3>
  <p class="leben">{esc(leben)}</p>
  <p>{text} {q(*ids, einfach=einfach)}</p>{mehr}
</div></article>''')
    return '\n'.join(out)


def tabelle_html():
    rows = []
    lager_txt = {'M': 'Mittelmächte', 'A': 'Alliierte'}
    for k, name, lager, ein, eintxt, qe, aus, austxt, qa, per, hinweis in STAATEN:
        e1 = len(set(qe)) < 2
        a_q = q(*qa, einfach=len(set(qa)) < 2) if qa else '<span class="einfach">ohne eigenen Beleg</span>'
        h = f'<br><span class="stand">{esc(hinweis)}</span>' if hinweis else ''
        rows.append(f'<tr><td><span class="lager {lager}" aria-hidden="true"></span>{esc(name)}{h}</td><td>{lager_txt[lager]}</td>'
                    f'<td class="d">{ein}</td><td>{esc(eintxt)} {q(*qe, einfach=e1)}</td>'
                    f'<td class="d">{aus}</td><td>{esc(austxt)} {a_q}</td></tr>')
    return '\n'.join(rows)


def main():
    ORDER.clear()
    T = (HIER / 'werkzeuge' / 'vorlage.html').read_text()
    # Platzhalter {{q:ID,ID}} und {{q1:ID}} (einfach belegt) in der Vorlage ersetzen
    import re
    def rep(m):
        art, ids = m.group(1), m.group(2).split(',')
        return q(*[i.strip() for i in ids], einfach=(art == 'q1'))
    T = re.sub(r'\{\{(q1?):([^}]+)\}\}', rep, T)
    T = T.replace('{{TABELLE}}', tabelle_html())
    T = T.replace('{{PERSONEN}}', personen_html())
    T = T.replace('{{BILDER}}', bildnachweis_html())
    T = T.replace('{{KARTE}}', (HIER / 'karte.svg').read_text())
    T = T.replace('{{N_STAATEN}}', str(len(STAATEN)))
    T = T.replace('{{N_M}}', str(sum(1 for s in STAATEN if s[2] == 'M')))
    T = T.replace('{{N_A}}', str(sum(1 for s in STAATEN if s[2] == 'A')))
    # Kartenquelle immer aufführen
    q('HGB')
    ql = []
    for i in ORDER:
        t, u, z = Q[i]
        zz = f' {esc(z)}' if z else ''
        ql.append(f'<li id="q-{i}"><b>[{ORDER.index(i)+1}]</b> {esc(t)}. <a href="{u}">{esc(u)}</a>. Abgerufen am {ABRUF}.{zz}</li>')
    T = T.replace('{{QUELLEN}}', '\n'.join(ql))
    (HIER / 'index.html').write_text(T)
    daten = {
        k: {'n': name, 'p': per} for k, name, lager, ein, eintxt, qe, aus, austxt, qa, per, hinweis in STAATEN
    }
    schritte = [{'d': d, 't': t, 'k': ks} for d, t, ks in SCHRITTE]
    (HIER / 'daten.js').write_text('/* Erzeugt mit werkzeuge/bau.py, nicht von Hand ändern. */\n'
                                   'window.WK_STAATEN=' + json.dumps(daten, ensure_ascii=False, separators=(',', ':')) + ';\n'
                                   'window.WK_SCHRITTE=' + json.dumps(schritte, ensure_ascii=False, separators=(',', ':')) + ';\n')
    print('index.html und daten.js geschrieben;', len(ORDER), 'Quellen')


if __name__ == '__main__':
    main()
