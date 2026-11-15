/* Karte „Beteiligte Staaten im Zeitverlauf“. Daten: window.WK_STAATEN und window.WK_SCHRITTE aus daten.js.
   Status je Staat zu einem Datum: M = Mittelmächte, A = Alliierte, X = ausgeschieden, B = nur Beziehungen abgebrochen, sonst nicht beteiligt. */
(function () {
  var svg = document.getElementById('wk-karte');
  if (!svg || !window.WK_STAATEN) return;
  var ST = window.WK_STAATEN, SCHRITTE = window.WK_SCHRITTE;
  var regler = document.getElementById('wk-regler');
  var tag = document.getElementById('wk-stichtag');
  var text = document.getElementById('wk-ereignis');
  var zaehler = document.getElementById('wk-zaehler');
  var play = document.getElementById('wk-play');
  var flaechen = Array.prototype.slice.call(svg.querySelectorAll('path[data-k]'));
  var MONATE = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'];

  function datumText(iso) {
    var t = iso.split('-');
    return (+t[2]) + '. ' + MONATE[+t[1] - 1] + ' ' + t[0];
  }
  function status(k, iso) {
    var s = ST[k];
    if (!s) return '';
    var r = '';
    for (var i = 0; i < s.p.length; i++) {      // Perioden [ab, Status], aufsteigend
      if (s.p[i][0] <= iso) r = s.p[i][1];
    }
    return r;
  }
  function zeige(i) {
    var sch = SCHRITTE[i], iso = sch.d, neu = sch.k || [];
    tag.textContent = datumText(iso);
    text.textContent = sch.t;
    var n = { M: 0, A: 0 };
    Object.keys(ST).forEach(function (k) { var s = status(k, iso); if (n[s] !== undefined) n[s]++; });
    zaehler.textContent = 'Im Krieg: ' + n.A + ' Staaten auf alliierter Seite, ' + n.M + ' Mittelmächte (ohne Kolonien und Dominions).';
    flaechen.forEach(function (p) {
      var k = p.getAttribute('data-k'), s = status(k, iso);
      p.setAttribute('class', (p.classList.contains('kol') ? 'kol ' : '') + (s ? 'st-' + s : '') + (neu.indexOf(k) >= 0 && !p.classList.contains('kol') ? ' neu' : ''));
    });
    regler.setAttribute('aria-valuetext', datumText(iso) + ': ' + sch.t);
  }
  regler.max = SCHRITTE.length - 1;
  regler.addEventListener('input', function () { stop(); zeige(+regler.value); });

  var timer = null;
  function stop() { if (timer) { clearInterval(timer); timer = null; play.textContent = '▶'; play.setAttribute('aria-label', 'Abspielen'); } }
  play.addEventListener('click', function () {
    if (timer) { stop(); return; }
    if (+regler.value >= SCHRITTE.length - 1) regler.value = 0;
    play.textContent = '❚❚'; play.setAttribute('aria-label', 'Anhalten');
    zeige(+regler.value);
    timer = setInterval(function () {
      var v = +regler.value + 1;
      if (v > SCHRITTE.length - 1) { stop(); return; }
      regler.value = v; zeige(v);
    }, 1600);
  });

  // Ausschnitt Welt / Europa
  var welt = svg.getAttribute('data-welt'), europa = svg.getAttribute('data-europa');
  Array.prototype.forEach.call(document.querySelectorAll('[data-ausschnitt]'), function (b) {
    b.addEventListener('click', function () {
      var eu = b.getAttribute('data-ausschnitt') === 'europa';
      svg.setAttribute('viewBox', eu ? europa : welt);
      Array.prototype.forEach.call(document.querySelectorAll('[data-ausschnitt]'), function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
    });
  });
  var start = 0;
  regler.value = start; zeige(start);
})();

