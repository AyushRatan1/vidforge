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
  if (o.texture !== "stone") return mat(color);
  if (Array.isArray(o.block)) return stoneMat(color, w / (4 * num(o.block[0], 1.2)), h / (4 * num(o.block[1], 0.6)));   // block [w, h]
  return stoneMat(color, w / 2.2, h / 1.1);
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

// ------------------------------------------------------------------ geometry helpers
// Software WebGL pays per draw call, so composite objects merge their static meshes into one mesh per material.
// With `rebase` the merged part's origin moves to the bottom of its bounds, so "rise" and stagger grow it from its base.
const KEEP_ATTRS = new Set(["position", "normal", "uv", "color"]);
function merged(root, rebase = true) {
  root.updateMatrixWorld(true);
  const inv = root.matrixWorld.clone().invert();
  const byMat = new Map();
  let minY = Infinity;
  root.traverse((c) => {
    if (!c.isMesh) return;
    const geo = c.geometry.index ? c.geometry.toNonIndexed() : c.geometry.clone();
    geo.applyMatrix4(new THREE.Matrix4().multiplyMatrices(inv, c.matrixWorld));
    for (const k of Object.keys(geo.attributes)) if (!KEEP_ATTRS.has(k)) geo.deleteAttribute(k);
    if (!geo.attributes.uv) geo.setAttribute("uv", new THREE.Float32BufferAttribute(new Float32Array(geo.attributes.position.count * 2), 2));
    if (!geo.attributes.normal) geo.computeVertexNormals();
    geo.computeBoundingBox();
    minY = Math.min(minY, geo.boundingBox.min.y);
    if (!byMat.has(c.material)) byMat.set(c.material, []);
    byMat.get(c.material).push(geo);
  });
  const out = new THREE.Group();
  if (!isFinite(minY)) return out;
  const dy = rebase ? minY : 0;
  for (const [m, geos] of byMat) {
    const g = mergeGeometries(geos, false);
    if (!g) continue;
    if (dy) g.translate(0, -dy, 0);
    out.add(new THREE.Mesh(g, m));
  }
  out.position.y = dy;
  return out;
}

const tint = (hex, f = 1) => { const c = new THREE.Color(hex); if (f !== 1) c.multiplyScalar(f); return c; };

// A flat-shaded, vertex-coloured triangle soup: a whole rock, ramp or road becomes one mesh and one draw call.
// `out` is the direction the face should look; the winding is fixed to match so nothing is culled by mistake.
class Soup {
  constructor() { this.pos = []; this.col = []; }
  tri(a, b, c, color, out) {
    if (out) {
      const ux = b[0] - a[0], uy = b[1] - a[1], uz = b[2] - a[2], vx = c[0] - a[0], vy = c[1] - a[1], vz = c[2] - a[2];
      const nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
      if (nx * out[0] + ny * out[1] + nz * out[2] < 0) { const t = b; b = c; c = t; }
    }
    this.pos.push(a[0], a[1], a[2], b[0], b[1], b[2], c[0], c[1], c[2]);
    for (let i = 0; i < 3; i++) this.col.push(color.r, color.g, color.b);
  }
  quad(a, b, c, d, color, out) { this.tri(a, b, c, color, out); this.tri(a, c, d, color, out); }
  geometry(geo, matrix, color) {          // append a ready-made geometry (already wound correctly)
    const g = (geo.index ? geo.toNonIndexed() : geo.clone()).applyMatrix4(matrix);
    const p = g.attributes.position.array;
    for (let i = 0; i < p.length; i += 9) {
      this.pos.push(p[i], p[i + 1], p[i + 2], p[i + 3], p[i + 4], p[i + 5], p[i + 6], p[i + 7], p[i + 8]);
      const c = typeof color === "function" ? color(i / 9) : color;
      for (let k = 0; k < 3; k++) this.col.push(c.r, c.g, c.b);
    }
  }
  mesh() {
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(this.pos, 3));
    g.setAttribute("color", new THREE.Float32BufferAttribute(this.col, 3));
    g.setAttribute("uv", new THREE.Float32BufferAttribute(new Float32Array((this.pos.length / 3) * 2), 2));
    g.computeVertexNormals();
    return new THREE.Mesh(g, mat("#ffffff", { vertexColors: true }));
  }
}

// an arched opening (round or pointed) standing on y=0, centred on x=0, facing +z
function archShape(w, h, pointed = false) {
  const s = new THREE.Shape(), r = w / 2;
  if (pointed) {
    const spring = Math.max(0.02, h - r * 1.25);
    s.moveTo(-r, 0); s.lineTo(-r, spring);
    s.quadraticCurveTo(-r, spring + r * 0.95, 0, spring + r * 1.25);
    s.quadraticCurveTo(r, spring + r * 0.95, r, spring);
    s.lineTo(r, 0); s.lineTo(-r, 0);
  } else {
    const spring = Math.max(0.02, h - r);
    s.moveTo(-r, 0); s.lineTo(-r, spring);
    s.absarc(0, spring, r, Math.PI, 0, true);
    s.lineTo(r, 0); s.lineTo(-r, 0);
  }
  return s;
}
function archMesh(w, h, color, pointed = true) {
  return new THREE.Mesh(new THREE.ShapeGeometry(archShape(w, h, pointed), 5), mat(color));
}

// a small domed kiosk (chhatri): four posts, a slab and a dome
function chhatri(g, x, y, z, r, light, dark) {
  const ph = r * 1.5;
  for (const [sx, sz] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) g.add(box(r * 0.2, ph, r * 0.2, mat(light), x + sx * r * 0.72, y + ph / 2, z + sz * r * 0.72));
  g.add(box(r * 2.0, r * 0.2, r * 2.0, mat(dark), x, y + ph + r * 0.1, z));
  const dm = new THREE.Mesh(new THREE.SphereGeometry(r * 0.88, 10, 5, 0, Math.PI * 2, 0, Math.PI / 2), mat(light));
  dm.position.set(x, y + ph + r * 0.2, z); g.add(dm);
  const fin = new THREE.Mesh(new THREE.ConeGeometry(r * 0.12, r * 0.6, 6), mat("#c9a24a"));
  fin.position.set(x, y + ph + r * 0.2 + r * 0.88 + r * 0.25, z); g.add(fin);
}

