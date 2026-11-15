/* Koalitionsrechner: reine Rechenfunktionen (ohne DOM), im Browser als window.Koalitionen,
   in Node per require() für die Tests. Alle Zahlenwerte mit „Startwert“ sind bewusst
   gewählte Voreinstellungen und können in data.json["regeln"] angepasst werden. */
(function (wurzel) {
  'use strict';

  var STANDARD = {
    sperrklausel: 5,          // Prozent, gilt im Bund und in allen Ländern
    fenster_tage: 90,         // Startwert: Umfragen bis 90 Tage vor der neuesten zählen
    max_alter_tage: 365,      // Startwert: ist die neueste Umfrage älter, wird nicht gerechnet
    max_partner: 3,           // Startwert: Koalitionen aus höchstens drei Parteien
    knapp_bis: 52             // Startwert: Mehrheit unter 52 % der Sitze gilt als knapp
  };

  function regeln(r) {
    var o = {};
    for (var k in STANDARD) o[k] = (r && r[k] != null) ? r[k] : STANDARD[k];
    return o;
  }

  function tageZwischen(a, b) {
    return Math.round((Date.parse(b) - Date.parse(a)) / 86400000);
  }

  /* Umfragen nach der letzten Wahl, je Institut nur die neueste, und davon nur die,
     die höchstens fenster_tage vor der neuesten Umfrage liegen. */
  function auswahl(umfragen, letzteWahl, r) {
    r = regeln(r);
    var nach = (umfragen || []).filter(function (u) { return !letzteWahl || u.datum > letzteWahl; });
    nach.sort(function (a, b) { return a.datum < b.datum ? 1 : a.datum > b.datum ? -1 : 0; });
    var gesehen = {}, je = [];
    nach.forEach(function (u) { if (!gesehen[u.institut]) { gesehen[u.institut] = 1; je.push(u); } });
    if (!je.length) return [];
    var neueste = je[0].datum;
    return je.filter(function (u) { return tageZwischen(u.datum, neueste) <= r.fenster_tage; });
  }

  /* Mittelwert je Partei über die ausgewählten Umfragen. Eine Partei, die ein Institut
     nicht einzeln ausweist, zählt dort nicht mit (sie steckt dann in „Sonstige“). */
  function mittel(auswahlListe) {
    var summe = {}, n = {};
    auswahlListe.forEach(function (u) {
      for (var p in u.werte) { summe[p] = (summe[p] || 0) + u.werte[p]; n[p] = (n[p] || 0) + 1; }
    });
    var out = {};
    for (var p in summe) out[p] = Math.round(summe[p] / n[p] * 10) / 10;
    return out;
  }

  /* Wer käme ins Parlament: ab Sperrklausel, dazu ausdrücklich befreite Parteien (SSW). */
  function imParlament(werte, parl, r) {
    r = regeln(r);
    var befreit = (parl && parl.befreit) || [];
    var drin = [], drausen = [];
    Object.keys(werte).forEach(function (p) {
      if (p === 'Sonstige') return;
      if (werte[p] >= r.sperrklausel || befreit.indexOf(p) >= 0) drin.push(p); else drausen.push(p);
    });
    var sortiert = function (a, b) { return werte[b] - werte[a] || (a < b ? -1 : 1); };
    return { drin: drin.sort(sortiert), drausen: drausen.sort(sortiert) };
  }

  function sitzanteile(werte, drin) {
    var gesamt = drin.reduce(function (s, p) { return s + werte[p]; }, 0);
    var out = {};
    drin.forEach(function (p) { out[p] = gesamt ? werte[p] / gesamt * 100 : 0; });
    return out;
  }

  function teilmengen(liste, max) {
    var out = [];
    (function weiter(start, akt) {
      if (akt.length) out.push(akt.slice());
      if (akt.length === max) return;
      for (var i = start; i < liste.length; i++) { akt.push(liste[i]); weiter(i + 1, akt); akt.pop(); }
    })(0, []);
    return out;
  }

  function schluessel(parteien) { return parteien.slice().sort().join('+'); }

  /* Gab es diese Parteienkombination (genau diese, ohne weitere Partner) schon als Regierung? */
  function gabEs(parteien, historie) {
    var k = schluessel(parteien);
    return (historie || []).some(function (h) { return schluessel(h) === k; });
  }

  /* Alle Mehrheiten aus höchstens max_partner Parteien, die keinen überflüssigen Partner
     enthalten (fällt einer weg, ist die Mehrheit weg). */
  function koalitionen(werte, parl, r) {
    r = regeln(r);
    var ip = imParlament(werte, parl, r);
    var anteil = sitzanteile(werte, ip.drin);
    var summe = function (ps) { return ps.reduce(function (s, p) { return s + anteil[p]; }, 0); };
    var mehrheit = function (ps) { return summe(ps) > 50; };
    var liste = teilmengen(ip.drin, r.max_partner).filter(function (ps) {
      if (!mehrheit(ps)) return false;
      return ps.every(function (p) { return !mehrheit(ps.filter(function (q) { return q !== p; })); });
    }).map(function (ps) {
      var s = summe(ps);
      return {
        parteien: ps,
        sitzanteil: Math.round(s * 10) / 10,
        stimmen: Math.round(ps.reduce(function (t, p) { return t + werte[p]; }, 0) * 10) / 10,
        knapp: s < r.knapp_bis,
        gab_es: gabEs(ps, parl && parl.historie)
      };
    });
    liste.sort(function (a, b) { return a.parteien.length - b.parteien.length || b.sitzanteil - a.sitzanteil; });
    return { drin: ip.drin, drausen: ip.drausen, anteil: anteil, koalitionen: liste };
  }

  /* Parteien unter der Sperrklausel, die nur über die Grundmandatsklausel einziehen könnten.
     Das lässt sich aus Umfragen nicht ableiten; die Seite weist nur darauf hin (Startwert: ab 3 %). */
  function grundmandatKandidaten(werte, parl, r) {
    r = regeln(r);
    if (!parl || !parl.grundmandat) return [];
    return imParlament(werte, parl, r).drausen.filter(function (p) { return werte[p] >= 3; });
  }

  /* Gesamtauswertung eines Parlaments. heute im Format JJJJ-MM-TT. */
  function auswerten(parl, umfragen, heute, r) {
    r = regeln(r);
    var aw = auswahl(umfragen, parl.letzte_wahl, r);
    if (!aw.length) return { status: 'keine', auswahl: [] };
    var alter = tageZwischen(aw[0].datum, heute);
    if (alter > r.max_alter_tage) return { status: 'veraltet', auswahl: aw, alter: alter };
    var werte = mittel(aw);
    var k = koalitionen(werte, parl, r);
    k.status = 'ok'; k.auswahl = aw; k.werte = werte; k.alter = alter;
    k.grundmandat = grundmandatKandidaten(werte, parl, r);
    return k;
  }

  var api = { STANDARD: STANDARD, regeln: regeln, auswahl: auswahl, mittel: mittel,
    imParlament: imParlament, sitzanteile: sitzanteile, koalitionen: koalitionen,
    gabEs: gabEs, grundmandatKandidaten: grundmandatKandidaten, auswerten: auswerten,
    tageZwischen: tageZwischen };
  if (typeof module === 'object' && module.exports) module.exports = api;
  else wurzel.Koalitionen = api;
})(this);
