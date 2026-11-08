// VidForge component library. Every page composes only these pure functions, each returning a DOM node.
// Styles live in styles.css (tokens in tokens.css). Icons come from icons.js. No raw colours here.
//
//   DOM         h(tag, attrs, ...children)  clear(el)  append(el, children)  $(sel, root)
//   Actions     Button({label, variant, icon, size, onClick, type, disabled, ariaLabel, href, download, target, block})
//                 variant: primary (gradient) | secondary (glass) | ghost | destructive | icon
//   Surfaces    Card({title, subtitle, actions, body, footer, class, flush})      GlassCard = Card
//               BentoTile({span: "1x1" | "2x1" | "2x2", title, subtitle, actions, body, footer, class, onClick, flush})
//               StatTile({label, value, delta: {cur, prev, inverse}, hint, icon, sample})
//   Controls    Segmented(items, value, onChange, {size})         -> el.set(v) el.value()
//               Switch(checked, onChange, label)                   -> el.set(v) el.checked()
//               Chip({label, selected, onClick, small, removable, onRemove})
//               ChipGroup(options, value, {multi, custom, small, onChange}) -> el.set(v) el.value()
//               Stepper(value, min, max, onChange, {label})        -> el.value() el.set(v)
//               Field({label, control, hint, error, id, inline})   wraps a control with label, helper and error
//               Input(attrs)  Textarea(attrs)  Select(options, value, onChange, attrs)
//               SecretInput({value, placeholder, onInput, ariaLabel})  masked with a reveal toggle
//   Status      Pill(text, tone)  tone: ok | warn | err | info | neutral | accent
//               Status(status)    maps queued/making/ready/posted/failed/running/done to a Pill with icon
//               PlatformMark(platform, href)   Avatar(nameOrEmail, {size})
//   Progress    ProgressRing({value 0..1, size, stroke, label, indeterminate})   ProgressBar(value 0..1)
//               StepList(steps, activeIndex, {done, failed, compact})
//   Lists       ListRow({title, sub, icon, iconTone, control, value, onClick, stacked, body})
//               Table({columns: [{key, label, align, render}], rows, caption, onRow})
//   Overlays    Sheet({title, body, onClose, wide}) -> dialog with open() close()
//               toast(message, kind: ok | err | info)
//               Tooltip(target, text)
//   Feedback    EmptyState({icon, title, text, action})   Skeleton({lines, height, class})
//   Navigation  Tabs(items, value, onChange)

import {icon} from "./icons.js";
export {icon};

// ------------------------------------------------------------------ DOM
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
let uid = 0;
const nextId = p => `${p}-${(++uid).toString(36)}`;

// ------------------------------------------------------------------ Button
export function Button({label, variant = "secondary", icon: ic, iconRight, size = "md", onClick, type = "button", disabled = false, ariaLabel, href, download, target, block = false, cls = "", busy = false} = {}) {
  const tag = href ? "a" : "button";
  const el = h(tag, {
    class: `btn btn-${variant} btn-${size}${block ? " btn-block" : ""}${busy ? " is-busy" : ""} ${cls}`.trim(),
    type: href ? null : type, href: href || null, download: download || null, target: target || null, rel: target === "_blank" ? "noopener" : null,
    disabled: disabled || null, "aria-label": ariaLabel || null, "aria-busy": busy ? "true" : null, onClick,
  });
  if (busy) el.append(h("span", {class: "spinner", "aria-hidden": "true"}));
  if (ic) el.append(typeof ic === "string" ? icon(ic, {size: size === "sm" ? 16 : 18}) : ic);
  if (label) el.append(h("span", {class: "btn-label"}, label));
  if (iconRight) el.append(icon(iconRight, {size: size === "sm" ? 16 : 18}));
  el.setBusy = v => { el.classList.toggle("is-busy", v); el.disabled = v; el.setAttribute("aria-busy", String(!!v)); if (v && !el.querySelector(".spinner")) el.prepend(h("span", {class: "spinner", "aria-hidden": "true"})); if (!v) el.querySelector(".spinner")?.remove(); };
  return el;
}

