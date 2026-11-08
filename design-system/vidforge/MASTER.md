# Design System Master File

> **LOGIC:** When building a specific page, first check `design-system/pages/[page-name].md`.
> If that file exists, its rules **override** this Master file.
> If not, strictly follow the rules below.

---

**Project:** VidForge
**Generated:** 2026-11-08 07:53:36
**Category:** RPA / Automation Dashboard
**Design Dials:** Variance 7/10 (Balanced / Modern) | Motion 5/10 (Standard) | Density 7/10 (Standard)

---

## Global Rules

### Color Palette

| Role | Hex | CSS Variable |
|------|-----|--------------|
| Primary | `#0F172A` | `--color-primary` |
| On Primary | `#FFFFFF` | `--color-on-primary` |
| Secondary | `#1E293B` | `--color-secondary` |
| On Secondary | `#FFFFFF` | `--color-on-secondary` |
| Accent/CTA | `#16A34A` | `--color-accent` |
| On Accent/CTA | `#0F172A` | `--color-on-accent` |
| Background | `#020617` | `--color-background` |
| Foreground | `#F8FAFC` | `--color-foreground` |
| Card | `#0E1223` | `--color-card` |
| Card Foreground | `#F8FAFC` | `--color-card-foreground` |
| Muted | `#1A1E2F` | `--color-muted` |
| Muted Foreground | `#94A3B8` | `--color-muted-foreground` |
| Border | `#334155` | `--color-border` |
| Destructive | `#DC2626` | `--color-destructive` |
| On Destructive | `#FFFFFF` | `--color-on-destructive` |
| Ring | `#FFFFFF` | `--color-ring` |

**Color Notes:** Dark terminal + running green + failed red + queued amber

### Typography

- **Heading Font:** Fira Code
- **Body Font:** Fira Sans
- **Mood:** dashboard, data, analytics, code, technical, precise
- **Google Fonts:** [Fira Code + Fira Sans](https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Fira+Sans:wght@300;400;500;600;700&display=swap)

**CSS Import:**
```css
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Fira+Sans:wght@300;400;500;600;700&display=swap');
```

### Spacing Variables

*Density: 7/10 — Standard*

| Token | Value | Usage |
|-------|-------|-------|
| `--space-xs` | `4px` / `0.25rem` | Tight gaps |
| `--space-sm` | `8px` / `0.5rem` | Icon gaps, inline spacing |
| `--space-md` | `16px` / `1rem` | Standard padding |
| `--space-lg` | `24px` / `1.5rem` | Section padding |
| `--space-xl` | `32px` / `2rem` | Large gaps |
| `--space-2xl` | `48px` / `3rem` | Section margins |
| `--space-3xl` | `64px` / `4rem` | Hero padding |

### Shadow Depths

| Level | Value | Usage |
|-------|-------|-------|
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.05)` | Subtle lift |
| `--shadow-md` | `0 4px 6px rgba(0,0,0,0.1)` | Cards, buttons |
| `--shadow-lg` | `0 10px 15px rgba(0,0,0,0.1)` | Modals, dropdowns |
| `--shadow-xl` | `0 20px 25px rgba(0,0,0,0.15)` | Hero images, featured cards |

---

## Component Specs

### Buttons

```css
/* Primary Button */
.btn-primary {
  background: #16A34A;
  color: #0F172A;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  transition: all 200ms ease;
  cursor: pointer;
}

.btn-primary:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

/* Secondary Button */
.btn-secondary {
  background: transparent;
  color: #F8FAFC;
  border: 2px solid #0F172A;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  transition: all 200ms ease;
  cursor: pointer;
}
```

### Cards

```css
.card {
  background: #020617;
  border-radius: 12px;
  padding: 24px;
  box-shadow: var(--shadow-md);
  transition: all 200ms ease;
  cursor: pointer;
}

.card:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
}
```

### Inputs

```css
.input {
  padding: 12px 16px;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  font-size: 16px;
  transition: border-color 200ms ease;
}

.input:focus {
  border-color: #0F172A;
  outline: none;
  box-shadow: 0 0 0 3px #0F172A20;
}
```

### Modals

```css
.modal-overlay {
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
}

