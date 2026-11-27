/* Technik im Modell: lädt ein 3D-Modell erst auf Klick.
   Die Modellskripte liegen in modell/ (seit 21.11.2026 nur noch hier, nicht mehr auf den Einzelseiten)
   und suchen beim Laden ihr Element per id (dr1, mk2, g98, luetzow). three.js 0.159.0 wird einmal geladen. */
(function () {
  "use strict";
  var THREE_URL = "modell/vendor/three-0.159.0.min.js";
  var dreiLaden = null;

  function skript(src) {
    return new Promise(function (ok, fehler) {
      var s = document.createElement("script");
      s.src = src;
      s.onload = ok;
      s.onerror = function () { fehler(new Error(src)); };
      document.head.appendChild(s);
    });
  }

  function laden(karte, knopf) {
    var buehne = karte.querySelector(".m-buehne");
    var vorlage = karte.querySelector("template");
    knopf.disabled = true;
    knopf.textContent = "Lädt …";
    if (!dreiLaden) dreiLaden = window.THREE ? Promise.resolve() : skript(THREE_URL);
    dreiLaden
      .then(function () {
        buehne.replaceChildren(vorlage.content.cloneNode(true));
        buehne.classList.add("geladen");
        return skript(karte.dataset.skript);
      })
      .then(function () {
        /* Der Ladeknopf ist weg: Fokus auf den ersten Ansichtsknopf, damit Tastaturnutzer nicht an den Seitenanfang springen */
        var b = buehne.querySelector("[data-view]");
        if (b) b.focus({ preventScroll: true });
      })
      .catch(function () {
        dreiLaden = window.THREE ? dreiLaden : null;
        var p = document.createElement("p");
        p.className = "m-fehler";
        p.setAttribute("role", "status");
        p.textContent = "Das 3D-Modell konnte nicht geladen werden. Bitte später erneut versuchen oder die Einzelseite öffnen.";
        if (!buehne.classList.contains("geladen")) {
          knopf.disabled = false;
          knopf.textContent = "Erneut versuchen";
        }
        buehne.appendChild(p);
      });
  }

  document.querySelectorAll(".modell").forEach(function (karte) {
    var knopf = karte.querySelector(".m-laden");
    if (knopf) knopf.addEventListener("click", function () { laden(karte, knopf); });
  });
})();