// ------------------------------------------------------------------ Surfaces
export function Card({title, subtitle, actions, body, footer, class: cls = "", flush = false, as = "section"} = {}) {
  const el = h(as, {class: `card glass${flush ? " card-flush" : ""} ${cls}`.trim()});
  if (title || actions) {
    el.append(h("header", {class: "card-head"},
      h("div", {class: "card-heading"}, title ? h("h2", {class: "card-title"}, title) : null, subtitle ? h("p", {class: "card-sub"}, subtitle) : null),
      actions ? h("div", {class: "card-actions"}, actions) : null));
  }
  if (body) el.append(h("div", {class: "card-body"}, body));
  if (footer) el.append(h("footer", {class: "card-foot"}, footer));
  return el;
}
export const GlassCard = Card;

export function BentoTile({span = "1x1", title, subtitle, actions, body, footer, class: cls = "", onClick, flush = false, label} = {}) {
  const el = Card({title, subtitle, actions, body, footer, flush, class: `tile tile-${span} ${cls}`.trim(), as: onClick ? "button" : "section"});
  if (onClick) { el.type = "button"; el.addEventListener("click", onClick); el.classList.add("tile-clickable"); }
  if (label) el.setAttribute("aria-label", label);
  return el;
}

export function StatTile({label, value, delta, hint, icon: ic, sample = false, span = "1x1", onClick}) {
  let deltaEl = null;
  if (delta) {
    const {cur, prev, inverse = false} = delta;
    const same = cur === prev, up = cur > prev;
    const good = same ? null : (up !== inverse);
    deltaEl = h("span", {class: `delta ${same ? "delta-flat" : good ? "delta-up" : "delta-down"}`, title: "Compared with the 7 days before"},
      same ? icon("minus", {size: 14}) : icon(up ? "trendUp" : "trendDown", {size: 14}), h("span", {class: "num"}, pctText(cur, prev)));
  }
  const body = h("div", {class: "stat"},
    h("div", {class: "stat-top"}, h("span", {class: "stat-label"}, label), ic ? h("span", {class: "stat-icon"}, icon(ic, {size: 16})) : null),
    h("div", {class: "stat-value num"}, value),
    h("div", {class: "stat-foot"}, deltaEl, hint ? h("span", {class: "stat-hint"}, hint) : null, sample ? Pill("Sample", "neutral", {small: true}) : null));
  return BentoTile({span, body, class: "tile-stat", onClick, flush: true});
}
function pctText(a, b) { if (!b) return a ? "new" : "0%"; const p = Math.round(((a - b) / b) * 100); return (p > 0 ? "+" : "") + p + "%"; }

// ------------------------------------------------------------------ Controls
export function Segmented(items, value, onChange, {size = "md", ariaLabel} = {}) {
  const el = h("div", {class: `seg seg-${size}`, role: "group", "aria-label": ariaLabel || null});
  const set = v => { value = v; for (const b of el.children) b.setAttribute("aria-pressed", String(b.dataset.v === String(v))); };
  for (const it of items) el.append(h("button", {type: "button", class: "seg-item", "data-v": String(it.value), "aria-pressed": String(it.value === value), onClick: () => { set(it.value); onChange?.(it.value); }}, it.icon ? icon(it.icon, {size: 16}) : null, it.label));
  el.value = () => value; el.set = set;
  return el;
}

export function Switch(checked, onChange, label = "") {
  const el = h("button", {type: "button", class: "switch", role: "switch", "aria-checked": String(!!checked), "aria-label": label || null}, h("span", {class: "switch-knob"}));
  el.addEventListener("click", () => { const v = el.getAttribute("aria-checked") !== "true"; el.setAttribute("aria-checked", String(v)); onChange?.(v); });
  el.checked = () => el.getAttribute("aria-checked") === "true";
  el.set = v => el.setAttribute("aria-checked", String(!!v));
  return el;
}

export function Chip({label, selected = false, onClick, small = false, removable = false, onRemove, icon: ic} = {}) {
  const el = h("button", {type: "button", class: `chip${small ? " chip-sm" : ""}`, "aria-pressed": String(!!selected), onClick}, ic ? icon(ic, {size: 14}) : null, h("span", {}, label));
  if (removable) el.append(h("span", {class: "chip-x", role: "button", "aria-label": `Remove ${label}`, tabIndex: 0, onClick: e => { e.stopPropagation(); onRemove?.(); }, onKeydown: e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); e.stopPropagation(); onRemove?.(); } }}, icon("x", {size: 12})));
  return el;
}

