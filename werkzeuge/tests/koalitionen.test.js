// Tests für politik/koalitionen/koalitionen.js. Aufruf: node --test werkzeuge/tests/
const test = require('node:test');
const assert = require('node:assert');
const K = require('../../politik/koalitionen/koalitionen.js');
const d = require('../../politik/koalitionen/data.json');

const U = (institut, datum, werte) => ({ institut, datum, werte });

test('nur Umfragen nach der Wahl, je Institut die neueste, im 90-Tage-Fenster', () => {
  const a = K.auswahl([
    U('A', '2026-01-01', { X: 1 }), U('A', '2026-03-01', { X: 2 }),
    U('B', '2025-09-01', { X: 3 }), U('C', '2025-05-01', { X: 4 })], '2025-06-01');
  assert.deepStrictEqual(a.map((u) => u.institut + u.datum), ['A2026-03-01']);
});

test('Sperrklausel 5 %, Sonstige zählen nie, SSW befreit', () => {
  const ip = K.imParlament({ CDU: 30, SSW: 3, FDP: 4.9, Sonstige: 10, SPD: 5 }, { befreit: ['SSW'] });
  assert.deepStrictEqual(ip.drin, ['CDU', 'SPD', 'SSW']);
  assert.deepStrictEqual(ip.drausen, ['FDP']);
});

test('Mehrheit über 50 % der Sitze, ohne überflüssigen Partner', () => {
  const r = K.koalitionen({ A: 40, B: 30, C: 20, D: 10 }, { historie: [['B', 'A']] });
  const k = r.koalitionen.map((x) => x.parteien.join('+'));
  assert.ok(k.includes('A+B'));
  assert.ok(k.includes('A+C'));
  assert.ok(!k.includes('A+B+C'), 'A+B+C hat einen überflüssigen Partner');
  assert.ok(!k.includes('A+D'), 'genau 50 % ist keine Mehrheit');
  assert.strictEqual(r.koalitionen.find((x) => x.parteien.join('+') === 'A+B').gab_es, true);
  assert.strictEqual(r.koalitionen.find((x) => x.parteien.join('+') === 'A+C').gab_es, false);
});

test('Allein-Mehrheit wird als eine Partei geführt', () => {
  const r = K.koalitionen({ A: 55, B: 30, C: 15 }, {});
  assert.deepStrictEqual(r.koalitionen.map((x) => x.parteien.join('+')), ['A']);
});

test('Historie: nur exakt gleiche Kombination zählt', () => {
  assert.strictEqual(K.gabEs(['SPD', 'CDU'], [['CDU', 'SPD', 'FDP']]), false);
  assert.strictEqual(K.gabEs(['SPD', 'CDU'], [['CDU', 'SPD']]), true);
});

test('Grundmandat-Hinweis nur wo vorgesehen und ab 3 %', () => {
  const w = { A: 50, B: 45, C: 4, D: 2 };
  assert.deepStrictEqual(K.grundmandatKandidaten(w, { grundmandat: 'drei Wahlkreise' }), ['C']);
  assert.deepStrictEqual(K.grundmandatKandidaten(w, {}), []);
});

test('veraltete und fehlende Umfragen', () => {
  assert.strictEqual(K.auswerten({ letzte_wahl: '2026-01-01' }, [], '2026-11-15').status, 'keine');
  assert.strictEqual(K.auswerten({ letzte_wahl: '2020-01-01' }, [U('A', '2024-01-01', { X: 60 })], '2026-11-15').status, 'veraltet');
});

test('data.json: jedes Parlament vollständig, Parteikürzel der Historie passen zu dawum', () => {
  const bekannt = new Set(['CDU/CSU', 'CDU', 'CSU', 'SPD', 'Grüne', 'FDP', 'Linke', 'AfD', 'BSW', 'Freie Wähler', 'SSW', 'Thüringen.Gerecht']);
  assert.strictEqual(d.parlamente.length, 17);
  for (const p of d.parlamente) {
    for (const f of ['id', 'name', 'dawum', 'wahltermin', 'sortierung', 'letzte_wahl', 'historie', 'historie_quelle']) assert.ok(p[f], p.id + ' ohne ' + f);
    for (const g of p.historie) for (const x of g) assert.ok(bekannt.has(x), p.id + ': unbekannte Partei ' + x);
    for (const u of p.umfragen) assert.ok(u.datum > p.letzte_wahl, p.id + ': Umfrage vor der letzten Wahl');
  }
});
