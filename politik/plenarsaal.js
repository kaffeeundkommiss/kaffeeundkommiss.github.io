/* Politik-Übersicht: Plenarsaal des 21. Bundestages (26.11.2026, Raumzonen zusammengeführt 27.11.2026).
   Datenquelle ist allein die Tabelle #sitze-tabelle in index.html (Sitze heute und bei der Wahl 2025, Farbe über data-linie, Rolle, Stichtag in caption).
   Zeichnet einen schematischen Halbkreis mit Präsidium, Regierungs- und Bundesratsbank, Wehrbeauftragtem und Tribünen,
   zählt ausgewählte Fraktionen gegen die Mehrheit der Mitglieder und die Zweidrittelmehrheit,
   schaltet zwischen Stichtag und Wahl 2025 um und verknüpft die Raumzonen mit den markierten Begriffen (.ps-begriff) im Text.
   Ohne JavaScript bleibt die Tabelle sichtbar. */
(function () {
  'use strict';
  var tab = document.getElementById('sitze-tabelle');
  var bild = document.getElementById('ps-bild');
  var wahl = document.getElementById('ps-wahl');
  var erg = document.getElementById('ps-ergebnis');
  if (!tab || !bild || !wahl || !erg || !document.createElementNS) return;

  var NS = 'http://www.w3.org/2000/svg';
  var fr = [].map.call(tab.tBodies[0].rows, function (z) {
    var heute = +z.getAttribute('data-sitze');
    return {
      id: z.getAttribute('data-linie'),
      name: z.cells[0].textContent.trim(),
      sitze: heute,
      heute: heute,
      wahl: +z.getAttribute('data-wahl'),
      rolle: z.getAttribute('data-rolle')
    };
  });
  var cap = tab.caption && tab.caption.textContent.match(/Stand\s+([\d.]+)/);
  var STICHTAG = cap ? cap[1] : '';
  var modus = 'heute';                              // 'heute' oder 'wahl'
  var gesamt = fr.reduce(function (s, f) { return s + f.sitze; }, 0);
  var MEHRHEIT = Math.floor(gesamt / 2) + 1;      // Art. 121 GG: Mehrheit der gesetzlichen Mitgliederzahl
  var ZWEIDRITTEL = Math.ceil(gesamt * 2 / 3);     // Art. 79 Abs. 2 GG
  var gewaehlt = {};
  var zoneAn = null;
  var gruppen, zonen, svg;

  function el(n, a, eltern) {
    var e = document.createElementNS(NS, n);
    for (var k in a) e.setAttribute(k, a[k]);
    if (eltern) eltern.appendChild(e);
    return e;
  }
  var prozent = function (n) { return (n / gesamt * 100).toFixed(1).replace('.', ',') + ' %'; };
  var sitzeText = function (n) { return n + (n === 1 ? ' Sitz' : ' Sitze'); };

  // Erklärungen der Raumzonen, Wortlaut wie im Text .ps-erkl und in der Belegmatrix
  var ZONEN = {
    tribuenen: 'Tribünen: fast 400 Plätze über dem Saal, drei Tribünen für Besucherinnen und Besucher, zwei für Presse und Medien. Dazwischenrufen und Klatschen sind dort nicht erlaubt.',
    praesidium: 'Präsidium: Präsidentin Julia Klöckner (CDU) in der Mitte, daneben die Vizepräsidentinnen und Vizepräsidenten. Der Platz der AfD-Fraktion ist unbesetzt. Vor dem Präsidium steht das Rednerpult.',
    regierung: 'Regierungsbank (vom Präsidium aus rechts): Bundeskanzler Friedrich Merz (CDU) und 17 Bundesministerinnen und Bundesminister, getragen von CDU/CSU und SPD.',
    bundesrat: 'Bundesratsbank (vom Präsidium aus links): Mitglieder der Landesregierungen. Sie dürfen an jeder Sitzung teilnehmen und müssen jederzeit gehört werden (Art. 43 Abs. 2 GG).',
    wehrbeauftragter: 'Wehrbeauftragter: einzelner Platz neben der Bundesratsbank (Lage vereinfacht). Er ist kein Abgeordneter, sondern Hilfsorgan des Bundestages bei der Kontrolle der Bundeswehr.'
  };
  function textOhne() {
    var o = fr.filter(function (f) { return f.id === 'ohne'; })[0];
    if (!o) return '';
    return modus === 'wahl'
      ? 'Fraktionslos bei der Wahl 2025: ' + sitzeText(o.wahl) + ' (Stefan Seidler, SSW). Lage vereinfacht.'
      : 'Fraktionslos am ' + STICHTAG + ': ' + sitzeText(o.heute) + ' (Stefan Seidler, SSW; Sieghard Knodel nach Austritt aus der AfD; Jan Wenzel Schmidt nach Ausschluss aus der AfD-Fraktion). Lage vereinfacht.';
  }

  // Umschalter Stichtag / Wahl 2025 und Infozeile für die Raumzonen
  var kopf = document.createElement('div');
  kopf.className = 'ps-stand';
  kopf.setAttribute('role', 'group');
  kopf.setAttribute('aria-label', 'Sitzverteilung zeigen');
  kopf.innerHTML = '<button type="button" class="ps-stand-knopf" data-m="heute" aria-pressed="true"></button><button type="button" class="ps-stand-knopf" data-m="wahl" aria-pressed="false">Wahl 2025</button>';
  kopf.firstChild.textContent = STICHTAG ? 'Stand ' + STICHTAG : 'Stand heute';
  var info = document.createElement('p');
  info.className = 'ps-info';
  info.setAttribute('aria-live', 'polite');
  var INFO_START = 'Tippen Sie auf Präsidium, Regierungsbank, Bundesrat, Wehrbeauftragten oder Tribünen, um zu sehen, wer dort sitzt.';
  info.textContent = INFO_START;

  // Halbkreis: Reihen mit Sitzzahl proportional zum Radius (Startwerte: 13 Reihen, Radius 165 bis 450)
  var W = 1000, CX = 500, CY = 540, R0 = 165, R1 = 450, REIHEN = 13, PUNKT = 7.6;

  function zeichnen() {
    var imSaal = fr.filter(function (f) { return f.id !== 'ohne'; });
    var ohne = fr.filter(function (f) { return f.id === 'ohne'; })[0];
    var nSaal = imSaal.reduce(function (s, f) { return s + f.sitze; }, 0);
    var radien = [], summeR = 0;
    for (var i = 0; i < REIHEN; i++) { var r = R0 + (R1 - R0) * i / (REIHEN - 1); radien.push(r); summeR += r; }
    var proReihe = radien.map(function (r) { return Math.floor(nSaal * r / summeR); });
    var rest = nSaal - proReihe.reduce(function (a, b) { return a + b; }, 0);
    for (var j = REIHEN - 1; rest > 0; j = (j - 1 + REIHEN) % REIHEN, rest--) proReihe[j]++;
    var plaetze = [];
    radien.forEach(function (r, ri) {
      var n = proReihe[ri];
      for (var k = 0; k < n; k++) {
        var w = Math.PI - Math.PI * (k + 0.5) / n;   // von links (180°) nach rechts (0°)
        plaetze.push({ w: w, x: CX + r * Math.cos(w), y: CY - r * Math.sin(w), ri: ri });
      }
    });
    plaetze.sort(function (a, b) { return b.w - a.w || a.ri - b.ri; });

    gruppen = {}; zonen = {};
    svg = el('svg', { viewBox: '-70 -14 ' + (W + 160) + ' 694', role: 'group', 'aria-labelledby': 'ps-titel' });
    var t = el('title', { id: 'ps-titel' }, svg);
    t.textContent = 'Schematischer Plenarsaal mit ' + gesamt + ' Sitzen' + (modus === 'wahl' ? ' nach der Wahl 2025' : '') + ': ' + fr.map(function (f) { return f.name + ' ' + f.sitze; }).join(', ') + '.';

    function zone(id, label, eltern) {
      var g = el('g', { 'class': 'ps-zone', 'data-zone': id, tabindex: '0', role: 'button', 'aria-label': label }, eltern || svg);
      zonen[id] = g;
      return g;
    }
    function txt(x, y, s, eltern) { var e = el('text', { x: x, y: y, 'text-anchor': 'middle', 'class': 'ps-klein' }, eltern); e.textContent = s; return e; }

    // Tribünen über dem Saal (Besucher, Presse), als gestrichelter Bogen hinter den Sitzen; breiter unsichtbarer Bogen als Tippfläche
    var zt = zone('tribuenen', 'Tribünen für Besucher und Presse');
    var bogen = 'M' + (CX - 520) + ' ' + CY + ' A520 520 0 0 1 ' + (CX + 520) + ' ' + CY;
    el('path', { d: bogen, 'class': 'ps-trib' }, zt);
    el('path', { d: bogen, 'class': 'ps-tipp' }, zt);
    txt(CX, CY - 528, 'Tribünen: Besucher und Presse', zt);

    var p = 0;
    imSaal.forEach(function (f) {
      var g = el('g', { 'data-linie': f.id, 'class': 'ps-fr', 'data-id': f.id }, svg);
      gruppen[f.id] = g;
      for (var k = 0; k < f.sitze; k++, p++) el('circle', { cx: plaetze[p].x.toFixed(1), cy: plaetze[p].y.toFixed(1), r: PUNKT }, g);
      // Blockbeschriftung über der äußersten Reihe
      var mitte = plaetze[p - Math.ceil(f.sitze / 2)].w;
      var lx = CX + (R1 + 34) * Math.cos(mitte), ly = CY - (R1 + 34) * Math.sin(mitte);
      var tx = el('text', { x: lx.toFixed(0), y: ly.toFixed(0), 'class': 'ps-lbl', 'text-anchor': 'middle' }, g);
      tx.textContent = (f.id === 'gruene' ? 'Grüne' : f.name.replace('Die ', '')) + ' ' + f.sitze;
    });

    // Unterer Teil, Blick vom Präsidium in den Saal: links Bundesratsbank und Platz des Wehrbeauftragten,
    // Mitte Präsidium, rechts Regierungsbank (Wikipedia „Deutscher Bundestag“; OA-Kommentar Art. 43 GG, Rn. 19 f.)
    var unten = el('g', { 'class': 'ps-unten' }, svg);
    var y0 = CY + 40;
    // Präsidium: Präsidentin in der Mitte, je zwei Stellvertreter daneben, rechts außen der unbesetzte Platz
    var praes = [
      { x: CX - 110, l: 'union', t: 'Lindholz (CSU)' }, { x: CX - 55, l: 'spd', t: 'Ortleb (SPD)' },
      { x: CX, l: 'union', t: 'Klöckner (CDU), Präsidentin', gross: true },
      { x: CX + 55, l: 'gruene', t: 'Nouripour (Grüne)' }, { x: CX + 110, l: 'linke', t: 'Ramelow (Linke)' },
      { x: CX + 165, l: 'afd', t: 'Platz der AfD-Fraktion unbesetzt', leer: true }
    ];
    var zp = zone('praesidium', 'Präsidium', unten);
    el('rect', { x: CX - 135, y: y0 - 22, width: 325, height: 44, rx: 4, 'class': 'ps-tisch' }, zp);
    praes.forEach(function (q) {
      var c = el('circle', { cx: q.x, cy: y0, r: q.gross ? 15 : 11, 'data-linie': q.l, 'class': q.leer ? 'ps-leer' : 'ps-praes' }, zp);
      el('title', {}, c).textContent = q.t;
    });
    txt(CX + 27, y0 + 46, 'Präsidium', zp);
    // Bundesratsbank: Mitglieder der Landesregierungen, etwa Ministerpräsidenten (Art. 43 Abs. 2, Art. 51 Abs. 1 GG)
    var zb = zone('bundesrat', 'Bundesratsbank', unten);
    el('rect', { x: -50, y: y0 - 20, width: 180, height: 42, rx: 4, 'class': 'ps-br' }, zb);
    txt(40, y0 + 46, 'Bundesrat', zb);
    var zw = zone('wehrbeauftragter', 'Platz des Wehrbeauftragten', unten);
    el('circle', { cx: 200, cy: y0, r: 10, 'class': 'ps-wb' }, zw);
    el('circle', { cx: 200, cy: y0 + 20, r: 34, 'class': 'ps-tipp-flaeche' }, zw);
    txt(200, y0 + 46, 'Wehrbeauftragter', zw);
    // Regierungsbank: 18 Plätze (Bundeskanzler und 17 Bundesministerinnen und -minister)
    var zr = zone('regierung', 'Regierungsbank', unten);
    for (var m = 0; m < 18; m++) el('rect', { x: 710 + (m % 9) * 26, y: y0 - 20 + Math.floor(m / 9) * 24, width: 18, height: 18, rx: 3, 'class': 'ps-reg' }, zr);
    txt(710 + 4 * 26 + 9, y0 + 46, 'Regierungsbank (18)', zr);
    if (ohne) {
      var go = el('g', { 'data-linie': 'ohne', 'class': 'ps-fr', 'data-id': 'ohne' }, svg);
      gruppen.ohne = go;
      for (var o = 0; o < ohne.sitze; o++) el('circle', { cx: 988 + o * 22, cy: y0, r: PUNKT }, go);
      txt(1010, y0 + 46, 'fraktionslos', go);
      txt(1010, y0 + 70, '(' + ohne.sitze + ')', go);
    }

    svg.addEventListener('click', function (e) {
      var z = e.target.closest && e.target.closest('.ps-zone');
      if (z) { zeigeZone(z.getAttribute('data-zone')); return; }
      var g = e.target.closest && e.target.closest('.ps-fr');
      if (g) { zeigeZone(null); var id = g.getAttribute('data-id'); gewaehlt[id] = !gewaehlt[id]; zeigen(); }
    });
    svg.addEventListener('keydown', function (e) {
      var z = e.target.closest && e.target.closest('.ps-zone');
      if (z && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); zeigeZone(z.getAttribute('data-zone')); }
    });
    bild.textContent = '';
    bild.appendChild(svg);
    bild.appendChild(info);
  }

  // Raumzone hervorheben (erneutes Tippen hebt auf); 'fraktionslos' hebt die fraktionslosen Sitze hervor
  function zeigeZone(id) {
    if (id && id === zoneAn) id = null;
    zoneAn = id;
    svg.classList.toggle('ps-fokus', !!id);
    Object.keys(zonen).forEach(function (k) { zonen[k].classList.toggle('ps-zone-an', k === id); });
    if (gruppen.ohne) gruppen.ohne.classList.toggle('ps-zone-an', id === 'fraktionslos');
    [].forEach.call(document.querySelectorAll('.ps-begriff'), function (b) {
      var an = b.getAttribute('data-ziel') === id;
      b.classList.toggle('aktiv', an);
      b.setAttribute('aria-pressed', an ? 'true' : 'false');
    });
    info.textContent = !id ? INFO_START : id === 'fraktionslos' ? textOhne() : ZONEN[id];
  }

  // Auswahlknöpfe (eigentliche Bedienung, auch per Tastatur); Klick in die Grafik schaltet dieselben Knöpfe
  var knoepfe = {};
  fr.forEach(function (f) {
    var b = document.createElement('button');
    b.type = 'button';
    b.className = 'ps-knopf';
    b.setAttribute('data-linie', f.id);
    b.setAttribute('aria-pressed', 'false');
    b.innerHTML = '<span class="ps-n"></span><span class="ps-z"></span>';
    b.firstChild.textContent = f.name;
    b.addEventListener('click', function () { zeigeZone(null); gewaehlt[f.id] = !gewaehlt[f.id]; zeigen(); });
    knoepfe[f.id] = b;
    wahl.appendChild(b);
  });
  var schnell = document.createElement('div');
  schnell.className = 'ps-schnell';
  schnell.innerHTML = '<button type="button" class="ps-mini" data-a="reg">Regierungskoalition</button><button type="button" class="ps-mini" data-a="leer">Auswahl löschen</button>';
  schnell.addEventListener('click', function (e) {
    var a = e.target.getAttribute && e.target.getAttribute('data-a');
    if (!a) return;
    zeigeZone(null);
    gewaehlt = {};
    if (a === 'reg') fr.forEach(function (f) { if (f.rolle === 'Regierung') gewaehlt[f.id] = true; });
    zeigen();
  });
  wahl.appendChild(schnell);

  kopf.addEventListener('click', function (e) {
    var m = e.target.getAttribute && e.target.getAttribute('data-m');
    if (!m || m === modus) return;
    modus = m;
    [].forEach.call(kopf.children, function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-m') === m ? 'true' : 'false'); });
    fr.forEach(function (f) { f.sitze = m === 'wahl' ? f.wahl : f.heute; });
    var alt = zoneAn;
    zeichnen();
    zoneAn = null;
    if (alt) zeigeZone(alt);
    zeigen();
  });
  wahl.parentNode.insertBefore(kopf, wahl);

  [].forEach.call(document.querySelectorAll('.ps-begriff'), function (b) {
    b.setAttribute('aria-pressed', 'false');
    b.addEventListener('click', function () {
      zeigeZone(b.getAttribute('data-ziel'));
      var r = svg.getBoundingClientRect();
      if (r.top < 0 || r.bottom > window.innerHeight) bild.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });

  function zeigen() {
    var aus = fr.filter(function (f) { return gewaehlt[f.id]; });
    var summe = aus.reduce(function (s, f) { return s + f.sitze; }, 0);
    fr.forEach(function (f) {
      knoepfe[f.id].lastChild.textContent = f.sitze;
      knoepfe[f.id].setAttribute('aria-pressed', gewaehlt[f.id] ? 'true' : 'false');
      if (gruppen[f.id]) gruppen[f.id].classList.toggle('ps-blass', !!(aus.length && !gewaehlt[f.id]));
    });
    var balken = '<div class="ps-balken" aria-hidden="true">' + aus.map(function (f) {
      return '<span data-linie="' + f.id + '" style="width:' + (f.sitze / gesamt * 100).toFixed(2) + '%"></span>';
    }).join('') + '<i class="ps-marke" style="left:' + (MEHRHEIT / gesamt * 100).toFixed(2) + '%"></i><i class="ps-marke" style="left:' + (ZWEIDRITTEL / gesamt * 100).toFixed(2) + '%"></i></div>' +
      '<div class="ps-skala" aria-hidden="true"><span style="left:' + (MEHRHEIT / gesamt * 100).toFixed(2) + '%">' + MEHRHEIT + '</span><span style="left:' + (ZWEIDRITTEL / gesamt * 100).toFixed(2) + '%">' + ZWEIDRITTEL + '</span></div>';
    var h;
    if (!aus.length) {
      h = '<p class="ps-summe">Keine Fraktion ausgewählt</p><p class="ps-zeile">Tippen Sie auf eine Fraktion oder in die Grafik.</p>';
    } else {
      var einzel = aus.length === 1 ? aus[0] : null;
      h = '<p class="ps-summe">' + summe + ' von ' + gesamt + ' Sitzen <span>(' + prozent(summe) + (modus === 'wahl' ? ', Wahl 2025' : '') + ')</span></p>';
      if (einzel) {
        var d = einzel.heute - einzel.wahl;
        var rolle = einzel.rolle === 'fraktionslos' ? 'Abgeordnete ohne Fraktion' : einzel.rolle === 'Regierung' ? 'Trägt die Bundesregierung' : 'Opposition';
        h += '<p class="ps-zeile">' + rolle + (modus === 'wahl'
          ? (d ? ' · heute ' + einzel.heute + ' (Stand ' + STICHTAG + ')' : ' · bis heute unverändert')
          : (d ? ' · ' + (d > 0 ? '+' : '−') + Math.abs(d) + ' seit der Wahl 2025 (' + einzel.wahl + ')' : ' · unverändert seit der Wahl 2025')) + '</p>';
      }
      h += '<p class="ps-zeile">' + (summe >= MEHRHEIT ? '✓ Mehrheit der Mitglieder (mindestens ' + MEHRHEIT + ')' : 'Bis zur Mehrheit der Mitglieder fehlen ' + (MEHRHEIT - summe)) + '</p>';
      h += '<p class="ps-zeile">' + (summe >= ZWEIDRITTEL ? '✓ Zweidrittelmehrheit (mindestens ' + ZWEIDRITTEL + ')' : 'Bis zur Zweidrittelmehrheit fehlen ' + (ZWEIDRITTEL - summe)) + '</p>';
    }
    erg.innerHTML = h + balken;
  }

  zeichnen();
  bild.hidden = false; wahl.hidden = false; erg.hidden = false;
  tab.classList.add('ps-tab-klein');
  zeigen();
})();