.modal {
  background: white;
  border-radius: 16px;
  padding: 32px;
  box-shadow: var(--shadow-xl);
  max-width: 500px;
  width: 90%;
}
```

---

## Style Guidelines

**Style:** Dark Mode (OLED)

**Keywords:** Dark theme, low light, high contrast, deep black, midnight blue, eye-friendly, OLED, night mode, power efficient

**Best For:** Night-mode apps, coding platforms, entertainment, eye-strain prevention, OLED devices, low-light

**Key Effects:** Minimal glow (text-shadow: 0 0 10px), dark-to-light transitions, low white emission, high readability, visible focus

### Page Pattern

**Pattern Name:** Real-Time / Operations Landing

- **Conversion Strategy:** Offer a demo or sandbox and show trust signals. Label telemetry as live only when backed by a current source, with update time and stale state. Provide pause/hide or update-frequency controls for tickers and previews, stop offscreen/hidden work, support keyboard controls, and render a static final snapshot under reduced motion.
- **CTA Placement:** Primary CTA in nav + After metrics
- **Section Order:** Hero (product + live preview or status) > Key metrics/indicators > How it works > CTA (Start trial / Contact)

---

## Motion

**Stagger List** (Standard) — Trigger: load or scroll | Duration: 300-450ms | Easing: `back.out(1.4)`

```js
gsap.from('.grid-item', { opacity: 0, scale: 0.92, y: 16, duration: 0.4, stagger: { each: 0.06, from: 'start', grid: 'auto' }, ease: 'back.out(1.4)' });
```

**Framework notes:** grid: 'auto' lets GSAP infer rows/columns from a CSS grid layout for a natural wave stagger; Use matchMedia('(prefers-reduced-motion: reduce)') to skip non-essential motion and render the final state immediately

- ✅ Combine with from: 'center' for a bento-grid layout to draw the eye inward first
- ❌ Don't use back.out on dense data tables; the overshoot reads as sloppy on informational UI
- ⚡ Group DOM writes; avoid interleaving layout reads (getBoundingClientRect) between staggered tweens

---

## Anti-Patterns (Do NOT Use)

- ❌ Slow dashboards
- ❌ decorative charts
- ❌ hidden error states

### Additional Forbidden Patterns

- ❌ **Emojis as icons** — Use SVG icons (Heroicons, Lucide, Simple Icons)
- ❌ **Missing cursor:pointer** — All clickable elements must have cursor:pointer
- ❌ **Layout-shifting hovers** — Avoid scale transforms that shift layout
- ❌ **Low contrast text** — Maintain 4.5:1 minimum contrast ratio
- ❌ **Instant state changes** — Always use transitions (150-300ms)
- ❌ **Invisible focus states** — Focus states must be visible for a11y

---

## Pre-Delivery Checklist

Before delivering any UI code, verify:

- [ ] No emojis used as icons (use SVG instead)
- [ ] All icons from consistent icon set (Heroicons/Lucide)
- [ ] `cursor-pointer` on all clickable elements
- [ ] Hover states with smooth transitions (150-300ms)
- [ ] Light mode: text contrast 4.5:1 minimum
- [ ] Focus states visible for keyboard navigation
- [ ] `prefers-reduced-motion` respected
- [ ] Responsive: 375px, 768px, 1024px, 1440px
- [ ] No content hidden behind fixed navbars
- [ ] No horizontal scroll on mobile


## VidForge overrides (revised 2026-11-08 at the owner's request, these win over everything above)

Owner feedback on the glass/gradient version: "looks so AI generated". New direction: **clean black and white,
boxy, Apple OS-like** (macOS System Settings, Finder, Activity Monitor). Styles: Apple Native Experience +
Minimalism & Swiss Style, dark appearance only.

- Colour: monochrome only. Window #000000, sidebar #0A0A0A, surfaces #111111 and #161616, hover #1C1C1C,
  hairline separators #262626, strong border #333333. Labels #FFFFFF, #A1A1A1 (secondary), #6B6B6B (tertiary).
  Primary button: white fill, black text. Secondary: #161616 fill, 1px #333 border, white text.
  Status is shown with text + a 6px dot in greyscale (filled white = posted, ring = ready, half = making,
  dash = failed); the only non-grey colour allowed is a muted red #FF453A for errors and destructive actions.
  Platform marks are monochrome glyphs, never brand colours. Charts: white line for YouTube, #8A8A8A dashed for
  Instagram, no fills except a 6% white area under the selected series.
- No gradients, no glow, no aurora, no blur-heavy glass, no coloured shadows, no emoji, no gradient text.
  At most one hairline shadow on popovers and sheets (0 8px 24px rgba(0,0,0,.6)).
- Shape: boxy. Radius 6px on controls and cards, 8px on sheets/popovers, 4px on chips/tags, 0 on tables.
  1px borders define every box; spacing on a strict 8pt grid; dense but breathable (density 7).
- Type: system stack (-apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", Inter, sans-serif),
  Inter only as fallback. Large title 26/700 -0.02em, title 20/600, headline 15/600, body 14/400,
  label 12/500 #A1A1A1, numerals tabular. No all-caps, no tracking tricks.
- Layout (macOS): left sidebar 220px with section labels ("Workspace", "Account"), SF-Symbols-like 16px line icons,
  selected item = #1C1C1C box with white text; unified toolbar 52px tall with title on the left, actions right.
  Content max width 1280, 24px gutters. Dashboard uses a plain grid of equal-height boxes (not a bento collage):
  a 4-up metric row (label above, number, small grey delta text), one full-width chart box with a segmented
  control (All | YouTube | Instagram) in its header, then two columns (Autopilot + Making now | Recent runs),
  then a Top videos table with row hover.
- Controls: macOS-style segmented control (boxy, 1px border, selected segment #2A2A2A), checkbox-style toggles or
  compact switches in white/grey, inputs 32px tall with 1px #333 border and 6px radius, focus ring 2px white at
  40% opacity. Chips are square-ish tags with 1px border, selected = white fill + black text.
- Start page: black, a single headline in white, one line of grey copy, white "Sign in" button, a monochrome
  phone/video frame, a plain 5-step list ("Find trend, Research, Write and direct, Render, Post") in a bordered
  box, and the sign-in form. No decorative elements.
- Motion: 120 to 180 ms ease-out on hover/press and sheet open only. No staggered entrances. Reduced motion respected.
