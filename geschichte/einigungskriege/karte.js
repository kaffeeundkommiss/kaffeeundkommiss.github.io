// Karte der beteiligten Staaten 1863–1871 mit Zeitregler.
// Grundkarte in karte-daten.js (window.KARTE), Schritte und Zuordnungen hier.
(function () {
  "use strict";
  const K = window.KARTE;
  const NS = "http://www.w3.org/2000/svg";

  // Rollen: Farbe kommt aus der CSS-Variable --r-<rolle> in einigungskriege.css
  const ROLLEN = {
    pr: "Preußen",
    pv: "Verbündete Preußens",
    ge: "Kriegsgegner",
    gv: "Verbündete des Gegners",
    db: "Weitere Staaten des Deutschen Bundes",
    neu: "Nicht beteiligt"
  };

  const NAMEN = {
    DK: "Dänemark", SCHL: "Schleswig", HOL: "Holstein", PR: "Preußen", AT: "Österreich", VEN: "Venetien", IT: "Italien",
    SAX: "Sachsen", HAN: "Hannover", BAY: "Bayern", WUE: "Württ.", BAD: "Baden", KUR: "Kurhessen", HESD: "Hessen",
    OHES: "", NAS: "Nassau", KLEIN: "", ELS: "", FR: "Frankreich", CH: "Schweiz", NL: "Niederlande", BE: "Belgien",
    LU: "Lux.", GB: "", SE: "Schweden-Norwegen", RU: "Russland", OTT: "", SM: "", REST: ""
  };

  // Auf schmalen Bildschirmen ausgeblendete Beschriftungen
  const KLEIN = ["LU", "WUE", "BAD", "NAS", "KUR", "HESD", "HOL", "SCHL", "SE", "RU", "CH", "VEN", "BE"];
  const WICHTIG = ["Berlin", "Wien", "Paris", "Kopenhagen", "Königgrätz", "Sedan", "Düppel", "Versailles", "Gastein", "Langensalza", "Custozza", "Frankfurt"];
  const DEUTSCH = ["SAX", "HAN", "BAY", "WUE", "BAD", "HESD", "OHES", "KUR", "NAS", "KLEIN", "FFM"];
  function alle(rolle, ids, extra) { const o = {}; ids.forEach(i => o[i] = rolle); return Object.assign(o, extra || {}); }

  // Jeder Schritt: Rollen je Einheit (fehlende Einheit = neu), Legende mit eigenen Texten, Orte, Erläuterung (HTML aus dem Dokument)
  const SCHRITTE = [
    { id: "s1863", kurz: "1863", titel: "Ausgangslage Ende 1863",
      rollen: alle("db", DEUTSCH, { PR: "pr", AT: "pv", VEN: "pv", DK: "ge", SCHL: "ge", HOL: "gv" }),
      legende: { pr: "Preußen", pv: "Österreich (Großmacht im Deutschen Bund)", ge: "Dänemark mit Schleswig", gv: "Holstein (und Lauenburg): dänischer König als Herzog, Mitglied des Deutschen Bundes", db: "Weitere Staaten des Deutschen Bundes" },
      namen: { HOL: "Holstein" },
      orte: ["Berlin", "Wien", "Kopenhagen", "Kiel"] },
    { id: "s1864", kurz: "1864", titel: "Deutsch-Dänischer Krieg, Februar bis Oktober 1864",
      rollen: alle("db", DEUTSCH, { PR: "pr", AT: "pv", VEN: "pv", DK: "ge", SCHL: "ge", HOL: "pv" }),
      legende: { pr: "Preußen", pv: "Österreich; Holstein besetzt", ge: "Dänemark mit Schleswig", db: "Deutscher Bund, nicht kriegführend" },
      orte: ["Berlin", "Wien", "Kopenhagen", "Düppel"] },
    { id: "s1865", kurz: "1865", titel: "Gasteiner Konvention, August 1865",
      rollen: alle("db", DEUTSCH, { PR: "pr", SCHL: "pr", AT: "gv", VEN: "gv", HOL: "gv" }),
      legende: { pr: "Preußen und preußisch verwaltetes Schleswig", gv: "Österreich und österreichisch verwaltetes Holstein", db: "Weitere Staaten des Deutschen Bundes" },
      orte: ["Berlin", "Wien", "Gastein", "Kiel"] },
    { id: "s1866", kurz: "1866", titel: "Deutscher Krieg, Juni bis August 1866",
      rollen: alle("gv", ["SAX", "HAN", "BAY", "WUE", "BAD", "HESD", "OHES", "KUR", "NAS", "FFM"], { PR: "pr", SCHL: "pr", HOL: "pr", IT: "pv", KLEIN: "pv", AT: "ge", VEN: "ge" }),
      legende: { pr: "Preußen (mit Schleswig und Holstein)", pv: "Italien und norddeutsche Kleinstaaten (vereinfacht)", ge: "Österreich", gv: "Mit Österreich verbündete Staaten des Deutschen Bundes" },
      orte: ["Berlin", "Wien", "Langensalza", "Königgrätz", "Custozza", "Prag"] },
    { id: "s1867", kurz: "1867", titel: "Norddeutscher Bund und Mainlinie, 1867",
      rollen: alle("pr", ["HAN", "KUR", "NAS", "FFM", "SCHL", "HOL"], { PR: "pr", SAX: "pv", OHES: "pv", KLEIN: "pv", BAY: "db", WUE: "db", BAD: "db", HESD: "db" }),
      legende: { pr: "Preußen nach den Annexionen von 1866", pv: "Weitere Mitglieder des Norddeutschen Bundes", db: "Süddeutsche Staaten, durch Bündnisse mit Preußen verbunden" },
      namen: { HAN: "", KUR: "", NAS: "", SCHL: "", HOL: "", IT: "Italien (mit Venetien)", VEN: "" },
      orte: ["Berlin", "Wien", "München", "Stuttgart"] },
    { id: "s1870", kurz: "1870", titel: "Deutsch-Französischer Krieg, Juli 1870 bis Januar 1871",
      rollen: alle("pr", ["HAN", "KUR", "NAS", "FFM", "SCHL", "HOL"], { PR: "pr", SAX: "pv", OHES: "pv", KLEIN: "pv", BAY: "pv", WUE: "pv", BAD: "pv", HESD: "pv", FR: "ge", ELS: "ge" }),
      legende: { pr: "Preußen", pv: "Norddeutscher Bund und süddeutsche Verbündete", ge: "Frankreich" },
      namen: { HAN: "", KUR: "", NAS: "", SCHL: "", HOL: "", IT: "Italien", VEN: "" },
      orte: ["Berlin", "Paris", "Wörth", "Spichern", "Mars-la-Tour", "Metz", "Sedan", "Versailles"] },
    { id: "s1871", kurz: "1871", titel: "Deutsches Reich nach dem Frankfurter Frieden, Mai 1871",
      rollen: alle("pr", ["HAN", "KUR", "NAS", "FFM", "SCHL", "HOL"], { PR: "pr", SAX: "pv", OHES: "pv", KLEIN: "pv", BAY: "pv", WUE: "pv", BAD: "pv", HESD: "pv", ELS: "gv" }),
      legende: { pr: "Preußen im Deutschen Reich", pv: "Weitere Bundesstaaten des Deutschen Reichs", gv: "Reichsland Elsass-Lothringen (von Frankreich abgetreten)" },
      namen: { HAN: "", KUR: "", NAS: "", SCHL: "", HOL: "", ELS: "Elsass-Lothr.", IT: "Italien", VEN: "", PR: "Deutsches Reich" },
      orte: ["Berlin", "Paris", "Versailles", "Frankfurt", "Metz"] }
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
  // Freie Stadt Frankfurt: in der Grundlage nicht als Fläche enthalten, daher als Kreis
  const ff = document.createElementNS(NS, "circle");
  const [fx, fy] = K.orte["Frankfurt"];
  ff.setAttribute("cx", fx); ff.setAttribute("cy", fy); ff.setAttribute("r", 5.5); ff.setAttribute("class", "ek-land r-neu");
  svg.appendChild(ff); flaechen.FFM = ff;

  const gNamen = document.createElementNS(NS, "g"); gNamen.setAttribute("class", "ek-namen"); svg.appendChild(gNamen);
  const gOrte = document.createElementNS(NS, "g"); gOrte.setAttribute("class", "ek-orte"); svg.appendChild(gOrte);

  function text(g, x, y, t, cls) {
    const e = document.createElementNS(NS, "text");
    e.setAttribute("x", x); e.setAttribute("y", y); e.textContent = t; if (cls) e.setAttribute("class", cls);
    g.appendChild(e); return e;
  }

  // Schaltflächen
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
    for (const [id, el] of Object.entries(flaechen)) {
      el.setAttribute("class", "ek-land r-" + (s.rollen[id] || "neu"));
    }
    // Namen
    gNamen.textContent = "";
    for (const [id, pos] of Object.entries(K.lab)) {
      const n = (s.namen && id in s.namen) ? s.namen[id] : NAMEN[id];
      if (!n) continue;
      const cls = ["PR", "AT", "FR", "DK"].includes(id) ? "gross" : (KLEIN.includes(id) ? "klein" : "");
      text(gNamen, pos[0], pos[1], n, cls);
    }
    // Orte
    gOrte.textContent = "";
    for (const o of s.orte) {
      const p = K.orte[o]; if (!p) continue;
      const c = document.createElementNS(NS, "circle");
      c.setAttribute("cx", p[0]); c.setAttribute("cy", p[1]); c.setAttribute("r", 3.2);
      gOrte.appendChild(c);
      const links = ["Versailles", "Paris", "Mars-la-Tour", "Metz"].includes(o) && s.id === "s1870";
      const t = text(gOrte, p[0] + (links ? -6 : 6), p[1] + 4, o, WICHTIG.includes(o) ? "" : "klein");
      if (links) t.setAttribute("text-anchor", "end");
      if (o === "Paris" && s.id === "s1870") t.setAttribute("y", p[1] - 6);
      if (o === "Versailles") t.setAttribute("y", p[1] + 14);
      if (o === "Metz" && s.id === "s1870") t.setAttribute("y", p[1] + 16);
      if (o === "Gravelotte" || o === "Spichern") t.setAttribute("y", p[1] - 4);
    }
    // Legende
    legende.textContent = "";
    for (const [r, t] of Object.entries(s.legende)) {
      const li = document.createElement("li");
      const f = document.createElement("span"); f.className = "feld r-" + r; f.setAttribute("aria-hidden", "true");
      li.appendChild(f); li.appendChild(document.createTextNode(t)); legende.appendChild(li);
    }
    const li = document.createElement("li");
    const f = document.createElement("span"); f.className = "feld r-neu"; f.setAttribute("aria-hidden", "true");
    li.appendChild(f); li.appendChild(document.createTextNode("Nicht beteiligt")); legende.appendChild(li);
    // Erläuterung
    document.querySelectorAll(".ek-schritt").forEach(e => { e.hidden = e.dataset.schritt !== s.id; });
  }
  zeige(0);
})();
