/* Wahlen und Koalitionen: Tabelle „Koalitionen in den Ländern“ aus ../koalitionen/data.json.
   Gleiche Daten wie der Koalitionsrechner (wöchentliche Routine). Ohne JS bleibt der Hinweis stehen. */
(function () {
  'use strict';
  var feld = document.getElementById('laender-tab');
  if (!feld || !window.fetch) return;
  var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  var land = function (n) { return String(n).replace(/^(Landtagswahl|Bürgerschaftswahl|Abgeordnetenhauswahl) /, ''); };
  // Allein regierende Parteien zuerst, dann Zweier-, dann Dreierbündnisse; innerhalb alphabetisch
  var sortiere = function (h) { return h.slice().sort(function (a, b) { return a.length - b.length || a.join().localeCompare(b.join(), 'de'); }); };
  fetch('../koalitionen/data.json', { cache: 'no-cache' }).then(function (r) { return r.ok ? r.json() : null; }).then(function (d) {
    if (!d || !d.parlamente) return;
    var reihen = d.parlamente.filter(function (p) { return p.id !== 'bund' && p.historie; })
      .sort(function (a, b) { return land(a.name).localeCompare(land(b.name), 'de'); })
      .map(function (p) {
        var q = p.historie_quelle || {};
        var b = sortiere(p.historie).map(function (k) { return '<li>' + esc(k.length === 1 ? k[0] + ' allein' : k.join(' – ')) + '</li>'; }).join('');
        var abg = p.historie_abgleich ? ' · abgeglichen' : '';
        return '<tr><td>' + esc(land(p.name)) + '</td><td><ul class="buendnisse">' + b + '</ul></td>' +
          '<td class="qz">' + (q.url ? '<a href="' + esc(q.url) + '">' + esc(q.name) + '</a>' : esc(q.name || '')) + esc(abg) + '</td></tr>';
      }).join('');
    feld.innerHTML = '<table class="laender"><thead><tr><th scope="col">Land</th><th scope="col">Bündnisse, die schon regiert haben</th><th scope="col">Quelle</th></tr></thead><tbody>' + reihen + '</tbody></table>';
    var st = document.getElementById('laender-stand');
    if (st && d.historie_stand) st.textContent = d.historie_stand.split('-').reverse().join('.');
  }).catch(function () {});
})();
