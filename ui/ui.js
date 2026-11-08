// Small DOM helpers, SF Symbols-like icons and the controls every page shares.

export function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") el.className = v;
    else if (k === "html") el.innerHTML = v;
    else if (k === "value") el.value = v;
    else if (k.startsWith("on") && typeof v === "function") el.addEventListener(k.slice(2).toLowerCase(), v);
    else if (k === "style" && typeof v === "object") Object.assign(el.style, v);
    else if (k in el && typeof v !== "string" && k !== "list") el[k] = v;
    else el.setAttribute(k, v === true ? "" : v);
  }
  append(el, children);
  return el;
}
export function append(el, children) {
  for (const c of children.flat(Infinity)) {
    if (c === null || c === undefined || c === false) continue;
    el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return el;
}
export function clear(el) { while (el.firstChild) el.removeChild(el.firstChild); return el; }
export const $ = (sel, root = document) => root.querySelector(sel);

// Icons: 24 viewBox, 1.5 stroke, round caps. Drawn to feel like SF Symbols.
const P = {
  grid: '<rect x="3.5" y="3.5" width="7" height="7" rx="2"/><rect x="13.5" y="3.5" width="7" height="7" rx="2"/><rect x="3.5" y="13.5" width="7" height="7" rx="2"/><rect x="13.5" y="13.5" width="7" height="7" rx="2"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  plusCircle: '<circle cx="12" cy="12" r="8.5"/><path d="M12 8.5v7M8.5 12h7"/>',
  library: '<rect x="3.5" y="5.5" width="17" height="13" rx="2.5"/><path d="M10 9.5v5l4.5-2.5z" fill="currentColor" stroke="none"/>',
  gear: '<circle cx="12" cy="12" r="3"/><path d="M12 3.5v2M12 18.5v2M3.5 12h2M18.5 12h2M6 6l1.4 1.4M16.6 16.6 18 18M6 18l1.4-1.4M16.6 7.4 18 6"/>',
  play: '<path d="M8 6.5v11l9-5.5z" fill="currentColor" stroke="none"/>',
  check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
  x: '<path d="M6.5 6.5l11 11M17.5 6.5l-11 11"/>',
  xCircle: '<circle cx="12" cy="12" r="8.5"/><path d="M9.5 9.5l5 5M14.5 9.5l-5 5"/>',
  chevron: '<path d="m9 6 6 6-6 6"/>',
  chevronDown: '<path d="m6 9 6 6 6-6"/>',
  arrowUp: '<path d="M12 19V5M6 11l6-6 6 6"/>',
  arrowDown: '<path d="M12 5v14M6 13l6 6 6-6"/>',
  minus: '<path d="M6 12h12"/>',
  search: '<circle cx="11" cy="11" r="6.5"/><path d="m16 16 4.5 4.5"/>',
  eye: '<path d="M2.5 12s3.5-6.5 9.5-6.5S21.5 12 21.5 12s-3.5 6.5-9.5 6.5S2.5 12 2.5 12z"/><circle cx="12" cy="12" r="2.8"/>',
  eyeOff: '<path d="M3.5 3.5l17 17M10 5.8A10 10 0 0 1 12 5.5c6 0 9.5 6.5 9.5 6.5a16 16 0 0 1-3.2 3.9M6.4 6.9A15.6 15.6 0 0 0 2.5 12s3.5 6.5 9.5 6.5a9.6 9.6 0 0 0 3.6-.7"/><path d="M9.9 9.9a2.8 2.8 0 0 0 4 4"/>',
  download: '<path d="M12 4v11M7.5 10.5 12 15l4.5-4.5M5 19h14"/>',
  link: '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',
  copy: '<rect x="8.5" y="8.5" width="11" height="11" rx="2.5"/><path d="M15.5 8.5v-2a2 2 0 0 0-2-2h-7a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h2"/>',
  trash: '<path d="M4.5 7h15M9.5 7V5a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1v2M7 7l.8 12a1 1 0 0 0 1 1h6.4a1 1 0 0 0 1-1L17 7"/>',
  sparkle: '<path d="M12 3.5l1.8 5.2 5.2 1.8-5.2 1.8L12 17.5l-1.8-5.2L5 10.5l5.2-1.8z"/><path d="M19 16.5l.7 1.8 1.8.7-1.8.7-.7 1.8-.7-1.8-1.8-.7 1.8-.7z"/>',
  bolt: '<path d="M13 3.5 5.5 13.5h6l-1 7 8-10.5h-6z"/>',
  clock: '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
  film: '<rect x="3.5" y="4.5" width="17" height="15" rx="2.5"/><path d="M7.5 4.5v15M16.5 4.5v15M3.5 9h4M16.5 9h4M3.5 15h4M16.5 15h4"/>',
  upload: '<path d="M12 15V4M7.5 8.5 12 4l4.5 4.5M5 19h14"/>',
  warn: '<path d="M12 4.5 3 19.5h18z"/><path d="M12 10v4.5M12 17v.5"/>',
  info: '<circle cx="12" cy="12" r="8.5"/><path d="M12 11v5M12 8v.5"/>',
  person: '<circle cx="12" cy="8.5" r="3.5"/><path d="M5 19.5c1.2-3.3 3.8-5 7-5s5.8 1.7 7 5"/>',
  logout: '<path d="M10 4.5H6a1.5 1.5 0 0 0-1.5 1.5v12A1.5 1.5 0 0 0 6 19.5h4M15 8l4 4-4 4M19 12H9.5"/>',
  refresh: '<path d="M20 12a8 8 0 0 1-14.5 4.6M4 12a8 8 0 0 1 14.5-4.6"/><path d="M18.5 3.5v4h-4M5.5 20.5v-4h4"/>',
  ext: '<path d="M14 4.5h5.5V10M19.5 4.5 11 13M18 14v4.5a1 1 0 0 1-1 1H5.5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1H10"/>',
  youtube: '<path d="M21.6 7.2c-.2-.9-.9-1.6-1.8-1.8C18.2 5 12 5 12 5s-6.2 0-7.8.4c-.9.2-1.6.9-1.8 1.8C2 8.8 2 12 2 12s0 3.2.4 4.8c.2.9.9 1.6 1.8 1.8C5.8 19 12 19 12 19s6.2 0 7.8-.4c.9-.2 1.6-.9 1.8-1.8.4-1.6.4-4.8.4-4.8s0-3.2-.4-4.8zM10 15V9l5.2 3L10 15z" fill="currentColor" stroke="none"/>',
  instagram: '<rect x="3.5" y="3.5" width="17" height="17" rx="4.5"/><circle cx="12" cy="12" r="4"/><circle cx="17.3" cy="6.7" r="1" fill="currentColor" stroke="none"/>',
  phone: '<rect x="6.5" y="2.5" width="11" height="19" rx="2.5"/><path d="M10.5 5.5h3"/>',
};
export function icon(name, cls = "") {
  const t = document.createElement("template");
  t.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" class="${cls}">${P[name] || ""}</svg>`;
  return t.content.firstChild;
}

// Segmented control: items = [{value, label}], onChange(value)
export function segmented(items, value, onChange, cls = "") {
  const el = h("div", {class: "seg " + cls, role: "group"});
  const set = v => { value = v; for (const b of el.children) b.setAttribute("aria-pressed", String(b.dataset.v === v)); };
  for (const it of items) el.append(h("button", {type: "button", "data-v": it.value, "aria-pressed": String(it.value === value), onClick: () => { set(it.value); onChange?.(it.value); }}, it.label));
  el.value = () => value;
  el.set = set;
  return el;
}

// iOS-style switch
export function toggle(checked, onChange, label = "") {
  const el = h("button", {type: "button", class: "switch", role: "switch", "aria-checked": String(!!checked), "aria-label": label || null});
  el.addEventListener("click", () => { const v = el.getAttribute("aria-checked") !== "true"; el.setAttribute("aria-checked", String(v)); onChange?.(v); });
  el.checked = () => el.getAttribute("aria-checked") === "true";
  el.set = v => el.setAttribute("aria-checked", String(!!v));
  return el;
}

// Chip group. options = [{value,label}]; multi => array value; custom => trailing editable chip
export function chips(options, value, {multi = false, custom = false, onChange, small = false} = {}) {
  const el = h("div", {class: "chips", role: "group"});
  let selected = multi ? [...(value || [])] : value;
  const known = new Set(options.map(o => o.value));
  const render = () => {
    clear(el);
    for (const o of options) {
      const on = multi ? selected.includes(o.value) : selected === o.value;
      el.append(h("button", {type: "button", class: "chip" + (small ? " sm" : ""), "aria-pressed": String(on), onClick: () => {
        if (multi) selected = on ? selected.filter(v => v !== o.value) : [...selected, o.value];
        else selected = o.value;
        render(); onChange?.(selected);
      }}, o.label));
    }
    if (custom) {
      const customVal = multi ? selected.find(v => !known.has(v)) : (!known.has(selected) && selected ? selected : "");
      const input = h("input", {type: "text", placeholder: "Custom", value: customVal || "", "aria-label": "Custom value"});
      const chip = h("label", {class: "chip" + (small ? " sm" : ""), "aria-pressed": String(!!customVal)}, input);
      input.addEventListener("input", () => {
        const v = input.value.trim();
        if (multi) selected = [...selected.filter(x => known.has(x)), ...(v ? [v] : [])];
        else selected = v;
        chip.setAttribute("aria-pressed", String(!!v));
        for (const b of el.querySelectorAll("button.chip")) b.setAttribute("aria-pressed", String(multi ? selected.includes(b.textContent) : false));
        onChange?.(selected);
      });
      el.append(chip);
    }
  };
  render();
  el.value = () => selected;
  el.set = v => { selected = multi ? [...(v || [])] : v; render(); };
  return el;
}

export function stepper(value, min, max, onChange) {
  const val = h("span", {class: "val num"}, value);
  const set = v => { value = Math.min(max, Math.max(min, v)); val.textContent = value; onChange?.(value); };
  const el = h("div", {class: "stepper", role: "group"},
    h("button", {type: "button", "aria-label": "Decrease", onClick: () => set(value - 1)}, icon("minus")),
    val,
    h("button", {type: "button", "aria-label": "Increase", onClick: () => set(value + 1)}, icon("plus")));
  el.value = () => value;
  return el;
}

export function field(label, control, hint) {
  const id = control.id || ("f" + Math.random().toString(36).slice(2, 8));
  control.id = id;
  return h("div", {class: "field"}, h("label", {for: id}, label), control, hint ? h("div", {class: "hint"}, hint) : null);
}

export function row(opts) {
  const {title, sub, value, control, icon: ic, iconColor, onClick, stacked} = opts;
  const r = h(onClick ? "button" : "div", {class: "row" + (onClick ? " button" : "") + (stacked ? " stacked" : "") + (ic ? " inset-sep" : ""), type: onClick ? "button" : null, onClick});
  if (stacked) {
    r.append(h("div", {class: "row-head"}, h("div", {class: "row-main"}, h("div", {class: "row-title"}, title), sub ? h("div", {class: "row-sub"}, sub) : null), control || null));
    if (opts.body) r.append(opts.body);
    return r;
  }
  if (ic) r.append(h("span", {class: "row-icon", style: iconColor ? {background: iconColor} : null}, icon(ic)));
  r.append(h("div", {class: "row-main"}, h("div", {class: "row-title"}, title), sub ? h("div", {class: "row-sub"}, sub) : null));
  if (value !== undefined) r.append(h("span", {class: "row-value num"}, value));
  if (control) r.append(control);
  if (onClick) r.append(icon("chevron", "chev"));
  return r;
}

export function platformMark(p, href) {
  const el = h(href ? "a" : "span", {class: `mark ${p === "youtube" ? "yt" : "ig"}${href ? "" : " off"}`, href: href || null, target: href ? "_blank" : null, rel: "noopener", title: p === "youtube" ? "YouTube" : "Instagram", onClick: href ? e => e.stopPropagation() : null}, icon(p));
  return el;
}

export function statusPill(status) {
  const label = {queued: "Queued", making: "Making", ready: "Ready", posted: "Posted", failed: "Failed", running: "Running", done: "Done"}[status] || status;
  return h("span", {class: "pill " + status}, label);
}

export function empty(title, text, action) {
  return h("div", {class: "empty"}, h("strong", {}, title), text, action || null);
}

let toastHost;
export function toast(msg, kind = "") {
  toastHost ||= document.body.appendChild(h("div", {class: "toasts", "aria-live": "polite"}));
  const t = h("div", {class: "toast " + kind}, kind === "ok" ? icon("check") : kind === "err" ? icon("warn") : null, msg);
  toastHost.append(t);
  setTimeout(() => { t.style.opacity = "0"; setTimeout(() => t.remove(), 200); }, kind === "err" ? 6000 : 3200);
}

// Formatting
export const fmt = {
  int: n => (n ?? 0).toLocaleString("en-IN"),
  compact: n => { n = n ?? 0; if (n >= 1e7) return (n / 1e7).toFixed(1).replace(/\.0$/, "") + " Cr"; if (n >= 1e5) return (n / 1e5).toFixed(1).replace(/\.0$/, "") + " L"; if (n >= 1e3) return (n / 1e3).toFixed(n >= 1e4 ? 0 : 1).replace(/\.0$/, "") + "K"; return String(Math.round(n)); },
  usd: n => "$" + (n ?? 0).toFixed(2),
  dur: s => { s = Math.round(s || 0); return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`; },
  date: iso => iso ? new Date(iso).toLocaleDateString("en-IN", {day: "numeric", month: "short"}) : "",
  dateTime: iso => iso ? new Date(iso).toLocaleString("en-IN", {day: "numeric", month: "short", hour: "numeric", minute: "2-digit"}) : "",
  ago: iso => { if (!iso) return ""; const m = Math.round((Date.now() - new Date(iso)) / 60000); if (m < 1) return "just now"; if (m < 60) return m + " min ago"; const hh = Math.round(m / 60); if (hh < 24) return hh + " h ago"; return Math.round(hh / 24) + " d ago"; },
  pct: (a, b) => { if (!b) return a ? "new" : "0%"; const p = Math.round(((a - b) / b) * 100); return (p > 0 ? "+" : "") + p + "%"; },
};

export const LANGS = [["en", "English"], ["hi", "Hindi"], ["hinglish", "Hinglish"], ["es", "Spanish"], ["fr", "French"], ["it", "Italian"], ["pt", "Portuguese"]];
export const NICHES = [["space", "Space"], ["science", "Science"], ["tech", "Tech"], ["stories", "Stories"], ["mythology", "Mythology"], ["kids", "Kids"], ["news", "News explained"], ["sports", "Sports"], ["animals", "Animals"], ["food", "Food"], ["travel", "Travel"], ["trending", "Anything trending"]];
export const FORMATS = [["auto", "Auto"], ["facts", "Facts explainer"], ["trend", "Trend explained"], ["story", "Story"], ["toplist", "Top list"], ["festival", "Festival story"], ["quiz", "Quiz"], ["kids_learning", "Kids learning"], ["kids_story", "Kids story"]];
export const WRITERS = [["claude-opus-5-5", "Opus 5.5"], ["claude-fable-5-1", "Fable 5.1"], ["claude-sonnet-5-5", "Sonnet 5.5"]];
export const opts = pairs => pairs.map(([value, label]) => ({value, label}));
export const langName = code => Object.fromEntries(LANGS)[code] || code || "";
export const nicheName = code => Object.fromEntries(NICHES)[code] || code || "";