// ------------------------------------------------------------------ styles
const STYLES = {
  desert: { sky: "#dccfb6", fog: [40, 120], ground: "#d9bf8f", sun: [14, 22, 10], sunColor: "#fff1d8", sunI: 2.1,
            hemiSky: "#fff4e2", hemiGround: "#7a5536", hemiI: 1.25,
            strata: [["#d9bf8f", 0.35], ["#b98a5c", 1.6], ["#8c5f3e", 2.6], ["#6f4a31", 3.2], ["#5a3c28", 14]],
            rock: ["#a56f4b", "#8f5f40", "#b5815a", "#7f5439", "#9a6847"], rockTop: "#c09a6c" },
  golden: { sky: "#e8c9a0", fog: [35, 110], ground: "#d7b07a", sun: [-16, 12, 8], sunColor: "#ffd9a8", sunI: 2.3,
            hemiSky: "#ffe6c7", hemiGround: "#6b4630", hemiI: 1.1,
            strata: [["#d7b07a", 0.35], ["#b07d50", 1.6], ["#875a3a", 2.6], ["#6b452e", 3.2], ["#563824", 14]],
            rock: ["#a86d47", "#925d3c", "#ba7f55", "#83543a", "#9c6644"], rockTop: "#c49a66" },
  green: { sky: "#cfe0e6", fog: [45, 130], ground: "#8db35c", sun: [12, 22, 10], sunColor: "#fffaf0", sunI: 2.0,
           hemiSky: "#f2fbff", hemiGround: "#5a4a32", hemiI: 1.3,
           strata: [["#8db35c", 0.3], ["#8a6a45", 1.6], ["#6f5236", 2.6], ["#5b4330", 3.2], ["#4a3627", 14]],
           rock: ["#8e877a", "#7a7469", "#9e978b", "#6c675e", "#857e72"], rockTop: "#86a95a" },
  overcast: { sky: "#c9ccd1", fog: [35, 110], ground: "#b9b2a2", sun: [10, 24, 6], sunColor: "#f4f4f4", sunI: 1.4,
              hemiSky: "#f0f2f5", hemiGround: "#6d6559", hemiI: 1.5,
              strata: [["#b9b2a2", 0.35], ["#9a8c76", 1.6], ["#7b6d5a", 2.6], ["#62574a", 3.2], ["#4f463c", 14]],
              rock: ["#8f877b", "#7d766b", "#a0988c", "#6f695f", "#878074"], rockTop: "#a59e8e" },
  night: { sky: "#141a2b", fog: [30, 90], ground: "#4a4a55", sun: [-8, 18, 6], sunColor: "#aebbe0", sunI: 1.0,
           hemiSky: "#5b6a92", hemiGround: "#1d1d24", hemiI: 0.9,
           strata: [["#4a4a55", 0.35], ["#3d3a40", 1.6], ["#332f35", 2.6], ["#2a272c", 3.2], ["#221f24", 14]],
           rock: ["#4a4650", "#403c46", "#56525c", "#38353d", "#46424c"], rockTop: "#55535e" },
};
let STYLE = STYLES.desert;

