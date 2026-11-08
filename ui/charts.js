// Inline SVG charts, no library. Both redraw when the container resizes.
import {h, clear, fmt} from "./ui.js";

const NS = "http://www.w3.org/2000/svg";
const s = (tag, attrs = {}) => { const el = document.createElementNS(NS, tag); for (const [k, v] of Object.entries(attrs)) if (v !== null && v !== undefined) el.setAttribute(k, v); return el; };

// Largest axis value as 4 steps of a round number (1, 2, 2.5, 5 times a power of ten).
function niceMax(v) {
  if (v <= 0) return 4;
  const raw = v / 4;
  const p = Math.pow(10, Math.floor(Math.log10(raw)));
  const n = raw / p;
  const step = (n <= 1 ? 1 : n <= 2 ? 2 : n <= 2.5 ? 2.5 : n <= 5 ? 5 : 10) * p;
  return step * 4;
}
function smoothPath(pts) {
  if (pts.length < 2) return pts.length ? `M${pts[0][0]},${pts[0][1]}` : "";
  let d = `M${pts[0][0]},${pts[0][1]}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[i - 1] || pts[i], p1 = pts[i], p2 = pts[i + 1], p3 = pts[i + 2] || p2;
    const t = .2;
    const c1 = [p1[0] + (p2[0] - p0[0]) * t, p1[1] + (p2[1] - p0[1]) * t];
    const c2 = [p2[0] - (p3[0] - p1[0]) * t, p2[1] - (p3[1] - p1[1]) * t];
    d += ` C${c1[0].toFixed(1)},${c1[1].toFixed(1)} ${c2[0].toFixed(1)},${c2[1].toFixed(1)} ${p2[0].toFixed(1)},${p2[1].toFixed(1)}`;
  }
  return d;
}
const dayLabel = d => new Date(d + "T00:00:00").toLocaleDateString("en-IN", {day: "numeric", month: "short"});

function observe(el, draw) {
  let raf;
  const run = () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(() => { if (el.clientWidth > 0) draw(el.clientWidth); }); };
  if (typeof ResizeObserver !== "undefined") new ResizeObserver(run).observe(el);
  else window.addEventListener("resize", run);
  run();
}

// Area chart. series = [{name, color, values: number[]}], days = ["2026-10-10", ...] (same length)
export function areaChart(el, {series, days, height = 240, stacked = true, valueFmt = fmt.compact}) {
  observe(el, width => {
    clear(el);
    const pad = {l: 44, r: 12, t: 16, b: 28};
    const W = width, H = height, iw = W - pad.l - pad.r, ih = H - pad.t - pad.b;
    const n = days.length;
    const totals = days.map((_, i) => stacked ? series.reduce((a, se) => a + (se.values[i] || 0), 0) : Math.max(...series.map(se => se.values[i] || 0)));
    const max = niceMax(Math.max(...totals, 1) * 1.1);
    const x = i => pad.l + (n > 1 ? (i / (n - 1)) * iw : iw / 2);
    const y = v => pad.t + ih - (v / max) * ih;
    const svg = s("svg", {viewBox: `0 0 ${W} ${H}`, width: W, height: H, role: "img", "aria-label": "Daily views"});
    // grid
    for (let g = 0; g <= 4; g++) {
      const v = (max / 4) * g, yy = y(v);
      svg.append(s("line", {x1: pad.l, x2: W - pad.r, y1: yy, y2: yy, class: "grid"}));
      const t = s("text", {x: pad.l - 8, y: yy + 4, "text-anchor": "end", class: "axis"}); t.textContent = valueFmt(v); svg.append(t);
    }
    // x labels (about 6)
    const step = Math.max(1, Math.round(n / 6));
    for (let i = 0; i < n; i += step) {
      const t = s("text", {x: x(i), y: H - 8, "text-anchor": i === 0 ? "start" : "middle", class: "axis"}); t.textContent = dayLabel(days[i]); svg.append(t);
    }
    // areas and lines, stacked bottom-up
    const base = new Array(n).fill(0);
    const layers = [];
    for (const se of series) {
      const top = se.values.map((v, i) => (stacked ? base[i] : 0) + (v || 0));
      const pts = top.map((v, i) => [x(i), y(v)]);
      const lower = stacked ? base.map((v, i) => [x(i), y(v)]) : days.map((_, i) => [x(i), y(0)]);
      const path = smoothPath(pts) + " L" + [...lower].reverse().map(p => `${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(" L") + " Z";
      svg.append(s("path", {d: path, fill: se.color, class: "area"}));
      svg.append(s("path", {d: smoothPath(pts), stroke: se.color, class: "line"}));
      layers.push({se, pts});
      if (stacked) for (let i = 0; i < n; i++) base[i] = top[i];
    }
    // hover
    const hl = s("line", {class: "hover-line", y1: pad.t, y2: pad.t + ih, opacity: 0});
    svg.append(hl);
    const dots = layers.map(l => { const d = s("circle", {r: 4, fill: l.se.color, class: "dot", opacity: 0}); svg.append(d); return d; });
    const tt = h("div", {class: "tt", style: {opacity: 0}});
    const hit = s("rect", {x: pad.l, y: pad.t, width: iw, height: ih, fill: "transparent"});
    svg.append(hit);
    el.append(svg, tt);
    const show = i => {
      hl.setAttribute("x1", x(i)); hl.setAttribute("x2", x(i)); hl.setAttribute("opacity", 1);
      layers.forEach((l, k) => { dots[k].setAttribute("cx", l.pts[i][0]); dots[k].setAttribute("cy", l.pts[i][1]); dots[k].setAttribute("opacity", 1); });
      clear(tt);
      tt.append(h("div", {class: "tt-day"}, dayLabel(days[i])));
      for (const l of layers) tt.append(h("div", {class: "tt-row"}, h("span", {}, h("span", {class: "sw", style: {background: l.se.color}}), l.se.name), h("strong", {class: "num"}, fmt.int(l.se.values[i] || 0))));
      if (series.length > 1) tt.append(h("div", {class: "tt-row"}, h("span", {class: "secondary"}, "Total"), h("strong", {class: "num"}, fmt.int(totals[i]))));
      const px = (x(i) / W) * el.clientWidth;
      tt.style.left = Math.min(Math.max(px, 90), el.clientWidth - 90) + "px";
      tt.style.top = (Math.min(...layers.map(l => l.pts[i][1])) / H) * el.clientHeight + "px";
      tt.style.opacity = 1;
    };
    const hide = () => { hl.setAttribute("opacity", 0); dots.forEach(d => d.setAttribute("opacity", 0)); tt.style.opacity = 0; };
    const idx = ev => { const r = svg.getBoundingClientRect(); const px = ((ev.clientX - r.left) / r.width) * W; return Math.max(0, Math.min(n - 1, Math.round(((px - pad.l) / iw) * (n - 1)))); };
    hit.addEventListener("pointermove", ev => show(idx(ev)));
    hit.addEventListener("pointerleave", hide);
    svg.tabIndex = 0;
    svg.addEventListener("keydown", ev => { if (ev.key === "ArrowRight" || ev.key === "ArrowLeft") { svg._i = Math.max(0, Math.min(n - 1, (svg._i ?? n - 1) + (ev.key === "ArrowRight" ? 1 : -1))); show(svg._i); ev.preventDefault(); } });
    svg.addEventListener("blur", hide);
  });
}

