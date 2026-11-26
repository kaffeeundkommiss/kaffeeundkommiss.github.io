/* Politik-Übersicht: Plenarsaal des 21. Bundestages (26.11.2026).
   Datenquelle ist allein die Tabelle #sitze-tabelle in index.html (Sitze, Farbe über data-linie, Rolle).
   Zeichnet einen schematischen Halbkreis, Präsidium, Regierungs- und Bundesratsbank und
   zählt ausgewählte Fraktionen gegen die Mehrheit der Mitglieder und die Zweidrittelmehrheit.
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
    return {
      id: z.getAttribute('data-linie'),
      name: z.cells[0].textContent.trim(),
      sitze: +z.getAttribute('data-sitze'),
      wahl: +z.getAttribute('data-wahl'),
      rolle: z.getAttribute('data-rolle')
    };
  });
  var gesamt = fr.reduce(function (s, f) { return s + f.sitze; }, 0);
  var MEHRHEIT = Math.floor(gesamt / 2) + 1;      // Art. 121 GG: Mehrheit der gesetzlichen Mitgliederzahl
  var ZWEIDRITTEL = Math.ceil(gesamt * 2 / 3);     // Art. 79 Abs. 2 GG
  var imSaal = fr.filter(function (f) { return f.id !== 'ohne'; });
  var ohne = fr.filter(function (f) { return f.id === 'ohne'; })[0];
  var nSaal = imSaal.reduce(function (s, f) { return s + f.sitze; }, 0);
  var gewaehlt = {};

  function el(n, a, eltern) {
    var e = document.createElementNS(NS, n);
    for (var k in a) e.setAttribute(k, a[k]);
    if (eltern) eltern.appendChild(e);
    return e;
  }
  var prozent = function (n) { return (n / gesamt * 100).toFixed(1).replace('.', ',') + ' %'; };

  // Halbkreis: Reihen mit Sitzzahl proportional zum Radius (Startwerte: 13 Reihen, Radius 165 bis 450)
  var W = 1000, CX = 500, CY = 460, R0 = 165, R1 = 450, REIHEN = 13, PUNKT = 7.6;
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

  var svg = el('svg', { viewBox: '-70 0 ' + (W + 140) + ' 590', role: 'img', 'aria-labelledby': 'ps-titel' });
  var t = el('title', { id: 'ps-titel' }, svg);
  t.textContent = 'Schematischer Plenarsaal mit ' + gesamt + ' Sitzen: ' + fr.map(function (f) { return f.name + ' ' + f.sitze; }).join(', ') + '.';
  var gruppen = {};
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

  // Unterer Teil: Regierungsbank (links), Präsidium (Mitte), Bundesratsbank (rechts), Fraktionslose
  var unten = el('g', { 'class': 'ps-unten' }, svg);
  var y0 = CY + 40;
  // Präsidium: Präsidentin in der Mitte, je zwei Stellvertreter daneben, rechts außen der unbesetzte Platz
  var praes = [
    { x: CX - 110, l: 'union', t: 'Lindholz (CSU)' }, { x: CX - 55, l: 'spd', t: 'Ortleb (SPD)' },
    { x: CX, l: 'union', t: 'Klöckner (CDU), Präsidentin', gross: true },
    { x: CX + 55, l: 'gruene', t: 'Nouripour (Grüne)' }, { x: CX + 110, l: 'linke', t: 'Ramelow (Linke)' },
    { x: CX + 165, l: 'afd', t: 'Platz der AfD-Fraktion unbesetzt', leer: true }
  ];
  el('rect', { x: CX - 135, y: y0 - 22, width: 325, height: 44, rx: 4, 'class': 'ps-tisch' }, unten);
  praes.forEach(function (q) {
    var c = el('circle', { cx: q.x, cy: y0, r: q.gross ? 15 : 11, 'data-linie': q.l, 'class': q.leer ? 'ps-leer' : 'ps-praes' }, unten);
    el('title', {}, c).textContent = q.t;
  });
  var tp = el('text', { x: CX + 27, y: y0 + 46, 'text-anchor': 'middle', 'class': 'ps-klein' }, unten);
  tp.textContent = 'Präsidium';
  // Regierungsbank: 18 Plätze (Bundeskanzler und 17 Bundesministerinnen und -minister)
  var rb = el('g', {}, unten);
  for (var m = 0; m < 18; m++) el('rect', { x: 20 + (m % 9) * 26, y: y0 - 20 + Math.floor(m / 9) * 24, width: 18, height: 18, rx: 3, 'class': 'ps-reg' }, rb);
  var tr = el('text', { x: 20 + 4 * 26 + 9, y: y0 + 46, 'text-anchor': 'middle', 'class': 'ps-klein' }, unten);
  tr.textContent = 'Regierungsbank (18)';
  el('rect', { x: 730, y: y0 - 20, width: 110, height: 42, rx: 4, 'class': 'ps-br' }, unten);
  var tb = el('text', { x: 785, y: y0 + 46, 'text-anchor': 'middle', 'class': 'ps-klein' }, unten);
  tb.textContent = 'Bundesrat';
  if (ohne) {
    var go = el('g', { 'data-linie': 'ohne', 'class': 'ps-fr', 'data-id': 'ohne' }, svg);
    gruppen.ohne = go;
    for (var o = 0; o < ohne.sitze; o++) el('circle', { cx: 940 + o * 22, cy: y0, r: PUNKT }, go);
    var to = el('text', { x: 962, y: y0 + 46, 'text-anchor': 'middle', 'class': 'ps-klein' }, go);
    to.textContent = 'fraktionslos (' + ohne.sitze + ')';
  }
  bild.appendChild(svg);

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
    b.lastChild.textContent = f.sitze;
    b.addEventListener('click', function () { gewaehlt[f.id] = !gewaehlt[f.id]; zeigen(); });
    knoepfe[f.id] = b;
    wahl.appendChild(b);
  });
  var schnell = document.createElement('div');
  schnell.className = 'ps-schnell';
  schnell.innerHTML = '<button type="button" class="ps-mini" data-a="reg">Regierungskoalition</button><button type="button" class="ps-mini" data-a="leer">Auswahl löschen</button>';
  schnell.addEventListener('click', function (e) {
    var a = e.target.getAttribute && e.target.getAttribute('data-a');
    if (!a) return;
    gewaehlt = {};
    if (a === 'reg') fr.forEach(function (f) { if (f.rolle === 'Regierung') gewaehlt[f.id] = true; });
    zeigen();
  });
  wahl.appendChild(schnell);
  svg.addEventListener('click', function (e) {
    var g = e.target.closest && e.target.closest('.ps-fr');
    if (g) { var id = g.getAttribute('data-id'); gewaehlt[id] = !gewaehlt[id]; zeigen(); }
  });

  function zeigen() {
    var aus = fr.filter(function (f) { return gewaehlt[f.id]; });
    var summe = aus.reduce(function (s, f) { return s + f.sitze; }, 0);
    fr.forEach(function (f) {
      knoepfe[f.id].setAttribute('aria-pressed', gewaehlt[f.id] ? 'true' : 'false');
      if (gruppen[f.id]) gruppen[f.id].setAttribute('class', 'ps-fr' + (aus.length && !gewaehlt[f.id] ? ' ps-blass' : ''));
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
      h = '<p class="ps-summe">' + summe + ' von ' + gesamt + ' Sitzen <span>(' + prozent(summe) + ')</span></p>';
      if (einzel) {
        var d = einzel.sitze - einzel.wahl;
        h += '<p class="ps-zeile">' + (einzel.rolle === 'fraktionslos' ? 'Abgeordnete ohne Fraktion' : einzel.rolle === 'Regierung' ? 'Trägt die Bundesregierung' : 'Opposition') +
          (d ? ' · ' + (d > 0 ? '+' : '−') + Math.abs(d) + ' seit der Wahl 2025 (' + einzel.wahl + ')' : ' · unverändert seit der Wahl 2025') + '</p>';
      }
      h += '<p class="ps-zeile">' + (summe >= MEHRHEIT ? '✓ Mehrheit der Mitglieder (mindestens ' + MEHRHEIT + ')' : 'Bis zur Mehrheit der Mitglieder fehlen ' + (MEHRHEIT - summe)) + '</p>';
      h += '<p class="ps-zeile">' + (summe >= ZWEIDRITTEL ? '✓ Zweidrittelmehrheit (mindestens ' + ZWEIDRITTEL + ')' : 'Bis zur Zweidrittelmehrheit fehlen ' + (ZWEIDRITTEL - summe)) + '</p>';
    }
    erg.innerHTML = h + balken;
  }

  bild.hidden = false; wahl.hidden = false; erg.hidden = false;
  tab.classList.add('ps-tab-klein');
  zeigen();
})();
