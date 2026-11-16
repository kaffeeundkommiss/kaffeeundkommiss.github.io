/* Gemeinsame Reiter der Übersichtsseiten (geschichte/erster-weltkrieg/, geschichte/einigungskriege/, sicherheitspolitik/bundeswehr/), Aussehen wie auf der Richthofen-Seite.
   Ohne JavaScript bleiben alle Abschnitte sichtbar und die Reiter springen per Anker. Ein Anker auf ein Element
   in einem anderen Bereich (etwa ein Quellenverweis #q-…) wechselt in diesen Bereich. */
(function () {
  var reiter = Array.prototype.slice.call(document.querySelectorAll('nav.pages a[data-reiter]'));
  var teile = Array.prototype.slice.call(document.querySelectorAll('main section[data-reiter]'));
  if (!reiter.length) return;
  var namen = reiter.map(function (a) { return a.getAttribute('data-reiter'); });
  function bereichVon(id) {
    if (!id) return null;
    if (namen.indexOf(id) >= 0) return id;
    var el = document.getElementById(id);
    var teil = el && el.closest('[data-reiter]');
    return teil ? teil.getAttribute('data-reiter') : null;
  }
  function zeige(bereich, ziel) {
    teile.forEach(function (t) { t.hidden = t.getAttribute('data-reiter') !== bereich; });
    reiter.forEach(function (a) {
      if (a.getAttribute('data-reiter') === bereich) a.setAttribute('aria-current', 'page');
      else a.removeAttribute('aria-current');
    });
    if (ziel && namen.indexOf(ziel) < 0) {
      var el = document.getElementById(ziel);
      if (el) el.scrollIntoView();
    } else {
      var kopf = document.querySelector('.seitenkopf');
      if (kopf && kopf.getBoundingClientRect().top < 0) kopf.scrollIntoView();
    }
  }
  function ausAdresse() {
    var id = decodeURIComponent(location.hash.slice(1));
    zeige(bereichVon(id) || namen[0], id);
  }
  window.addEventListener('hashchange', ausAdresse);
  document.documentElement.classList.add('mit-reitern');
  ausAdresse();
  // Der Browser springt beim Laden selbst zum Anker; danach Reiter wieder sichtbar machen.
  window.addEventListener('load', function () { setTimeout(ausAdresse, 0); });
})();
