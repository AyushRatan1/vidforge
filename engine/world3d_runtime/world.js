// VidForge world3d runtime: builds a low-poly diorama from a JSON "world" and renders it frame by frame.
// Driven from Python (engine/world3d.py) through Playwright: VF.setup(world, opts) once, then VF.frame(t) per frame.
// All times in the world are absolute seconds (Python resolves scene references before calling setup).
// Everything is deterministic: no Math.random, no wall clock.

import * as THREE from "./vendor/three.module.js";
import { mergeGeometries } from "./vendor/BufferGeometryUtils.js";

// ------------------------------------------------------------------ helpers
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, u) => a + (b - a) * u;
const easeInOut = (x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
const easeOut = (x) => 1 - Math.pow(1 - x, 3);
const easeOutBack = (x) => { const c1 = 1.4, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); };
const num = (v, d) => (typeof v === "number" && isFinite(v) ? v : d);
const vec = (a, d = [0, 0, 0]) => (Array.isArray(a) ? [num(a[0], d[0]), num(a[1], d[1]), num(a[2], d[2])] : d.slice());

function rng(seed) {
  let a = (seed >>> 0) || 1;
  return () => {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// progress of a {from, to} window at time t (0 before, 1 after)
function prog(w, t, defDur = 1) {
  if (!w) return 1;
  const f = num(w.from, 0), to = num(w.to, f + defDur);
  if (t <= f) return 0;
  if (t >= to) return 1;
  return (t - f) / Math.max(1e-6, to - f);
}

// ------------------------------------------------------------------ materials
const MAT = new Map();
function mat(color, opts = {}) {
  const key = color + JSON.stringify(opts);
  if (!MAT.has(key)) {
    const m = new THREE.MeshLambertMaterial({ color, flatShading: true, ...opts });
    MAT.set(key, m);
  }
  return MAT.get(key);
}

let STONE_TEX = null;
function stoneTexture() {
  if (STONE_TEX) return STONE_TEX;
  const c = document.createElement("canvas");
  c.width = c.height = 256;
  const g = c.getContext("2d");
  g.fillStyle = "#ffffff"; g.fillRect(0, 0, 256, 256);
  const r = rng(11);
  const rows = 4;
  for (let y = 0; y < rows; y++) {
    const h = 256 / rows, off = (y % 2) * 32;
    for (let x = -64; x < 256; x += 64) {
      const v = 228 + Math.floor(r() * 22);
      g.fillStyle = `rgb(${v},${v - 2},${v - 6})`;
      g.fillRect(x + off + 2, y * h + 2, 60, h - 4);
    }
  }
  g.fillStyle = "rgba(90,80,70,0.55)";
  for (let y = 0; y <= rows; y++) g.fillRect(0, y * (256 / rows) - 1, 256, 2);
  STONE_TEX = new THREE.CanvasTexture(c);
  STONE_TEX.colorSpace = THREE.SRGBColorSpace;
  STONE_TEX.wrapS = STONE_TEX.wrapT = THREE.RepeatWrapping;
  STONE_TEX.anisotropy = 1;
  return STONE_TEX;
}
function stoneMat(color, rx = 1, ry = 1) {
  const key = `stone:${color}:${rx.toFixed(2)}:${ry.toFixed(2)}`;
  if (!MAT.has(key)) {
    const tex = stoneTexture().clone();
    tex.needsUpdate = true;
    tex.repeat.set(Math.max(0.25, rx), Math.max(0.25, ry));
    MAT.set(key, new THREE.MeshLambertMaterial({ color, map: tex }));
  }
  return MAT.get(key);
}
function surface(o, color, w, h) {
  return o.texture === "stone" ? stoneMat(color, w / 2.2, h / 1.1) : mat(color);
}

function shadow(obj, cast = true, recv = true) {
  obj.traverse((m) => { if (m.isMesh) { m.castShadow = cast; m.receiveShadow = recv; } });
  return obj;
}

function box(w, h, d, m, x = 0, y = 0, z = 0) {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m);
  mesh.position.set(x, y, z);
  return mesh;
}

// ------------------------------------------------------------------ styles
const STYLES = {
  desert: { sky: "#dccfb6", fog: [40, 120], ground: "#d9bf8f", sun: [14, 22, 10], sunColor: "#fff1d8", sunI: 2.1,
            hemiSky: "#fff4e2", hemiGround: "#7a5536", hemiI: 1.25,
            strata: [["#d9bf8f", 0.35], ["#b98a5c", 1.6], ["#8c5f3e", 2.6], ["#6f4a31", 3.2], ["#5a3c28", 14]] },
  golden: { sky: "#e8c9a0", fog: [35, 110], ground: "#d7b07a", sun: [-16, 12, 8], sunColor: "#ffd9a8", sunI: 2.3,
            hemiSky: "#ffe6c7", hemiGround: "#6b4630", hemiI: 1.1,
            strata: [["#d7b07a", 0.35], ["#b07d50", 1.6], ["#875a3a", 2.6], ["#6b452e", 3.2], ["#563824", 14]] },
  green: { sky: "#cfe0e6", fog: [45, 130], ground: "#8db35c", sun: [12, 22, 10], sunColor: "#fffaf0", sunI: 2.0,
           hemiSky: "#f2fbff", hemiGround: "#5a4a32", hemiI: 1.3,
           strata: [["#8db35c", 0.3], ["#8a6a45", 1.6], ["#6f5236", 2.6], ["#5b4330", 3.2], ["#4a3627", 14]] },
  overcast: { sky: "#c9ccd1", fog: [35, 110], ground: "#b9b2a2", sun: [10, 24, 6], sunColor: "#f4f4f4", sunI: 1.4,
              hemiSky: "#f0f2f5", hemiGround: "#6d6559", hemiI: 1.5,
              strata: [["#b9b2a2", 0.35], ["#9a8c76", 1.6], ["#7b6d5a", 2.6], ["#62574a", 3.2], ["#4f463c", 14]] },
  night: { sky: "#141a2b", fog: [30, 90], ground: "#4a4a55", sun: [-8, 18, 6], sunColor: "#aebbe0", sunI: 1.0,
           hemiSky: "#5b6a92", hemiGround: "#1d1d24", hemiI: 0.9,
           strata: [["#4a4a55", 0.35], ["#3d3a40", 1.6], ["#332f35", 2.6], ["#2a272c", 3.2], ["#221f24", 14]] },
};

// ------------------------------------------------------------------ build animation wrapper
// Every object sits in a holder group. `build` animates its appearance, `hide` its removal.
function applyBuild(holder, o, t) {
  const b = o.build;
  let visible = true;
  if (o.hide && num(o.hide.at, Infinity) <= t) {
    const p = clamp((t - o.hide.at) / Math.max(0.05, num(o.hide.dur, 0.4)));
    if (p >= 1) { holder.visible = false; return; }
    holder.scale.setScalar(Math.max(0.001, 1 - easeInOut(p)));
    holder.visible = true;
    return;
  }
  holder.scale.set(1, 1, 1);
  holder.position.copy(holder.userData.base);
  if (!b) { holder.visible = true; return; }
  const p = prog(b, t);
  const op = b.op || "rise";
  if (p <= 0 && op !== "none") visible = false;
  holder.visible = visible;
  if (!visible) return;
  if (op === "rise") holder.scale.y = Math.max(0.001, easeOut(p));
  else if (op === "grow") holder.scale.setScalar(Math.max(0.001, easeOutBack(p)));
  else if (op === "drop") holder.position.y += (1 - easeOut(p)) * num(b.height, 8);
  else if (op === "slide") {
    const d = vec(b.offset, [0, 0, 6]);
    const u = 1 - easeInOut(p);
    holder.position.x += d[0] * u; holder.position.y += d[1] * u; holder.position.z += d[2] * u;
  }
  // "stagger" ops are handled by the object itself through holder.userData.stagger(p)
  if (holder.userData.stagger) holder.userData.stagger(op === "stagger" || b.stagger ? p : 1);
}

// Composite objects reveal their parts one by one when build.stagger is set (or op is "stagger").
function staggerParts(parts, mode = "rise") {
  return (p) => {
    const n = parts.length;
    parts.forEach((m, k) => {
      const a = k / n, w = Math.max(1 / n, 0.15);
      const q = clamp((p - a * (1 - w)) / w);
      m.visible = q > 0;
      if (!m.visible) return;
      const base = m.userData.baseY ?? (m.userData.baseY = m.position.y);
      if (mode === "drop") { m.position.y = base + (1 - easeOut(q)) * 3; m.scale.set(1, 1, 1); }
      else { m.position.y = base; m.scale.set(1, Math.max(0.001, easeOut(q)), 1); }
    });
  };
}

// ------------------------------------------------------------------ terrain with animated excavations
function makeTerrain(T, style) {
  const width = num(T.width, 40), length = num(T.length, 40), cut = num(T.cut, 0);
  const X0 = -width / 2, X1 = width / 2, Z0 = cut - length, Z1 = cut;
  const strata = (T.strata || style.strata).map((s) => (Array.isArray(s) ? { color: s[0], thickness: s[1] } : s));
  const D = strata.reduce((a, s) => a + num(s.thickness, 1), 0);
  const bounds = []; let acc = 0;
  for (const s of strata) { bounds.push([-acc, -(acc + num(s.thickness, 1)), s.color]); acc += num(s.thickness, 1); }
  const colorAt = (y) => { for (const [a, b, c] of bounds) if (y <= a && y >= b) return c; return bounds[bounds.length - 1][2]; };
  const digs = (T.digs || []).map((d) => ({
    x0: Math.max(X0, Math.min(num(d.x0, -2), num(d.x1, 2))), x1: Math.min(X1, Math.max(num(d.x0, -2), num(d.x1, 2))),
    z0: Math.max(Z0, Math.min(num(d.z0, -2), num(d.z1, 2))), z1: Math.min(Z1, Math.max(num(d.z0, -2), num(d.z1, 2))),
    depth: Math.min(D - 0.05, num(d.depth, 3)), from: d.from, to: d.to, start: num(d.start_depth, 0),
  }));
  const group = new THREE.Group();
  let last = "";

  // the world outside the block: three flat aprons so the horizon reads as endless ground
  const apron = mat(style.ground);
  const far = 260;
  const aprons = new THREE.Group();
  aprons.add(box(far * 2, 0.2, far, apron, 0, -0.1, Z0 - far / 2));
  aprons.add(box(far, 0.2, length, apron, X0 - far / 2, -0.1, (Z0 + Z1) / 2));
  aprons.add(box(far, 0.2, length, apron, X1 + far / 2, -0.1, (Z0 + Z1) / 2));
  shadow(aprons, false, true);

  function depths(t) {
    return digs.map((d) => {
      if (!d.from && d.from !== 0) return d.depth;
      return lerp(d.start, d.depth, easeInOut(prog({ from: d.from, to: d.to }, t)));
    });
  }

  function rebuild(ds) {
    for (const c of group.children.slice()) { group.remove(c); c.geometry && c.geometry.dispose(); }
    const ys = new Set([0, -D]);
    for (const [a, b] of bounds) { ys.add(a); ys.add(b); }
    ds.forEach((d) => { if (d > 0.001 && d < D) ys.add(-d); });
    const Y = [...ys].sort((a, b) => b - a);
    for (let k = 0; k < Y.length - 1; k++) {
      const ya = Y[k], yb = Y[k + 1];
      if (ya - yb < 1e-4) continue;
      const color = colorAt((ya + yb) / 2);
      const rects = digs.filter((d, i) => ds[i] >= -yb - 1e-4 && ds[i] > 0.001);
      const xs = [...new Set([X0, X1, ...rects.flatMap((r) => [r.x0, r.x1])])].sort((a, b) => a - b);
      const zs = [...new Set([Z0, Z1, ...rects.flatMap((r) => [r.z0, r.z1])])].sort((a, b) => a - b);
      for (let zi = 0; zi < zs.length - 1; zi++) {
        const za = zs[zi], zb = zs[zi + 1];
        if (zb - za < 1e-4) continue;
        let runStart = null;
        for (let xi = 0; xi <= xs.length - 1; xi++) {
          const xa = xs[xi], xb = xs[xi + 1];
          const inside = xi < xs.length - 1 && rects.some((r) => xa >= r.x0 - 1e-6 && xb <= r.x1 + 1e-6 && za >= r.z0 - 1e-6 && zb <= r.z1 + 1e-6);
          const solid = xi < xs.length - 1 && !inside && xb - xa > 1e-4;
          if (solid && runStart === null) runStart = xa;
          if ((!solid || xi === xs.length - 1) && runStart !== null) {
            const end = solid ? xb : xa;
            const m = box(end - runStart, ya - yb, zb - za, mat(color), (runStart + end) / 2, (ya + yb) / 2, (za + zb) / 2);
            m.castShadow = true; m.receiveShadow = true;
            group.add(m);
            runStart = null;
          }
        }
      }
    }
  }

  return {
    group, aprons, digs, bounds: { X0, X1, Z0, Z1, D },
    dugAt(x, z, t) {
      const ds = depths(t);
      return digs.some((d, i) => ds[i] > 0.05 && x >= d.x0 && x <= d.x1 && z >= d.z0 && z <= d.z1);
    },
    update(t) {
      const ds = depths(t);
      const sig = ds.map((v) => v.toFixed(3)).join(",");
      if (sig !== last) { rebuild(ds); last = sig; }
    },
  };
}

// ------------------------------------------------------------------ object kit
const KIT = {};

KIT.box = (o) => {
  const w = num(o.w, 2), h = num(o.h, 2), d = num(o.d, 2);
  return box(w, h, d, surface(o, o.color || "#d8cfc0", w, h), 0, h / 2, 0);
};

KIT.slab = KIT.box;

KIT.cylinder = (o) => {
  const r = num(o.r, 1), h = num(o.h, 2);
  const m = new THREE.Mesh(new THREE.CylinderGeometry(num(o.r_top, r), r, h, num(o.segments, 12)), mat(o.color || "#d8cfc0"));
  m.position.y = h / 2;
  return m;
};

KIT.cone = (o) => {
  const r = num(o.r, 1), h = num(o.h, 2);
  const m = new THREE.Mesh(new THREE.ConeGeometry(r, h, num(o.segments, 4)), mat(o.color || "#c9a77a"));
  m.position.y = h / 2;
  if (num(o.segments, 4) === 4) m.rotation.y = Math.PI / 4;
  return m;
};

KIT.pyramid = (o) => KIT.cone({ ...o, segments: 4 });

KIT.dome = (o) => {
  const r = num(o.r, 1.5);
  const m = new THREE.Mesh(new THREE.SphereGeometry(r, 12, 8, 0, Math.PI * 2, 0, Math.PI / 2), mat(o.color || "#efe6d6"));
  return m;
};

KIT.sphere = (o) => {
  const r = num(o.r, 1);
  const m = new THREE.Mesh(new THREE.IcosahedronGeometry(r, 1), mat(o.color || "#d8cfc0"));
  m.position.y = r;
  return m;
};

KIT.mound = (o) => {
  const r = num(o.r, 2), h = num(o.h, 1.2);
  const m = new THREE.Mesh(new THREE.IcosahedronGeometry(1, 1), mat(o.color || "#a8774c"));
  m.scale.set(r, h, r * num(o.stretch, 1));
  m.position.y = h * 0.35;
  return m;
};

KIT.wall = (o) => {
  // a wall built from courses of stone, from [x,z] to [x,z]
  // from/to are [x, z] (or [x, y, z], y ignored: the wall stands on the holder's pos)
  const xz = (p, d) => (Array.isArray(p) ? (p.length === 2 ? [num(p[0], d[0]), num(p[1], d[1])] : [num(p[0], d[0]), num(p[2], d[1])]) : d);
  const [ax, az] = xz(o.from, [0, 0]), [bx, bz] = xz(o.to, [4, 0]);
  const len = Math.hypot(bx - ax, bz - az) || 1, h = num(o.h, 3), th = num(o.thickness, 0.6);
  const courses = Math.max(1, Math.round(num(o.courses, Math.ceil(h / 0.7))));
  const g = new THREE.Group();
  const parts = [];
  const ch = h / courses;
  const m = o.texture === "plain" ? mat(o.color || "#e2d6c2") : stoneMat(o.color || "#e2d6c2", len / 2.2, ch / 1.1 * 0.9);
  for (let k = 0; k < courses; k++) {
    const c = box(len, ch * 0.98, th, m, 0, ch * k + ch / 2, 0);
    g.add(c); parts.push(c);
  }
  g.position.set((ax + bx) / 2, 0, (az + bz) / 2);
  g.rotation.y = -Math.atan2(bz - az, bx - ax);
  const outer = new THREE.Group(); outer.add(g);
  outer.userData.stagger = staggerParts(parts, "rise");
  return outer;
};

KIT.stairs = (o) => {
  // solid flight of steps from `from` (top) to `to` (bottom), `width` wide
  const a = vec(o.from, [0, 0, 0]), b = vec(o.to, [0, -3, 6]);
  const n = Math.max(2, Math.round(num(o.steps, 12)));
  const width = num(o.width, 3);
  const hx = b[0] - a[0], hz = b[2] - a[2];
  const run = Math.hypot(hx, hz) / n, rise = (a[1] - b[1]) / n;
  const g = new THREE.Group();
  const parts = [];
  const m = stoneMat(o.color || "#e6dccb", width / 2.2, 0.4);
  for (let k = 0; k < n; k++) {
    const top = a[1] - k * rise;
    const hgt = Math.max(rise, top - b[1] + (o.solid === false ? 0 : 0));
    const s = box(width, hgt, run * 1.02, m, 0, top - hgt / 2, run * (k + 0.5));
    g.add(s); parts.push(s);
  }
  g.position.set(a[0], 0, a[2]);
  g.rotation.y = Math.atan2(hx, hz);
  const outer = new THREE.Group(); outer.add(g);
  outer.userData.stagger = staggerParts(parts, "drop");
  outer.userData.abs = true;
  return outer;
};

KIT.pillar = (o) => {
  const h = num(o.h, 3), w = num(o.w, 0.4), c = o.color || "#e9dfcd";
  const g = new THREE.Group();
  g.add(box(w * 1.5, 0.2, w * 1.5, mat(c), 0, 0.1, 0));
  g.add(box(w, h - 0.4, w, mat(c), 0, h / 2, 0));
  g.add(box(w * 1.6, 0.2, w * 1.6, mat(c), 0, h - 0.1, 0));
  return g;
};

KIT.pavilion = (o) => {
  // a pillared hall (mandapa): grid of pillars and a roof slab; stagger raises pillars then drops the roof
  const w = num(o.w, 6), d = num(o.d, 3), h = num(o.h, 3);
  const cols = Math.max(2, num(o.cols, 4)), rows = Math.max(1, num(o.rows, 2));
  const c = o.color || "#e9dfcd";
  const g = new THREE.Group();
  const parts = [];
  for (let i = 0; i < cols; i++) for (let j = 0; j < rows; j++) {
    const p = KIT.pillar({ h, w: num(o.pillar_w, 0.35), color: c });
    p.position.set(-w / 2 + (w * i) / (cols - 1), 0, rows === 1 ? 0 : -d / 2 + (d * j) / (rows - 1));
    g.add(p); parts.push(p);
  }
  if (o.roof !== false) {
    const roof = box(w + 0.8, 0.35, d + 0.8, stoneMat(c, (w + 0.8) / 2.2, 0.3), 0, h + 0.17, 0);
    g.add(roof); parts.push(roof);
  }
  g.userData.stagger = staggerParts(parts, "rise");
  return g;
};

KIT.spire = (o) => {
  // stacked, tapering tiers like a temple shikhara, topped with an amalaka and a kalash
  const w = num(o.w, 3), h = num(o.h, 6), tiers = Math.max(2, num(o.tiers, 6)), c = o.color || "#d9c3a0";
  const g = new THREE.Group(); const parts = [];
  for (let k = 0; k < tiers; k++) {
    const f = 1 - (k / tiers) * 0.7, th = h / tiers;
    const s = box(w * f, th * 0.92, w * f, stoneMat(c, w * f / 2.2, 0.4), 0, th * k + th / 2, 0);
    g.add(s); parts.push(s);
  }
  const am = new THREE.Mesh(new THREE.CylinderGeometry(w * 0.22, w * 0.22, 0.25, 12), mat(c));
  am.position.y = h + 0.12; g.add(am); parts.push(am);
  const ka = new THREE.Mesh(new THREE.ConeGeometry(0.14, 0.6, 8), mat(o.top || "#d9a441"));
  ka.position.y = h + 0.55; g.add(ka); parts.push(ka);
  g.userData.stagger = staggerParts(parts, "rise");
  return g;
};

KIT.arch = (o) => {
  const w = num(o.w, 3), h = num(o.h, 3), t = num(o.thickness, 0.5), c = o.color || "#e2d6c2";
  const g = new THREE.Group();
  g.add(box(t, h, t, mat(c), -w / 2, h / 2, 0));
  g.add(box(t, h, t, mat(c), w / 2, h / 2, 0));
  const arc = new THREE.Mesh(new THREE.TorusGeometry(w / 2, t / 2, 6, 16, Math.PI), mat(c));
  arc.position.y = h;
  g.add(arc);
  return g;
};

KIT.water = (o) => {
  const x0 = num(o.x0, -2), x1 = num(o.x1, 2), z0 = num(o.z0, -2), z1 = num(o.z1, 2);
  const yb = num(o.y_bottom, -6), yf = num(o.level_from, yb), yt = num(o.level, num(o.level_to, yb + 1));
  const m = new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1),
    new THREE.MeshLambertMaterial({ color: o.color || "#4f8fc9", transparent: true, opacity: num(o.opacity, 0.88) }));
  m.receiveShadow = true;
  const g = new THREE.Group(); g.add(m);
  // a few sparkles on the surface
  const sp = new THREE.Group(); const r = rng(5);
  for (let k = 0; k < 18; k++) {
    const s = new THREE.Mesh(new THREE.PlaneGeometry(0.12, 0.12), new THREE.MeshBasicMaterial({ color: "#ffffff", transparent: true, opacity: 0.8 }));
    s.rotation.x = -Math.PI / 2;
    s.position.set(lerp(x0, x1, r()), 0.005, lerp(z0, z1, r()));
    s.userData.ph = r() * 6.28;
    sp.add(s);
  }
  g.add(sp);
  g.userData.abs = true;
  g.userData.tick = (t) => {
    const p = easeInOut(prog({ from: o.from, to: o.to }, t));
    const top = lerp(yf, yt, o.from === undefined ? 1 : p);
    const hh = Math.max(0.01, top - yb);
    m.scale.set(x1 - x0, hh, z1 - z0);
    m.position.set((x0 + x1) / 2, yb + hh / 2, (z0 + z1) / 2);
    sp.position.y = top;
    sp.children.forEach((s) => { s.material.opacity = 0.25 + 0.6 * Math.max(0, Math.sin(t * 3 + s.userData.ph)); });
    g.visible = top > yb + 0.02;
  };
  return g;
};