// ------------------------------------------------------------------ build animation wrapper
// Every object sits in a holder group. `build` animates its appearance, `hide` its removal.
function applyBuild(holder, o, t) {
  const b = o.build;
  let visible = true;
  if (o.hide && num(o.hide.at, Infinity) <= t) {
    // hide ops: "shrink" (default, scale to nothing), "lower" (flatten into the ground), "sink" (slide down)
    const p = clamp((t - o.hide.at) / Math.max(0.05, num(o.hide.dur, 0.4)));
    if (p >= 1) { holder.visible = false; return; }
    holder.position.copy(holder.userData.base);
    const hop = o.hide.op || "shrink";
    if (hop === "lower") holder.scale.set(1, Math.max(0.001, 1 - easeInOut(p)), 1);
    else if (hop === "sink") { holder.scale.set(1, 1, 1); holder.position.y -= easeInOut(p) * num(o.hide.depth, 4); }
    else holder.scale.setScalar(Math.max(0.001, 1 - easeInOut(p)));
    if (holder.userData.stagger) holder.userData.stagger(1);
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
  if (op === "rise" || (op === "stagger" && !holder.userData.stagger)) holder.scale.y = Math.max(0.001, easeOut(p));
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
  let last = null;     // not "": a terrain without digs has an empty signature and must still be built once

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
  if (o.crenels) {   // merlons along the top, laid last
    const cg = new THREE.Group(), n = Math.max(2, Math.floor(len / 0.85)), mm = mat(o.color || "#e2d6c2");
    for (let k = 0; k < n; k++) cg.add(box(0.44, 0.42, th * 0.9, mm, -len / 2 + ((k + 0.5) * len) / n, h + 0.21, 0));
    const crown = merged(cg);
    g.add(crown); parts.push(crown);
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

// ------------------------------------------------------------------ landforms and monuments
// Fallback outline when Python did not supply one (it normally does, so walls and paths can follow it).
function genOutline(o) {
  const r = rng(num(o.seed, 5)), n = Math.max(5, Math.round(num(o.sides, 11)));
  const rx = num(o.w, 2 * num(o.r, 9)) / 2, rz = num(o.d, 2 * num(o.r, 9)) / 2, jag = num(o.jag, 0.16);
  const p1 = r() * 6.28, p2 = r() * 6.28, pts = [];
  for (let i = 0; i < n; i++) {
    const a = (i / n) * Math.PI * 2 + (r() - 0.5) * 0.5 * (Math.PI * 2 / n);
    const f = 1 + jag * (0.35 * Math.sin(2 * a + p1) + 0.25 * Math.sin(3 * a + p2) + (r() - 0.5) * 0.6);
    pts.push([Math.sin(a) * rx * f, Math.cos(a) * rz * f]);
  }
  return pts;
}

// a road on the cliff: deck, retaining skirt and a low parapet on the drop side; `bleed` pushes the uphill edge into the rock
function roadRibbon(soup, pts, w, bleed, cols) {
  const n = pts.length;
  if (n < 2) return;
  const tan = (i) => {
    const a = pts[Math.max(0, i - 1)], b = pts[Math.min(n - 1, i + 1)];
    const dx = b[0] - a[0], dz = b[2] - a[2], L = Math.hypot(dx, dz) || 1;
    return [dx / L, dz / L];
  };
  const mi = Math.floor((n - 1) / 2), tm = tan(mi);
  const sign = (tm[1] * -pts[mi][0] + -tm[0] * -pts[mi][2]) >= 0 ? 1 : -1;   // which perpendicular points at the hill centre
  const E = pts.map((p, i) => {
    const t = tan(i), inx = sign * t[1], inz = -sign * t[0];
    const dy = Math.min(p[1] + 0.02, 0.75);
    const ib = w / 2 + (bleed ? num(bleed, 0) : 0);
    return { p, inx, inz, dy,
      i: [p[0] + inx * ib, p[1], p[2] + inz * ib], o: [p[0] - inx * w / 2, p[1], p[2] - inz * w / 2] };
  });
  const down = (v, d) => [v[0], v[1] - d, v[2]], up = (v, d) => [v[0], v[1] + d, v[2]];
  const inset = (v, e, d) => [v[0] + e.inx * d, v[1], v[2] + e.inz * d];
  for (let k = 0; k < n - 1; k++) {
    const a = E[k], b = E[k + 1];
    const outN = [-a.inx, 0, -a.inz], inN = [a.inx, 0, a.inz];
    soup.quad(a.i, a.o, b.o, b.i, cols.road, [0, 1, 0]);
    soup.quad(a.o, b.o, down(b.o, b.dy), down(a.o, a.dy), cols.skirt, outN);
    soup.quad(a.i, b.i, down(b.i, b.dy), down(a.i, a.dy), cols.skirt, inN);
    if (bleed) {   // parapet on the drop side
      const ph = 0.3, pa = inset(a.o, a, 0.16), pb = inset(b.o, b, 0.16);
      soup.quad(a.o, b.o, up(b.o, ph), up(a.o, ph), cols.parapet, outN);
      soup.quad(up(a.o, ph), up(b.o, ph), up(pb, ph), up(pa, ph), cols.parapet, [0, 1, 0]);
      soup.quad(pa, pb, up(pb, ph), up(pa, ph), cols.parapet, inN);
    }
  }
}

function roadPad(soup, p, rad, cols) {
  const dy = Math.min(p[1] + 0.02, 0.75), ring = [];
  for (let k = 0; k < 8; k++) { const a = (k / 8) * Math.PI * 2 + Math.PI / 8; ring.push([p[0] + Math.sin(a) * rad, p[1], p[2] + Math.cos(a) * rad]); }
  for (let k = 0; k < 8; k++) {
    const a = ring[k], b = ring[(k + 1) % 8];
    soup.tri(p, a, b, cols.road, [0, 1, 0]);
    const mx = (a[0] + b[0]) / 2 - p[0], mz = (a[2] + b[2]) / 2 - p[2];
    soup.quad(a, b, [b[0], b[1] - dy, b[2]], [a[0], a[1] - dy, a[2]], cols.skirt, [mx, 0, mz]);
  }
}

// hill / cliff: a faceted rock plateau. A talus apron at the foot, near-vertical jagged faces in rock strata with
// gullies, buttresses that end in flat ledges at different heights, scree, a flat top at height h for buildings, and
// an optional road winding up (computed in Python). The rim is exactly the outline so walls can sit on it.
const HILL_BULGE = 0.07;    // largest outward bulge of a buttress (fraction of radius); none on the road side
KIT.hill = (o) => {
  const h = num(o.h, 8), batter = num(o.batter, 0.14), talus = num(o.talus, 0.12), r = rng(num(o.seed, 5) * 7 + 1);
  const outline = Array.isArray(o.outline) && o.outline.length >= 3 ? o.outline.map((p) => [num(p[0], 0), num(p[1], 0)]) : genOutline(o);
  const rockHex = Array.isArray(o.colors) && o.colors.length ? o.colors : STYLE.rock;
  const rock = rockHex.map((c) => new THREE.Color(c));
  const top = new THREE.Color(o.top || STYLE.rockTop);
  const ledge = top.clone().lerp(rock[0], 0.35);
  const scree = new THREE.Color(STYLE.ground).lerp(rock[0], 0.55);
  const jag = num(o.jag, 0.06), th = h * 0.15;
  const sAt = (y) => 1 + batter * Math.pow(Math.max(0, 1 - y / h), 1.3);
  // columns: facets about 1.4 m wide along the outline, some cut back as gullies
  const cols = [];
  outline.forEach((a, i) => {
    const b = outline[(i + 1) % outline.length];
    const m = Math.max(1, Math.round(Math.hypot(b[0] - a[0], b[1] - a[1]) / num(o.facet, 1.4)));
    for (let j = 0; j < m; j++) {
      const gully = r() < 0.16;
      cols.push({ x: lerp(a[0], b[0], j / m), z: lerp(a[1], b[1], j / m), d: (j === 0 ? 0.4 : 1) * jag * (gully ? 1.9 : 0.2 + 0.8 * r()), gully });
    }
  });
  const C = cols.length;
  // ring heights from the top of the talus to the rim
  const K = Math.max(3, Math.round((h - th) / num(o.band, 1.15)));
  const ys = [];
  for (let k = 0; k <= K; k++) ys.push(th + ((h - th) * k) / K + (k > 0 && k < K ? (r() - 0.5) * ((h - th) / K) * 0.45 : 0));
  // buttresses: an arc of columns stands proud from the foot up to a ledge at ring kTop
  const events = [];
  const nE = 3 + Math.round(K * 0.9);
  for (let e = 0; e < nE; e++) {
    events.push({ k: 1 + Math.floor(r() * (K - 1)), j0: Math.floor(r() * C), n: Math.max(2, Math.round(C * (0.12 + 0.3 * r()))), a: 0.022 + 0.028 * r() });
  }
  // the road side stays free of buttresses so the road (computed in Python against the outline) hugs the face
  const road = o.path && typeof o.path === "object" ? o.path : null;
  const roadAng = [];
  if (road) for (const rb of road.ribbons || []) for (const p of rb.pts || []) roadAng.push(Math.atan2(num(p[0], 0), num(p[2], 0)));
  const nearRoad = cols.map((c) => { const a = Math.atan2(c.x, c.z); return roadAng.some((b) => Math.abs(Math.atan2(Math.sin(a - b), Math.cos(a - b))) < 0.22); });
  const bulge = (j, k, withTopOf) => {   // outward bulge of column j at ring k (events ending at k count only if withTopOf)
    if (nearRoad[j]) return 0;
    let s = 0;
    for (const e of events) {
      const dj = (j - e.j0 + C) % C;
      if (dj >= e.n) continue;
      if (k < e.k || (k === e.k && withTopOf)) s += e.a * (dj === 0 || dj === e.n - 1 ? 0.6 : 1);
    }
    return Math.min(HILL_BULGE, s);
  };
  const wander = cols.map(() => 0);
  const dipA = r() * Math.PI * 2, dip = num(o.dip, 0.09) * (h - th) / K, R0 = outline.reduce((s0, p) => s0 + Math.hypot(p[0], p[1]), 0) / outline.length;
  const ringAt = (k, withTop) => cols.map((c, j) => {
    const rim = k === K;
    const f = sAt(ys[k]) * (rim ? 1 : 1 - c.d - wander[j] + bulge(j, k, withTop));
    const y = rim || k === 0 ? ys[k] : ys[k] + dip * K * 0.5 * ((c.x * Math.cos(dipA) + c.z * Math.sin(dipA)) / R0);
    return [c.x * f, Math.min(h - 0.15, Math.max(th * 0.6, y)), c.z * f];
  });
  const rings = [];
  for (let k = 0; k <= K; k++) {
    if (k > 0 && k < K) cols.forEach((c, j) => { wander[j] = clamp(wander[j] + (r() - 0.5) * 0.03, 0, 0.05); });
    const hasLedge = k < K && events.some((e) => e.k === k);
    rings.push({ y: ys[k], k, v: ringAt(k, true) });
    if (hasLedge) rings.push({ y: ys[k], k, v: ringAt(k, false), ledge: true });
  }
  const soup = new Soup();
  // talus: from a wider footprint on the ground up to the foot of the cliff
  const foot = rings[0].v.map((p, j) => { const c = cols[j], f = sAt(0) + talus * (0.8 + 0.4 * r()); return [c.x * f, 0, c.z * f]; });
  for (let j = 0; j < C; j++) {
    const j2 = (j + 1) % C, a = foot[j], b = foot[j2], c = rings[0].v[j2], d = rings[0].v[j];
    soup.quad(a, b, c, d, scree.clone().multiplyScalar(0.9 + r() * 0.16), [(a[0] + b[0]) / 2, 0.6, (a[2] + b[2]) / 2]);
  }
  const coff = Math.floor(r() * rock.length);
  for (let i = 0; i < rings.length - 1; i++) {
    const A = rings[i], B = rings[i + 1], flat = Math.abs(B.y - A.y) < 1e-4;
    const band = rock[(A.k + coff) % rock.length];
    for (let j = 0; j < C; j++) {
      const j2 = (j + 1) % C;
      const a = A.v[j], b = A.v[j2], c = B.v[j2], d = B.v[j];
      if (flat) {
        if (Math.hypot(a[0] - d[0], a[2] - d[2]) + Math.hypot(b[0] - c[0], b[2] - c[2]) < 0.02) continue;
        soup.quad(a, b, c, d, ledge.clone().multiplyScalar(0.92 + r() * 0.12), [0, 1, 0]);
      } else {
        const f = (cols[j].gully ? 0.8 : 0.9) + r() * 0.16;
        soup.quad(a, b, c, d, band.clone().multiplyScalar(f), [(a[0] + b[0]) / 2, 0, (a[2] + b[2]) / 2]);
      }
    }
  }
  const rim = rings[rings.length - 1].v, cen = [0, h, 0];
  for (let j = 0; j < C; j++) soup.tri(cen, rim[j], rim[(j + 1) % C], top.clone().multiplyScalar(0.98 + r() * 0.03), [0, 1, 0]);
  // the road, its landings, then scree that keeps clear of the road
  const rcols = { road: tint(o.road || "#bf9a70"), skirt: tint(o.road_wall || "#a97d55"), parapet: tint(o.road_wall || "#a97d55", 1.1) };
  const roadPts = [];
  const meanR = outline.reduce((s0, p) => s0 + Math.hypot(p[0], p[1]), 0) / outline.length;
  if (road) {
    const w = num(road.width, 1.6);
    for (const rb of road.ribbons || []) {
      const pts = (rb.pts || []).map((p) => vec(p));
      roadRibbon(soup, pts, w, rb.bleed === false ? 0 : num(road.bleed, meanR * jag * 1.2 + 0.3), rcols);
      pts.forEach((p) => roadPts.push(p));
    }
    for (const p of road.pads || []) roadPad(soup, vec(p), w * 0.85, rcols);
  }
  const nScree = Math.round(num(o.scree, C * 1.2));
  const dark = rock.map((c) => c.clone().multiplyScalar(0.85));
  for (let k = 0; k < nScree; k++) {
    const j = Math.floor(r() * C), c = foot[j], L = Math.hypot(c[0], c[2]) || 1;
    const rad = 0.16 + r() * r() * 0.7, out = r() * 1.1 - 0.2;
    const x = c[0] + (c[0] / L) * out, z = c[2] + (c[2] / L) * out;
    if (roadPts.some((p) => p[1] < 2.2 && Math.hypot(p[0] - x, p[2] - z) < num(road && road.width, 1.6) + rad + 0.4)) continue;
    const m4 = new THREE.Matrix4().compose(new THREE.Vector3(x, rad * 0.15, z),
      new THREE.Quaternion().setFromEuler(new THREE.Euler(r() * 3, r() * 3, r() * 3)), new THREE.Vector3(1, 0.62, 1));
    const col = dark[Math.floor(r() * dark.length)];
    soup.geometry(new THREE.DodecahedronGeometry(rad, 0), m4, () => col.clone().multiplyScalar(0.9 + r() * 0.2));
  }
  return soup.mesh();
};
KIT.cliff = (o) => KIT.hill({ batter: 0.06, jag: 0.09, ...o });

// frustum: a square frustum (w at the base, w_top at the top; w_top 0 makes a pyramid) with per-face baked shading
// [front +z, right +x, back -z, left -x], so neighbouring faces never merge into one flat shape in strong light
KIT.frustum = (o) => {
  const w = num(o.w, 4), d = num(o.d, w), wt = num(o.w_top, w * 0.5), dt = num(o.d_top, d * (wt / (w || 1))), h = num(o.h, 2);
  const sh = Array.isArray(o.shade) ? o.shade.map((v) => num(v, 1)) : [0.8, 1.0, 0.7, 0.74];
  const c = tint(o.color || "#e6d6b8"), soup = new Soup();
  const B = [[-w / 2, 0, d / 2], [w / 2, 0, d / 2], [w / 2, 0, -d / 2], [-w / 2, 0, -d / 2]];
  const T = [[-wt / 2, h, dt / 2], [wt / 2, h, dt / 2], [wt / 2, h, -dt / 2], [-wt / 2, h, -dt / 2]];
  const outs = [[0, 0.3, 1], [1, 0.3, 0], [0, 0.3, -1], [-1, 0.3, 0]];
  for (let f = 0; f < 4; f++) {
    const a = B[f], b = B[(f + 1) % 4], cc = T[(f + 1) % 4], dd = T[f], col = c.clone().multiplyScalar(sh[f]);
    if (wt > 1e-4 || dt > 1e-4) soup.quad(a, b, cc, dd, col, outs[f]); else soup.tri(a, b, [0, h, 0], col, outs[f]);
  }
  if (wt > 1e-4 && o.cap !== false) soup.quad(T[0], T[1], T[2], T[3], c, [0, 1, 0]);
  return soup.mesh();
};

// ramp: a sloped embankment from `from` to `to` (points, relative to pos), `width` wide, solid down to `base`
KIT.ramp = (o) => {
  const a = vec(o.from, [0, 0, 0]), b = vec(o.to, [0, 3, 8]);
  const w = num(o.width, 3), base = num(o.base, Math.min(a[1], b[1])), hw = w / 2;
  const dx = b[0] - a[0], dz = b[2] - a[2], L = Math.hypot(dx, dz) || 1;
  const n = Math.max(2, Math.round(num(o.segments, L / 1.6)));
  const topC = tint(o.color || "#c4a075"), sideC = topC.clone().multiplyScalar(0.8);
  const stag = !!(o.build && (o.build.op === "stagger" || o.build.stagger));
  const g = new THREE.Group(), parts = [];
  let soup = new Soup();
  for (let k = 0; k < n; k++) {
    if (stag) soup = new Soup();
    const z0 = (L * k) / n, z1 = (L * (k + 1)) / n;
    const y0 = lerp(a[1], b[1], k / n) - base, y1 = lerp(a[1], b[1], (k + 1) / n) - base;
    const f = k % 2 ? 0.95 : 1, tc = topC.clone().multiplyScalar(f), sc = sideC.clone().multiplyScalar(f);
    soup.quad([-hw, y0, z0], [hw, y0, z0], [hw, y1, z1], [-hw, y1, z1], tc, [0, 1, 0]);
    soup.quad([hw, 0, z0], [hw, 0, z1], [hw, y1, z1], [hw, y0, z0], sc, [1, 0, 0]);
    soup.quad([-hw, 0, z0], [-hw, 0, z1], [-hw, y1, z1], [-hw, y0, z0], sc, [-1, 0, 0]);
    if (stag || k === 0) soup.quad([-hw, 0, z0], [hw, 0, z0], [hw, y0, z0], [-hw, y0, z0], sc, [0, 0, -1]);
    if (stag || k === n - 1) soup.quad([-hw, 0, z1], [hw, 0, z1], [hw, y1, z1], [-hw, y1, z1], sc, [0, 0, 1]);
    if (stag) { const m = soup.mesh(); m.position.y = base; g.add(m); parts.push(m); }
  }
  if (!stag) { const m = soup.mesh(); m.position.y = base; g.add(m); }
  g.position.set(a[0], 0, a[2]);
  g.rotation.y = Math.atan2(dx, dz);
  const outer = new THREE.Group(); outer.add(g);
  if (stag) outer.userData.stagger = staggerParts(parts, "rise");
  return outer;
};

// blocks: a grid of cut stone blocks (cols along x, rows along z, layers up); stagger drops them in one by one
KIT.blocks = (o) => {
  const sz = Array.isArray(o.size) ? vec(o.size, [1.2, 0.8, 0.9]) : [num(o.bw, 1.2), num(o.bh, 0.8), num(o.bd, 0.9)];
  let cols = Math.max(1, Math.round(num(o.cols, 4))), rows = Math.max(1, Math.round(num(o.rows, 2))), layers = Math.max(1, Math.round(num(o.layers, 1)));
  if (o.count !== undefined && o.cols === undefined) { cols = Math.max(1, Math.round(num(o.count, 4))); rows = 1; layers = 1; }
  const gap = num(o.gap, 0.14), c = o.color || "#d8c49c", r = rng(num(o.seed, 3));
  const shades = [mat(c), mat(shade(c, 0.92)), mat(shade(c, 1.05))];
  const g = new THREE.Group(), parts = [];
  for (let l = 0; l < layers; l++) for (let j = 0; j < rows; j++) for (let i = 0; i < cols; i++) {
    const m = box(sz[0], sz[1], sz[2], shades[Math.floor(r() * 3)],
      (i - (cols - 1) / 2) * (sz[0] + gap), l * (sz[1] + 0.02) + sz[1] / 2, (j - (rows - 1) / 2) * (sz[2] + gap));
    g.add(m); parts.push(m);
  }
  if (!(o.build && (o.build.op === "stagger" || o.build.stagger))) return merged(g, false);
  g.userData.stagger = staggerParts(parts, "drop");
  return g;
};

// sledge: a wooden sledge carrying one block (give it a path to haul it)
KIT.sledge = (o) => {
  const w = num(o.w, 1.1), h = num(o.h, 0.8), d = num(o.d, 1.5), wood = o.wood || "#7a5232";
  const g = new THREE.Group();
  for (const sx of [-1, 1]) g.add(box(0.12, 0.14, d + 0.7, mat(wood), sx * w * 0.36, 0.07, 0.15));
  for (let k = 0; k < 3; k++) g.add(box(w * 0.95, 0.06, 0.14, mat(shade(wood, 1.1)), 0, 0.16, -d / 2 + (k * d) / 2));
  g.add(box(w, h, d, mat(o.color || "#d8c49c"), 0, 0.19 + h / 2, 0));
  return merged(g, false);
};

// boat: a Nile-style barge; `cargo` true or {w,h,d,color} puts a block on deck, `sail` adds a mast and sail
KIT.boat = (o) => {
  const L = num(o.length, 7), w = num(o.w, 2.2), hh = num(o.h, 0.7), wood = o.color || "#8a5a36";
  const s = new THREE.Shape();
  s.moveTo(-L / 2, hh * 1.35); s.lineTo(-L / 2 + L * 0.16, 0); s.lineTo(L / 2 - L * 0.16, 0);
  s.lineTo(L / 2, hh * 1.35); s.lineTo(L / 2 - 0.35, hh); s.lineTo(-L / 2 + 0.35, hh); s.lineTo(-L / 2, hh * 1.35);
  const hull = new THREE.ExtrudeGeometry(s, { depth: w, bevelEnabled: false });
  hull.translate(0, 0, -w / 2); hull.rotateY(Math.PI / 2);
  const g = new THREE.Group();
  g.add(new THREE.Mesh(hull, mat(wood)));
  g.add(box(w * 0.9, 0.08, L * 0.7, mat(shade(wood, 1.18)), 0, hh - 0.02, 0));
  g.add(box(0.1, 0.1, 1.8, mat(shade(wood, 0.8)), w * 0.25, hh * 0.9, -L / 2 - 0.4));   // steering oar
  if (o.cargo) {
    const cg = typeof o.cargo === "object" ? o.cargo : {};
    const cw = num(cg.w, w * 0.62), ch = num(cg.h, 0.85), cd = num(cg.d, L * 0.34);
    g.add(box(cw, ch, cd, mat(cg.color || "#a3827a"), 0, hh + ch / 2, 0));
  }
  if (o.sail) {
    g.add(box(0.1, 3.2, 0.1, mat(shade(wood, 0.8)), 0, hh + 1.6, L * 0.18));
    g.add(box(w * 1.2, 1.9, 0.05, mat(o.sail_color || "#efe6d2"), 0, hh + 2.1, L * 0.18 + 0.08));
  }
  const inner = merged(g, false), ph = num(o.seed, 1);
  const outer = new THREE.Group(); outer.add(inner);
  outer.userData.tick = (t) => { inner.position.y = Math.sin(t * 1.4 + ph) * 0.05; inner.rotation.z = Math.sin(t * 1.1 + ph) * 0.025; };
  return outer;
};

// flag: a pole with a waving cloth
KIT.flag = (o) => {
  const ph = num(o.h, 3), fw = num(o.w, 1.3), fh = num(o.flag_h, fw * 0.62);
  const g = new THREE.Group();
  const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.05, ph, 6), mat(o.pole || "#6b4a33"));
  pole.position.y = ph / 2; g.add(pole);
  const knob = new THREE.Mesh(new THREE.SphereGeometry(0.08, 6, 4), mat("#c9a24a"));
  knob.position.y = ph + 0.05; g.add(knob);
  const geo = new THREE.PlaneGeometry(fw, fh, 8, 2); geo.translate(fw / 2, 0, 0);
  const cloth = new THREE.Mesh(geo, mat(o.color || "#d9772b", { side: THREE.DoubleSide }));
  cloth.position.set(0.04, ph - fh / 2 - 0.05, 0); g.add(cloth);
  const P = geo.attributes.position, base0 = P.array.slice(), ph0 = num(o.seed, 0);
  g.userData.tick = (t) => {
    for (let i = 0; i < P.count; i++) {
      const x = base0[i * 3];
      P.array[i * 3 + 2] = Math.sin(x * 2.4 - t * 6 + ph0) * 0.14 * Math.pow(x / fw, 0.8);
    }
    P.needsUpdate = true;
  };
  return g;
};

// gate: a gatehouse with a dark arched passage between two towers, merlons on top; `drop` sinks it into the slope
KIT.gate = (o) => {
  const w = num(o.w, 4), h = num(o.h, 3.4), d = num(o.d, 2), c = o.color || "#c99a64", drop = num(o.drop, 0);
  const body = new THREE.Group();
  body.add(box(w, h + drop, d, stoneMat(c, w / 2.2, (h + drop) / 1.1), 0, (h - drop) / 2, 0));
  const tr = Math.min(d * 0.62, w * 0.24), th = h * 1.2, towers = o.towers !== false;
  for (const sx of towers ? [-1, 1] : []) {
    const t = new THREE.Mesh(new THREE.CylinderGeometry(tr * 0.9, tr, th + drop, 8), mat(shade(c, 0.95)));
    t.position.set(sx * (w / 2), (th - drop) / 2, 0); body.add(t);
    const cap = new THREE.Mesh(new THREE.CylinderGeometry(tr * 1.12, tr * 0.95, 0.28, 8), mat(shade(c, 0.86)));
    cap.position.set(sx * (w / 2), th + 0.14, 0); body.add(cap);
  }
  const dw = Math.min(w * 0.4, 1.8), dh = Math.min(h * 0.68, h - 0.5);
  const frame = archMesh(dw + 0.34, dh + 0.2, shade(c, 1.12));
  frame.position.set(0, 0, d / 2 + 0.01); body.add(frame);
  for (const sz of [1, -1]) {
    const dm = archMesh(dw, dh, "#3a2a20");
    dm.position.set(0, 0, sz * (d / 2 + 0.02)); if (sz < 0) dm.rotation.y = Math.PI; body.add(dm);
  }
  const crown = new THREE.Group(), nm = Math.max(3, Math.round(w / 0.7));
  for (let k = 0; k < nm; k++) crown.add(box(0.36, 0.42, d * 0.92, mat(c), -w / 2 + ((k + 0.5) * w) / nm, h + 0.21, 0));
  for (const sx of towers ? [-1, 1] : []) for (let k = 0; k < 6; k++) {
    const a = (k / 6) * Math.PI * 2;
    crown.add(box(0.26, 0.36, 0.22, mat(c), sx * (w / 2) + Math.sin(a) * tr * 0.95, th + 0.46, Math.cos(a) * tr * 0.95));
  }
  const parts = [merged(body), merged(crown)];
  const g = new THREE.Group(); parts.forEach((p) => g.add(p));
  g.userData.stagger = staggerParts(parts, "rise");
  return g;
};

// bastion: a round tower in stone courses with a corbelled crown and merlons
KIT.bastion = (o) => {
  const r = num(o.r, 1.2), h = num(o.h, 4), c = o.color || "#c99a64", n = 3, sh = h / n, taper = num(o.taper, 0.16);
  const g = new THREE.Group(), parts = [];
  for (let k = 0; k < n; k++) {
    const ra = r * (1 + taper * (1 - k / n) - taper * 0.15), rb = r * (1 + taper * (1 - (k + 1) / n) - taper * 0.15);
    const m = new THREE.Mesh(new THREE.CylinderGeometry(rb, ra, sh * 0.995, 16), stoneMat(c, (2 * Math.PI * r) / 2.4, sh / 1.0));
    m.position.y = k * sh + sh / 2; g.add(m); parts.push(m);
  }
  const top = new THREE.Group(), rt = r * 0.93;
  const ring = new THREE.Mesh(new THREE.CylinderGeometry(rt * 1.1, rt * 0.98, 0.32, 16), mat(shade(c, 0.88)));
  ring.position.y = h + 0.16; top.add(ring);
  const nm = Math.max(6, Math.round((2 * Math.PI * rt) / 0.8));
  for (let k = 0; k < nm; k++) {
    const a = (k / nm) * Math.PI * 2, mb = box(0.4, 0.46, 0.3, mat(c), Math.sin(a) * rt * 1.02, h + 0.32 + 0.23, Math.cos(a) * rt * 1.02);
    mb.rotation.y = a; top.add(mb);
  }
  const crown = merged(top); g.add(crown); parts.push(crown);
  g.userData.stagger = staggerParts(parts, "rise");
  return g;
};

// minaret: tall tapered shaft with 2-3 balconies, a lantern and a small dome; `tilt` leans it (degrees, towards tilt_dir)
KIT.minaret = (o) => {
  const h = num(o.h, 10), r = num(o.r, 0.6), rt = num(o.r_top, r * 0.72), c = o.color || "#efe9de";
  const nb = Math.round(clamp(num(o.balconies, 3), 1, 3));
  const fr = nb === 1 ? [0.8] : nb === 2 ? [0.5, 0.86] : [0.36, 0.64, 0.88];
  const shaftH = h * 0.86, rAt = (y) => lerp(r, rt, y / shaftH);
  const parts = [];
  let y0 = 0;
  for (let k = 0; k <= nb; k++) {
    const y1 = k < nb ? fr[k] * shaftH : shaftH, sec = new THREE.Group();
    const s = new THREE.Mesh(new THREE.CylinderGeometry(rAt(y1), rAt(y0), y1 - y0, 12), mat(k % 2 ? shade(c, 0.96) : c));
    s.position.y = (y0 + y1) / 2; sec.add(s);
    if (k < nb) {
      const rb = rAt(y1) * 1.6;
      const cor = new THREE.Mesh(new THREE.CylinderGeometry(rb, rAt(y1), 0.38, 12), mat(shade(c, 0.9)));
      cor.position.y = y1 - 0.19; sec.add(cor);
      const slab = new THREE.Mesh(new THREE.CylinderGeometry(rb, rb, 0.12, 12), mat(shade(c, 0.94)));
      slab.position.y = y1 + 0.06; sec.add(slab);
      const rail = new THREE.Mesh(new THREE.CylinderGeometry(rb, rb, 0.3, 12, 1, true), mat(c, { side: THREE.DoubleSide }));
      rail.position.y = y1 + 0.27; sec.add(rail);
    }
    parts.push(merged(sec)); y0 = y1;
  }
  const top = new THREE.Group(), rl = rt * 1.05, lh = Math.max(0.6, h * 0.07);
  for (let k = 0; k < 6; k++) { const a = (k / 6) * Math.PI * 2; top.add(box(0.07, lh, 0.07, mat(c), Math.sin(a) * rl * 0.85, shaftH + lh / 2, Math.cos(a) * rl * 0.85)); }
  const cap = new THREE.Mesh(new THREE.CylinderGeometry(rl * 1.25, rl * 1.25, 0.08, 10), mat(shade(c, 0.9)));
  cap.position.y = shaftH + lh + 0.04; top.add(cap);
  const dm = new THREE.Mesh(new THREE.SphereGeometry(rl * 1.05, 10, 6, 0, Math.PI * 2, 0, Math.PI / 2), mat(o.dome || c));
  dm.position.y = shaftH + lh + 0.08; top.add(dm);
  const fin = new THREE.Mesh(new THREE.ConeGeometry(0.05, 0.5, 6), mat("#c9a24a"));
  fin.position.y = shaftH + lh + 0.08 + rl * 1.05 + 0.2; top.add(fin);
  parts.push(merged(top));
  const lean = new THREE.Group(); parts.forEach((p) => lean.add(p));
  lean.rotation.x = (num(o.tilt, 0) * Math.PI) / 180;
  const yaw = new THREE.Group(); yaw.add(lean);
  yaw.rotation.y = (num(o.tilt_dir, 0) * Math.PI) / 180;
  yaw.userData.stagger = staggerParts(parts, "rise");
  return yaw;
};

// tomb: plinth, chamfered cube with arched niches and a framed great arch on each face, onion dome on a drum,
// chhatris on the roof corners and optional minarets at the plinth corners (a generic Mughal mausoleum)
KIT.tomb = (o) => {
  const w = num(o.w, 8), h = num(o.h, w * 0.72), c = o.color || "#efe9de";
  const accent = shade(c, 0.86), deep = o.niche || shade(c, 0.55);
  const pH = o.plinth === false ? 0 : num(o.plinth_h, w * 0.16), P = num(o.plinth_w, w * 1.8);
  const parts = [];
  if (pH > 0) {
    const pl = new THREE.Group();
    pl.add(box(P, pH, P, stoneMat(shade(c, 0.95), P / 2.4, pH / 1.1), 0, pH / 2, 0));
    const na = Math.max(3, Math.round(P / 1.4));
    for (let f = 0; f < 4; f++) {
      const side = new THREE.Group();
      for (let k = 0; k < na; k++) { const a = archMesh(0.5, pH * 0.7, accent); a.position.set(-P / 2 + ((k + 0.5) * P) / na, pH * 0.12, P / 2 + 0.01); side.add(a); }
      side.rotation.y = (f * Math.PI) / 2; pl.add(side);
    }
    parts.push(merged(pl));
  }
  const body = new THREE.Group(), cf = w * 0.17;
  const sh = new THREE.Shape();
  const oct = [[-w / 2 + cf, -w / 2], [w / 2 - cf, -w / 2], [w / 2, -w / 2 + cf], [w / 2, w / 2 - cf], [w / 2 - cf, w / 2], [-w / 2 + cf, w / 2], [-w / 2, w / 2 - cf], [-w / 2, -w / 2 + cf]];
  sh.moveTo(oct[0][0], oct[0][1]); oct.slice(1).forEach((p) => sh.lineTo(p[0], p[1])); sh.lineTo(oct[0][0], oct[0][1]);
  const eg = new THREE.ExtrudeGeometry(sh, { depth: h, bevelEnabled: false }); eg.rotateX(-Math.PI / 2);
  const bm = new THREE.Mesh(eg, mat(c)); bm.position.y = pH; body.add(bm);
  body.add(box(w - 0.2, 0.25, w - 0.2, mat(accent), 0, pH + h + 0.12, 0));
  for (let k = 0; k < 4; k++) {
    const f = new THREE.Group(), pw = w * 0.44, phh = h * 1.12;
    f.add(box(pw, phh, 0.3, mat(shade(c, 1.03)), 0, pH + phh / 2, w / 2 + 0.15));
    const a1 = archMesh(pw * 0.7, phh * 0.8, accent); a1.position.set(0, pH, w / 2 + 0.31); f.add(a1);
    const a2 = archMesh(pw * 0.48, phh * 0.62, deep); a2.position.set(0, pH, w / 2 + 0.32); f.add(a2);
    for (const sx of [-1, 1]) for (const row of [0, 1]) {
      const n = archMesh(w * 0.12, h * 0.36, accent); n.position.set(sx * w * 0.34, pH + h * (0.05 + row * 0.48), w / 2 + 0.01); f.add(n);
      const nn = archMesh(w * 0.075, h * 0.27, deep); nn.position.set(sx * w * 0.34, pH + h * (0.05 + row * 0.48), w / 2 + 0.02); f.add(nn);
    }
    f.rotation.y = (k * Math.PI) / 2; body.add(f);
  }
  const cd = (w - cf) / Math.SQRT2;
  for (let k = 0; k < 4; k++) {
    const f = new THREE.Group();
    for (const row of [0, 1]) {
      const n = archMesh(cf * 0.85, h * 0.36, accent); n.position.set(0, pH + h * (0.05 + row * 0.48), cd + 0.01); f.add(n);
      const nn = archMesh(cf * 0.5, h * 0.27, deep); nn.position.set(0, pH + h * (0.05 + row * 0.48), cd + 0.02); f.add(nn);
    }
    f.rotation.y = Math.PI / 4 + (k * Math.PI) / 2; body.add(f);
  }
  parts.push(merged(body));
  const dome = new THREE.Group(), rd = w * 0.3, dh = w * 0.14, y0 = pH + h + 0.25;
  const drum = new THREE.Mesh(new THREE.CylinderGeometry(rd, rd, dh, 16), mat(shade(c, 0.97)));
  drum.position.y = y0 + dh / 2; dome.add(drum);
  const prof = [[0.98, 0], [1.1, 0.22], [1.17, 0.5], [1.12, 0.8], [0.92, 1.1], [0.6, 1.36], [0.28, 1.56], [0.08, 1.7], [0, 1.74]]
    .map(([x, y]) => new THREE.Vector2(x * rd, y * rd));
  const on = new THREE.Mesh(new THREE.LatheGeometry(prof, 16), mat(o.dome || c));
  on.position.y = y0 + dh; dome.add(on);
  const fin = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.08, rd * 0.7, 6), mat(o.finial || "#cfa64a"));
  fin.position.y = y0 + dh + rd * 1.74 + rd * 0.3; dome.add(fin);
  parts.push(merged(dome));
  const ch = new THREE.Group(), cr = w * 0.08;
  for (const [sx, sz] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) chhatri(ch, sx * w * 0.33, pH + h + 0.25, sz * w * 0.33, cr, c, accent);
  parts.push(merged(ch));
  if (o.minarets) {
    const mg = new THREE.Group(), mh = num(o.minaret_h, w * 1.15);
    for (const [sx, sz] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) {
      const m = KIT.minaret({ h: mh, r: w * 0.055, color: c, balconies: 3 });
      m.position.set(sx * (P / 2 - w * 0.08), pH, sz * (P / 2 - w * 0.08)); mg.add(m);
    }
    parts.push(merged(mg));
  }
  const g = new THREE.Group(); parts.forEach((p) => g.add(p));
  g.userData.stagger = staggerParts(parts, "rise");
  return g;
};

