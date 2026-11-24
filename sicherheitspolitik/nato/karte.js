// Karte der NATO-Erweiterungen 1949–2024 mit Zeitregler. Grundkarten in karte-daten.js (window.KARTE), Schritte hier.
// Karte a: Grenzen 1960 (bis 1982), Karte b: Grenzen 2010 (ab 1990).
(function () {
  "use strict";
  const K = window.KARTE;
  const NS = "http://www.w3.org/2000/svg";
  const GRUENDER = ["BE", "DK", "FR", "IS", "IT", "LU", "NL", "NO", "PT", "GB"];
  const SCHRITTE = [
    { id: "s1949", kurz: "1949", titel: "Gründung 1949: zwölf Staaten", karte: "a", neu: GRUENDER,
      neuText: "Gründungsmitglieder (dazu USA und Kanada)" },
    { id: "s1952", kurz: "1952", titel: "1952: Griechenland und Türkei", karte: "a", neu: ["GR", "TR"] },
    { id: "s1955", kurz: "1955", titel: "1955: Bundesrepublik Deutschland", karte: "a", neu: ["DE"] },
    { id: "s1982", kurz: "1982", titel: "1982: Spanien", karte: "a", neu: ["ES"] },
    { id: "s1990", kurz: "1990", titel: "1990: Deutsche Einheit", karte: "b", neu: ["DE"],
      neuText: "Vereintes Deutschland" },
    { id: "s1999", kurz: "1999", titel: "1999: Polen, Tschechien, Ungarn", karte: "b", neu: ["PL", "CZ", "HU"] },
    { id: "s2004", kurz: "2004", titel: "2004: sieben Staaten", karte: "b", neu: ["BG", "EE", "LV", "LT", "RO", "SK", "SI"] },
    { id: "s2009", kurz: "2009", titel: "2009: Albanien und Kroatien", karte: "b", neu: ["AL", "HR"] },
    { id: "s2017", kurz: "2017", titel: "2017: Montenegro", karte: "b", neu: ["ME"] },
    { id: "s2020", kurz: "2020", titel: "2020: Nordmazedonien", karte: "b", neu: ["MK"] },
    { id: "s2023", kurz: "2023", titel: "2023: Finnland", karte: "b", neu: ["FI"] },
    { id: "s2024", kurz: "2024", titel: "2024: Schweden, 32 Mitglieder", karte: "b", neu: ["SE"] }
  ];

  const svg = document.getElementById("nm-svg");
  const legende = document.getElementById("nm-legende");
  const knoepfe = document.getElementById("nm-schritte");
  const regler = document.getElementById("nm-regler");
  const titel = document.getElementById("nm-titel");
  if (!svg || !K) return;

  svg.setAttribute("viewBox", `0 0 ${K.W} ${K.H}`);
  const meer = document.createElementNS(NS, "rect");
  meer.setAttribute("width", K.W); meer.setAttribute("height", K.H); meer.setAttribute("class", "nm-meer");
  svg.appendChild(meer);
  const gruppen = {}, flaechen = { a: {}, b: {} };
  for (const [k, units] of Object.entries(K.karten)) {
    const g = document.createElementNS(NS, "g"); g.dataset.karte = k; svg.appendChild(g); gruppen[k] = g;
    for (const [id, d] of Object.entries(units)) {
      const p = document.createElementNS(NS, "path");
      p.setAttribute("d", d); p.setAttribute("class", "nm-land m-nicht"); g.appendChild(p); flaechen[k][id] = p;
    }
  }
  const gNamen = document.createElementNS(NS, "g"); gNamen.setAttribute("class", "nm-namen"); svg.appendChild(gNamen);
  const namen = {};
  for (const [id, pos] of Object.entries(K.lab)) {
    const t = document.createElementNS(NS, "text");
    t.setAttribute("x", pos[0]); t.setAttribute("y", pos[1]); t.textContent = K.namen[id];
    gNamen.appendChild(t); namen[id] = t;
  }

  SCHRITTE.forEach((s, i) => {
    const b = document.createElement("button");
    b.type = "button"; b.textContent = s.kurz; b.dataset.i = i;
    b.addEventListener("click", () => zeige(i));
    knoepfe.appendChild(b);
  });
  regler.max = SCHRITTE.length - 1;
  regler.addEventListener("input", () => zeige(+regler.value));

  function zeige(i) {
    const s = SCHRITTE[i];
    const vorher = new Set(SCHRITTE.slice(0, i).flatMap(x => x.neu));
    regler.value = i;
    regler.setAttribute("aria-valuetext", s.titel);
    knoepfe.querySelectorAll("button").forEach(b => b.setAttribute("aria-pressed", String(+b.dataset.i === i)));
    titel.textContent = s.titel;
    for (const k of Object.keys(gruppen)) gruppen[k].style.display = k === s.karte ? "" : "none";
    for (const [id, el] of Object.entries(flaechen[s.karte])) {
      const r = s.neu.includes(id) ? "neu" : (vorher.has(id) ? "mitglied" : "nicht");
      el.setAttribute("class", "nm-land m-" + r);
    }
    for (const [id, t] of Object.entries(namen)) {
      t.style.display = (s.neu.includes(id) || vorher.has(id)) ? "" : "none";
    }
    legende.textContent = "";
    const eintraege = [["neu", s.neuText || "In diesem Schritt beigetreten"]];
    if (i > 0) eintraege.push(["mitglied", "Bereits Mitglied"]);
    eintraege.push(["nicht", "Nicht Mitglied"]);
    for (const [r, t] of eintraege) {
      const li = document.createElement("li");
      const f = document.createElement("span"); f.className = "feld m-" + r; f.setAttribute("aria-hidden", "true");
      li.appendChild(f); li.appendChild(document.createTextNode(t)); legende.appendChild(li);
    }
    document.querySelectorAll(".nm-schritt").forEach(e => { e.hidden = e.dataset.schritt !== s.id; });
  }
  zeige(0);
})();
