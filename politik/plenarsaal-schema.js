/**
 * plenarsaal-schema.js
 * Interaktives Raumschema (Vogelperspektive) für den 21. Deutschen Bundestag.
 * Liest alle Sitzdaten direkt aus der bestehenden Tabelle #sitze-tabelle aus
 * ("Single Source of Truth") und verknüpft den Grundriss mit den Erklärtexten.
 */
(function () {
  'use strict';

  // Warten, bis das DOM vollständig geladen ist
  document.addEventListener('DOMContentLoaded', function () {
    const svg = document.getElementById('ps-raum-svg');
    const tabelle = document.getElementById('sitze-tabelle');
    const infoBox = document.getElementById('ps-schema-info');

    if (!svg || !tabelle || !infoBox) return;

    // 1. Minimal-Styles für die interaktiven Buttons & die Schema-Box injizieren
    // (fügt sich nahtlos in das bestehende Design ein, ohne style.css ändern zu müssen)
    const style = document.createElement('style');
    style.textContent = `
      .ps-schema-box {
        margin: 0 0 1.4rem 0;
        padding: 0.9rem;
        border: 1px solid rgba(128, 120, 105, 0.3);
        border-radius: 12px;
        background: rgba(35, 33, 28, 0.04);
      }
      .ps-schema-kopf {
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        align-items: center;
        gap: 0.6rem;
        margin-bottom: 0.75rem;
        font-size: 0.92rem;
      }
      .ps-stand-wahl {
        display: inline-flex;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid rgba(128, 120, 105, 0.45);
      }
      .ps-stand-btn {
        background: transparent;
        border: none;
        padding: 0.42rem 0.75rem;
        font: inherit;
        font-size: 0.84rem;
        cursor: pointer;
        color: inherit;
        transition: background 0.2s ease, color 0.2s ease;
      }
      .ps-stand-btn.aktiv {
        background: #23211c;
        color: #f4f1ea;
        font-weight: 600;
      }
      .ps-schema-info {
        margin-top: 0.65rem;
        padding: 0.55rem 0.75rem;
        border-radius: 8px;
        background: rgba(35, 33, 28, 0.07);
        font-size: 0.88rem;
        line-height: 1.4;
      }
      .ps-begriff {
        background: rgba(230, 194, 110, 0.22);
        border: none;
        border-bottom: 1.5px dashed currentColor;
        border-radius: 4px;
        padding: 0.05rem 0.3rem;
        font: inherit;
        color: inherit;
        cursor: pointer;
        transition: background 0.2s ease;
      }
      .ps-begriff:hover, .ps-begriff.aktiv {
        background: rgba(230, 194, 110, 0.5);
      }
    `;
    document.head.appendChild(style);

    // 2. Sitzdaten aus #sitze-tabelle einlesen
    const daten = {};
    const zeilen = tabelle.querySelectorAll('tbody tr[data-linie]');
    zeilen.forEach(function (tr) {
      const linie = tr.getAttribute('data-linie');
      daten[linie] = {
        name: tr.querySelector('th') ? tr.querySelector('th').textContent.trim() : linie,
        aktuell: parseInt(tr.getAttribute('data-sitze'), 10) || 0,
        wahl: parseInt(tr.getAttribute('data-wahl'), 10) || 0,
        rolle: tr.getAttribute('data-rolle') || ''
      };
    });

    // 3. Beschreibungen für die einzelnen Raumzonen
    const zonenInfo = {
      praesidium: 'Präsidium & Rednerpult: Sitzungsleitung oben in der Mitte mit Blick in den Saal. Der Platz der AfD im Präsidium ist unbesetzt.',
      regierung: 'Regierungsbank (vom Präsidium aus rechts): Bundeskanzler Friedrich Merz (CDU) und 17 Ministerinnen und Minister von CDU/CSU und SPD.',
      bundesrat: 'Bundesratsbank (vom Präsidium aus links): Vertreter der Landesregierungen mit jederzeitigen Teilnehme- und Rederecht (Art. 43 Abs. 2 GG).',
      wehrbeauftragter: 'Wehrbeauftragter des Bundestages: Einzelplatz neben der Bundesratsbank; Hilfsorgan des Parlaments zur Kontrolle der Bundeswehr.',
      tribuenen: 'Tribünen: Fast 400 Plätze über dem Saal (3 für Besucherinnen/Besucher, 2 für Presse/Medien). Beifall oder Zwischenrufe sind untersagt.',
      fraktionslos: 'Fraktionslose Abgeordnete: Aktuell 3 Sitze (Stefan Seidler/SSW seit Wahl 2025 sowie Sieghard Knodel und Jan Wenzel Schmidt nach Austritt/Ausschluss aus der AfD).'
    };

    let aktiveZone = null;
    let aktiverModus = 'aktuell'; // 'aktuell' oder 'wahl'

    // 4. Zone im SVG und im Text hervorheben
    function setzeFokus(zoneKey, fraktionKey) {
      const zonen = svg.querySelectorAll('.raum-zone');
      const begriffe = document.querySelectorAll('.ps-begriff');

      // Erneuter Klick auf dieselbe Zone hebt den Filter wieder auf
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
        const zName = z.getAttribute('data-zone');
        const fName = z.getAttribute('data-fraktion');
        const treffer = fraktionKey ? (fName === fraktionKey) : (zName === zoneKey);
        z.classList.toggle('fokus', treffer);
      });

      begriffe.forEach(function (b) {
        b.classList.toggle('aktiv', b.getAttribute('data-ziel') === zoneKey);
      });

      // Infotext aktualisieren
      if (fraktionKey && daten[fraktionKey]) {
        const f = daten[fraktionKey];
        const zahl = aktiverModus === 'aktuell' ? f.aktuell : f.wahl;
        const diff = f.aktuell - f.wahl;
        const diffText = diff !== 0 ? ' (' + (diff > 0 ? '+' : '') + diff + ' gegenüber Wahl 2025)' : '';
        infoBox.textContent = f.name + ' (' + f.rolle + '): ' + zahl + ' Sitze' + (aktiverModus === 'aktuell' ? diffText : ' bei der Wahl 2025') + '.';
      } else if (zonenInfo[zoneKey]) {
        infoBox.textContent = zonenInfo[zoneKey];
      }
    }

    // Event-Listener für SVG-Zonen (Klick + Tastatur)
    svg.querySelectorAll('.raum-zone').forEach(function (el) {
      function aktivieren() {
        const zone = el.getAttribute('data-zone');
        const fraktion = el.getAttribute('data-fraktion');
        setzeFokus(zone, fraktion);
      }
      el.addEventListener('click', aktivieren);
      el.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          aktivieren();
        }
      });
    });

    // Event-Listener für hervorgehobene Text-Begriffe
    document.querySelectorAll('.ps-begriff').forEach(function (btn) {
      btn.addEventListener('click', function () {
        const ziel = btn.getAttribute('data-ziel');
        setzeFokus(ziel, null);
        // Auf kleinen Bildschirmen sanft zum Grundriss scrollen, falls er aus dem Blickfeld ist
        const rect = svg.getBoundingClientRect();
        if (rect.top < 0 || rect.bottom > window.innerHeight) {
          svg.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
      });
    });

    // 5. Umschalter: Stand 26.11.2026 vs. Wahl 2025
    const standBtns = document.querySelectorAll('.ps-stand-btn');
    standBtns.forEach(function (btn) {
      btn.addEventListener('click', function () {
        const modus = btn.getAttribute('data-stand');
        if (modus === aktiverModus) return;
        aktiverModus = modus;

        standBtns.forEach(function (b) {
          b.classList.toggle('aktiv', b === btn);
        });

        // Sitzwerte im SVG aktualisieren
        Object.keys(daten).forEach(function (linie) {
          const textEl = document.getElementById('svg-sitze-' + linie);
          if (!textEl) return;
          const wert = modus === 'aktuell' ? daten[linie].aktuell : daten[linie].wahl;
          if (linie === 'ohne') {
            textEl.textContent = 'Fraktionslos: ' + wert + (wert === 1 ? ' Sitz' : ' Sitze');
          } else {
            textEl.textContent = String(wert);
          }
        });

        infoBox.textContent = modus === 'wahl'
          ? 'Ansicht „Wahl 2025“: AfD noch mit 152 Sitzen, nur 1 fraktionsloser Abgeordneter (SSW).'
          : 'Ansicht „Stand 26.11.2026“: AfD mit 150 Sitzen, 3 fraktionslose Abgeordnete (+2 durch Austritt/Ausschluss).';
      });
    });
  });
})();