// palace: floors of sandstone with rows of jharokha balconies, cornices, a flat roof with a parapet and chhatris
const SANDSTONE = ["#d9a066", "#cf9358", "#e0b07a", "#c98a52"];
function jharokha(g, x, y, z, jw, fh, light, dark, win) {
  const bh = fh * 0.5, dep = 0.42;
  g.add(box(jw * 0.95, 0.12, dep * 0.9, mat(dark), x, y - 0.06, z + dep * 0.45));
  g.add(box(jw * 0.45, 0.24, dep * 0.5, mat(dark), x, y - 0.24, z + dep * 0.25));
  g.add(box(jw, bh, dep, mat(light), x, y + bh / 2, z + dep / 2));
  g.add(box(jw * 0.62, bh * 0.6, 0.04, mat(win), x, y + bh * 0.5, z + dep + 0.02));
  const roof = new THREE.Mesh(new THREE.CylinderGeometry(dep * 0.66, dep * 0.66, jw * 1.1, 8, 1, false, 0, Math.PI), mat(dark));
  roof.rotation.z = Math.PI / 2; roof.position.set(x, y + bh, z + dep / 2); g.add(roof);
}
KIT.palace = (o) => {
  const w = num(o.w, 6), d = num(o.d, 4), h = num(o.h, 5);
  const floors = Math.max(1, Math.round(num(o.floors, Math.max(2, h / 1.7)))), fh = h / floors;
  const c = o.color || SANDSTONE[Math.abs(Math.round(num(o.seed, 0))) % SANDSTONE.length];
  const light = shade(c, 1.1), dark = shade(c, 0.8), win = o.window || "#4a2f22";
  const J = Math.max(1, Math.round(num(o.jharokhas, Math.max(2, Math.floor(w / 1.5)))));
  const Js = Math.max(1, Math.round(J * (d / w)));
  const faces = o.sides === "front" ? [0] : [0, 1, 3];     // front and both sides (the back rarely shows)
  const parts = [];
  for (let f = 0; f < floors; f++) {
    const fl = new THREE.Group(), y0 = f * fh;
    fl.add(box(w, fh, d, mat(f % 2 ? shade(c, 0.97) : c), 0, y0 + fh / 2, 0));
    fl.add(box(w + 0.24, 0.13, d + 0.24, mat(dark), 0, y0 + fh - 0.065, 0));
    for (const face of faces) {
      const fw = face === 0 ? w : d, fz = face === 0 ? d / 2 : w / 2, n = face === 0 ? J : Js;
      const side = new THREE.Group();
      for (let j = 0; j < n; j++) {
        const x = -fw / 2 + ((j + 0.5) * fw) / n;
        if (f === 0) {
          const centre = face === 0 && j === Math.floor(n / 2);
          const a = archMesh(centre ? Math.min(1.3, (fw / n) * 0.7) : 0.42, centre ? fh * 0.8 : fh * 0.45, win);
          a.position.set(x, centre ? 0 : fh * 0.3, fz + 0.01); side.add(a);
        } else jharokha(side, x, y0 + fh * 0.24, fz, Math.min(0.95, (fw / n) * 0.7), fh, light, dark, win);
      }
      side.rotation.y = (face * Math.PI) / 2; fl.add(side);
    }
    parts.push(merged(fl));
  }
  const roof = new THREE.Group(), pt = 0.14, ph = 0.36;
  roof.add(box(w, ph, pt, mat(c), 0, h + ph / 2, d / 2 - pt / 2)); roof.add(box(w, ph, pt, mat(c), 0, h + ph / 2, -d / 2 + pt / 2));
  roof.add(box(pt, ph, d, mat(c), w / 2 - pt / 2, h + ph / 2, 0)); roof.add(box(pt, ph, d, mat(c), -w / 2 + pt / 2, h + ph / 2, 0));
  const nd = Math.max(0, Math.round(num(o.domes, 2))), cr = Math.min(0.62, w * 0.09, d * 0.16);
  for (let k = 0; k < nd; k++) {
    const x = nd === 1 ? 0 : -w / 2 + cr * 1.6 + (k * (w - cr * 3.2)) / (nd - 1);
    chhatri(roof, x, h, d * 0.12 * (k % 2 ? -1 : 1), cr, light, dark);
  }
  if (o.dome) {     // one larger central dome on a drum
    const rd = Math.min(w, d) * 0.22;
    const drum = new THREE.Mesh(new THREE.CylinderGeometry(rd, rd, rd * 0.5, 14), mat(c)); drum.position.y = h + rd * 0.25; roof.add(drum);
    const dm = new THREE.Mesh(new THREE.SphereGeometry(rd * 1.05, 14, 7, 0, Math.PI * 2, 0, Math.PI / 2), mat(light)); dm.position.y = h + rd * 0.5; roof.add(dm);
  }
  parts.push(merged(roof));
  const g = new THREE.Group(); parts.forEach((p) => g.add(p));
  g.userData.stagger = staggerParts(parts, "rise");
  return g;
};

