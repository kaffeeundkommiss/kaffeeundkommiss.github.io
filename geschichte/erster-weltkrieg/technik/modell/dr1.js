/* 3D-Modell Fokker Dr.I für die Seite „Technik im Modell“ (bis 21.11.2026 im Repo erster-Weltkrieg).
   Geometrie übernommen aus dem claude.ai-Entwurf „Fokker Dr.I 3D“ (17.11.2026), an Seitenfarben hell/dunkel angepasst.
   Benötigt modell/vendor/three-0.159.0.min.js (MIT-Lizenz, siehe three-LICENSE.txt). */
(function () {
  "use strict";
  const box = document.getElementById("dr1");
  if (!box) return;
  const cv = box.querySelector("canvas");
  const msg = box.querySelector(".dr1-msg");
  const reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const state = { spin: !reduce, prop: !reduce };
  const VIEWS = {
    drei: { theta: 0.9, phi: 1.22, dist: 11.5 },
    seite: { theta: 0.0, phi: 1.53, dist: 11 },
    vorne: { theta: Math.PI / 2, phi: 1.45, dist: 11 },
    oben: { theta: 0.0, phi: 0.06, dist: 12 },
    heck: { theta: -2.3, phi: 1.2, dist: 11.5 },
    unten: { theta: 0.6, phi: 2.2, dist: 11.5 }
  };
  const c = { theta: 0.9, phi: 1.22, dist: 11.5, tTheta: 0.9, tPhi: 1.22, tDist: 11.5 };
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
  scene.background = new T.Color(0x181d1a);
  scene.fog = new T.Fog(0x181d1a, 16, 34);
  const cam = new T.PerspectiveCamera(32, 1, 0.1, 100);

  const hemi = new T.HemisphereLight(0xdfe8f5, 0x3a2f28, 0.9);
  scene.add(hemi);
  const key = new T.DirectionalLight(0xfff1dc, 2.4);
  key.position.set(5, 10, 6);
  key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048);
  const sc = key.shadow.camera;
  sc.left = -6; sc.right = 6; sc.top = 6; sc.bottom = -6; sc.near = 1; sc.far = 30;
  key.shadow.bias = -0.0005;
  key.shadow.normalBias = 0.02;
  scene.add(key);
  const fill = new T.DirectionalLight(0x9fb4d0, 0.55);
  fill.position.set(-6, 3, -4);
  scene.add(fill);

  const groundMat = new T.MeshStandardMaterial({ color: 0x22272d, roughness: 1 });
  const ground = new T.Mesh(new T.CircleGeometry(10, 72), groundMat);
  ground.rotation.x = -Math.PI / 2;
  ground.receiveShadow = true;
  scene.add(ground);
  const ringMat = new T.MeshBasicMaterial({ color: 0x353b43 });
  const ring = new T.Mesh(new T.RingGeometry(4.9, 4.93, 96), ringMat);
  ring.rotation.x = -Math.PI / 2; ring.position.y = 0.002;
  scene.add(ring);

    const std = (c, r, m, extra) => new T.MeshStandardMaterial(Object.assign({ color: c, roughness: r, metalness: m || 0 }, extra || {}));
    const mats = {
      red: std('#B0201A', 0.6, 0, { side: T.DoubleSide }),
      black: std(0x1b1c1e, 0.45, 0.6),
      metal: std(0x8d8b86, 0.35, 0.8),
      wood: std(0x7a4a25, 0.45, 0),
      tire: std(0x1f1f1f, 0.9, 0),
      white: std(0xe9e6df, 0.6, 0, { side: T.DoubleSide }),
      dark: std(0x0c0c0d, 0.9, 0, { side: T.DoubleSide })
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
      const m = add(parent, new T.CylinderGeometry(r, r, d.length(), 10), mat);
      m.position.copy(A).add(B).multiplyScalar(0.5);
      m.quaternion.setFromUnitVectors(new T.Vector3(0, 1, 0), d.normalize());
      return m;
    };

    const plane = new T.Group();

    // Rumpf
    const S = [
      // nach Seiten- und Draufsicht "Flight" 1918 (x: vorn +, y: über Schublinie 0,5)
      [1.48, 0.34, 0.15, 0.88], [1.15, 0.31, 0.17, 0.94], [0.2, 0.3, 0.13, 0.98],
      [-0.8, 0.28, 0.15, 1.03], [-1.9, 0.18, 0.31, 0.93], [-2.86, 0.05, 0.46, 0.83],
      [-2.93, 0.02, 0.48, 0.82]
    ];
    const corners = (s) => [[s[0], s[2], -s[1]], [s[0], s[2], s[1]], [s[0], s[3], s[1]], [s[0], s[3], -s[1]]];
    const pos = [];
    const quad = (a, b, c, d) => { pos.push(...a, ...b, ...c, ...a, ...c, ...d); };
    for (let i = 0; i < S.length - 1; i++) {
      const p = corners(S[i]), q = corners(S[i + 1]);
      for (let k = 0; k < 4; k++) { const n = (k + 1) % 4; quad(p[k], q[k], q[n], p[n]); }
    }
    const f0 = corners(S[0]), f1 = corners(S[S.length - 1]);
    quad(f0[0], f0[1], f0[2], f0[3]);
    quad(f1[0], f1[1], f1[2], f1[3]);
    const fg = new T.BufferGeometry();
    fg.setAttribute('position', new T.Float32BufferAttribute(pos, 3));
    fg.computeVertexNormals();
    add(plane, fg, mats.red);

    // Tragflächen
    const makeWing = (span, chord, thick, LEx, y) => {
      const th = thick / chord, m = 0.035 * chord;
      const yt = (t) => 5 * th * chord * (0.2969 * Math.sqrt(t) - 0.126 * t - 0.3516 * t * t + 0.2843 * t * t * t - 0.1036 * t * t * t * t);
      const yc = (t) => 4 * m * t * (1 - t);
      const N = 28, ts = [];
      for (let i = 0; i <= N; i++) ts.push(0.5 * (1 - Math.cos(Math.PI * i / N)));
      const shape = new T.Shape();
      for (let i = N; i >= 0; i--) {
        const t = ts[i], X = LEx - t * chord, Y = y + yc(t) + yt(t);
        if (i === N) shape.moveTo(X, Y); else shape.lineTo(X, Y);
      }
      for (let i = 1; i <= N; i++) { const t = ts[i]; shape.lineTo(LEx - t * chord, y + yc(t) - yt(t)); }
      const g = new T.ExtrudeGeometry(shape, { depth: span, bevelEnabled: false, steps: 1 });
      g.translate(0, 0, -span / 2);
      const mesh = add(plane, g, mats.red);
      return {
        mesh,
        top: (x) => { const t = Math.min(1, Math.max(0, (LEx - x) / chord)); return y + yc(t) + yt(t); },
        bot: (x) => { const t = Math.min(1, Math.max(0, (LEx - x) / chord)); return y + yc(t) - yt(t); }
      };
    };
    // Spannweiten 7,19 (mit Querruder-Ausgleich) / 6,22 / 5,72 m, Flügeltiefe 1,0 m, Flügelabstand je 0,86 m
    const upper = makeWing(6.76, 1.0, 0.14, 1.41, 1.84);
    makeWing(6.22, 1.0, 0.14, 1.18, 0.97);
    const lower = makeWing(5.72, 1.0, 0.14, 0.92, 0.1);

    // Querruder-Ausgleichsflächen, ragen je 0,2 m über die Flügelspitzen hinaus
    [1, -1].forEach((s) => {
      const sh = new T.Shape();
      sh.moveTo(0.8, 0); sh.lineTo(0.8, 0.12);
      sh.quadraticCurveTo(0.8, 0.215, 0.62, 0.215);
      sh.lineTo(0.42, 0.215); sh.lineTo(0.42, 0); sh.closePath();
      const g = new T.ExtrudeGeometry(sh, { depth: 0.05, bevelEnabled: false, curveSegments: 8 });
      g.rotateX(Math.PI / 2);
      const m = add(plane, g, mats.red);
      m.position.set(0, 1.9, s * 3.38);
      m.scale.z = s;
    });

    // Schleifkufen unter den Enden des Unterflügels
    [2.55, -2.55].forEach((z) => {
      const k = add(plane, new T.TorusGeometry(0.16, 0.015, 6, 20, Math.PI), mats.wood);
      k.rotation.x = Math.PI;
      k.position.set(0.45, 0.03, z);
    });

    // Interplane-Streben (I-Form)
    [2.6, -2.6].forEach((z) => {
      const sh = new T.Shape();
      sh.moveTo(0.75, 0.05); sh.lineTo(0.3, 0.05); sh.lineTo(0.7, 1.86); sh.lineTo(1.15, 1.86); sh.closePath();
      const g = new T.ExtrudeGeometry(sh, { depth: 0.04, bevelEnabled: false });
      g.translate(0, 0, z - 0.02);
      add(plane, g, mats.red);
    });

    // Baldachin-Streben
    [1, -1].forEach((s) => {
      rod(plane, [1.38, 0.93, 0.28 * s], [1.25, 1.86, 0.55 * s], 0.025, mats.black);
      rod(plane, [0.7, 0.98, 0.28 * s], [0.75, 1.86, 0.55 * s], 0.025, mats.black);
      rod(plane, [1.38, 0.93, 0.28 * s], [0.75, 1.86, 0.55 * s], 0.012, mats.black);
    });

    // Motorhaube (Hufeisen, unten offen)
    const gap = 1.2;
    const cowl = add(plane, new T.CylinderGeometry(0.5, 0.53, 0.39, 48, 1, true, Math.PI / 2 + gap / 2, Math.PI * 2 - gap), mats.red);
    cowl.rotation.z = -Math.PI / 2;
    cowl.position.set(1.655, 0.5, 0);
    const lipG = new T.TorusGeometry(0.5, 0.022, 8, 48, Math.PI * 2 - gap);
    lipG.rotateY(Math.PI / 2);
    lipG.rotateX(Math.PI * 1.5 + gap / 2);
    const lip = add(plane, lipG, mats.red);
    lip.position.set(1.85, 0.5, 0);
    const fw = add(plane, new T.CircleGeometry(0.52, 40), mats.dark);
    fw.rotation.y = Math.PI / 2;
    fw.position.set(1.47, 0.5, 0);
    // Übergang vom runden Motorquerschnitt zum kleineren Rumpfkasten
    const fair = add(plane, new T.CylinderGeometry(0.53, 0.36, 0.3, 32, 1, true), mats.red);
    fair.rotation.z = -Math.PI / 2;
    fair.position.set(1.31, 0.53, 0);
    fair.scale.set(1, 1, 0.92);
    fair.rotation.y = 0;

    // Umlaufmotor (dreht mit dem Propeller)
    const engine = new T.Group();
    engine.position.set(1.68, 0.5, 0);
    const crank = add(engine, new T.CylinderGeometry(0.13, 0.13, 0.2, 24), mats.metal);
    crank.rotation.z = Math.PI / 2;
    for (let k = 0; k < 9; k++) {
      const a = k * Math.PI * 2 / 9;
      const cyl = add(engine, new T.CylinderGeometry(0.055, 0.07, 0.3, 14), mats.metal);
      cyl.rotation.x = a;
      cyl.position.set(0, Math.cos(a) * 0.26, Math.sin(a) * 0.26);
      const head = add(engine, new T.CylinderGeometry(0.06, 0.06, 0.05, 14), mats.black);
      head.rotation.x = a;
      head.position.set(0, Math.cos(a) * 0.42, Math.sin(a) * 0.42);
    }
    plane.add(engine);

    // Propeller
    const prop = new T.Group();
    prop.position.set(2.0, 0.5, 0);
    const hub = add(prop, new T.CylinderGeometry(0.09, 0.1, 0.16, 20), mats.metal);
    hub.rotation.z = Math.PI / 2;
    const bs = new T.Shape();
    bs.moveTo(-0.05, 0.06);
    bs.lineTo(-0.085, 0.4); bs.lineTo(-0.095, 0.8); bs.lineTo(-0.08, 1.12);
    bs.quadraticCurveTo(-0.06, 1.31, 0, 1.31);
    bs.quadraticCurveTo(0.06, 1.31, 0.08, 1.12);
    bs.lineTo(0.095, 0.8); bs.lineTo(0.085, 0.4); bs.lineTo(0.05, 0.06); bs.closePath();
    const bg = new T.ExtrudeGeometry(bs, { depth: 0.03, bevelEnabled: true, bevelThickness: 0.008, bevelSize: 0.008, bevelSegments: 2, curveSegments: 8 });
    bg.translate(0, 0, -0.015);
    bg.rotateY(Math.PI / 2);
    [0, Math.PI].forEach((r) => {
      const holder = new T.Group();
      holder.rotation.x = r;
      const blade = add(holder, bg, mats.wood);
      blade.rotation.y = 0.28;
      prop.add(holder);
    });
    const disc = new T.Mesh(new T.CircleGeometry(1.31, 64), new T.MeshBasicMaterial({ color: 0x7a4a25, transparent: true, opacity: 0.1, depthWrite: false, side: T.DoubleSide }));
    disc.rotation.y = Math.PI / 2;
    disc.position.set(2.0, 0.5, 0);
    plane.add(prop);
    plane.add(disc);

    // Bewaffnung: 2 x LMG 08/15 "Spandau", 7,92 mm, synchronisiert (Form angenähert)
    const slot = document.createElement('canvas');
    slot.width = 64; slot.height = 256;
    const sctx = slot.getContext('2d');
    sctx.fillStyle = '#4a4b4f'; sctx.fillRect(0, 0, 64, 256);
    sctx.fillStyle = '#050505';
    for (let r = 0; r < 8; r++) for (let k = 0; k < 2; k++) { sctx.beginPath(); sctx.ellipse(16 + k * 32, 16 + r * 32, 8, 11, 0, 0, Math.PI * 2); sctx.fill(); }
    const slotTex = new T.CanvasTexture(slot);
    slotTex.wrapS = T.RepeatWrapping; slotTex.wrapT = T.RepeatWrapping;
    slotTex.repeat.set(4, 1);
    slotTex.colorSpace = T.SRGBColorSpace;
    const jacketMat = std(0xffffff, 0.45, 0.6, { map: slotTex });
    const brass = std(0xb08a3e, 0.35, 0.8);
    [0.12, -0.12].forEach((z) => {
      const s = Math.sign(z);
      const jacket = add(plane, new T.CylinderGeometry(0.043, 0.043, 0.72, 20, 1, false), jacketMat);
      jacket.rotation.z = Math.PI / 2;
      jacket.position.set(0.99, 1.13, z);
      const cap = add(plane, new T.CylinderGeometry(0.046, 0.046, 0.03, 20), mats.black);
      cap.rotation.z = Math.PI / 2;
      cap.position.set(1.35, 1.13, z);
      const muzzle = add(plane, new T.CylinderGeometry(0.022, 0.028, 0.08, 12), mats.black);
      muzzle.rotation.z = Math.PI / 2;
      muzzle.position.set(1.4, 1.13, z);
      const rec = add(plane, new T.BoxGeometry(0.44, 0.13, 0.095), mats.black);
      rec.position.set(0.42, 1.12, z);
      const top = add(plane, new T.BoxGeometry(0.3, 0.02, 0.07), mats.metal);
      top.position.set(0.44, 1.195, z);
      const feed = add(plane, new T.BoxGeometry(0.09, 0.06, 0.05), mats.black);
      feed.position.set(0.55, 1.13, z - s * 0.07);
      const belt = add(plane, new T.BoxGeometry(0.05, 0.012, 0.11), brass);
      belt.position.set(0.55, 1.1, z - s * 0.13);
      belt.rotation.x = s * 0.6;
      const lever = rod(plane, [0.26, 1.12, z + s * 0.048], [0.26, 1.12, z + s * 0.1], 0.012, mats.metal);
      const knob = add(plane, new T.SphereGeometry(0.02, 10, 8), mats.black);
      knob.position.set(0.26, 1.12, z + s * 0.105);
      const mount = add(plane, new T.BoxGeometry(0.3, 0.06, 0.07), mats.black);
      mount.position.set(0.42, 1.04, z);
      const sightF = add(plane, new T.BoxGeometry(0.01, 0.04, 0.01), mats.black);
      sightF.position.set(1.32, 1.19, z);
    });

    // Cockpit
    const coamG = new T.TorusGeometry(0.29, 0.035, 10, 40);
    coamG.rotateX(Math.PI / 2);
    coamG.scale(1.35, 1, 1);
    const coam = add(plane, coamG, mats.black);
    coam.position.set(-0.4, 1.005, 0);
    const holeG = new T.CircleGeometry(0.29, 40);
    holeG.rotateX(-Math.PI / 2);
    holeG.scale(1.35, 1, 1);
    const hole = add(plane, holeG, mats.dark);
    hole.position.set(-0.4, 1.008, 0);

    // Fahrwerk
    // Spurweite 1,60 m (5'3"), Rad ca. 0,74 m Durchmesser
    const AX = 1.22, AY = -0.64, WR = 0.37, WZ = 0.8;
    [1, -1].forEach((s) => {
      rod(plane, [1.42, 0.17, 0.29 * s], [AX, AY, 0.66 * s], 0.025, mats.red);
      rod(plane, [0.72, 0.13, 0.29 * s], [AX, AY, 0.66 * s], 0.025, mats.red);
      rod(plane, [1.42, 0.17, 0.29 * s], [AX, AY, -0.66 * s], 0.006, mats.black);
      const tire = add(plane, new T.TorusGeometry(0.3, 0.07, 14, 40), mats.tire);
      tire.position.set(AX, AY, WZ * s);
      const cover = add(plane, new T.CylinderGeometry(0.29, 0.29, 0.09, 32), mats.red);
      cover.rotation.x = Math.PI / 2;
      cover.position.set(AX, AY, WZ * s);
    });
    rod(plane, [AX, AY, -0.9], [AX, AY, 0.9], 0.025, mats.black);
    {
      const sh = new T.Shape();
      const c = 0.45, LE = AX + 0.2, y0 = AY;
      for (let i = 0; i <= 20; i++) { const t = i / 20; const yy = 0.045 * Math.sin(Math.PI * Math.sqrt(t)); if (i === 0) sh.moveTo(LE - t * c, y0 + yy); else sh.lineTo(LE - t * c, y0 + yy); }
      for (let i = 20; i >= 0; i--) { const t = i / 20; sh.lineTo(LE - t * c, y0 - 0.025 * Math.sin(Math.PI * Math.sqrt(t))); }
      const g = new T.ExtrudeGeometry(sh, { depth: 1.44, bevelEnabled: false });
      g.translate(0, 0, -0.72);
      add(plane, g, mats.red);
    }

    // Hecksporn
    rod(plane, [-2.72, 0.44, 0], [-3.07, 0.15, 0], 0.025, mats.wood);

    // Höhenleitwerk
    {
      const sh = new T.Shape();
      // Spannweite 2,69 m (8'10"), Flosse 1,22 m tief, Ruder 0,41 m; Oberseite bündig mit dem Rumpfrücken
      sh.moveTo(-1.62, 0);
      sh.lineTo(-2.8, 1.2);
      sh.quadraticCurveTo(-2.86, 1.345, -3.0, 1.345);
      sh.quadraticCurveTo(-3.21, 1.345, -3.21, 1.15);
      sh.lineTo(-3.21, -1.15);
      sh.quadraticCurveTo(-3.21, -1.345, -3.0, -1.345);
      sh.quadraticCurveTo(-2.86, -1.345, -2.8, -1.2);
      sh.closePath();
      const g = new T.ExtrudeGeometry(sh, { depth: 0.04, bevelEnabled: false, curveSegments: 12 });
      g.rotateX(Math.PI / 2);
      const m = add(plane, g, mats.red);
      m.position.y = 0.845;
    }

    // Seitenruder (Kommaform, weiß)
    {
      const sh = new T.Shape();
      // 0,86 m lang (2'10"), 0,91 m hoch (3'0")
      sh.moveTo(-2.86, 0.5);
      sh.lineTo(-2.86, 1.12);
      sh.bezierCurveTo(-2.86, 1.43, -3.12, 1.44, -3.3, 1.43);
      sh.bezierCurveTo(-3.58, 1.42, -3.77, 1.2, -3.76, 0.96);
      sh.bezierCurveTo(-3.75, 0.7, -3.55, 0.52, -3.3, 0.52);
      sh.lineTo(-2.86, 0.5);
      const g = new T.ExtrudeGeometry(sh, { depth: 0.04, bevelEnabled: false, curveSegments: 16 });
      g.translate(0, 0, -0.02);
      add(plane, g, mats.white);
    }

    // Balkenkreuze
    const cvs = document.createElement('canvas');
    cvs.width = 256; cvs.height = 256;
    const ctx = cvs.getContext('2d');
    const drawCross = (w, color) => { ctx.fillStyle = color; ctx.fillRect(128 - w / 2, 16, w, 224); ctx.fillRect(16, 128 - w / 2, 224, w); };
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(4, 128 - 40, 248, 80); ctx.fillRect(128 - 40, 4, 80, 248);
    drawCross(56, '#111111');
    ctx.clearRect(0, 0, 256, 4); ctx.clearRect(0, 252, 256, 4); ctx.clearRect(0, 0, 4, 256); ctx.clearRect(252, 0, 4, 256);
    const tex = new T.CanvasTexture(cvs);
    tex.colorSpace = T.SRGBColorSpace;
    tex.anisotropy = 4;
    const decalMat = new T.MeshStandardMaterial({ map: tex, alphaTest: 0.5, roughness: 0.65, side: T.DoubleSide, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 });
    const decal = (size, cx, cy, cz, ry) => {
      const m = new T.Mesh(new T.PlaneGeometry(size, size), decalMat);
      m.position.set(cx, cy, cz); m.rotation.y = ry; m.receiveShadow = true;
      plane.add(m);
    };
    const conform = (size, cx, cz, fn, off, down) => {
      const g = new T.PlaneGeometry(size, size, 16, 16);
      g.rotateX(down ? Math.PI / 2 : -Math.PI / 2);
      g.translate(cx, 0, cz);
      const p = g.attributes.position;
      for (let i = 0; i < p.count; i++) p.setY(i, fn(p.getX(i)) + off);
      g.computeVertexNormals();
      const m = new T.Mesh(g, decalMat);
      m.receiveShadow = true;
      plane.add(m);
    };
    const slope = 0.1 / 1.1, xs = -1.7, hw = 0.28 - slope * 0.9;
    decal(0.48, xs, 0.62, hw + 0.006, -slope);
    decal(0.48, xs, 0.62, -hw - 0.006, Math.PI + slope);
    decal(0.6, -3.3, 0.97, 0.024, 0);
    decal(0.6, -3.3, 0.97, -0.024, Math.PI);
    [2.75, -2.75].forEach((z) => conform(0.82, 0.91, z, upper.top, 0.004, false));
    [2.25, -2.25].forEach((z) => conform(0.82, 0.42, z, lower.bot, -0.004, true));

    // Standwinkel: Räder und Sporn auf dem Boden
    const shiftX = 0.9;
    plane.position.x = shiftX;
    const wheelY = (a) => (AX + shiftX) * Math.sin(a) + AY * Math.cos(a) - WR;
    const skidY = (a) => (-3.07 + shiftX) * Math.sin(a) + 0.12 * Math.cos(a);
    let lo = 0, hi = 0.5;
    for (let i = 0; i < 40; i++) { const mid = (lo + hi) / 2; if (wheelY(mid) - skidY(mid) < 0) lo = mid; else hi = mid; }
    const ang = (lo + hi) / 2;
    const rig = new T.Group();
    rig.add(plane);
    rig.rotation.z = ang;
    rig.position.y = -wheelY(ang);
    scene.add(rig);


  const target = new T.Vector3(0, 1.15, 0);

  /* Farben aus dem Seitenschema (hell/dunkel) übernehmen */
  function applyTheme() {
    const cs = getComputedStyle(box);
    const bg = (cs.getPropertyValue("--dr1-bg") || "#181d1a").trim();
    const gr = (cs.getPropertyValue("--dr1-ground") || "#22272d").trim();
    const rl = (cs.getPropertyValue("--dr1-ring") || "#353b43").trim();
    const dark = (cs.getPropertyValue("--dr1-dark") || "1").trim() === "1";
    scene.background.set(bg);
    scene.fog.color.set(bg);
    groundMat.color.set(gr);
    ringMat.color.set(rl);
    hemi.intensity = dark ? 0.9 : 1.15;
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
  function resize() {
    const w = cv.clientWidth, h = cv.clientHeight;
    if (!w || !h) return;
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
  function zoom(f) { c.tDist = Math.min(22, Math.max(5.5, c.tDist * f)); dirty = true; }

  function setPressed(btn, on) { btn.setAttribute("aria-pressed", on ? "true" : "false"); }
  box.querySelectorAll("[data-view]").forEach((btn) => btn.addEventListener("click", () => {
    const v = VIEWS[btn.dataset.view];
    let t = v.theta;
    while (t - c.theta > Math.PI) t -= Math.PI * 2;
    while (c.theta - t > Math.PI) t += Math.PI * 2;
    c.tTheta = t; c.tPhi = v.phi; c.tDist = v.dist;
    state.spin = false;
    box.querySelectorAll("[data-view]").forEach((b) => setPressed(b, b === btn));
    syncToggles();
    dirty = true;
  }));
  box.querySelectorAll("[data-zoom]").forEach((btn) => btn.addEventListener("click", () => zoom(btn.dataset.zoom === "in" ? 0.85 : 1.18)));
  function syncToggles() {
    box.querySelectorAll("[data-toggle]").forEach((b) => setPressed(b, state[b.dataset.toggle]));
  }
  box.querySelectorAll("[data-toggle]").forEach((btn) => btn.addEventListener("click", () => {
    state[btn.dataset.toggle] = !state[btn.dataset.toggle];
    if (btn.dataset.toggle === "spin" && state.spin) box.querySelectorAll("[data-view]").forEach((b) => setPressed(b, false));
    syncToggles();
    dirty = true;
  }));
  syncToggles();

  /* Nur zeichnen, wenn das Modell sichtbar ist */
  let visible = true;
  if (window.IntersectionObserver) new IntersectionObserver((en) => { visible = en[0].isIntersecting; if (visible) dirty = true; }).observe(cv);
  document.addEventListener("visibilitychange", () => { if (!document.hidden) dirty = true; });

  function loop() {
    requestAnimationFrame(loop);
    if (!visible || document.hidden) return;
    const moving = state.spin || state.prop || drag ||
      Math.abs(c.tTheta - c.theta) > 1e-4 || Math.abs(c.tPhi - c.phi) > 1e-4 || Math.abs(c.tDist - c.dist) > 1e-3;
    if (!moving && !dirty) return;
    dirty = false;
    if (state.spin && !drag) { c.tTheta += 0.0035; c.theta += 0.0035; }
    c.theta += (c.tTheta - c.theta) * 0.08;
    c.phi += (c.tPhi - c.phi) * 0.08;
    c.dist += (c.tDist - c.dist) * 0.1;
    const sp = Math.sin(c.phi);
    /* schmale Kästen: Abstand vergrößern, damit die Flügel nicht abgeschnitten werden */
    const d = c.dist * Math.max(1, 1.5 / cam.aspect);
    cam.position.set(target.x + d * sp * Math.sin(c.theta), target.y + d * Math.cos(c.phi), target.z + d * sp * Math.cos(c.theta));
    if (cam.position.y < 0.15) cam.position.y = 0.15;
    cam.lookAt(target);
    ground.visible = c.phi < 1.62;
    ring.visible = ground.visible;
    if (state.prop) { prop.rotation.x += 0.42; engine.rotation.x += 0.42; disc.visible = true; }
    else disc.visible = false;
    renderer.render(scene, cam);
  }
  loop();
  box.classList.add("ready");
})();