// Bars (count per day) with a line (average score 0-10) on a second axis.
export function barLineChart(el, {days, counts, scores, height = 200, barColor = "#0A84FF", lineColor = "#30D158"}) {
  observe(el, width => {
    clear(el);
    const pad = {l: 30, r: 34, t: 16, b: 28};
    const W = width, H = height, iw = W - pad.l - pad.r, ih = H - pad.t - pad.b;
    const n = days.length;
    const maxC = Math.max(4, ...counts);
    const yc = v => pad.t + ih - (v / maxC) * ih;
    const ys = v => pad.t + ih - (v / 10) * ih;
    const slot = iw / n, bw = Math.max(3, Math.min(18, slot * .6));
    const xc = i => pad.l + slot * i + slot / 2;
    const svg = s("svg", {viewBox: `0 0 ${W} ${H}`, width: W, height: H, role: "img", "aria-label": "Videos per day and review score"});
    for (let g = 0; g <= 2; g++) {
      const v = Math.round((maxC / 2) * g), yy = yc(v);
      svg.append(s("line", {x1: pad.l, x2: W - pad.r, y1: yy, y2: yy, class: "grid"}));
      const t = s("text", {x: pad.l - 8, y: yy + 4, "text-anchor": "end", class: "axis"}); t.textContent = v; svg.append(t);
      const t2 = s("text", {x: W - pad.r + 8, y: yy + 4, class: "axis"}); t2.textContent = g * 5; svg.append(t2);
    }
    const step = Math.max(1, Math.round(n / 6));
    for (let i = 0; i < n; i += step) { const t = s("text", {x: xc(i), y: H - 8, "text-anchor": "middle", class: "axis"}); t.textContent = dayLabel(days[i]); svg.append(t); }
    counts.forEach((c, i) => { if (c > 0) svg.append(s("rect", {x: xc(i) - bw / 2, y: yc(c), width: bw, height: yc(0) - yc(c), fill: barColor, class: "bar"})); });
    const pts = scores.map((v, i) => v == null ? null : [xc(i), ys(v)]);
    // one line through the days that have a score, with a dot on each
    const known = pts.filter(Boolean);
    if (known.length > 1) svg.append(s("path", {d: smoothPath(known), stroke: lineColor, class: "line", opacity: .9}));
    for (const p of known) svg.append(s("circle", {cx: p[0], cy: p[1], r: 3.5, fill: lineColor, class: "dot"}));
    const tt = h("div", {class: "tt", style: {opacity: 0}});
    const hit = s("rect", {x: pad.l, y: pad.t, width: iw, height: ih, fill: "transparent"});
    svg.append(hit); el.append(svg, tt);
    hit.addEventListener("pointermove", ev => {
      const r = svg.getBoundingClientRect(); const px = ((ev.clientX - r.left) / r.width) * W;
      const i = Math.max(0, Math.min(n - 1, Math.floor((px - pad.l) / slot)));
      clear(tt);
      tt.append(h("div", {class: "tt-day"}, dayLabel(days[i])),
        h("div", {class: "tt-row"}, h("span", {}, h("span", {class: "sw", style: {background: barColor}}), "Videos made"), h("strong", {class: "num"}, counts[i])),
        h("div", {class: "tt-row"}, h("span", {}, h("span", {class: "sw", style: {background: lineColor}}), "Review score"), h("strong", {class: "num"}, scores[i] == null ? "none" : scores[i].toFixed(1))));
      tt.style.left = Math.min(Math.max((xc(i) / W) * el.clientWidth, 90), el.clientWidth - 90) + "px";
      tt.style.top = ((pts[i] ? pts[i][1] : yc(counts[i])) / H) * el.clientHeight + "px";
      tt.style.opacity = 1;
    });
    hit.addEventListener("pointerleave", () => tt.style.opacity = 0);
  });
}