KIT.tree = (o, r = rng(num(o.seed, 3))) => {
  const s = num(o.scale, 1);
  const g = new THREE.Group();
  const trunkH = 2.2 * s * (0.85 + r() * 0.3);
  const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.13 * s, 0.24 * s, trunkH, 6), mat(o.trunk || "#6b4428"));
  trunk.position.y = trunkH / 2; g.add(trunk);
  const leaf = o.color || "#4f8a3a";
  const blobs = 3 + Math.floor(r() * 3);
  for (let k = 0; k < blobs; k++) {
    const b = new THREE.Mesh(new THREE.IcosahedronGeometry((0.75 + r() * 0.35) * s, 1), mat(k % 2 ? leaf : shade(leaf, 0.92)));
    b.position.set((r() - 0.5) * 1.4 * s, trunkH + (0.1 + r() * 0.5) * s, (r() - 0.5) * 1.0 * s);
    b.scale.y = 0.75;
    g.add(b);
  }
  g.rotation.y = r() * 6.28;
  return g;
};

function shade(hex, f) {
  const c = new THREE.Color(hex); c.multiplyScalar(f); return "#" + c.getHexString();
}

KIT.house = (o) => {
  const w = num(o.w, 2.4), d = num(o.d, 2.4), h = num(o.h, 1.8);
  const g = new THREE.Group();
  g.add(box(w, h, d, mat(o.color || "#efe6d6"), 0, h / 2, 0));
  const roof = new THREE.Mesh(new THREE.ConeGeometry(Math.max(w, d) * 0.78, h * 0.6, 4), mat(o.roof || "#c4583a"));
  roof.position.y = h + h * 0.3; roof.rotation.y = Math.PI / 4; g.add(roof);
  g.add(box(0.5, 0.9, 0.05, mat("#5a3b2a"), 0, 0.45, d / 2 + 0.01));
  g.add(box(0.45, 0.45, 0.05, mat("#3b2a20"), w * 0.28, h * 0.6, d / 2 + 0.01));
  return g;
};

