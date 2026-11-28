/* 3D-Modell des Großen Kreuzers (Schlachtkreuzers) SMS Lützow für die Seite „Technik im Modell“ (27.11.2026).
   Geometrie übernommen aus dem claude.ai-Entwurf „SMS Lützow 3D“ (27.11.2026),
   Steuerung, Farben und Laden nach dem Muster des Mark-II-Modells (modell/mk2.js).
   Maßstab: 1 Einheit = 1 m. Rumpfform, Aufbauten, Masten, Boote und 8,8-cm-Geschütze sind angenähert,
   die Lage der Torpedorohre ist schematisch.
   Benötigt modell/vendor/three-0.159.0.min.js (MIT-Lizenz, siehe three-LICENSE.txt). */
(function () {
  "use strict";
  const root = document.getElementById("luetzow");
  if (!root) return;
  const cv = root.querySelector("canvas");
  const msg = root.querySelector(".lz-msg");
  const labels = ["a", "b", "c", "d"].map((k) => root.querySelector('[data-label="' + k + '"]'));
  const reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const state = { spin: !reduce, water: true, broad: false, labels: true };
  const VIEWS = {
    drei: { theta: 0.75, phi: 1.2, dist: 216 },
    seite: { theta: 0.0, phi: 1.52, dist: 198 },
    vorne: { theta: Math.PI / 2, phi: 1.4, dist: 122 },
    oben: { theta: 0.0, phi: 0.05, dist: 209 },
    heck: { theta: -2.3, phi: 1.2, dist: 194 },
    unten: { theta: 0.5, phi: 1.75, dist: 198 }
  };
  const c = { theta: 0.75, phi: 1.2, dist: 216, tTheta: 0.75, tPhi: 1.2, tDist: 216 };
  const ANSTRICH = "#8A9097";
  function fail(text) { if (msg) { msg.textContent = text; msg.hidden = false; } }
  const T = window.THREE;
  if (!T) { fail("Das 3D-Modell konnte nicht geladen werden."); return; }
  let renderer;
  try { renderer = new T.WebGLRenderer({ canvas: cv, antialias: true }); }
  catch (e) { fail("WebGL ist in diesem Browser nicht verfügbar."); return; }
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = T.PCFSoftShadowMap;
  renderer.toneMapping = T.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;

  const scene = new T.Scene();
  scene.background = new T.Color(0x15181c);
  scene.fog = new T.Fog(0x15181c, 520, 1200);
  const cam = new T.PerspectiveCamera(32, 1, 1, 3000);

  const hemi = new T.HemisphereLight(0xdfe8f5, 0x2e3238, 1.0);
  scene.add(hemi);
  const key = new T.DirectionalLight(0xfff1dc, 2.4);
  key.position.set(120, 220, 160);
  key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048);
  const sc = key.shadow.camera;
  sc.left = -130; sc.right = 130; sc.top = 130; sc.bottom = -130; sc.near = 10; sc.far = 600;
  key.shadow.bias = -0.0004;
  key.shadow.normalBias = 0.3;
  scene.add(key);
  const fill = new T.DirectionalLight(0x9fb4d0, 0.55);
  fill.position.set(-200, 80, -150);
  scene.add(fill);

  /* Wasserfläche mit Ring als Maßstabshilfe (Radius 150 m) */
  const waterMat = new T.MeshStandardMaterial({ color: 0x1c3243, roughness: 0.35, metalness: 0.1, transparent: true, opacity: 0.9 });
  const water = new T.Mesh(new T.CircleGeometry(700, 96), waterMat);
  water.rotation.x = -Math.PI / 2;
  water.receiveShadow = true;
  scene.add(water);
  const ringMat = new T.MeshBasicMaterial({ color: 0x35506a });
  const wl = new T.Mesh(new T.RingGeometry(150, 150.6, 160), ringMat);
  wl.rotation.x = -Math.PI / 2; wl.position.y = 0.05;
  scene.add(wl);

  const std = (c, r, m, extra) => new T.MeshStandardMaterial(Object.assign({ color: c, roughness: r, metalness: m || 0 }, extra || {}));
  const mats = {
    grey: std(ANSTRICH, 0.7, 0.2),
    dark: std(0x2a2d31, 0.6, 0.4),
    black: std(0x161718, 0.7, 0.2),
    deck: std(0xa08967, 0.85, 0),
    gun: std(0x50555b, 0.45, 0.6),
    boat: std(0xd9d6cf, 0.7, 0),
    torp: new T.MeshBasicMaterial({ color: 0xffb14a })
  };

  const add = (parent, geo, mat) => {
    const m = new T.Mesh(geo, mat);
    m.castShadow = true; m.receiveShadow = true;
    parent.add(m);
    return m;
  };
  const rod = (parent, a, b, r, mat) => {
    const A = new T.Vector3(a[0], a[1], a[2]);
    const B = new T.Vector3(b[0], b[1], b[2]);
    const d = B.clone().sub(A);
    const m = add(parent, new T.CylinderGeometry(r, r, d.length(), 8), mat);
    m.position.copy(A).add(B).multiplyScalar(0.5);
    m.quaternion.setFromUnitVectors(new T.Vector3(0, 1, 0), d.normalize());
    return m;
  };
  const box = (parent, sx, sy, sz, x, y, z, mat) => {
    const m = add(parent, new T.BoxGeometry(sx, sy, sz), mat || mats.grey);
    m.position.set(x, y, z);
    return m;
  };

  const ship = new T.Group();
  scene.add(ship);

  // Rumpf: Spantenmodell (x: Bug +, y: Wasserlinie 0), 210,4 m über alles, 29,0 m breit, 9,56 m Tiefgang
  const XF = 105.2, XA = -105.2;
  const halfB = (x) => {
    let b = 14.5;
    if (x > 10) { const t = Math.min(1, (x - 10) / (XF - 10)); b = 14.5 * Math.pow(Math.max(0, 1 - t * t), 0.75); }
    if (x < -35) { const t = Math.min(1, (-35 - x) / (-35 - XA)); b = 14.5 * Math.pow(Math.max(0, 1 - Math.pow(t, 2.4)), 0.55); }
    return Math.max(b, 0.3);
  };
  const deckY = (x) => {
    if (x > 10) return 7.0 + 2.8 * Math.pow((x - 10) / (XF - 10), 2);
    if (x < -50) return 7.0 - 0.8 * ((-50 - x) / (-50 - XA));
    return 7.0;
  };
  const keelY = (x) => {
    let k = -9.4;
    if (x > 88) k += 5.6 * Math.pow((x - 88) / (XF - 88), 2);
    if (x < -80) k += 6.6 * Math.pow((-80 - x) / (-80 - XA), 1.5);
    return k;
  };
  const NS = 141;
  const ring = (x) => {
    const b = halfB(x), d = deckY(x), k = keelY(x);
    const p3 = Math.min(k + 4, -1.0);
    const p2 = Math.max(k + 0.6, Math.min(k + 1.8, p3 - 0.5));
    const half = [[b, d], [b, 0.3], [b, -0.3], [b, p3], [0.97 * b, p2], [0.55 * b, k]];
    const pts = [];
    half.forEach((p) => pts.push([-p[0], p[1]]));
    pts.push([0, k]);
    for (let i = half.length - 1; i >= 0; i--) pts.push([half[i][0], half[i][1]]);
    return pts;
  };
  const pos = [], col = [], idx = [];
  const RP = 13;
  const xsAll = [];
  for (let s = 0; s < NS; s++) xsAll.push(XA + (XF - XA) * s / (NS - 1));
  xsAll.forEach((x) => {
    ring(x).forEach((p) => { pos.push(x, p[1], p[0]); col.push(0, 0, 0); });
  });
  for (let s = 0; s < NS - 1; s++) {
    for (let i = 0; i < RP - 1; i++) {
      const a = s * RP + i, b = a + 1, c = a + RP, d = c + 1;
      idx.push(a, c, b, b, c, d);
    }
  }
  // Endkappen
  [0, NS - 1].forEach((s) => {
    const x = xsAll[s];
    const ci = pos.length / 3;
    pos.push(x, (deckY(x) + keelY(x)) / 2, 0); col.push(0, 0, 0);
    for (let i = 0; i < RP - 1; i++) idx.push(ci, s * RP + i, s * RP + i + 1);
    idx.push(ci, s * RP + RP - 1, s * RP);
  });
  const hullG = new T.BufferGeometry();
  hullG.setAttribute('position', new T.Float32BufferAttribute(pos, 3));
  hullG.setAttribute('color', new T.Float32BufferAttribute(col, 3));
  hullG.setIndex(idx);
  hullG.computeVertexNormals();
  const hullMat = new T.MeshStandardMaterial({ vertexColors: true, roughness: 0.65, metalness: 0.15, side: T.DoubleSide });
  const hullMesh = add(ship, hullG, hullMat);
  const red = new T.Color(0x7a2a22), boot = new T.Color(0x1b1c1e);
  const paintHull = (hex) => {
    const gc = new T.Color(hex);
    const P = hullG.attributes.position, C = hullG.attributes.color;
    for (let i = 0; i < P.count; i++) {
      const y = P.getY(i);
      const c = y < -0.29 ? red : (y < 0.31 ? boot : gc);
      C.setXYZ(i, c.r, c.g, c.b);
    }
    C.needsUpdate = true;
  };
  paintHull(ANSTRICH);

  // Oberdeck (Glattdeck)
  {
    const dp = [], di = [];
    xsAll.forEach((x) => { const b = halfB(x) - 0.05, d = deckY(x) + 0.02; dp.push(x, d, -b, x, d, b); });
    for (let s = 0; s < NS - 1; s++) { const a = s * 2; di.push(a, a + 2, a + 1, a + 1, a + 2, a + 3); }
    const g = new T.BufferGeometry();
    g.setAttribute('position', new T.Float32BufferAttribute(dp, 3));
    g.setIndex(di);
    g.computeVertexNormals();
    const m = new T.Mesh(g, new T.MeshStandardMaterial({ color: 0xa08967, roughness: 0.85, side: T.DoubleSide }));
    m.receiveShadow = true;
    ship.add(m);
  }

  // Türme A–D, je 2 × 30,5 cm
  const turrets = [];
  const makeTurret = (x, raise, aft) => {
    const g0 = new T.Group();
    const y0 = deckY(x) + raise;
    if (raise > 0) {
      const bb = add(ship, new T.CylinderGeometry(5.2, 5.4, raise + 0.2, 32), mats.grey);
      bb.position.set(x, deckY(x) + (raise + 0.2) / 2, 0);
    }
    g0.position.set(x, y0, 0);
    ship.add(g0);
    const t = new T.Group();
    g0.add(t);
    const sh = new T.Shape();
    sh.moveTo(-5.6, 0); sh.lineTo(4.4, 0); sh.lineTo(5.6, 1.5); sh.lineTo(4.9, 3.2); sh.lineTo(-5.6, 3.2); sh.closePath();
    const tg = new T.ExtrudeGeometry(sh, { depth: 9.6, bevelEnabled: true, bevelThickness: 0.25, bevelSize: 0.25, bevelSegments: 2 });
    tg.translate(0, 0, -4.8);
    add(t, tg, mats.grey);
    const rf = add(t, new T.CylinderGeometry(0.4, 0.4, 10.5, 12), mats.dark);
    rf.rotation.x = Math.PI / 2;
    rf.position.set(-3.2, 3.75, 0);
    const guns = new T.Group();
    guns.position.set(4.5, 1.6, 0);
    t.add(guns);
    [1.75, -1.75].forEach((z) => {
      const b = add(guns, new T.CylinderGeometry(0.3, 0.45, 15.25, 16), mats.gun);
      b.rotation.z = -Math.PI / 2;
      b.position.set(7.6, 0, z);
    });
    const base = aft ? Math.PI : 0;
    t.rotation.y = base;
    const anchor = new T.Object3D();
    anchor.position.set(0, 7.5, 0);
    g0.add(anchor);
    turrets.push({ t, guns, base, aft, anchor });
  };
  makeTurret(76, 0, false);
  makeTurret(61, 3.6, false);
  makeTurret(-52, 3.6, true);
  makeTurret(-67, 0, true);

  // Mittelartillerie: 7 Kasematten je Seite, 15 cm
  [38, 27, 16, 5, -6, -17, -28].forEach((x) => {
    [1, -1].forEach((s) => {
      const b = halfB(x);
      const y = deckY(x) - 2.6;
      const sh = add(ship, new T.CylinderGeometry(1.1, 1.1, 0.6, 16), mats.grey);
      sh.rotation.x = Math.PI / 2;
      sh.position.set(x, y, s * (b + 0.15));
      const brl = add(ship, new T.CylinderGeometry(0.16, 0.2, 5.5, 10), mats.gun);
      brl.rotation.x = Math.PI / 2;
      brl.position.set(x + 0.4, y, s * (b + 2.9));
    });
  });

  // Vorderer Aufbau mit Kommandoturm und Brücke
  {
    const x0 = 43, d = deckY(x0);
    box(ship, 14, 3, 12, x0, d + 1.5, 0);
    const ct = add(ship, new T.CylinderGeometry(3.0, 3.0, 3.4, 28), mats.grey);
    ct.position.set(x0 + 3.5, d + 4.7, 0);
    const ctr = add(ship, new T.CylinderGeometry(3.1, 3.1, 0.3, 28), mats.dark);
    ctr.position.set(x0 + 3.5, d + 6.5, 0);
    box(ship, 6, 0.4, 19, x0 - 1, d + 7.2, 0, mats.dark);
    box(ship, 5, 2.2, 8, x0 - 1.5, d + 8.5, 0);
    box(ship, 4, 0.3, 12, x0 - 1.5, d + 9.8, 0, mats.dark);
  }
  // Mittschiffsaufbau, Bootsdeck
  box(ship, 42, 2.6, 16, 6, 7.0 + 1.3, 0);
  // Achterer Aufbau mit achterem Kommandoturm
  {
    const x0 = -33, d = deckY(x0);
    box(ship, 16, 3, 12, x0, d + 1.5, 0);
    const ct = add(ship, new T.CylinderGeometry(2.3, 2.3, 2.6, 24), mats.grey);
    ct.position.set(x0 - 4, d + 4.3, 0);
    box(ship, 5, 0.3, 14, x0 + 2, d + 5.6, 0, mats.dark);
  }

  // Schornsteine
  const funnelTops = [];
  [20, 3].forEach((x) => {
    const h = 15;
    const f = add(ship, new T.CylinderGeometry(3.1, 3.3, h, 28), mats.grey);
    f.scale.set(1.35, 1, 0.82);
    f.position.set(x, 9.6 + h / 2, 0);
    const cap = add(ship, new T.CylinderGeometry(3.15, 3.15, 1.6, 28), mats.black);
    cap.scale.set(1.35, 1, 0.82);
    cap.position.set(x, 9.6 + h - 0.6, 0);
    const pf = add(ship, new T.CylinderGeometry(5.2, 5.2, 0.3, 24), mats.dark);
    pf.scale.set(1.2, 1, 1);
    pf.position.set(x, 9.6 + 6, 0);
    funnelTops.push([x, 9.6 + h]);
    [1, -1].forEach((s) => {
      const sl = add(ship, new T.CylinderGeometry(0.75, 0.75, 1.1, 16), mats.dark);
      sl.rotation.z = Math.PI / 2;
      sl.position.set(x, 9.6 + 6.8, s * 4.2);
    });
  });

  // Masten (Pfahlmasten mit Beobachtungsstand, angenähert)
  const foreX = 38, mainX = -40;
  const foreTop = 7.0 + 3 + 38, mainTop = 6.8 + 3 + 30;
  {
    const m = add(ship, new T.CylinderGeometry(0.35, 0.6, 38, 12), mats.grey);
    m.position.set(foreX, deckY(foreX) + 3 + 19, 0);
    box(ship, 3.4, 2.6, 3.4, foreX, deckY(foreX) + 3 + 26, 0);
    rod(ship, [foreX, deckY(foreX) + 34, -7], [foreX, deckY(foreX) + 34, 7], 0.15, mats.dark);
    const m2 = add(ship, new T.CylinderGeometry(0.3, 0.5, 30, 12), mats.grey);
    m2.position.set(mainX, deckY(mainX) + 3 + 15, 0);
    box(ship, 2.6, 2, 2.6, mainX, deckY(mainX) + 3 + 20, 0);
    rod(ship, [mainX, deckY(mainX) + 27, -5.5], [mainX, deckY(mainX) + 27, 5.5], 0.13, mats.dark);
    const ant = new T.BufferGeometry().setFromPoints([new T.Vector3(foreX, deckY(foreX) + 40, 0), new T.Vector3(mainX, deckY(mainX) + 32.5, 0)]);
    ship.add(new T.Line(ant, new T.LineBasicMaterial({ color: 0x3a4048 })));
  }

  // Boote und Bootskräne auf dem Mittschiffsaufbau
  [[-6, 5], [-6, -5], [9, 5.4], [9, -5.4], [-12, 3], [-12, -3]].forEach((p) => {
    const b = add(ship, new T.SphereGeometry(1, 16, 10), mats.boat);
    b.scale.set(4.2, 0.9, 1.2);
    b.position.set(p[0], 7.0 + 2.6 + 0.8, p[1]);
  });
  [1, -1].forEach((s) => {
    rod(ship, [-1, 9.6, s * 6.8], [-1, 19, s * 6.8], 0.45, mats.grey);
    rod(ship, [-1, 18.5, s * 6.8], [-11, 15.5, s * 7.5], 0.3, mats.grey);
  });

  // 8,8-cm-Geschütze auf den Aufbauten (Anzahl und Lage angenähert; die Quellen nennen unterschiedliche Zahlen)
  [[30, 5.2], [30, -5.2], [24, 6.5], [24, -6.5], [-12, 7], [-12, -7], [-27, 5.2], [-27, -5.2]].forEach((p) => {
    const x = p[0];
    const top = (x > 15) ? 9.6 : (x < -24 ? deckY(x) + 3 : 9.6);
    const mnt = add(ship, new T.CylinderGeometry(0.55, 0.7, 1.0, 12), mats.dark);
    mnt.position.set(x, top + 0.5, p[1]);
    const br = add(ship, new T.CylinderGeometry(0.08, 0.1, 4.0, 8), mats.gun);
    br.rotation.z = -Math.PI / 2 - 0.35;
    br.position.set(x + 1.8, top + 1.4, p[1]);
  });

  // Anker
  [1, -1].forEach((s) => {
    const a = add(ship, new T.BoxGeometry(1.6, 1.8, 0.4), mats.black);
    a.position.set(95, 6.2, s * (halfB(95) + 0.1));
  });

  // Torpedorohre 60 cm (Lage schematisch): Bug, Heck, je eins pro Seite
  const torps = new T.Group();
  ship.add(torps);
  [[XF - 0.6, -4.2, 0], [XA + 1.2, -3.6, 0], [58, -5.5, halfB(58) + 0.2], [58, -5.5, -halfB(58) - 0.2]].forEach((p) => {
    const m = new T.Mesh(new T.SphereGeometry(0.9, 16, 12), mats.torp);
    m.position.set(p[0], p[1], p[2]);
    torps.add(m);
  });

  // Schrauben und Ruder
  [[-84, 4.2], [-84, -4.2], [-74, 8.5], [-74, -8.5]].forEach((p) => {
    const pr = new T.Group();
    pr.position.set(p[0], -6.6, p[1]);
    ship.add(pr);
    const hub = add(pr, new T.SphereGeometry(0.5, 12, 8), mats.dark);
    hub.scale.set(1.6, 1, 1);
    for (let k = 0; k < 3; k++) {
      const bl = add(pr, new T.BoxGeometry(0.15, 1.9, 0.9), mats.dark);
      bl.rotation.x = k * Math.PI * 2 / 3;
      bl.position.set(0, Math.cos(k * Math.PI * 2 / 3) * 0.95, Math.sin(k * Math.PI * 2 / 3) * 0.95);
    }
    rod(ship, [p[0] + 0.5, -6.6, p[1]], [p[0] + 14, -6.8, p[1] * 0.7], 0.25, mats.dark);
  });
  box(ship, 4.5, 5.5, 0.5, -96, -5.0, 0, mats.dark);

  const target = new T.Vector3(0, 6, 0);

  /* Farben aus dem Seitenschema (hell/dunkel) übernehmen */
  function applyTheme() {
    const cs = getComputedStyle(root);
    const bg = (cs.getPropertyValue("--lz-bg") || "#15181c").trim();
    const wa = (cs.getPropertyValue("--lz-water") || "#1c3243").trim();
    const rl = (cs.getPropertyValue("--lz-ring") || "#35506a").trim();
    const dark = (cs.getPropertyValue("--lz-dark") || "1").trim() === "1";
    scene.background.set(bg);
    scene.fog.color.set(bg);
    waterMat.color.set(wa);
    ringMat.color.set(rl);
    hemi.intensity = dark ? 1.0 : 1.2;
    waterMat.roughness = 0.8;
    renderer.toneMappingExposure = dark ? 1.05 : 0.95;
    dirty = true;
  }
  let dirty = true;
  applyTheme();
  new MutationObserver(applyTheme).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme", "class"] });
  if (window.matchMedia) {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    (mq.addEventListener ? mq.addEventListener("change", applyTheme) : mq.addListener(applyTheme));
  }

  /* Größe an den Kasten anpassen */
  let W = 1, H = 1;
  function resize() {
    const w = cv.clientWidth, h = cv.clientHeight;
    if (!w || !h) return;
    W = w; H = h;
    renderer.setSize(w, h, false);
    cam.aspect = w / h;
    cam.updateProjectionMatrix();
    dirty = true;
  }
  resize();
  if (window.ResizeObserver) new ResizeObserver(resize).observe(cv); else window.addEventListener("resize", resize);

  /* Steuerung: Ziehen dreht, Strg/⌘ + Mausrad oder Schaltflächen zoomen; die Seite scrollt normal weiter */
  let drag = null;
  cv.addEventListener("pointerdown", (e) => {
    drag = { x: e.clientX, y: e.clientY };
    try { cv.setPointerCapture(e.pointerId); } catch (x) {}
    cv.classList.add("grab");
  });
  cv.addEventListener("pointermove", (e) => {
    if (!drag) return;
    const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
    drag = { x: e.clientX, y: e.clientY };
    c.tTheta -= dx * 0.008; c.theta -= dx * 0.008;
    c.tPhi = Math.min(2.6, Math.max(0.05, c.tPhi - dy * 0.006));
    c.phi = c.tPhi;
    dirty = true;
  });
  const up = (e) => { drag = null; try { cv.releasePointerCapture(e.pointerId); } catch (x) {} cv.classList.remove("grab"); };
  cv.addEventListener("pointerup", up);
  cv.addEventListener("pointercancel", up);
  cv.addEventListener("wheel", (e) => {
    if (!e.ctrlKey && !e.metaKey) return;
    e.preventDefault();
    zoom(1 + e.deltaY * 0.0012);
  }, { passive: false });
  function zoom(f) { c.tDist = Math.min(700, Math.max(60, c.tDist * f)); dirty = true; }

  function setPressed(btn, on) { btn.setAttribute("aria-pressed", on ? "true" : "false"); }
  function syncToggles() {
    root.querySelectorAll("[data-toggle]").forEach((b) => setPressed(b, state[b.dataset.toggle]));
  }
  root.querySelectorAll("[data-view]").forEach((btn) => btn.addEventListener("click", () => {
    const v = VIEWS[btn.dataset.view];
    let t = v.theta;
    while (t - c.theta > Math.PI) t -= Math.PI * 2;
    while (c.theta - t > Math.PI) t += Math.PI * 2;
    c.tTheta = t; c.tPhi = v.phi; c.tDist = v.dist;
    state.spin = false;
    if (btn.dataset.view === "unten") state.water = false;
    root.querySelectorAll("[data-view]").forEach((b) => setPressed(b, b === btn));
    syncToggles();
    dirty = true;
  }));
  root.querySelectorAll("[data-zoom]").forEach((btn) => btn.addEventListener("click", () => zoom(btn.dataset.zoom === "in" ? 0.85 : 1.18)));
  root.querySelectorAll("[data-toggle]").forEach((btn) => btn.addEventListener("click", () => {
    state[btn.dataset.toggle] = !state[btn.dataset.toggle];
    if (btn.dataset.toggle === "spin" && state.spin) root.querySelectorAll("[data-view]").forEach((b) => setPressed(b, false));
    syncToggles();
    dirty = true;
  }));
  syncToggles();

  /* Nur zeichnen, wenn das Modell sichtbar ist */
  let visible = true;
  if (window.IntersectionObserver) new IntersectionObserver((en) => { visible = en[0].isIntersecting; if (visible) dirty = true; }).observe(cv);
  document.addEventListener("visibilitychange", () => { if (!document.hidden) dirty = true; });

  const tmp = new T.Vector3();
  let broadK = 0, labK = state.labels ? 1 : 0;
  function loop() {
    requestAnimationFrame(loop);
    if (!visible || document.hidden) return;
    const bT = state.broad ? 1 : 0, lT = state.labels ? 1 : 0;
    const moving = state.spin || drag || Math.abs(bT - broadK) > 1e-3 || Math.abs(lT - labK) > 1e-3 ||
      Math.abs(c.tTheta - c.theta) > 1e-4 || Math.abs(c.tPhi - c.phi) > 1e-4 || Math.abs(c.tDist - c.dist) > 1e-3;
    if (!moving && !dirty) return;
    dirty = false;
    if (state.spin && !drag) { c.tTheta += 0.0025; c.theta += 0.0025; }
    c.theta += (c.tTheta - c.theta) * 0.08;
    c.phi += (c.tPhi - c.phi) * 0.08;
    c.dist += (c.tDist - c.dist) * 0.1;
    const sp = Math.sin(c.phi);
    /* schmale Kästen: Abstand vergrößern, damit das Schiff nicht abgeschnitten wird */
    const d = c.dist * Math.max(1, 1.45 / cam.aspect);
    cam.position.set(target.x + d * sp * Math.sin(c.theta), target.y + d * Math.cos(c.phi), target.z + d * sp * Math.cos(c.theta));
    cam.lookAt(target);

    const showWater = state.water && cam.position.y > 0.5;
    water.visible = showWater;
    wl.visible = showWater;
    torps.visible = !state.water;

    /* Breitseite: Türme schwenken nach Steuerbord */
    broadK += (bT - broadK) * (reduce ? 1 : 0.04);
    turrets.forEach((tt) => {
      tt.t.rotation.y = tt.base + (tt.aft ? 1 : -1) * (Math.PI / 2) * broadK;
      tt.guns.rotation.z = 0.12 * broadK;
    });

    /* Turmbezeichnungen A bis D */
    labK += (lT - labK) * (reduce ? 1 : 0.12);
    turrets.forEach((tt, i) => {
      const el = labels[i];
      if (!el) return;
      tt.anchor.getWorldPosition(tmp);
      tmp.project(cam);
      const x = (tmp.x * 0.5 + 0.5) * W, y = (-tmp.y * 0.5 + 0.5) * H;
      el.style.transform = "translate(" + x.toFixed(1) + "px," + y.toFixed(1) + "px) translate(-50%, -100%)";
      el.style.opacity = (tmp.z < 1 ? labK : 0).toFixed(2);
    });

    renderer.render(scene, cam);
  }
  loop();
  root.classList.add("ready");
})();
