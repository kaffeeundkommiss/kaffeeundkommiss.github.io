/* Politik-Übersicht: füllt im Kasten „Mögliche Koalitionen“ die Liste der nächsten Wahlen aus koalitionen/data.json.
   Gleiche Datenquelle wie der Koalitionsrechner (wöchentliche Routine). Ohne JS oder ohne Daten bleibt die Liste verborgen. */
(function () {
  'use strict';
  var feld = document.getElementById('naechste-wahlen');
  if (!feld || !window.fetch) return;
  var ANZAHL = 5; // Startwert: so viele Wahlen zeigt der Kasten
  var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  var kurzname = function (n) { return String(n).replace(/^(Landtagswahl|Bürgerschaftswahl|Abgeordnetenhauswahl) /, ''); };
  var d = new Date();
  var heute = new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
  fetch('koalitionen/data.json', { cache: 'no-cache' }).then(function (r) { return r.ok ? r.json() : null; }).then(function (data) {
    if (!data || !data.parlamente) return;
    // "sortierung" ist JJJJ-MM-TT (fester Termin) oder JJJJ-MM (voraussichtlich); vergangene Termine fallen weg.
    var kommende = data.parlamente.filter(function (p) { return p.sortierung && p.sortierung >= heute.slice(0, p.sortierung.length); })
      .sort(function (a, b) { return a.sortierung < b.sortierung ? -1 : a.sortierung > b.sortierung ? 1 : 0; })
      .slice(0, ANZAHL);
    if (!kommende.length) return;
    feld.querySelector('.rk-liste').innerHTML = kommende.map(function (p) {
      return '<span class="rk-zeile"><span>' + esc(kurzname(p.name)) + '</span><span class="wt">' + esc(p.wahltermin) + '</span></span>';
    }).join('');
    feld.hidden = false;
  }).catch(function () {});
})();