KIT.ladder = (o) => {
  const h = num(o.h, 4), w = num(o.w, 0.6), c = o.color || "#7a5232";
  const g = new THREE.Group();
  g.add(box(0.08, h, 0.08, mat(c), -w / 2, h / 2, 0));
  g.add(box(0.08, h, 0.08, mat(c), w / 2, h / 2, 0));
  for (let y = 0.3; y < h; y += 0.4) g.add(box(w, 0.06, 0.06, mat(c), 0, y, 0));
  g.rotation.x = -num(o.lean, 0.12);
  return g;
};

KIT.well = (o) => {
  // a wooden well frame with a pulley, a rope that lowers, and a bucket
  const w = num(o.w, 3.2), h = num(o.h, 3), c = o.color || "#7a5232";
  const g = new THREE.Group();
  g.add(box(0.22, h, 0.22, mat(c), -w / 2, h / 2, 0));
  g.add(box(0.22, h, 0.22, mat(c), w / 2, h / 2, 0));
  g.add(box(w + 0.6, 0.2, 0.24, mat(c), 0, h, 0));
  const wheel = new THREE.Mesh(new THREE.TorusGeometry(0.22, 0.06, 6, 12), mat("#5d3d26"));
  wheel.position.set(0, h - 0.25, 0); g.add(wheel);
  const rope = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 1, 5), mat("#d8c9a8"));
  const bucket = new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.24, 0.45, 10), mat("#8a5a36"));
  g.add(rope); g.add(bucket);
  const r0 = num(o.rope_from, 1), r1 = num(o.rope_to, r0);
  g.userData.tick = (t) => {
    const p = easeInOut(prog({ from: o.rope_start, to: o.rope_end }, t));
    const L = lerp(r0, r1, o.rope_start === undefined ? 0 : p) + Math.sin(t * 1.3) * 0.03;
    rope.scale.y = L; rope.position.set(0, h - 0.3 - L / 2, 0);
    bucket.position.set(0, h - 0.3 - L - 0.2, 0);
  };
  return g;
};

