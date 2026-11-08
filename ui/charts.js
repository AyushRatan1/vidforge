// Inline SVG charts, no library. Colours come from CSS classes (styles.css), never from here.
// areaChart(el, {series: [{name, tone: "yt" | "ig" | "accent", values}], days, height})
//   Stacked, smoothed, gradient-filled areas with a hover and keyboard tooltip. Redraws on resize.
import {h, clear} from "./components.js";
import {fmt} from "./format.js";

const NS = "http://www.w3.org/2000/svg";
const s = (tag, attrs = {}) => { const el = document.createElementNS(NS, tag); for (const [k, v] of Object.entries(attrs)) if (v !== null && v !== undefined) el.setAttribute(k, v); return el; };
let gid = 0;

function niceMax(v) {
  if (v <= 0) return 4;
  const raw = v / 4, p = Math.pow(10, Math.floor(Math.log10(raw))), n = raw / p;
  return (n <= 1 ? 1 : n <= 2 ? 2 : n <= 2.5 ? 2.5 : n <= 5 ? 5 : 10) * p * 4;
}
function smoothPath(pts) {
  if (pts.length < 2) return pts.length ? `M${pts[0][0]},${pts[0][1]}` : "";
  let d = `M${pts[0][0]},${pts[0][1]}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[i - 1] || pts[i], p1 = pts[i], p2 = pts[i + 1], p3 = pts[i + 2] || p2, t = .2;
    const c1 = [p1[0] + (p2[0] - p0[0]) * t, p1[1] + (p2[1] - p0[1]) * t];
    const c2 = [p2[0] - (p3[0] - p1[0]) * t, p2[1] - (p3[1] - p1[1]) * t];
    d += ` C${c1[0].toFixed(1)},${c1[1].toFixed(1)} ${c2[0].toFixed(1)},${c2[1].toFixed(1)} ${p2[0].toFixed(1)},${p2[1].toFixed(1)}`;
  }
  return d;
}
const dayLabel = d => new Date(d + "T00:00:00").toLocaleDateString("en-IN", {day: "numeric", month: "short"});

function observe(el, draw) {
  let raf, lastW = 0;
  const paint = () => { const w = el.clientWidth; if (w > 0 && w !== lastW) { lastW = w; draw(w); } };
  const run = () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(paint); };
  if (typeof ResizeObserver !== "undefined") new ResizeObserver(run).observe(el);
  window.addEventListener("resize", run);
  paint(); // draw at once when the element already has a size
}

export function areaChart(el, {series, days, height = 260, stacked = true, valueFmt = fmt.compact, ariaLabel = "Daily views"}) {
  const H = height;
  el.style.height = H + "px";
  observe(el, width => {
    clear(el);
    const narrow = width < 420;
    const pad = {l: narrow ? 36 : 44, r: 10, t: 14, b: 26};
    const W = width, iw = W - pad.l - pad.r, ih = H - pad.t - pad.b, n = days.length;
    const totals = days.map((_, i) => stacked ? series.reduce((a, se) => a + (se.values[i] || 0), 0) : Math.max(...series.map(se => se.values[i] || 0)));
    const max = niceMax(Math.max(...totals, 1) * 1.08);
    const x = i => pad.l + (n > 1 ? (i / (n - 1)) * iw : iw / 2);
    const y = v => pad.t + ih - (v / max) * ih;
    const svg = s("svg", {viewBox: `0 0 ${W} ${H}`, width: W, height: H, role: "img", "aria-label": `${ariaLabel}: ${series.map(se => `${se.name} ${fmt.int(se.values.reduce((a, b) => a + b, 0))}`).join(", ")} over ${n} days`, class: "chart-svg"});
    const defs = s("defs"); svg.append(defs);
    for (let g = 0; g <= 4; g++) {
      const v = (max / 4) * g, yy = y(v);
      svg.append(s("line", {x1: pad.l, x2: W - pad.r, y1: yy, y2: yy, class: "chart-grid"}));
      const t = s("text", {x: pad.l - 8, y: yy + 4, "text-anchor": "end", class: "chart-axis"}); t.textContent = g === 0 ? "0" : valueFmt(v); svg.append(t);
    }
    const step = Math.max(1, Math.round(n / (narrow ? 4 : 6)));
    for (let i = 0; i < n; i += step) {
      const t = s("text", {x: x(i), y: H - 7, "text-anchor": i === 0 ? "start" : i + step >= n ? "end" : "middle", class: "chart-axis"}); t.textContent = dayLabel(days[i]); svg.append(t);
    }
    const base = new Array(n).fill(0), layers = [];
    for (const se of series) {
      const id = `ag${++gid}`;
      const grad = s("linearGradient", {id, x1: 0, y1: 0, x2: 0, y2: 1});
      grad.append(s("stop", {offset: "0%", class: `chart-stop-a tone-${se.tone}`}), s("stop", {offset: "100%", class: `chart-stop-b tone-${se.tone}`}));
      defs.append(grad);
      const top = se.values.map((v, i) => (stacked ? base[i] : 0) + (v || 0));
      const pts = top.map((v, i) => [x(i), y(v)]);
      const lower = stacked ? base.map((v, i) => [x(i), y(v)]) : days.map((_, i) => [x(i), y(0)]);
      const path = smoothPath(pts) + " L" + [...lower].reverse().map(p => `${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(" L") + " Z";
      svg.append(s("path", {d: path, fill: `url(#${id})`, class: "chart-area"}));
      svg.append(s("path", {d: smoothPath(pts), class: `chart-line tone-${se.tone}`}));
      layers.push({se, pts});
      if (stacked) for (let i = 0; i < n; i++) base[i] = top[i];
    }
    const hl = s("line", {class: "chart-hover", y1: pad.t, y2: pad.t + ih, opacity: 0}); svg.append(hl);
    const dots = layers.map(l => { const d = s("circle", {r: 4.5, class: `chart-dot tone-${l.se.tone}`, opacity: 0}); svg.append(d); return d; });
    const tt = h("div", {class: "chart-tip", style: {opacity: 0}, "aria-hidden": "true"});
    const hit = s("rect", {x: pad.l, y: pad.t, width: iw, height: ih, fill: "transparent", class: "chart-hit"}); svg.append(hit);
    el.append(svg, tt);
    const live = h("div", {class: "sr-only", "aria-live": "polite"}); el.append(live);
    const show = i => {
      hl.setAttribute("x1", x(i)); hl.setAttribute("x2", x(i)); hl.setAttribute("opacity", 1);
      layers.forEach((l, k) => { dots[k].setAttribute("cx", l.pts[i][0]); dots[k].setAttribute("cy", l.pts[i][1]); dots[k].setAttribute("opacity", 1); });
      clear(tt).append(h("div", {class: "chart-tip-day"}, dayLabel(days[i])));
      for (const l of layers) tt.append(h("div", {class: "chart-tip-row"}, h("span", {class: "chart-tip-name"}, h("span", {class: `swatch tone-${l.se.tone}`}), l.se.name), h("strong", {class: "num"}, fmt.int(l.se.values[i] || 0))));
      if (series.length > 1) tt.append(h("div", {class: "chart-tip-row chart-tip-total"}, h("span", {class: "chart-tip-name"}, "Total"), h("strong", {class: "num"}, fmt.int(totals[i]))));
      const px = (x(i) / W) * el.clientWidth;
      tt.style.left = Math.min(Math.max(px, 92), el.clientWidth - 92) + "px";
      tt.style.top = Math.max(8, (Math.min(...layers.map(l => l.pts[i][1])) / H) * el.clientHeight - 8) + "px";
      tt.style.opacity = 1;
      live.textContent = `${dayLabel(days[i])}: ${layers.map(l => `${l.se.name} ${fmt.int(l.se.values[i] || 0)}`).join(", ")}`;
    };
    const hide = () => { hl.setAttribute("opacity", 0); dots.forEach(d => d.setAttribute("opacity", 0)); tt.style.opacity = 0; };
    const idx = ev => { const r = svg.getBoundingClientRect(); const px = ((ev.clientX - r.left) / r.width) * W; return Math.max(0, Math.min(n - 1, Math.round(((px - pad.l) / iw) * (n - 1)))); };
    hit.addEventListener("pointermove", ev => show(idx(ev)));
    hit.addEventListener("pointerleave", hide);
    svg.tabIndex = 0;
    svg.addEventListener("keydown", ev => { if (ev.key === "ArrowRight" || ev.key === "ArrowLeft") { svg._i = Math.max(0, Math.min(n - 1, (svg._i ?? n - 1) + (ev.key === "ArrowRight" ? 1 : -1))); show(svg._i); ev.preventDefault(); } });
    svg.addEventListener("focus", () => show(svg._i ?? n - 1));
    svg.addEventListener("blur", hide);
  });
  return el;
}

// Tiny sparkline for stat tiles: values -> smoothed line, no axes.
export function sparkline(values, {width = 96, height = 28, tone = "accent"} = {}) {
  const max = Math.max(...values, 1), min = Math.min(...values, 0), n = values.length;
  const x = i => (i / Math.max(1, n - 1)) * (width - 2) + 1;
  const y = v => height - 2 - ((v - min) / (max - min || 1)) * (height - 4);
  const pts = values.map((v, i) => [x(i), y(v)]);
  const svg = s("svg", {viewBox: `0 0 ${width} ${height}`, width, height, class: "spark", "aria-hidden": "true"});
  svg.append(s("path", {d: smoothPath(pts), class: `chart-line tone-${tone}`}));
  return svg;
}