// town: flat-roofed houses scattered over an area (merged), e.g. the blue city under a fort or a workers' village
KIT.town = (o, terrain) => scatter({ count: 24, ...o }, (r) => {
  const cs = o.colors || ["#e9e1d0", "#d9c9a8", "#cdb48c"], s = num(o.scale, 1);
  const g = new THREE.Group(), c = cs[Math.floor(r() * cs.length)];
  const w = (0.9 + r() * 1.1) * s, d = (0.9 + r() * 1.0) * s, h = (0.8 + r() * 1.0) * s;
  g.add(box(w, h, d, mat(c), 0, h / 2, 0));
  g.add(box(w + 0.08, 0.1, d + 0.08, mat(shade(c, 0.86)), 0, h + 0.05, 0));
  if (r() < 0.4) g.add(box(w * 0.5, h * 0.45, d * 0.5, mat(c), (r() - 0.5) * w * 0.3, h + h * 0.22, (r() - 0.5) * d * 0.3));
  g.add(box(0.28 * s, 0.5 * s, 0.04, mat("#4a3326"), (r() - 0.5) * w * 0.4, 0.25 * s, d / 2 + 0.02));
  g.rotation.y = Math.floor(r() * 4) * (Math.PI / 2) + (r() - 0.5) * 0.3;
  return g;
}, terrain);

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
  if (num(world._extent, 0) > ext) Object.assign(sun.shadow.camera, { left: -world._extent, right: world._extent, top: world._extent, bottom: -world._extent, far: 220 });
  sun.target.position.set(0, -2, -10);
  SCENE.add(sun); SCENE.add(sun.target);

  STYLE = style;
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
    const it = { o, holder, inner };
    if (o.type !== "person" && Array.isArray(o.path) && o.path.length >= 2) it.follow = follower(o, holder);
    ITEMS.push(it);
  }
  CAM = makeCamera(world.camera, W, H);
  return { objects: ITEMS.length, width: W, height: H };
}

