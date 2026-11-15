/* Politik-Übersicht: zeichnet Linien in den Farben der Partei-Monitore zum Koalitionsrechner.
   Die Linien laufen nur durch die Lücken zwischen den Kacheln und passen sich jeder Spaltenzahl an. */
(function () {
  'use strict';
  var netz = document.getElementById('netz');
  if (!netz) return;
  var svg = netz.querySelector('.leitungen');
  var raster = netz.querySelector('.projekte');
  var knoten = netz.querySelector('.knoten');
  var STRICH = 3, ABSTAND = 7; // Startwerte: Linienstärke und Abstand der Linien im Sammelbereich (px)

  function zeichnen() {
    var kacheln = Array.prototype.slice.call(raster.querySelectorAll('.projekt[data-linie]'));
    var n = kacheln.length;
    if (!n) return;
    knoten.style.marginTop = Math.max(64, 28 + n * ABSTAND) + 'px';
    var basis = netz.getBoundingClientRect();
    var stil = getComputedStyle(raster);
    var luecke = parseFloat(stil.columnGap) || 16, zeilenluecke = parseFloat(stil.rowGap) || 16;
    var r = kacheln.map(function (k) {
      var b = k.getBoundingClientRect();
      return { l: b.left - basis.left, r: b.right - basis.left, t: Math.round(b.top - basis.top), u: b.bottom - basis.top };
    });
    var zeilen = r.map(function (x) { return x.t; }).filter(function (t, i, a) { return a.indexOf(t) === i; }).sort(function (a, b) { return a - b; });
    var rasterUnten = Math.max.apply(null, r.map(function (x) { return x.u; }));
    var k = knoten.getBoundingClientRect();
    var kOben = k.top - basis.top, kL = k.left - basis.left, kB = k.width;
    var spalten = r.map(function (x) { return Math.round(x.l); }).filter(function (l, i, a) { return a.indexOf(l) === i; }).sort(function (a, b) { return a - b; });
    var letzte = zeilen.length - 1;
    // Abstieg: Kacheln der letzten Zeile direkt nach unten, alle anderen durch eine innere Gasse
    // (rechts daneben, die letzte Spalte links daneben; bei nur einer Spalte am rechten Rand).
    var gassen = {};
    var linien = kacheln.map(function (kachel, i) {
      var x = r[i], z = zeilen.indexOf(x.t), s = spalten.indexOf(Math.round(x.l));
      var li = { kachel: kachel, x: x, z: z, mitte: (x.l + x.r) / 2 };
      if (z < letzte) {
        li.seite = (spalten.length > 1 && s === spalten.length - 1) ? -1 : 1;
        li.gasse = li.seite > 0 ? Math.round(x.r + (spalten.length > 1 ? luecke / 2 : 7)) : Math.round(x.l - luecke / 2);
        (gassen[li.gasse] = gassen[li.gasse] || []).push(li);
      }
      return li;
    });
    var spur = spalten.length > 1 ? Math.min(5, luecke / 4) : 3; // einspaltig: Linien im Seitenrand
    Object.keys(gassen).forEach(function (g) {
      var l = gassen[g];
      l.forEach(function (li, j) { li.ab = Number(g) + (j - (l.length - 1) / 2) * spur; });
    });
    linien.forEach(function (li) { if (li.ab == null) li.ab = li.mitte; });
    // Ziele am Kasten in derselben Reihenfolge wie die Abstiege, damit sich die Linien kaum kreuzen.
    var sortiert = linien.slice().sort(function (a, b) { return a.ab - b.ab; });
    sortiert.forEach(function (li, j) { li.ziel = kL + kB * (j + 0.5) / n; });
    // Höhe im Sammelbereich: Wer nach rechts läuft, biegt umso früher ab, je weiter rechts er absteigt; nach links spiegelbildlich.
    var rechts = sortiert.filter(function (li) { return li.ziel >= li.ab; }).reverse();
    var links = sortiert.filter(function (li) { return li.ziel < li.ab; });
    rechts.concat(links).forEach(function (li, j) { li.sammel = rasterUnten + 14 + j * ABSTAND; });
    var html = '';
    linien.forEach(function (li) {
      var x = li.x, d = 'M' + li.mitte + ' ' + x.u;
      if (li.z < letzte) d += ' V' + (x.u + zeilenluecke / 2 + (li.seite > 0 ? -1 : 1) * spur / 2) + ' H' + li.ab;
      d += ' V' + li.sammel + ' H' + li.ziel + ' V' + kOben;
      var farbe = getComputedStyle(li.kachel).getPropertyValue('--linie').trim() || 'currentColor';
      html += '<path d="' + d + '" fill="none" stroke="' + farbe + '" stroke-width="' + STRICH + '" stroke-linejoin="round" stroke-linecap="round"/>' +
        '<circle cx="' + li.ziel + '" cy="' + kOben + '" r="4.5" fill="' + farbe + '"/>';
    });
    svg.setAttribute('viewBox', '0 0 ' + basis.width + ' ' + basis.height);
    svg.innerHTML = html;
  }

  var geplant = false;
  function bald() { if (geplant) return; geplant = true; requestAnimationFrame(function () { geplant = false; zeichnen(); }); }
  zeichnen();
  if ('ResizeObserver' in window) new ResizeObserver(bald).observe(netz); else window.addEventListener('resize', bald);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(bald);
  if (window.matchMedia) { var m = matchMedia('(prefers-color-scheme: dark)'); if (m.addEventListener) m.addEventListener('change', bald); }
})();