KIT.person = (o) => {
  const s = num(o.scale, 1);
  const cloth = o.cloth || "#f3efe6", skin = o.skin || "#8a5a3a", head = o.turban === false ? null : (o.turban_color || "#f3efe6");
  const g = new THREE.Group();
  const body = new THREE.Mesh(new THREE.CylinderGeometry(0.17 * s, 0.27 * s, 0.85 * s, 8), mat(cloth));
  body.position.y = 0.42 * s; g.add(body);
  const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.16 * s, 0.17 * s, 0.35 * s, 8), mat(o.top || skin));
  torso.position.y = 0.98 * s; g.add(torso);
  const hd = new THREE.Mesh(new THREE.SphereGeometry(0.15 * s, 10, 8), mat(skin));
  hd.position.y = 1.3 * s; g.add(hd);
  if (head) {
    const tb = new THREE.Mesh(new THREE.SphereGeometry(0.165 * s, 10, 6, 0, Math.PI * 2, 0, Math.PI / 2), mat(head));
    tb.position.y = 1.33 * s; g.add(tb);
  }
  const armGeo = new THREE.CylinderGeometry(0.045 * s, 0.045 * s, 0.5 * s, 5);
  armGeo.translate(0, -0.25 * s, 0);
  const la = new THREE.Mesh(armGeo, mat(skin)), ra = new THREE.Mesh(armGeo, mat(skin));
  la.position.set(-0.2 * s, 1.12 * s, 0); ra.position.set(0.2 * s, 1.12 * s, 0);
  g.add(la); g.add(ra);
  let tool = null;
  if (o.action === "dig" || o.tool === "pick") {
    tool = new THREE.Group();
    tool.add(box(0.04 * s, 0.7 * s, 0.04 * s, mat("#6b4428"), 0, -0.35 * s, 0));
    tool.add(box(0.35 * s, 0.06 * s, 0.06 * s, mat("#7b7b7b"), 0, -0.68 * s, 0));
    ra.add(tool); tool.position.y = -0.45 * s;
  }
  if (o.action === "carry") {
    const basket = new THREE.Mesh(new THREE.CylinderGeometry(0.22 * s, 0.16 * s, 0.18 * s, 10), mat("#9b6a3a"));
    basket.position.y = 1.55 * s; g.add(basket);
    la.rotation.z = Math.PI * 0.85; ra.rotation.z = -Math.PI * 0.85;
  }
  const path = (o.path || []).map((p) => vec(p));
  const ph = num(o.phase, 0);
  g.userData.tick = (t) => {
    const tt = t + ph;
    if (o.action === "dig") {
      const sw = Math.sin(tt * 6.5);
      ra.rotation.x = -1.2 + sw * 1.0; la.rotation.x = -1.0 + sw * 0.9;
      g.children[0].rotation.x = 0; g.position.y = (g.userData.y0 || 0) + Math.max(0, -sw) * 0.04 * s;
    } else if (o.action === "walk" || o.action === "carry") {
      const sw = Math.sin(tt * 7);
      if (o.action === "walk") { la.rotation.x = sw * 0.6; ra.rotation.x = -sw * 0.6; }
      g.position.y = (g.userData.y0 || 0) + Math.abs(sw) * 0.05 * s;
    } else if (o.action === "climb") {
      const sw = Math.sin(tt * 5);
      la.rotation.x = -2.6 + sw * 0.3; ra.rotation.x = -2.6 - sw * 0.3;
    } else if (o.action === "wave") {
      ra.rotation.z = -2.4 + Math.sin(tt * 6) * 0.35;
    } else if (o.action === "pull") {
      const sw = Math.sin(tt * 3);
      la.rotation.x = -2.2 + sw * 0.5; ra.rotation.x = -2.2 + sw * 0.5;
    }
    if (path.length >= 2) {
      const p = o.from !== undefined ? easeInOut(prog({ from: o.from, to: o.to }, t)) : 0;
      const segs = path.length - 1, f = p * segs, i = Math.min(segs - 1, Math.floor(f)), u = f - i;
      const a = path[i], b = path[i + 1];
      const holder = g.parent;
      if (holder) {
        holder.userData.base.set(lerp(a[0], b[0], u), lerp(a[1], b[1], u), lerp(a[2], b[2], u));
        holder.position.copy(holder.userData.base);
      }
      if (p > 0 && p < 1) g.rotation.y = Math.atan2(b[0] - a[0], b[2] - a[2]);
    }
  };
  return g;
};

