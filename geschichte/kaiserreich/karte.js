// Bündniskarte 1871–1907 mit Zeitregler. Grundkarte in karte-daten.js (window.KARTE), Schritte hier.
// Farben aus ../einigungskriege/einigungskriege.css (--r-*), damit beide Karten dieselbe Farblogik haben.
(function () {
  "use strict";
  const K = window.KARTE;
  const NS = "http://www.w3.org/2000/svg";
  const NAMEN = { DE: "Deutsches Reich", AH: "Österreich-Ungarn", RU: "Russland", IT: "Italien", FR: "Frankreich",
    GB: "Großbritannien", OT: "Osmanisches Reich", ES: "Spanien" };
  const KLEIN = ["ES", "OT"];

  const SCHRITTE = [
    { id: "s1871", kurz: "1871", titel: "Reichsgründung 1871",
      rollen: { DE: "pr", FR: "ge" },
      legende: { pr: "Deutsches Reich", ge: "Frankreich: Kriegsgegner von 1870/71" } },
    { id: "s1873", kurz: "1873", titel: "Dreikaiserabkommen 1873",
      rollen: { DE: "pr", AH: "db", RU: "db", FR: "ge" },
      legende: { pr: "Deutsches Reich", db: "Partner im Dreikaiserabkommen", ge: "Frankreich, diplomatisch isoliert" } },
    { id: "s1879", kurz: "1879", titel: "Zweibund 1879",
      rollen: { DE: "pr", AH: "pv", FR: "ge" },
      legende: { pr: "Deutsches Reich", pv: "Österreich-Ungarn: Beistand bei russischem Angriff", ge: "Frankreich" } },
    { id: "s1881", kurz: "1881", titel: "Dreikaiserbund 1881",
      rollen: { DE: "pr", AH: "pv", RU: "db", FR: "ge" },
      legende: { pr: "Deutsches Reich", pv: "Zweibund-Partner Österreich-Ungarn", db: "Russland: Neutralitätszusage im Dreikaiserbund", ge: "Frankreich" } },
    { id: "s1882", kurz: "1882", titel: "Dreibund 1882",
      rollen: { DE: "pr", AH: "pv", IT: "pv", RU: "db", FR: "ge" },
      legende: { pr: "Deutsches Reich", pv: "Dreibund: Österreich-Ungarn und Italien", db: "Russland: Dreikaiserbund bis 1887", ge: "Frankreich" } },
    { id: "s1887", kurz: "1887", titel: "Rückversicherungsvertrag 1887",
      rollen: { DE: "pr", AH: "pv", IT: "pv", RU: "db", FR: "ge" },
      legende: { pr: "Deutsches Reich", pv: "Dreibund-Partner", db: "Russland: geheimer Neutralitätsvertrag mit dem Reich", ge: "Frankreich" } },
    { id: "s1894", kurz: "1894", titel: "Russisch-französisches Bündnis 1894",
      rollen: { DE: "pr", AH: "pv", IT: "pv", RU: "ge", FR: "ge" },
      legende: { pr: "Deutsches Reich", pv: "Dreibund-Partner", ge: "Russland und Frankreich, durch Militärkonvention verbunden" } },
    { id: "s1904", kurz: "1904", titel: "Entente cordiale 1904",
      rollen: { DE: "pr", AH: "pv", IT: "pv", RU: "ge", FR: "ge", GB: "gv" },
      legende: { pr: "Deutsches Reich", pv: "Dreibund-Partner", ge: "Russland und Frankreich", gv: "Großbritannien: Ausgleich mit Frankreich" } },
    { id: "s1907", kurz: "1907", titel: "Tripelentente 1907",
      rollen: { DE: "pr", AH: "pv", IT: "pv", RU: "ge", FR: "ge", GB: "gv" },
      legende: { pr: "Deutsches Reich", pv: "Dreibund-Partner", ge: "Russland und Frankreich", gv: "Großbritannien: Abkommen mit Frankreich (1904) und Russland (1907)" } }
  ];

  const svg = document.getElementById("ek-svg");
  const legende = document.getElementById("ek-legende");
  const knoepfe = document.getElementById("ek-schritte");
  const regler = document.getElementById("ek-regler");
  const titel = document.getElementById("ek-titel");
  if (!svg || !K) return;

  svg.setAttribute("viewBox", `0 0 ${K.W} ${K.H}`);
  const meer = document.createElementNS(NS, "rect");
  meer.setAttribute("width", K.W); meer.setAttribute("height", K.H); meer.setAttribute("class", "ek-meer");
  svg.appendChild(meer);
  const flaechen = {};
  for (const [id, d] of Object.entries(K.units)) {
    if (!d) continue;
    const p = document.createElementNS(NS, "path");
    p.setAttribute("d", d); p.setAttribute("class", "ek-land r-neu"); p.dataset.id = id;
    svg.appendChild(p); flaechen[id] = p;
  }
  const gNamen = document.createElementNS(NS, "g"); gNamen.setAttribute("class", "ek-namen"); svg.appendChild(gNamen);
  const gOrte = document.createElementNS(NS, "g"); gOrte.setAttribute("class", "ek-orte"); svg.appendChild(gOrte);
  function text(g, x, y, t, cls) {
    const e = document.createElementNS(NS, "text");
    e.setAttribute("x", x); e.setAttribute("y", y); e.textContent = t; if (cls) e.setAttribute("class", cls);
    g.appendChild(e); return e;
  }
  for (const [id, pos] of Object.entries(K.lab)) text(gNamen, pos[0], pos[1], NAMEN[id], KLEIN.includes(id) ? "klein" : (id === "DE" ? "gross" : ""));
  for (const [o, p] of Object.entries(K.orte)) {
    const c = document.createElementNS(NS, "circle");
    c.setAttribute("cx", p[0]); c.setAttribute("cy", p[1]); c.setAttribute("r", 3.2); gOrte.appendChild(c);
    text(gOrte, p[0] + 6, p[1] + 4, o, "klein");
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
    regler.value = i;
    regler.setAttribute("aria-valuetext", s.titel);
    knoepfe.querySelectorAll("button").forEach(b => b.setAttribute("aria-pressed", String(+b.dataset.i === i)));
    titel.textContent = s.titel;
    for (const [id, el] of Object.entries(flaechen)) el.setAttribute("class", "ek-land r-" + (s.rollen[id] || "neu"));
    legende.textContent = "";
    const eintraege = Object.entries(s.legende).concat([["neu", "Nicht beteiligt"]]);
    for (const [r, t] of eintraege) {
      const li = document.createElement("li");
      const f = document.createElement("span"); f.className = "feld r-" + r; f.setAttribute("aria-hidden", "true");
      li.appendChild(f); li.appendChild(document.createTextNode(t)); legende.appendChild(li);
    }
    document.querySelectorAll(".ek-schritt").forEach(e => { e.hidden = e.dataset.schritt !== s.id; });
  }
  zeige(0);
})();
