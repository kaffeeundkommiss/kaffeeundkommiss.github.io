/* Politik-Übersicht: Umfragevergleich Bundestag aus koalitionen/data.json (neueste Umfrage je Institut).
   Gleiche Datenquelle wie der Koalitionsrechner. Neutral: keine Parteifarben. */
(function () {
  'use strict';
  var feld = document.getElementById('umfragevergleich');
  if (!feld || !window.fetch) return;
  var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  var datum = function (iso) { return iso ? iso.slice(8, 10) + '.' + iso.slice(5, 7) + '.' : ''; };
  var zahl = function (v) { return v == null ? '–' : String(v).replace('.', ','); };
  // Reihenfolge nach dem Zweitstimmenergebnis 2025, wie die Monitore auf dieser Seite
  var REIHE = ['CDU/CSU', 'AfD', 'SPD', 'Grüne', 'Linke', 'BSW', 'FDP', 'Sonstige'];
  fetch('koalitionen/data.json', { cache: 'no-cache' }).then(function (r) { return r.ok ? r.json() : null; }).then(function (d) {
    var b = d && d.parlamente && d.parlamente.filter(function (p) { return p.id === 'bund'; })[0];
    if (!b || !b.umfragen || !b.umfragen.length) return;
    var u = b.umfragen.slice().sort(function (x, y) { return x.datum < y.datum ? 1 : -1; });
    // Wie im Koalitionsrechner: nur Umfragen höchstens fenster_tage (Startwert 90) vor der neuesten
    var tage = (d.regeln && d.regeln.fenster_tage) || 90;
    var grenze = new Date(new Date(u[0].datum).getTime() - tage * 864e5).toISOString().slice(0, 10);
    u = u.filter(function (x) { return x.datum >= grenze; });
    var spalten = REIHE.filter(function (p) { return u.some(function (x) { return x.werte[p] != null; }); });
    var mm = {};
    spalten.forEach(function (p) {
      var w = u.map(function (x) { return x.werte[p]; }).filter(function (v) { return v != null; });
      mm[p] = [Math.min.apply(null, w), Math.max.apply(null, w)];
    });
    var kopf = '<tr><th scope="col">Institut</th>' + spalten.map(function (p) { return '<th scope="col">' + esc(p) + '</th>'; }).join('') + '</tr>';
    var zeilen = u.map(function (x) {
      return '<tr><th scope="row">' + esc(x.institut) + ' <span class="uv-d">' + esc(datum(x.datum)) + '</span></th>' + spalten.map(function (p) {
        return '<td>' + zahl(x.werte[p]) + '</td>';
      }).join('') + '</tr>';
    }).join('');
    var spanne = '<tr class="spanne"><th scope="row">Spanne</th>' + spalten.map(function (p) {
      return '<td>' + (mm[p][0] === mm[p][1] ? zahl(mm[p][0]) : zahl(mm[p][0]) + '–' + zahl(mm[p][1])) + '</td>';
    }).join('') + '</tr>';
    feld.innerHTML = '<table><thead>' + kopf + '</thead><tbody>' + zeilen + '</tbody><tfoot>' + spanne + '</tfoot></table>';
    // Barrierefreiheit: Scrollbereich per Tastatur erreichbar; Hinweis nur, wenn die Tabelle breiter als ihr Rahmen ist
    feld.setAttribute('tabindex', '0');
    feld.setAttribute('role', 'region');
    feld.setAttribute('aria-label', 'Umfragen im Vergleich, Tabelle');
    var hinweis = document.getElementById('uv-hinweis');
    var pruefen = function () { if (hinweis) hinweis.hidden = feld.scrollWidth <= feld.clientWidth + 1; };
    pruefen();
    window.addEventListener('resize', pruefen);
    var st = document.getElementById('uv-stand');
    if (st && d.umfragen_stand) st.textContent = ', Stand ' + d.umfragen_stand.slice(8, 10) + '.' + d.umfragen_stand.slice(5, 7) + '.' + d.umfragen_stand.slice(0, 4);
  }).catch(function () {});
})();