// scatter helpers expand into many small objects
function scatter(o, maker, terrain) {
  const r = rng(num(o.seed, 7));
  const area = o.area || [-18, -30, 18, -2];
  const g = new THREE.Group();
  const items = [];
  for (let k = 0; k < num(o.count, 10); k++) {
    let x, z, tries = 0;
    do {
      x = lerp(area[0], area[2], r()); z = lerp(area[1], area[3], r()); tries++;
    } while (tries < 20 && terrain && (o.avoid || []).some((a) => x >= a[0] && x <= a[2] && z >= a[1] && z <= a[3]));
    const m = maker(r, x, z);
    m.position.set(x, num(o.y, 0), z);
    g.add(m); items.push(m);
  }
  g.userData.abs = true;
  // Software WebGL pays per draw call, so everything that can never be dug away is merged into one mesh per
  // material. Items standing where a dig will happen stay separate so they can disappear with the ground.
  const nearDig = (m) => terrain && terrain.digs.some((d) => m.position.x >= d.x0 - 0.6 && m.position.x <= d.x1 + 0.6 &&
                                                            m.position.z >= d.z0 - 0.6 && m.position.z <= d.z1 + 0.6);
  const keep = items.filter(nearDig), still = items.filter((m) => !nearDig(m));
  g.updateMatrixWorld(true);
  const byMat = new Map();
  for (const m of still) {
    m.traverse((c) => {
      if (!c.isMesh) return;
      let geo = c.geometry.index ? c.geometry.toNonIndexed() : c.geometry.clone();
      geo.applyMatrix4(c.matrixWorld);
      for (const k of Object.keys(geo.attributes)) if (!["position", "normal", "uv"].includes(k)) geo.deleteAttribute(k);
      if (!byMat.has(c.material)) byMat.set(c.material, []);
      byMat.get(c.material).push(geo);
    });
    g.remove(m);
  }
  for (const [m, geos] of byMat) {
    const merged = mergeGeometries(geos, false);
    if (merged) g.add(new THREE.Mesh(merged, m));
  }
  if (terrain && keep.length) g.userData.tick = (t) => { keep.forEach((m) => { m.visible = !terrain.dugAt(m.position.x, m.position.z, t); }); };
  return g;
}

