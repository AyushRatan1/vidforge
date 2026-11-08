// VidForge component library. Every page composes only these pure functions, each returning a DOM node.
// Styles live in styles.css (tokens in tokens.css). Icons come from icons.js. No raw colours here.
//
//   DOM         h(tag, attrs, ...children)  clear(el)  append(el, children)  $(sel, root)
//   Actions     Button({label, variant, icon, size, onClick, type, disabled, ariaLabel, href, download, target, block})
//                 variant: primary (white) | secondary (dark, bordered) | ghost | destructive | icon
//   Surfaces    Card({title, subtitle, actions, body, footer, class, flush})      Box = Card
//               Grid(cols, children, {class})                                    plain grid of equal boxes
//               StatTile({label, value, delta: {cur, prev}, deltaLabel, hint, sample, onClick})
//   Controls    Segmented(items, value, onChange, {size})         -> el.set(v) el.value()
//               Switch(checked, onChange, label)                   -> el.set(v) el.checked()
//               Chip({label, selected, onClick, small, removable, onRemove})
//               ChipGroup(options, value, {multi, custom, small, onChange}) -> el.set(v) el.value()
//               Stepper(value, min, max, onChange, {label})        -> el.value() el.set(v)
//               Field({label, control, hint, error, id, inline})   wraps a control with label, helper and error
//               Input(attrs)  Textarea(attrs)  Select(options, value, onChange, attrs)
//               SecretInput({value, placeholder, onInput, ariaLabel})  masked with a reveal toggle
//   Status      Pill(text, tone)  a square tag; tone err is the only coloured one
//               Status(status)    greyscale glyph + text: filled = posted/done, ring = ready, half = making, dash = failed
//               PlatformMark(platform, href)   Avatar(nameOrEmail, {size})
//   Progress    ProgressRing({value 0..1, size, stroke, label})   ProgressBar(value 0..1)
//               StepList(steps, activeIndex, {done, failed, compact})
//   Lists       ListRow({title, sub, icon, iconTone, control, value, onClick, stacked, body})
//               Table({columns: [{key, label, align, width, render}], rows, caption, onRow})
//   Overlays    Sheet({title, body, onClose, wide}) -> dialog with open_() close()
//               toast(message, kind: ok | err | info)
//   Feedback    EmptyState({title, text, action, compact})   Skeleton({lines, height, class})

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
const svgFrom = markup => { const t = document.createElement("template"); t.innerHTML = markup.trim(); return t.content.firstChild; };

// ------------------------------------------------------------------ Button
export function Button({label, variant = "secondary", icon: ic, iconRight, size = "md", onClick, type = "button", disabled = false, ariaLabel, href, download, target, block = false, cls = "", busy = false} = {}) {
  const tag = href ? "a" : "button";
  const square = !label && (ic || variant === "icon");
  const el = h(tag, {
    class: `btn btn-${variant} btn-${size}${square ? " btn-square" : ""}${block ? " btn-block" : ""}${busy ? " is-busy" : ""} ${cls}`.trim(),
    type: href ? null : type, href: href || null, download: download || null, target: target || null, rel: target === "_blank" ? "noopener" : null,
    disabled: disabled || null, "aria-label": ariaLabel || null, "aria-busy": busy ? "true" : null, onClick,
  });
  if (busy) el.append(h("span", {class: "spinner", "aria-hidden": "true"}));
  if (ic) el.append(typeof ic === "string" ? icon(ic, {size: size === "sm" ? 14 : 16}) : ic);
  if (label) el.append(h("span", {class: "btn-label"}, label));
  if (iconRight) el.append(icon(iconRight, {size: 14}));
  el.setBusy = v => { el.classList.toggle("is-busy", v); el.disabled = v; el.setAttribute("aria-busy", String(!!v)); if (v && !el.querySelector(".spinner")) el.prepend(h("span", {class: "spinner", "aria-hidden": "true"})); if (!v) el.querySelector(".spinner")?.remove(); };
  return el;
}

// ------------------------------------------------------------------ Surfaces
export function Card({title, subtitle, actions, body, footer, class: cls = "", flush = false, as = "section"} = {}) {
  const el = h(as, {class: `card${flush ? " card-flush" : ""} ${cls}`.trim()});
  if (title || actions) {
    el.append(h("header", {class: "card-head"},
      h("div", {class: "card-heading"}, title ? h("h2", {class: "card-title"}, title) : null, subtitle !== undefined && subtitle !== null ? h("p", {class: "card-sub"}, subtitle) : null),
      actions ? h("div", {class: "card-actions"}, actions) : null));
  }
  if (body) el.append(h("div", {class: "card-body"}, body));
  if (footer) el.append(h("footer", {class: "card-foot"}, footer));
  return el;
}
export const Box = Card;