// Any object with a `path` and a {from, to} window travels along it (constant speed, eased at the ends), facing
// its direction of travel; `pitch: true` also tilts it with the slope (a sledge on a ramp).
function follower(o, holder) {
  const pts = o.path.map((p) => vec(p)), acc = [0];
  for (let i = 1; i < pts.length; i++) acc.push(acc[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1], pts[i][2] - pts[i - 1][2]));
  const total = acc[acc.length - 1] || 1, yaw0 = (num(o.rot, 0) * Math.PI) / 180;
  holder.rotation.order = "YXZ";
  return (t) => {
    const p = o.from === undefined ? 0 : (o.ease === "linear" ? prog({ from: o.from, to: o.to }, t) : easeInOut(prog({ from: o.from, to: o.to }, t)));
    const d = p * total;
    let i = 0;
    while (i < pts.length - 2 && acc[i + 1] < d) i++;
    const a = pts[i], b = pts[i + 1], u = clamp((d - acc[i]) / Math.max(1e-6, acc[i + 1] - acc[i]));
    holder.userData.base.set(lerp(a[0], b[0], u), lerp(a[1], b[1], u), lerp(a[2], b[2], u));
    const dx = b[0] - a[0], dy = b[1] - a[1], dz = b[2] - a[2];
    if (o.face !== false) holder.rotation.y = Math.atan2(dx, dz) + yaw0;
    if (o.pitch) holder.rotation.x = -Math.atan2(dy, Math.hypot(dx, dz));
  };
}

function update(t) {
  if (TERRAIN) TERRAIN.update(t);
  for (const it of ITEMS) {
    if (it.follow) it.follow(t);
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

export const VF = { setup, frame, kit: Object.keys(KIT), styles: Object.keys(STYLES), info: () => ({ calls: R ? R.info.render.calls : 0, triangles: R ? R.info.render.triangles : 0 }) };