KIT.trees = (o, terrain) => scatter(o, (r) => KIT.tree({ ...o, seed: Math.floor(r() * 1e6), scale: num(o.scale, 1) * (0.8 + r() * 0.45) }, r), terrain);
KIT.grass = (o, terrain) => scatter({ count: 120, ...o }, (r) => {
  const g = new THREE.Group();
  const c = o.color || "#9aa65a";
  for (let k = 0; k < 4; k++) {
    const b = new THREE.Mesh(new THREE.ConeGeometry(0.04, 0.35 + r() * 0.25, 3), mat(k % 2 ? c : shade(c, 0.85)));
    b.position.set((r() - 0.5) * 0.25, 0.18, (r() - 0.5) * 0.25); b.rotation.z = (r() - 0.5) * 0.5;
    g.add(b);
  }
  return g;
}, terrain);
KIT.rocks = (o, terrain) => scatter({ count: 40, ...o }, (r) => {
  const m = new THREE.Mesh(new THREE.DodecahedronGeometry(0.12 + r() * 0.15, 0), mat(o.color || "#8f7a64"));
  m.scale.y = 0.6; m.rotation.set(r(), r(), r());
  return m;
}, terrain);
KIT.people = (o) => {
  const r = rng(num(o.seed, 9));
  const g = new THREE.Group();
  const area = o.area || [-3, -3, 3, 3];
  const cloths = o.cloths || ["#f3efe6", "#e7c36b", "#d9774b", "#f3efe6", "#c9d6e3"];
  for (let k = 0; k < num(o.count, 6); k++) {
    const p = KIT.person({ ...o, cloth: cloths[k % cloths.length], phase: r() * 3, path: undefined });
    const h = new THREE.Group(); h.add(p);
    h.position.set(lerp(area[0], area[2], r()), num(o.y, 0), lerp(area[1], area[3], r()));
    h.rotation.y = r() * 6.28;
    g.add(h);
  }
  g.userData.ticks = g.children.map((h) => h.children[0].userData.tick);
  g.userData.tick = (t) => g.userData.ticks.forEach((f) => f && f(t));
  return g;
};