export function Grid(cols, children, {class: cls = ""} = {}) {
  return h("div", {class: `grid grid-${cols} ${cls}`.trim()}, children);
}

export function StatTile({label, value, delta, deltaLabel = "vs prior 7 days", hint, sample = false, onClick} = {}) {
  let foot = hint || "";
  if (delta) {
    const {cur, prev} = delta;
    foot = !prev ? (cur ? `None in the prior 7 days` : `No change ${deltaLabel}`) : `${pctText(cur, prev)} ${deltaLabel}`;
  }
  const el = h(onClick ? "button" : "section", {class: `card stat${onClick ? " is-clickable" : ""}`, type: onClick ? "button" : null, onClick},
    h("div", {class: "stat-label"}, h("span", {}, label), sample ? Pill("Sample") : null),
    h("div", {class: "stat-value num"}, value),
    h("div", {class: "stat-delta num"}, foot));
  return el;
}
function pctText(a, b) { const p = Math.round(((a - b) / b) * 100); return (p > 0 ? "+" : "") + p + "%"; }

// ------------------------------------------------------------------ Controls
export function Segmented(items, value, onChange, {size = "md", ariaLabel} = {}) {
  const el = h("div", {class: `seg seg-${size}`, role: "group", "aria-label": ariaLabel || null});
  const set = v => { value = v; for (const b of el.children) b.setAttribute("aria-pressed", String(b.dataset.v === String(v))); };
  for (const it of items) el.append(h("button", {type: "button", class: `seg-item${it.label ? "" : " seg-icon"}`, "data-v": String(it.value), "aria-pressed": String(it.value === value), "aria-label": it.ariaLabel || null, title: it.ariaLabel || null, onClick: () => { set(it.value); onChange?.(it.value); }}, it.icon ? icon(it.icon, {size: 14}) : null, it.label || null));
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

export function Chip({label, selected = false, onClick, small = false, removable = false, onRemove} = {}) {
  const el = h("button", {type: "button", class: `chip${small ? " chip-sm" : ""}`, "aria-pressed": String(!!selected), onClick}, h("span", {}, label));
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
      const chip = h("label", {class: `chip chip-custom${small ? " chip-sm" : ""}`, "aria-pressed": String(!!customVal)}, input);
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
  const dec = h("button", {type: "button", class: "stepper-btn", "aria-label": `Decrease ${label}`, onClick: () => set(value - 1)}, icon("minus", {size: 14}));
  const inc = h("button", {type: "button", class: "stepper-btn", "aria-label": `Increase ${label}`, onClick: () => set(value + 1)}, icon("plus", {size: 14}));
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
  const wrap = h("div", {class: "select-wrap"}, sel, icon("chevronDown", {size: 14, cls: "select-chev"}));
  wrap.input = sel; wrap.value = () => sel.value; wrap.set = v => sel.value = v;
  return wrap;
}
export function SecretInput({value = "", placeholder = "", onInput, ariaLabel, mono = true} = {}) {
  const inp = h("input", {class: `input${mono ? " mono" : ""}`, type: "password", value, placeholder, autocomplete: "off", spellcheck: "false", "aria-label": ariaLabel || null, onInput});
  const btn = h("button", {type: "button", class: "input-affix", "aria-label": "Show value", "aria-pressed": "false", onClick: () => { const show = inp.type === "password"; inp.type = show ? "text" : "password"; btn.setAttribute("aria-pressed", String(show)); btn.setAttribute("aria-label", show ? "Hide value" : "Show value"); clear(btn).append(icon(show ? "eyeOff" : "eye", {size: 14})); }}, icon("eye", {size: 14}));
  const wrap = h("div", {class: "input-wrap"}, inp, btn);
  wrap.input = inp;
  return wrap;
}

// ------------------------------------------------------------------ Status
export function Pill(text, tone = "neutral") {
  return h("span", {class: `tag${tone === "err" ? " tag-err" : tone === "strong" ? " tag-strong" : ""}`}, text);
}

// 8px box, 6px glyph. Greyscale; failed is the one error state and uses the error colour.
const GLYPH = {
  fill: '<svg class="glyph" viewBox="0 0 8 8" width="8" height="8" aria-hidden="true"><circle cx="4" cy="4" r="3" fill="currentColor"/></svg>',
  ring: '<svg class="glyph" viewBox="0 0 8 8" width="8" height="8" aria-hidden="true"><circle cx="4" cy="4" r="2.5" fill="none" stroke="currentColor" stroke-width="1"/></svg>',
  half: '<svg class="glyph" viewBox="0 0 8 8" width="8" height="8" aria-hidden="true"><circle cx="4" cy="4" r="2.5" fill="none" stroke="currentColor" stroke-width="1"/><path d="M4 1.5a2.5 2.5 0 0 0 0 5z" fill="currentColor"/></svg>',
  dash: '<svg class="glyph" viewBox="0 0 8 8" width="8" height="8" aria-hidden="true"><path d="M1 4h6" stroke="currentColor" stroke-width="1.5"/></svg>',
};
export const glyph = kind => svgFrom(GLYPH[kind] || GLYPH.ring);
const STATUS = {
  queued: ["Queued", "ring", "dim"], making: ["Making", "half"], running: ["Running", "half"],
  ready: ["Ready", "ring"], posted: ["Posted", "fill"], done: ["Done", "fill"], failed: ["Failed", "dash", "err"],
};
export function Status(status) {
  const [label, kind, tone] = STATUS[status] || [status ? status.charAt(0).toUpperCase() + status.slice(1) : "Unknown", "ring", "dim"];
  return h("span", {class: `status${tone ? " status-" + tone : ""}`, "data-status": status || ""}, glyph(kind), h("span", {class: "status-text"}, label));
}
export function PlatformMark(platform, href, {size = 16} = {}) {
  const name = platform === "youtube" ? "YouTube" : "Instagram";
  return h(href ? "a" : "span", {class: `mark${href ? "" : " mark-off"}`, href: href || null, target: href ? "_blank" : null, rel: href ? "noopener" : null, title: href ? `Open on ${name}` : `Not on ${name}`, "aria-label": href ? `Open on ${name}` : null, onClick: href ? e => e.stopPropagation() : null}, icon(platform, {size, label: href ? null : `Not on ${name}`}));
}
export function Avatar(name = "", {size = 28} = {}) {
  const initials = (name.split("@")[0].match(/[a-z0-9]/gi) || ["?"]).slice(0, 2).join("").toUpperCase();
  return h("span", {class: "avatar", style: {width: size + "px", height: size + "px", fontSize: Math.round(size * 0.4) + "px"}, "aria-hidden": "true"}, initials);
}

// ------------------------------------------------------------------ Progress
export function ProgressRing({value = 0, size = 64, stroke = 4, label, children} = {}) {
  const r = (size - stroke) / 2, c = 2 * Math.PI * r;
  const clamp = v => Math.min(1, Math.max(0, v));
  const svg = svgFrom(`<svg viewBox="0 0 ${size} ${size}" width="${size}" height="${size}" aria-hidden="true">
    <circle class="ring-track" cx="${size / 2}" cy="${size / 2}" r="${r}" stroke-width="${stroke}" fill="none"/>
    <circle class="ring-bar" cx="${size / 2}" cy="${size / 2}" r="${r}" stroke-width="${stroke}" fill="none" stroke-dasharray="${c}" stroke-dashoffset="${c * (1 - clamp(value))}" transform="rotate(-90 ${size / 2} ${size / 2})"/></svg>`);
  const el = h("div", {class: "ring", role: "progressbar", "aria-valuemin": 0, "aria-valuemax": 100, "aria-valuenow": Math.round(value * 100), "aria-label": label || "Progress", style: {width: size + "px", height: size + "px"}}, svg,
    h("div", {class: "ring-center"}, children ?? (label ? h("span", {class: "ring-label num"}, Math.round(value * 100) + "%") : null)));
  el.set = v => { svg.querySelector(".ring-bar").setAttribute("stroke-dashoffset", c * (1 - clamp(v))); el.setAttribute("aria-valuenow", Math.round(v * 100)); const l = el.querySelector(".ring-label"); if (l) l.textContent = Math.round(v * 100) + "%"; };
  return el;
}
export function ProgressBar(value = 0, {label = "Progress"} = {}) {
  const el = h("div", {class: "bar", role: "progressbar", "aria-valuemin": 0, "aria-valuemax": 100, "aria-valuenow": Math.round(value * 100), "aria-label": label}, h("div", {class: "bar-fill", style: {width: Math.round(value * 100) + "%"}}));
  el.set = v => { el.setAttribute("aria-valuenow", Math.round(v * 100)); el.firstChild.style.width = Math.round(v * 100) + "%"; };
  return el;
}
export function StepList(steps, activeIndex = -1, {done = false, failed = false, compact = false} = {}) {
  return h("ol", {class: `steps${compact ? " steps-compact" : ""}`}, ...steps.map((name, i) => {
    const state = done || i < activeIndex ? "done" : failed && i === activeIndex ? "failed" : i === activeIndex ? "active" : "todo";
    return h("li", {class: `step step-${state}`, "aria-current": state === "active" ? "step" : null},
      glyph(state === "done" ? "fill" : state === "failed" ? "dash" : state === "active" ? "half" : "ring"),
      h("span", {class: "step-name"}, name),
      h("span", {class: "sr-only"}, state === "done" ? " (done)" : state === "active" ? " (in progress)" : state === "failed" ? " (failed)" : ""));
  }));
}

// ------------------------------------------------------------------ Lists and tables
export function ListRow({title, sub, icon: ic, iconTone, control, value, onClick, stacked = false, body, leading, trailing} = {}) {
  const el = h(onClick ? "button" : "div", {class: `lrow${onClick ? " lrow-button" : ""}${stacked ? " lrow-stacked" : ""}${iconTone === "err" ? " lrow-err" : ""}`, type: onClick ? "button" : null, onClick});
  const main = h("div", {class: "lrow-main"}, h("div", {class: "lrow-title"}, title), sub ? h("div", {class: "lrow-sub"}, sub) : null);
  const head = h("div", {class: "lrow-head"});
  if (leading) head.append(h("span", {class: "lrow-lead"}, leading));
  else if (ic) head.append(h("span", {class: "lrow-icon"}, icon(ic, {size: 16})));
  head.append(main);
  if (value !== undefined) head.append(h("span", {class: "lrow-value num"}, value));
  if (control) head.append(h("span", {class: "lrow-control"}, control));
  if (trailing) head.append(trailing);
  if (onClick) head.append(icon("chevronRight", {size: 14, cls: "lrow-chev"}));
  el.append(head);
  if (body) el.append(h("div", {class: "lrow-body"}, body));
  return el;
}

export function Table({columns, rows, caption, onRow, empty: emptyText = "Nothing here yet"} = {}) {
  const cell = (tag, c, content) => h(tag, {scope: tag === "th" ? "col" : null, class: [c.align ? `align-${c.align}` : "", c.class || ""].join(" ").trim() || null, style: c.width ? {width: c.width} : null}, content);
  const table = h("table", {class: "table"}, caption ? h("caption", {class: "sr-only"}, caption) : null,
    h("thead", {}, h("tr", {}, ...columns.map(c => cell("th", c, c.label)))),
    h("tbody", {}, ...(rows.length ? rows.map(r => h("tr", {class: onRow ? "row-clickable" : null, tabIndex: onRow ? 0 : null, onClick: onRow ? () => onRow(r) : null, onKeydown: onRow ? e => { if (e.key === "Enter") onRow(r); } : null},
      ...columns.map(c => cell("td", c, c.render ? c.render(r) : r[c.key])))) : [h("tr", {}, h("td", {colSpan: columns.length, class: "table-empty"}, emptyText))])));
  return h("div", {class: "table-wrap"}, table);
}

// ------------------------------------------------------------------ Overlays
export function Sheet({title, body, onClose, wide = false, subtitle} = {}) {
  const dlg = h("dialog", {class: `sheet${wide ? " sheet-wide" : ""}`, "aria-label": title || "Details"});
  const closeBtn = Button({variant: "icon", icon: "x", ariaLabel: "Close", onClick: () => dlg.close()});
  const head = h("header", {class: "sheet-head"}, h("div", {class: "sheet-heading"}, h("h2", {class: "sheet-title", tabIndex: -1, autofocus: true}, title || ""), subtitle ? h("p", {class: "sheet-sub"}, subtitle) : null), closeBtn);
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
  const t = h("div", {class: `toast toast-${kind}`}, icon(kind === "ok" ? "check" : kind === "err" ? "warning" : "info", {size: 16}), h("span", {}, message));
  toastHost.append(t);
  const ms = timeout || (kind === "err" ? 6500 : 3500);
  setTimeout(() => t.remove(), ms);
  return t;
}

// ------------------------------------------------------------------ Feedback
export function EmptyState({title, text, action, compact = false} = {}) {
  return h("div", {class: `empty${compact ? " empty-compact" : ""}`}, h("p", {class: "empty-title"}, title), text ? h("p", {class: "empty-text"}, text) : null, action ? h("div", {class: "empty-action"}, action) : null);
}
export function Skeleton({lines = 3, height, class: cls = ""} = {}) {
  if (height) return h("div", {class: `skeleton ${cls}`, style: {height: typeof height === "number" ? height + "px" : height}, "aria-hidden": "true"});
  return h("div", {class: `skeleton-lines ${cls}`, "aria-hidden": "true"}, ...[...Array(lines)].map((_, i) => h("div", {class: "skeleton", style: {width: (100 - i * 15) + "%"}})));
}
