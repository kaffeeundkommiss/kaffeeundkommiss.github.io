/* Abspielbarer Ablauf auf den Kriegsseiten (1864, 1866, 1870-71), nach dem Muster der Bullecourt-Karte.
   Ohne JavaScript bleiben alle Pfeile, Marken und Einträge sichtbar. */
(function () {
  var box = document.querySelector('.kk-ablauf');
  if (!box) return;
  var block = document.querySelector('.kk-kartenblock');
  var knoepfe = Array.prototype.slice.call(box.querySelectorAll('.kk-schritte button'));
  var play = box.querySelector('.kk-play');
  var teile = Array.prototype.slice.call(document.querySelectorAll('.kk-kartenblock [data-s]'));
  var zahl = knoepfe.length, cur = 1, timer = null;
  box.hidden = false;
  block.classList.add('mit-ablauf');
  function setze(n) {
    cur = n;
    knoepfe.forEach(function (b) { b.setAttribute('aria-pressed', +b.dataset.step === n ? 'true' : 'false'); });
    teile.forEach(function (el) {
      var an = el.getAttribute('data-s').split(' ').indexOf(String(n)) >= 0;
      el.classList.remove('an');
      if (an) { void el.getBoundingClientRect(); el.classList.add('an'); }
      if (el.tagName === 'LI') el.hidden = !an;
    });
  }
  function stopp() {
    if (timer) clearInterval(timer);
    timer = null; play.setAttribute('aria-pressed', 'false'); play.textContent = 'Abspielen';
  }
  function start() {
    if (cur >= zahl) setze(1);
    play.setAttribute('aria-pressed', 'true'); play.textContent = 'Anhalten';
    timer = setInterval(function () {
      if (cur >= zahl) { stopp(); return; }
      setze(cur + 1);
      if (cur >= zahl) stopp();
    }, 4500);
  }
  knoepfe.forEach(function (b) { b.addEventListener('click', function () { stopp(); setze(+b.dataset.step); }); });
  play.addEventListener('click', function () { if (timer) stopp(); else start(); });
  // Anker auf einen Eintrag (etwa Klick auf eine Kartenmarke) wählt dessen Schritt.
  function ausAdresse() {
    var el = document.getElementById(decodeURIComponent(location.hash.slice(1)));
    if (el && el.tagName === 'LI' && el.hasAttribute('data-s')) { stopp(); setze(+el.getAttribute('data-s')); }
  }
  window.addEventListener('hashchange', ausAdresse);
  setze(1);
  ausAdresse();
})();