// ------------------------------------------------------------------ camera
function makeCamera(keys, W, H) {
  const cam = new THREE.PerspectiveCamera(35, W / H, 0.1, 400);
  const ks = (keys && keys.length ? keys : [{ at: 0, pos: [22, 16, 26], look: [0, -2, -8] }])
    .map((k) => ({ at: num(k.at, 0), pos: new THREE.Vector3(...vec(k.pos, [20, 14, 24])), look: new THREE.Vector3(...vec(k.look, [0, -2, -8])),
                   fov: num(k.fov, 35), ease: k.ease || "inout" }))
    .sort((a, b) => a.at - b.at);
  const posCurve = ks.length > 1 ? new THREE.CatmullRomCurve3(ks.map((k) => k.pos), false, "centripetal") : null;
  const lookCurve = ks.length > 1 ? new THREE.CatmullRomCurve3(ks.map((k) => k.look), false, "centripetal") : null;
  const tmp = new THREE.Vector3(), tmpL = new THREE.Vector3();
  return {
    cam,
    update(t) {
      let i = 0;
      while (i < ks.length - 1 && t > ks[i + 1].at) i++;
      let s, fov;
      if (ks.length === 1 || t <= ks[0].at) { s = 0; fov = ks[0].fov; tmp.copy(ks[0].pos); tmpL.copy(ks[0].look); }
      else if (i >= ks.length - 1) { s = 1; fov = ks[ks.length - 1].fov; tmp.copy(ks[ks.length - 1].pos); tmpL.copy(ks[ks.length - 1].look); }
      else {
        const a = ks[i], b = ks[i + 1];
        let u = clamp((t - a.at) / Math.max(1e-6, b.at - a.at));
        u = b.ease === "linear" ? u : easeInOut(u);
        s = (i + u) / (ks.length - 1);
        posCurve.getPoint(s, tmp); lookCurve.getPoint(s, tmpL);
        fov = lerp(a.fov, b.fov, u);
      }
      // a gentle handheld drift so held shots never freeze
      tmp.x += Math.sin(t * 0.45) * 0.12; tmp.y += Math.sin(t * 0.37 + 1) * 0.08;
      cam.position.copy(tmp); cam.lookAt(tmpL);
      if (cam.fov !== fov) { cam.fov = fov; cam.updateProjectionMatrix(); }
    },
  };
}

