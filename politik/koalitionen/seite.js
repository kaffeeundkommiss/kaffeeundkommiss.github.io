/* Koalitionsrechner: lädt data.json, holt live die neuesten Umfragen von dawum.de und baut die Seite. */
(function () {
  'use strict';
  var K = window.Koalitionen;
  var DAWUM_URL = 'https://api.dawum.de/newest_surveys.json';
  var OFFEN_BIS = '2027-12-31'; // Startwert: Wahlen bis Ende 2027 stehen offen oben

  var FARBE = { 'CDU/CSU': '--p-union', 'CDU': '--p-union', 'CSU': '--p-csu', 'SPD': '--p-spd', 'Grüne': '--p-gruene',
    'FDP': '--p-fdp', 'Linke': '--p-linke', 'AfD': '--p-afd', 'BSW': '--p-bsw', 'Freie Wähler': '--p-fw', 'SSW': '--p-ssw' };
  var farbe = function (p) { return 'var(' + (FARBE[p] || '--p-sonst') + ')'; };
  var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  var zahl = function (v) { return v == null ? '–' : v.toLocaleString('de-DE', { minimumFractionDigits: 1, maximumFractionDigits: 1 }); };
  var datum = function (iso) { if (!iso) return '–'; var t = iso.slice(0, 10).split('-'); return t[2] + '.' + t[1] + '.' + t[0]; };
  var heute = function () { var d = new Date(); return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10); };

  function umfragenAusDawum(db) {
    var je = {};
    Object.keys(db.Surveys).forEach(function (id) {
      var u = db.Surveys[id], werte = {};
      Object.keys(u.Results).forEach(function (p) { werte[db.Parties[p].Shortcut] = Number(u.Results[p]); });
      var parl = db.Parliaments[u.Parliament_ID].Shortcut;
      (je[parl] = je[parl] || []).push({ institut: db.Institutes[u.Institute_ID].Name, datum: u.Date, werte: werte });
    });
    return je;
  }

  function partei(p) {
    return '<span class="partei"><span class="punkt" style="background:' + farbe(p) + '"></span>' + esc(p) + '</span>';
  }

  // Kuchendiagramm einer Koalition: Partner im Uhrzeigersinn ab 12 Uhr, Rest grau.
  // Die gestrichelte Linie von der Mitte nach unten (6 Uhr) markiert die Hälfte der Sitze.
  function kuchen(k, a) {
    var R = 44, C = 50, start = 0, teile = '';
    var punkt = function (anteil) {
      var w = 2 * Math.PI * anteil / 100;
      return (C + R * Math.sin(w)).toFixed(2) + ' ' + (C - R * Math.cos(w)).toFixed(2);
    };
    k.parteien.forEach(function (p) {
      var x = a.anteil[p], ende = start + x;
      teile += '<path d="M' + C + ' ' + C + ' L' + punkt(start) + ' A' + R + ' ' + R + ' 0 ' + (x > 50 ? 1 : 0) + ' 1 ' + punkt(Math.min(ende, 99.999)) +
        ' Z" style="fill:' + farbe(p) + '"/>';
      start = ende;
    });
    var titel = k.parteien.map(function (p) { return p + ' ' + zahl(a.anteil[p]) + ' %'; }).join(', ') + ', zusammen ' + zahl(k.sitzanteil) + ' % der Sitze';
    return '<svg class="kuchen" viewBox="0 0 100 100" role="img" aria-label="' + esc(titel) + '">' +
      '<circle cx="50" cy="50" r="' + R + '" class="rest"/>' + teile +
      '<line x1="50" y1="50" x2="50" y2="100" class="haelfte-grund"/><line x1="50" y1="50" x2="50" y2="100" class="haelfte"/></svg>';
  }

  function karte(parl, a, offen) {
    var h = '<details class="parl" id="' + esc(parl.id) + '"' + (offen ? ' open' : '') + '>' +
      '<summary><h3>' + esc(parl.name) + '</h3><span class="termin">Wahl: ' + esc(parl.wahltermin) + '</span></summary><div class="inhalt">';
    if (parl.termin_hinweis) h += '<p class="basis">' + esc(parl.termin_hinweis) + '</p>';
    if (a.status === 'keine') {
      h += '<p class="keine">Seit der letzten Wahl am ' + datum(parl.letzte_wahl) + ' liegt noch keine Umfrage vor. Sobald eine erscheint, rechnet die Seite automatisch.</p>';
      return h + quelleHistorie(parl) + '</div></details>';
    }
    if (a.status === 'veraltet') {
      h += '<p class="keine">Die neueste Umfrage ist ' + a.alter + ' Tage alt (vom ' + datum(a.auswahl[0].datum) + '). Für eine Rechnung ist das zu alt (Startwert: 365 Tage).</p>';
      return h + quelleHistorie(parl) + '</div></details>';
    }
    var aw = a.auswahl;
    var aelteste = aw[aw.length - 1].datum;
    h += '<p class="basis">Basis: ' + (aw.length === 1 ? 'eine Umfrage' : 'Mittel aus ' + aw.length + ' Umfragen') +
      ' (' + esc(aw.map(function (u) { return u.institut; }).join(', ')) + '), ' +
      (aw.length === 1 ? 'vom ' + datum(aw[0].datum) : datum(aelteste) + ' bis ' + datum(aw[0].datum)) + '.</p>';
    if (aw.length === 1) h += '<p class="warn">Nur eine einzige Umfrage seit der letzten Wahl im Zeitfenster: Das Ergebnis hängt an einem Institut und ist entsprechend unsicher.</p>';
    else if (a.alter > 60) h += '<p class="warn">Die neueste Umfrage ist ' + a.alter + ' Tage alt.</p>';
    if (parl.hinweis) h += '<p class="warn">' + esc(parl.hinweis) + '</p>';

    // Sitzverteilung
    h += '<p class="zwischen">Rechnerische Sitzverteilung</p><div class="sitze" role="img" aria-label="' +
      esc(a.drin.map(function (p) { return p + ' ' + zahl(a.anteil[p]) + ' %'; }).join(', ')) + '">' +
      a.drin.map(function (p) { return '<span class="seg" style="width:' + a.anteil[p] + '%;background:' + farbe(p) + '"></span>'; }).join('') +
      '<span class="mitte" title="Hälfte der Sitze"></span></div>';
    h += '<ul class="legende">' + a.drin.map(function (p) {
      return '<li>' + partei(p) + ' <span class="wert">' + zahl(a.werte[p]) + ' % · Sitze ' + zahl(a.anteil[p]) + ' %' +
        ((parl.befreit || []).indexOf(p) >= 0 ? ' (von der 5-%-Hürde befreit)' : '') + '</span></li>';
    }).join('') + '</ul>';
    var draussen = a.drausen.filter(function (p) { return a.werte[p] >= 1; });
    if (draussen.length) h += '<p class="draussen">Unter 5 %: ' + draussen.map(function (p) { return esc(p) + ' ' + zahl(a.werte[p]) + ' %'; }).join(', ') + '.</p>';
    if (a.grundmandat.length) h += '<p class="warn">' + esc(a.grundmandat.join(' und ')) + ' ' + (a.grundmandat.length > 1 ? 'liegen' : 'liegt') +
      ' zwischen 3 und 5 %. Über die Grundmandatsklausel (' + esc(parl.grundmandat) + ') wäre ein Einzug möglich; das bildet die Rechnung nicht ab.</p>';

    // Koalitionen
    h += '<p class="zwischen">Mehrheiten aus höchstens drei Parteien</p>';
    if (a.koalitionen.length) h += '<p class="kuchen-legende">Jeder Kuchen zeigt die Sitzanteile der Partner, beginnend oben. Grau sind die übrigen Sitze. Die gestrichelte Linie nach unten markiert die Hälfte: Reichen die Farben über sie hinaus, steht die Mehrheit.</p>';
    if (!a.koalitionen.length) h += '<p class="keine">Keine Kombination aus höchstens drei Parteien käme auf mehr als die Hälfte der Sitze.</p>';
    else h += '<ul class="koal">' + a.koalitionen.map(function (k) {
      return '<li>' + kuchen(k, a) +
        '<span class="wer">' + k.parteien.map(partei).join('<span class="plus">+</span>') + '</span>' +
        '<span class="zahl">' + zahl(k.sitzanteil) + ' % der Sitze</span>' +
        '<span class="marken">' + (k.gab_es ? '<span class="marke gab">gab es ' + (parl.ebene === 'Bund' ? 'im Bund' : 'im Land') + '</span>'
          : '<span class="marke rech">rein rechnerisch</span>') +
        (k.knapp ? '<span class="marke knapp">knapp</span>' : '') + '</span></li>';
    }).join('') + '</ul>';

    // Einzelumfragen
    var spalten = a.drin.concat(a.drausen.filter(function (p) { return a.werte[p] >= 3; }));
    h += '<details class="umfr"><summary>Einzelumfragen anzeigen</summary><div class="tabelle-scroll"><table><thead><tr><th>Institut</th><th>Datum</th>' +
      spalten.map(function (p) { return '<th>' + esc(p) + '</th>'; }).join('') + '</tr></thead><tbody>' +
      aw.map(function (u) {
        return '<tr><td>' + esc(u.institut) + '</td><td>' + datum(u.datum) + '</td>' +
          spalten.map(function (p) { return '<td class="w">' + (u.werte[p] == null ? '–' : zahl(u.werte[p])) + '</td>'; }).join('') + '</tr>';
      }).join('') + '</tbody></table></div></details>';
    return h + quelleHistorie(parl) + '</div></details>';
  }

  function quelleHistorie(parl) {
    var bisher = parl.historie.map(function (g) { return g.join(' + '); }).join(' · ');
    return '<p class="hist">Bisherige Regierungen ' + (parl.ebene === 'Bund' ? 'im Bund' : 'im Land') + ' (Parteienkombinationen): ' + esc(bisher) +
      '. Quelle: <a href="' + esc(parl.historie_quelle.url) + '" rel="noopener">' + esc(parl.historie_quelle.name) + '</a>.</p>' +
      '<p class="quelle">Umfragen: <a href="https://dawum.de/' + esc(parl.dawum.replace(/ \(NRW\)$/, '').replace(/ /g, '_')) + '/" rel="noopener">dawum.de</a>' +
      ' · letzte Wahl: ' + datum(parl.letzte_wahl) + '</p>';
  }

  function zeichnen(d, live, stand) {
    var r = d.regeln, tag = heute();
    var ps = d.parlamente.slice().sort(function (a, b) { return a.sortierung < b.sortierung ? -1 : a.sortierung > b.sortierung ? 1 : 0; });
    var bund = ps.filter(function (p) { return p.ebene === 'Bund'; });
    var laender = ps.filter(function (p) { return p.ebene !== 'Bund'; });
    var bald = laender.filter(function (p) { return p.sortierung <= OFFEN_BIS; });
    var spaeter = laender.filter(function (p) { return p.sortierung > OFFEN_BIS; });
    var block = function (liste, offen) {
      return '<div class="parlamente">' + liste.map(function (p) {
        return karte(p, K.auswerten(p, live ? (live[p.dawum] || []) : p.umfragen, tag, r), offen);
      }).join('') + '</div>';
    };
    document.getElementById('inhalt').innerHTML =
      '<h2 class="gruppe-titel">Bundestag</h2>' + block(bund, true) +
      '<h2 class="gruppe-titel">Landtagswahlen bis Ende 2027</h2><p class="gruppe-sub">Nächster Termin zuerst.</p>' + block(bald, true) +
      '<details class="gruppe"><summary><h2 class="gruppe-titel">Spätere Landtagswahlen</h2><span class="gruppe-sub">' + spaeter.length +
      ' Länder, Termine noch nicht festgelegt. Zum Ein- und Ausklappen antippen.</span></summary>' + block(spaeter, false) + '</details>';
    document.getElementById('stand').innerHTML =
      '<span>Umfragen: ' + (live ? 'live von dawum.de, Stand ' : 'gespeicherter Stand ') + esc(datum(stand)) + '</span>' +
      '<span>Bisherige Regierungen: Stand ' + esc(datum(d.historie_stand)) + '</span>';
    document.getElementById('quellen-liste').innerHTML =
      '<li>Umfragen: <a href="https://dawum.de/">dawum.de</a> (Datenbank der veröffentlichten Sonntagsfragen, ODC-ODbL), abgerufen ' + esc(datum(stand)) + '.</li>' +
      d.quellen_termine.map(function (q) { return '<li>Wahltermine: <a href="' + esc(q.url) + '" rel="noopener">' + esc(q.name) + '</a></li>'; }).join('') +
      '<li>Bisherige Regierungen: je Parlament angegeben (Wikipedia-Listen der Landesregierungen und Bundesregierungen, abgerufen ' + esc(datum(d.historie_stand)) + ').</li>';
    if (location.hash) { var z = document.getElementById(location.hash.slice(1)); if (z) { z.open = true; var g = z.closest('details.gruppe'); if (g) g.open = true; z.scrollIntoView(); } }
  }

  (async function () {
    var d;
    try { d = await (await fetch('data.json?t=' + Date.now(), { cache: 'no-store' })).json(); }
    catch (e) { document.getElementById('inhalt').innerHTML = '<p class="fehler">Die Daten konnten nicht geladen werden.</p>'; return; }
    var live = null, stand = d.umfragen_stand;
    var abbruch = new AbortController(), uhr = setTimeout(function () { abbruch.abort(); }, 6000); // Startwert 6 s
    try {
      var db = await (await fetch(DAWUM_URL, { signal: abbruch.signal })).json();
      live = umfragenAusDawum(db); stand = db.Database.Last_Update;
    } catch (e) { console.warn('dawum live nicht erreichbar, nutze data.json', e); }
    finally { clearTimeout(uhr); }
    zeichnen(d, live, stand);
  })();
})();