export function ChipGroup(options, value, {multi = false, custom = false, small = false, onChange, ariaLabel} = {}) {
  const el = h("div", {class: "chips", role: "group", "aria-label": ariaLabel || null});
  let selected = multi ? [...(value || [])] : value;
  const known = new Set(options.map(o => o.value));
  const render = () => {
    clear(el);
    for (const o of options) {
      const on = multi ? selected.includes(o.value) : selected === o.value;
      el.append(Chip({label: o.label, small, selected: on, onClick: () => {
        if (multi) selected = on ? selected.filter(v => v !== o.value) : [...selected, o.value];
        else selected = o.value;
        render(); onChange?.(selected);
      }}));
    }
    if (custom) {
      const customVal = multi ? selected.find(v => !known.has(v)) : (!known.has(selected) && selected ? selected : "");
      const input = h("input", {type: "text", placeholder: "Custom", value: customVal || "", "aria-label": "Custom value", size: 7});
      const chip = h("label", {class: `chip chip-custom${small ? " chip-sm" : ""}`, "aria-pressed": String(!!customVal)}, icon("penLine", {size: 14}), input);
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

export function Stepper(value, min, max, onChange, {label = "Value"} = {}) {
  const val = h("output", {class: "stepper-val num", "aria-live": "polite"}, value);
  const set = v => { value = Math.min(max, Math.max(min, v)); val.textContent = value; dec.disabled = value <= min; inc.disabled = value >= max; onChange?.(value); };
  const dec = h("button", {type: "button", class: "stepper-btn", "aria-label": `Decrease ${label}`, onClick: () => set(value - 1)}, icon("minus", {size: 16}));
  const inc = h("button", {type: "button", class: "stepper-btn", "aria-label": `Increase ${label}`, onClick: () => set(value + 1)}, icon("plus", {size: 16}));
  const el = h("div", {class: "stepper", role: "group", "aria-label": label}, dec, val, inc);
  dec.disabled = value <= min; inc.disabled = value >= max;
  el.value = () => value; el.set = v => { value = v; val.textContent = v; dec.disabled = v <= min; inc.disabled = v >= max; };
  return el;
}

export function Field({label, control, hint, error, id, inline = false, required = false} = {}) {
  const fid = id || control?.id || nextId("f");
  const isLabelable = control && /^(INPUT|TEXTAREA|SELECT)$/.test(control.tagName);
  if (isLabelable) control.id = fid;
  const hintEl = hint ? h("div", {class: "hint", id: fid + "-hint"}, hint) : null;
  const errEl = h("div", {class: "field-error", id: fid + "-err", role: "alert"}, error || "");
  if (isLabelable) { const ids = [hintEl && hintEl.id, error && errEl.id].filter(Boolean).join(" "); if (ids) control.setAttribute("aria-describedby", ids); if (error) control.setAttribute("aria-invalid", "true"); }
  const el = h("div", {class: `field${inline ? " field-inline" : ""}${error ? " has-error" : ""}`},
    h(isLabelable ? "label" : "div", {class: "field-label", for: isLabelable ? fid : null, id: isLabelable ? null : fid + "-label"}, label, required ? h("span", {class: "req", "aria-hidden": "true"}, " *") : null),
    control, hintEl, errEl);
  if (!isLabelable && control) control.setAttribute("aria-labelledby", fid + "-label");
  el.setError = msg => { errEl.textContent = msg || ""; el.classList.toggle("has-error", !!msg); if (isLabelable) { if (msg) control.setAttribute("aria-invalid", "true"); else control.removeAttribute("aria-invalid"); } };
  return el;
}

export const Input = (attrs = {}) => h("input", {class: "input", ...attrs});
export const Textarea = (attrs = {}) => h("textarea", {class: "input textarea", ...attrs});
export function Select(options, value, onChange, attrs = {}) {
  const sel = h("select", {class: "input select", onChange: e => onChange?.(e.target.value), ...attrs}, ...options.map(o => h("option", {value: o.value, selected: String(o.value) === String(value)}, o.label)));
  const wrap = h("div", {class: "select-wrap"}, sel, icon("chevronDown", {size: 16, cls: "select-chev"}));
  wrap.input = sel; wrap.value = () => sel.value; wrap.set = v => sel.value = v;
  return wrap;
}
export function SecretInput({value = "", placeholder = "", onInput, ariaLabel, mono = true} = {}) {
  const inp = h("input", {class: `input${mono ? " mono" : ""}`, type: "password", value, placeholder, autocomplete: "off", spellcheck: "false", "aria-label": ariaLabel || null, onInput});
  const btn = h("button", {type: "button", class: "input-affix", "aria-label": "Show value", "aria-pressed": "false", onClick: () => { const show = inp.type === "password"; inp.type = show ? "text" : "password"; btn.setAttribute("aria-pressed", String(show)); btn.setAttribute("aria-label", show ? "Hide value" : "Show value"); clear(btn).append(icon(show ? "eyeOff" : "eye", {size: 18})); }}, icon("eye", {size: 18}));
  const wrap = h("div", {class: "input-wrap"}, inp, btn);
  wrap.input = inp;
  return wrap;
}

// ------------------------------------------------------------------ Status
export function Pill(text, tone = "neutral", {small = false, icon: ic, dot = false} = {}) {
  return h("span", {class: `pill pill-${tone}${small ? " pill-sm" : ""}`}, dot ? h("span", {class: "pill-dot", "aria-hidden": "true"}) : null, ic ? icon(ic, {size: 12}) : null, text);
}
const STATUS = {
  queued: ["Queued", "neutral", "clock"], making: ["Making", "warn", "loader"], running: ["Running", "warn", "loader"],
  ready: ["Ready", "info", "check"], posted: ["Posted", "ok", "checkCircle"], done: ["Done", "ok", "check"], failed: ["Failed", "err", "warning"],
};
export function Status(status, {small = false} = {}) {
  const [label, tone, ic] = STATUS[status] || [status || "Unknown", "neutral", null];
  const el = Pill(label, tone, {small, icon: ic});
  if (status === "making" || status === "running") el.classList.add("pill-live");
  return el;
}
export function PlatformMark(platform, href, {size = 16} = {}) {
  const name = platform === "youtube" ? "YouTube" : "Instagram";
  const el = h(href ? "a" : "span", {class: `mark mark-${platform === "youtube" ? "yt" : "ig"}${href ? "" : " mark-off"}`, href: href || null, target: href ? "_blank" : null, rel: href ? "noopener" : null, title: href ? `Open on ${name}` : `Not on ${name}`, "aria-label": href ? `Open on ${name}` : null, onClick: href ? e => e.stopPropagation() : null}, icon(platform, {size, label: href ? null : `Not on ${name}`}));
  return el;
}
export function Avatar(name = "", {size = 32} = {}) {
  const initials = (name.split("@")[0].match(/[a-z0-9]/gi) || ["?"]).slice(0, 2).join("").toUpperCase();
  return h("span", {class: "avatar", style: {width: size + "px", height: size + "px", fontSize: Math.round(size * 0.38) + "px"}, "aria-hidden": "true"}, initials);
}

// ------------------------------------------------------------------ Progress
export function ProgressRing({value = 0, size = 64, stroke = 5, label, indeterminate = false, children} = {}) {
  const r = (size - stroke) / 2, c = 2 * Math.PI * r;
  const ns = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("viewBox", `0 0 ${size} ${size}`); svg.setAttribute("width", size); svg.setAttribute("height", size); svg.setAttribute("aria-hidden", "true");
  const id = nextId("ring");
  svg.innerHTML = `<defs><linearGradient id="${id}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" class="ring-stop-a"/><stop offset="1" class="ring-stop-b"/></linearGradient></defs>
    <circle class="ring-track" cx="${size / 2}" cy="${size / 2}" r="${r}" stroke-width="${stroke}" fill="none"/>
    <circle class="ring-bar" cx="${size / 2}" cy="${size / 2}" r="${r}" stroke-width="${stroke}" fill="none" stroke="url(#${id})" stroke-linecap="round" stroke-dasharray="${c}" stroke-dashoffset="${c * (1 - Math.min(1, Math.max(0, value)))}" transform="rotate(-90 ${size / 2} ${size / 2})"/>`;
  const el = h("div", {class: `ring${indeterminate ? " ring-indeterminate" : ""}`, role: "progressbar", "aria-valuemin": 0, "aria-valuemax": 100, "aria-valuenow": indeterminate ? null : Math.round(value * 100), "aria-label": label || "Progress", style: {width: size + "px", height: size + "px"}}, svg,
    h("div", {class: "ring-center"}, children ?? (label ? h("span", {class: "ring-label num"}, Math.round(value * 100) + "%") : null)));
  el.set = v => { const bar = svg.querySelector(".ring-bar"); bar.setAttribute("stroke-dashoffset", c * (1 - Math.min(1, Math.max(0, v)))); el.setAttribute("aria-valuenow", Math.round(v * 100)); const l = el.querySelector(".ring-label"); if (l) l.textContent = Math.round(v * 100) + "%"; };
  return el;
}
export function ProgressBar(value = 0, {label = "Progress", tone = "accent"} = {}) {
  const el = h("div", {class: `bar bar-${tone}`, role: "progressbar", "aria-valuemin": 0, "aria-valuemax": 100, "aria-valuenow": Math.round(value * 100), "aria-label": label}, h("div", {class: "bar-fill", style: {width: Math.round(value * 100) + "%"}}));
  el.set = v => { el.setAttribute("aria-valuenow", Math.round(v * 100)); el.firstChild.style.width = Math.round(v * 100) + "%"; };
  return el;
}
export function StepList(steps, activeIndex = -1, {done = false, failed = false, compact = false} = {}) {
  return h("ol", {class: `steps${compact ? " steps-compact" : ""}`}, ...steps.map((name, i) => {
    const state = done || i < activeIndex ? "done" : failed && i === activeIndex ? "failed" : i === activeIndex ? "active" : "todo";
    return h("li", {class: `step step-${state}`, "aria-current": state === "active" ? "step" : null},
      h("span", {class: "step-dot"}, state === "done" ? icon("check", {size: 12}) : state === "failed" ? icon("x", {size: 12}) : state === "active" ? h("span", {class: "step-pulse"}) : null),
      h("span", {class: "step-name"}, name),
      h("span", {class: "sr-only"}, state === "done" ? " (done)" : state === "active" ? " (in progress)" : state === "failed" ? " (failed)" : ""));
  }));
}

// ------------------------------------------------------------------ Lists and tables
export function ListRow({title, sub, icon: ic, iconTone, control, value, onClick, stacked = false, body, leading, trailing} = {}) {
  const el = h(onClick ? "button" : "div", {class: `lrow${onClick ? " lrow-button" : ""}${stacked ? " lrow-stacked" : ""}`, type: onClick ? "button" : null, onClick});
  const main = h("div", {class: "lrow-main"}, h("div", {class: "lrow-title"}, title), sub ? h("div", {class: "lrow-sub"}, sub) : null);
  const head = h("div", {class: "lrow-head"});
  if (leading) head.append(h("span", {class: "lrow-lead"}, leading));
  else if (ic) head.append(h("span", {class: `lrow-icon tone-${iconTone || "neutral"}`}, icon(ic, {size: 18})));
  head.append(main);
  if (value !== undefined) head.append(h("span", {class: "lrow-value num"}, value));
  if (control) head.append(h("span", {class: "lrow-control"}, control));
  if (trailing) head.append(trailing);
  if (onClick) head.append(icon("chevronRight", {size: 18, cls: "lrow-chev"}));
  el.append(head);
  if (body) el.append(h("div", {class: "lrow-body"}, body));
  return el;
}

export function Table({columns, rows, caption, onRow, empty: emptyText = "Nothing here yet"} = {}) {
  const table = h("table", {class: "table"}, caption ? h("caption", {class: "sr-only"}, caption) : null,
    h("thead", {}, h("tr", {}, ...columns.map(c => h("th", {scope: "col", class: c.align ? `align-${c.align}` : null}, c.label)))),
    h("tbody", {}, ...(rows.length ? rows.map(r => h("tr", {class: onRow ? "row-clickable" : null, tabIndex: onRow ? 0 : null, onClick: onRow ? () => onRow(r) : null, onKeydown: onRow ? e => { if (e.key === "Enter") onRow(r); } : null},
      ...columns.map(c => h("td", {class: c.align ? `align-${c.align}` : null}, c.render ? c.render(r) : r[c.key])))) : [h("tr", {}, h("td", {colSpan: columns.length, class: "table-empty"}, emptyText))])));
  return h("div", {class: "table-wrap"}, table);
}

// ------------------------------------------------------------------ Overlays
export function Sheet({title, body, onClose, wide = false, subtitle} = {}) {
  const dlg = h("dialog", {class: `sheet${wide ? " sheet-wide" : ""}`, "aria-label": title || "Details"});
  const closeBtn = Button({variant: "icon", icon: "x", ariaLabel: "Close", onClick: () => dlg.close()});
  const head = h("header", {class: "sheet-head"}, h("div", {class: "sheet-heading"}, h("h2", {class: "sheet-title"}, title || ""), subtitle ? h("p", {class: "sheet-sub"}, subtitle) : null), closeBtn);
  const content = h("div", {class: "sheet-body"}, body);
  dlg.append(head, content);
  dlg.addEventListener("click", e => { if (e.target === dlg) dlg.close(); });
  dlg.addEventListener("close", () => { onClose?.(); dlg.remove(); });
  dlg.open_ = () => { if (!dlg.isConnected) document.body.append(dlg); if (!dlg.open) dlg.showModal(); };
  dlg.setBody = node => clear(content).append(node);
  dlg.setTitle = t => { head.querySelector(".sheet-title").textContent = t; };
  return dlg;
}

let toastHost;
export function toast(message, kind = "info", {timeout} = {}) {
  toastHost ||= document.body.appendChild(h("div", {class: "toasts", "aria-live": "polite", role: "status"}));
  const t = h("div", {class: `toast toast-${kind}`}, icon(kind === "ok" ? "checkCircle" : kind === "err" ? "warning" : "info", {size: 18}), h("span", {}, message));
  toastHost.append(t);
  const ms = timeout || (kind === "err" ? 6500 : 3500);
  setTimeout(() => { t.classList.add("toast-out"); setTimeout(() => t.remove(), 220); }, ms);
  return t;
}

export function Tooltip(target, text) {
  const id = nextId("tip");
  const tip = h("span", {class: "tooltip", role: "tooltip", id}, text);
  target.setAttribute("aria-describedby", id);
  const wrap = h("span", {class: "tooltip-wrap"}, target, tip);
  return wrap;
}

// ------------------------------------------------------------------ Feedback
export function EmptyState({icon: ic = "sparkles", title, text, action, compact = false} = {}) {
  return h("div", {class: `empty${compact ? " empty-compact" : ""}`}, h("span", {class: "empty-icon"}, icon(ic, {size: compact ? 20 : 24})), h("strong", {class: "empty-title"}, title), text ? h("p", {class: "empty-text"}, text) : null, action ? h("div", {class: "empty-action"}, action) : null);
}
export function Skeleton({lines = 3, height, class: cls = ""} = {}) {
  if (height) return h("div", {class: `skeleton ${cls}`, style: {height: typeof height === "number" ? height + "px" : height}, "aria-hidden": "true"});
  return h("div", {class: `skeleton-lines ${cls}`, "aria-hidden": "true"}, ...[...Array(lines)].map((_, i) => h("div", {class: "skeleton", style: {width: (100 - i * 12) + "%"}})));
}

// ------------------------------------------------------------------ Navigation
export function Tabs(items, value, onChange, {ariaLabel = "Sections"} = {}) {
  const el = h("div", {class: "tabs", role: "tablist", "aria-label": ariaLabel});
  const set = v => { value = v; for (const b of el.children) { const on = b.dataset.v === String(v); b.setAttribute("aria-selected", String(on)); b.tabIndex = on ? 0 : -1; } };
  for (const it of items) el.append(h("button", {type: "button", role: "tab", class: "tab", "data-v": String(it.value), "aria-selected": String(it.value === value), tabIndex: it.value === value ? 0 : -1, onClick: () => { set(it.value); onChange?.(it.value); }, onKeydown: e => {
    const i = [...el.children].indexOf(e.currentTarget); const n = el.children.length;
    if (e.key === "ArrowRight" || e.key === "ArrowLeft") { e.preventDefault(); const j = (i + (e.key === "ArrowRight" ? 1 : n - 1)) % n; el.children[j].focus(); el.children[j].click(); }
  }}, it.icon ? icon(it.icon, {size: 16}) : null, it.label, it.count !== undefined ? h("span", {class: "tab-count num"}, it.count) : null));
  el.set = set; el.value = () => value;
  return el;
}
