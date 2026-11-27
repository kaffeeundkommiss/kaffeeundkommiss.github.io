/**
 * plenarsaal-schema.js (27.11.2026)
 * Interaktives Raumschema (Vogelperspektive) des Plenarsaals im 21. Deutschen Bundestag.
 * Entwurf von Jan (mit Gemini), für die Seite angepasst: Farben aus basis.css/style.css (heller und dunkler Modus),
 * alle Zahlen und der Stichtag kommen aus der Tabelle #sitze-tabelle (einzige Datenquelle, wie bei plenarsaal.js).
 * Verknüpft den Grundriss mit den markierten Begriffen im Erklärtext. Ohne JavaScript bleibt der Grundriss verborgen.
 */
(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    var box = document.getElementById('ps-schema');
    var svg = document.getElementById('ps-raum-svg');
    var tabelle = document.getElementById('sitze-tabelle');
    var infoBox = document.getElementById('ps-schema-info');
    if (!box || !svg || !tabelle || !infoBox) return;

    // 1. Styles für Schema-Box, Umschalter und Begriffe (style.css bleibt unverändert)
    var style = document.createElement('style');
    style.textContent = [
      '.ps-erkl .ps-schema-box{grid-column:1/-1;margin:0 0 14px;padding:16px;background:var(--kk-papier);border:1px solid var(--kk-linie);display:grid;grid-template-columns:minmax(0,600px) minmax(0,1fr);gap:12px 20px;align-items:start}',
      '.ps-schema-kopf{grid-column:1/-1;display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:8px 12px;font-size:15px}',
      '.ps-stand-wahl{display:inline-flex;border:1px solid var(--kk-linie)}',
      '.ps-stand-btn{min-height:40px;padding:0 12px;background:transparent;border:0;color:var(--kk-tinte);font:500 13px var(--kk-mono);cursor:pointer}',
      '.ps-stand-btn.aktiv{background:var(--kk-tinte);color:var(--kk-papier);font-weight:700}',
      '.ps-stand-btn:focus-visible,.ps-begriff:focus-visible{outline:3px solid var(--kk-akzent);outline-offset:2px}',
      '.ps-schema-info{padding:10px 12px;background:var(--kk-akzent-hell);border-left:4px solid var(--kk-tinte);font-size:15px;line-height:1.45;color:var(--kk-tinte)}',
      '.ps-begriff{background:var(--kk-akzent-hell);border:0;border-bottom:1.5px dashed var(--kk-tinte);padding:0 4px;font:inherit;color:inherit;cursor:pointer}',
      '.ps-begriff:hover,.ps-begriff.aktiv{background:var(--kk-tinte);color:var(--kk-papier)}',
      '@media (max-width:760px){.ps-erkl .ps-schema-box{grid-template-columns:1fr;padding:12px}}'
    ].join('\n');
    document.head.appendChild(style);
    box.hidden = false;

    // 2. Sitzdaten und Stichtag aus #sitze-tabelle
    var daten = {};
    tabelle.querySelectorAll('tbody tr[data-linie]').forEach(function (tr) {
      var linie = tr.getAttribute('data-linie');
      var th = tr.querySelector('th');
      daten[linie] = {
        name: th ? th.textContent.trim() : linie,
        aktuell: parseInt(tr.getAttribute('data-sitze'), 10) || 0,
        wahl: parseInt(tr.getAttribute('data-wahl'), 10) || 0,
        rolle: tr.getAttribute('data-rolle') || ''
      };
    });
    var cap = tabelle.querySelector('caption');
    var m = cap && cap.textContent.match(/Stand\s+([\d.]+)/);
    var stichtag = m ? m[1] : '';
    var standBtns = box.querySelectorAll('.ps-stand-btn');
    standBtns.forEach(function (b) {
      if (b.getAttribute('data-stand') === 'aktuell' && stichtag) b.textContent = 'Stand ' + stichtag;
    });

    function sitze(n) { return n + (n === 1 ? ' Sitz' : ' Sitze'); }
    function wert(linie, modus) { var d = daten[linie]; return d ? (modus === 'wahl' ? d.wahl : d.aktuell) : 0; }

    // 3. Beschreibungen der Raumzonen (Wortlaut wie im Erklärtext und in der Belegmatrix)
    var zonenInfo = {
      praesidium: 'Präsidium und Rednerpult: Sitzungsleitung in der Mitte mit Blick in den Saal. Der Platz der AfD-Fraktion im Präsidium ist unbesetzt.',
      regierung: 'Regierungsbank (vom Präsidium aus rechts): Bundeskanzler Friedrich Merz (CDU) und 17 Bundesministerinnen und Bundesminister, getragen von CDU/CSU und SPD.',
      bundesrat: 'Bundesratsbank (vom Präsidium aus links): Mitglieder der Landesregierungen. Sie dürfen an jeder Sitzung teilnehmen und müssen jederzeit gehört werden (Art. 43 Abs. 2 GG).',
      wehrbeauftragter: 'Wehrbeauftragter des Bundestages: einzelner Platz neben der Bundesratsbank (Lage im Schema vereinfacht). Er ist kein Abgeordneter, sondern Hilfsorgan des Bundestages bei der Kontrolle der Bundeswehr.',
      tribuenen: 'Tribünen: fast 400 Plätze über dem Saal, drei Tribünen für Besucherinnen und Besucher, zwei für Presse und Medien. Dazwischenrufen und Klatschen sind dort nicht erlaubt.'
    };
    function infoFraktionslos(modus) {
      return modus === 'wahl'
        ? 'Fraktionslos bei der Wahl 2025: ' + sitze(wert('ohne', 'wahl')) + ' (Stefan Seidler, SSW). Lage im Schema vereinfacht.'
        : 'Fraktionslos am ' + stichtag + ': ' + sitze(wert('ohne', 'aktuell')) + ' (Stefan Seidler, SSW; Sieghard Knodel nach Austritt aus der AfD; Jan Wenzel Schmidt nach Ausschluss aus der AfD-Fraktion). Lage im Schema vereinfacht.';
    }

    var aktiveZone = null;
    var aktiverModus = 'aktuell';

    // 4. Zone im Grundriss und Begriff im Text hervorheben
    function setzeFokus(zoneKey, fraktionKey) {
      var zonen = svg.querySelectorAll('.raum-zone');
      var begriffe = document.querySelectorAll('.ps-begriff');

      if (aktiveZone === (fraktionKey || zoneKey)) {
        aktiveZone = null;
        svg.classList.remove('hat-fokus');
        zonen.forEach(function (z) { z.classList.remove('fokus'); });
        begriffe.forEach(function (b) { b.classList.remove('aktiv'); });
        infoBox.textContent = 'Alle Bereiche sichtbar. Tippen Sie auf einen Bereich im Grundriss oder einen markierten Begriff im Text.';
        return;
      }

      aktiveZone = fraktionKey || zoneKey;
      svg.classList.add('hat-fokus');
      zonen.forEach(function (z) {
        var treffer = fraktionKey ? (z.getAttribute('data-fraktion') === fraktionKey) : (z.getAttribute('data-zone') === zoneKey);
        z.classList.toggle('fokus', treffer);
      });
      begriffe.forEach(function (b) { b.classList.toggle('aktiv', b.getAttribute('data-ziel') === zoneKey); });

      if (fraktionKey && daten[fraktionKey]) {
        var f = daten[fraktionKey];
        var diff = f.aktuell - f.wahl;
        var text = f.name + ' (' + f.rolle + '): ';
        if (aktiverModus === 'wahl') text += sitze(f.wahl) + ' bei der Wahl 2025.';
        else text += sitze(f.aktuell) + ' am ' + stichtag + (diff !== 0 ? ' (' + (diff > 0 ? '+' : '') + diff + ' gegenüber der Wahl 2025)' : '') + '.';
        infoBox.textContent = text;
      } else if (zoneKey === 'fraktionslos') {
        infoBox.textContent = infoFraktionslos(aktiverModus);
      } else if (zonenInfo[zoneKey]) {
        infoBox.textContent = zonenInfo[zoneKey];
      }
    }

    svg.querySelectorAll('.raum-zone').forEach(function (el) {
      function aktivieren() { setzeFokus(el.getAttribute('data-zone'), el.getAttribute('data-fraktion')); }
      el.addEventListener('click', aktivieren);
      el.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); aktivieren(); }
      });
    });

    document.querySelectorAll('.ps-begriff').forEach(function (btn) {
      btn.addEventListener('click', function () {
        setzeFokus(btn.getAttribute('data-ziel'), null);
        var rect = svg.getBoundingClientRect();
        if (rect.top < 0 || rect.bottom > window.innerHeight) svg.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      });
    });

    // 5. Sitzzahlen im Grundriss setzen und zwischen Stichtag und Wahl 2025 umschalten
    function zahlenSetzen(modus) {
      Object.keys(daten).forEach(function (linie) {
        var textEl = document.getElementById('svg-sitze-' + linie);
        if (!textEl) return;
        var w = wert(linie, modus);
        textEl.textContent = linie === 'ohne' ? 'Fraktionslos: ' + w : String(w);
      });
    }
    zahlenSetzen('aktuell');

    standBtns.forEach(function (btn) {
      btn.addEventListener('click', function () {
        var modus = btn.getAttribute('data-stand');
        if (modus === aktiverModus) return;
        aktiverModus = modus;
        standBtns.forEach(function (b) {
          b.classList.toggle('aktiv', b === btn);
          b.setAttribute('aria-pressed', b === btn ? 'true' : 'false');
        });
        zahlenSetzen(modus);
        // Unterschiede zwischen beiden Ständen aus der Tabelle beschreiben
        var teile = [];
        Object.keys(daten).forEach(function (linie) {
          var d = daten[linie];
          if (d.aktuell !== d.wahl) teile.push((linie === 'ohne' ? 'fraktionslos' : d.name) + ' ' + wert(linie, modus));
        });
        infoBox.textContent = (modus === 'wahl'
          ? 'Ansicht „Wahl 2025“ (endgültiges Ergebnis)'
          : 'Ansicht „Stand ' + stichtag + '“') + (teile.length ? ': ' + teile.join(', ') + '. Die übrigen Fraktionen sind unverändert.' : '.');
        aktiveZone = null;
        svg.classList.remove('hat-fokus');
        svg.querySelectorAll('.raum-zone').forEach(function (z) { z.classList.remove('fokus'); });
        document.querySelectorAll('.ps-begriff').forEach(function (b) { b.classList.remove('aktiv'); });
      });
    });
  });
})();
