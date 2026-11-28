/* Abspielbarer Ablauf für Seiten mit mehreren Karten, nach geschichte/einigungskriege/ablauf.js.
   Jeder Block .kk-ablauf steuert den direkt folgenden .kk-kartenblock.
   Ohne JavaScript bleiben alle Pfeile, Marken und Einträge sichtbar. */
(function () {
  var bloecke = [];
  Array.prototype.forEach.call(document.querySelectorAll('.kk-ablauf'), function (box) {
    var block = box.nextElementSibling;
    if (!block || !block.classList.contains('kk-kartenblock')) return;
    var knoepfe = Array.prototype.slice.call(box.querySelectorAll('.kk-schritte button'));
    var play = box.querySelector('.kk-play');
    var teile = Array.prototype.slice.call(block.querySelectorAll('[data-s]'));
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
    setze(1);
    bloecke.push({ block: block, stopp: stopp, setze: setze });
  });
  // Anker auf einen Eintrag (etwa Klick auf eine Kartenmarke) wählt dessen Schritt im passenden Block.
  function ausAdresse() {
    var el = document.getElementById(decodeURIComponent(location.hash.slice(1)));
    if (!el || el.tagName !== 'LI' || !el.hasAttribute('data-s')) return;
    bloecke.forEach(function (b) {
      if (b.block.contains(el)) { b.stopp(); b.setze(+el.getAttribute('data-s')); }
    });
  }
  window.addEventListener('hashchange', ausAdresse);
  ausAdresse();
})();
