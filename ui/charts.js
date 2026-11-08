// Inline SVG line chart, no library. Colours come from CSS classes (styles.css), never from here.
// lineChart(el, {series: [{name, tone: "yt" | "ig", values}], days, height, fill})
//   YouTube is a solid white line, Instagram a grey dashed line. Lines overlay (not stacked) so each reads on its own.
//   fill: true draws a flat 6% white area under the single series. Crosshair and tooltip on hover and arrow keys.
import {h, clear} from "./components.js";
import {fmt} from "./format.js";

const NS = "http://www.w3.org/2000/svg";
const s = (tag, attrs = {}) => { const el = document.createElementNS(NS, tag); for (const [k, v] of Object.entries(attrs)) if (v !== null && v !== undefined) el.setAttribute(k, v); return el; };

function niceMax(v) {
  if (v <= 0) return 4;
  const raw = v / 4, p = Math.pow(10, Math.floor(Math.log10(raw))), n = raw / p;
  return (n <= 1 ? 1 : n <= 2 ? 2 : n <= 2.5 ? 2.5 : n <= 5 ? 5 : 10) * p * 4;
}
const linePath = pts => pts.map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(" ");
const dayLabel = d => new Date(d + "T00:00:00").toLocaleDateString("en-IN", {day: "numeric", month: "short"});

// A short line sample in the series style, for the legend and the tooltip.
export function lineKey(tone) {
  const svg = s("svg", {viewBox: "0 0 16 8", width: 16, height: 8, class: "line-key", "aria-hidden": "true"});
  svg.append(s("path", {d: "M0 4h16", class: `chart-line tone-${tone}`}));
  return svg;
}

function observe(el, draw) {
  let raf, lastW = 0;
  const paint = () => { const w = el.clientWidth; if (w > 0 && w !== lastW) { lastW = w; draw(w); } };
  const run = () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(paint); };
  if (typeof ResizeObserver !== "undefined") new ResizeObserver(run).observe(el);
  window.addEventListener("resize", run);
  paint();
}

export function lineChart(el, {series, days, height = 240, fill = false, valueFmt = fmt.compact, ariaLabel = "Daily views"}) {
  const H = height;
  el.style.height = H + "px";
  observe(el, width => {
    clear(el);
    const narrow = width < 420;
    const pad = {l: narrow ? 34 : 42, r: 8, t: 12, b: 24};
    const W = width, iw = W - pad.l - pad.r, ih = H - pad.t - pad.b, n = days.length;
    const totals = days.map((_, i) => series.reduce((a, se) => a + (se.values[i] || 0), 0));
    const max = niceMax(Math.max(...series.flatMap(se => se.values), 1) * 1.08);
    const x = i => pad.l + (n > 1 ? (i / (n - 1)) * iw : iw / 2);
    const y = v => pad.t + ih - (v / max) * ih;
    const svg = s("svg", {viewBox: `0 0 ${W} ${H}`, width: W, height: H, role: "img", "aria-label": `${ariaLabel}: ${series.map(se => `${se.name} ${fmt.int(se.values.reduce((a, b) => a + b, 0))}`).join(", ")} over ${n} days`, class: "chart-svg"});
    for (let g = 0; g <= 4; g++) {
      const v = (max / 4) * g, yy = Math.round(y(v)) + 0.5;
      svg.append(s("line", {x1: pad.l, x2: W - pad.r, y1: yy, y2: yy, class: g === 0 ? "chart-base" : "chart-grid"}));
      const t = s("text", {x: pad.l - 8, y: yy + 4, "text-anchor": "end", class: "chart-axis"}); t.textContent = g === 0 ? "0" : valueFmt(v); svg.append(t);
    }
    const step = Math.max(1, Math.round(n / (narrow ? 4 : 6)));
    for (let i = 0; i < n; i += step) {
      const t = s("text", {x: x(i), y: H - 6, "text-anchor": i === 0 ? "start" : i + step >= n ? "end" : "middle", class: "chart-axis"}); t.textContent = dayLabel(days[i]); svg.append(t);
    }
    const layers = series.map(se => ({se, pts: se.values.map((v, i) => [x(i), y(v || 0)])}));
    if (fill && layers.length === 1) {
      const pts = layers[0].pts;
      svg.append(s("path", {d: linePath(pts) + ` L${x(n - 1).toFixed(1)},${y(0).toFixed(1)} L${x(0).toFixed(1)},${y(0).toFixed(1)} Z`, class: "chart-area"}));
    }
    // Instagram under YouTube so the white line stays on top.
    for (const l of [...layers].sort((a, b) => (a.se.tone === "yt") - (b.se.tone === "yt"))) svg.append(s("path", {d: linePath(l.pts), class: `chart-line tone-${l.se.tone}`}));
    const hl = s("line", {class: "chart-hover", y1: pad.t, y2: pad.t + ih, opacity: 0}); svg.append(hl);
    const dots = layers.map(l => { const d = s("circle", {r: 3.5, class: `chart-dot tone-${l.se.tone}`, opacity: 0}); svg.append(d); return d; });
    const tt = h("div", {class: "chart-tip", style: {opacity: 0}, "aria-hidden": "true"});
    const hit = s("rect", {x: pad.l, y: pad.t, width: iw, height: ih, fill: "transparent", class: "chart-hit"}); svg.append(hit);
    el.append(svg, tt);
    const live = h("div", {class: "sr-only", "aria-live": "polite"}); el.append(live);
    const show = i => {
      hl.setAttribute("x1", x(i)); hl.setAttribute("x2", x(i)); hl.setAttribute("opacity", 1);
      layers.forEach((l, k) => { dots[k].setAttribute("cx", l.pts[i][0]); dots[k].setAttribute("cy", l.pts[i][1]); dots[k].setAttribute("opacity", 1); });
      clear(tt).append(h("div", {class: "chart-tip-day"}, dayLabel(days[i])));
      for (const l of layers) tt.append(h("div", {class: "chart-tip-row"}, h("span", {class: "chart-tip-name"}, lineKey(l.se.tone), l.se.name), h("strong", {class: "num"}, fmt.int(l.se.values[i] || 0))));
      if (series.length > 1) tt.append(h("div", {class: "chart-tip-row chart-tip-total"}, h("span", {class: "chart-tip-name"}, "Total"), h("strong", {class: "num"}, fmt.int(totals[i]))));
      const px = (x(i) / W) * el.clientWidth;
      const tw = tt.offsetWidth || 160;
      tt.style.left = Math.min(Math.max(px + 12, 0), el.clientWidth - tw) + "px";
      if (px + 12 + tw > el.clientWidth) tt.style.left = Math.max(0, px - 12 - tw) + "px";
      tt.style.top = pad.t + "px";
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