// ------------------------------------------------------------------ world
let R = null, SCENE = null, CAM = null, TERRAIN = null, ITEMS = [], QUALITY = 0.9;

function setup(world, opts = {}) {
  const W = Math.round(num(opts.width, 1080)), H = Math.round(num(opts.height, 1920));
  QUALITY = num(opts.quality, 0.9);
  const canvas = document.getElementById("c");
  if (!R) {
    R = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
    R.shadowMap.enabled = true;
    R.shadowMap.type = THREE.PCFShadowMap;
    R.outputColorSpace = THREE.SRGBColorSpace;
    R.toneMapping = THREE.NeutralToneMapping;
  }
  R.setPixelRatio(1);
  R.setSize(W, H, false);
  const style = { ...STYLES[world.style] || STYLES.desert, ...(world.style_overrides || {}) };
  SCENE = new THREE.Scene();
  SCENE.background = new THREE.Color(style.sky);
  if (style.fog) SCENE.fog = new THREE.Fog(style.sky, style.fog[0], style.fog[1]);
  SCENE.add(new THREE.HemisphereLight(style.hemiSky, style.hemiGround, style.hemiI));
  SCENE.add(new THREE.AmbientLight("#ffffff", num(style.ambient, 0.45)));   // lifts the shade inside deep pits
  const sun = new THREE.DirectionalLight(style.sunColor, style.sunI);
  sun.position.set(...style.sun);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  const ext = num((world.terrain || {}).width, 40) * 0.75;
  Object.assign(sun.shadow.camera, { left: -ext, right: ext, top: ext, bottom: -ext, near: 1, far: 140 });
  sun.shadow.bias = -0.0006;
  sun.shadow.normalBias = 0.02;
  sun.target.position.set(0, -2, -10);
  SCENE.add(sun); SCENE.add(sun.target);

  TERRAIN = null; ITEMS = [];
  if (world.terrain !== false) {
    TERRAIN = makeTerrain(world.terrain || {}, style);
    SCENE.add(TERRAIN.group); SCENE.add(TERRAIN.aprons);
  }
  for (const o of world.objects || []) {
    const make = KIT[o.type];
    if (!make) { console.warn("world3d: unknown object type " + o.type); continue; }
    const inner = make(o, TERRAIN);
    shadow(inner, o.cast !== false, true);
    const holder = new THREE.Group();
    holder.add(inner);
    const p = inner.userData.abs ? [0, 0, 0] : vec(o.pos || [o.x, o.y, o.z], [0, 0, 0]);
    holder.userData.base = new THREE.Vector3(...p);
    holder.position.copy(holder.userData.base);
    holder.rotation.y = num(o.rot, 0) * Math.PI / 180;
    if (inner.userData.stagger) holder.userData.stagger = inner.userData.stagger;
    SCENE.add(holder);
    ITEMS.push({ o, holder, inner });
  }
  CAM = makeCamera(world.camera, W, H);
  return { objects: ITEMS.length, width: W, height: H };
}

function update(t) {
  if (TERRAIN) TERRAIN.update(t);
  for (const it of ITEMS) {
    applyBuild(it.holder, it.o, t);
    if (it.inner.userData.tick) it.inner.userData.tick(t);
  }
  CAM.update(t);
}

function frame(t, type = "image/jpeg") {
  update(t);
  R.render(SCENE, CAM.cam);
  return R.domElement.toDataURL(type, QUALITY);
}

export const VF = { setup, frame, kit: Object.keys(KIT), styles: Object.keys(STYLES) };
