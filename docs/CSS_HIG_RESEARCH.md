# CSS / HIG / HUD Engineering Reference — Job Hunter Pro Cockpit

Dense, cited reference for hand-written vanilla CSS/JS (no framework), files ≤150 lines,
degrading gracefully on low-end ARM Android and respecting `prefers-reduced-motion` / `Save-Data`.
Compiled early 2026 from authoritative sources (MDN, web.dev, WebKit blog, caniuse, Baseline).
Default posture: **ship the honest HTML/CSS tier unconditionally; gate every richness behind
`@supports` / JS feature-detection.**

> Versioning note: Apple moved to year-based naming Sept 2025. **iOS Safari 26 = iOS 26**;
> "18.x" was the prior generation. Devices stuck on iOS ≤18 never get 26-only features.

---

## 0. Implement-now vs Later (this pass)

| ✅ Implement now | 📋 Later / enhancement-only |
|---|---|
| 44px tap targets (`--tap`) | scroll-driven large-title collapse (iOS 26 only) |
| `safe-area-inset` env() | View Transitions drawer morph (enhance) |
| cubic-bezier iOS easing | `light-dark()` glass (enhance, fallback to media query) |
| OKLCH single-hue ramp + `color-mix()` | relative-color `oklch(from …)` (enhance) |
| `backdrop-filter` blur+saturate (`-webkit-` first) + opaque fallback | Popover API (enhance, `<details>` fallback) |
| `:has()`, subgrid, `@layer`, container size queries | `@starting-style` entry anims (enhance) |
| `text-wrap: balance/pretty` | `content-visibility: auto` long lists (enhance) |
| variable-font weight = confidence | `@property` typed-prop tweens (enhance) |
| SVG stroke-dashoffset gauges (geometric cap) | anchor positioning (**skip** — iOS ≤25 excluded) |
| custom-prop→visual binding (`calc(var(--conf)*40px)`) | `corner-shape: squircle` (**skip** — Chromium-only) |
| reduced-motion / reduced-transparency honor | Houdini Paint, WebGPU (**skip** core) |
| IndexedDB offline batch cache + manifest install | |

---

## 1. Apple HIG → Web

**1.1 Tap targets — ADOPT.** HIG = 44×44pt; WCAG 2.5.5 (AAA) aligns. Coarse pointers 44px, fine pointers may shrink to 32px.
```css
:root { --tap: 44px; }
.nav-btn, .btn, .icon-btn { min-height: var(--tap); }
@media (pointer: fine) { .btn { min-height: 32px; } }
```
Guard: `@media (pointer: coarse)`. Universal support.

**1.2 safe-area-inset — ADOPT (self-fallbacking).** Needs `viewport-fit=cover`. `env()` resolves to `0px` when absent.
```html
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
```
```css
.app-nav { padding-bottom: max(var(--s-2), env(safe-area-inset-bottom, 0px)); }
```
iOS 11+; all modern browsers.

**1.3 iOS easing — ADOPT cubic-bezier / ENHANCE `linear()` spring.** `cubic-bezier` cannot overshoot; `linear()` (Safari 17.2+) can do real spring/bounce.
```css
:root { --ease-ios: cubic-bezier(0.16, 1, 0.3, 1); }
@supports (transition-timing-function: linear(0,1)) {
  .drawer { transition-timing-function: linear(0, 0.4 7%, 1.02 40%, 0.99 70%, 1); }
}
```

**1.4 Large-title scroll collapse — ENHANCE.** CSS scroll-driven shipped **iOS Safari 26** only; JS fallback for older.
```css
@supports (animation-timeline: scroll()) {
  @media (prefers-reduced-motion: no-preference) {
    .hero__title { animation: shrink linear both; animation-timeline: scroll(nearest block); animation-range: 0 120px; }
    @keyframes shrink { to { font-size: var(--fs-4); opacity: .85; } }
  }
}
```
JS fallback gated by `if (!CSS.supports('animation-timeline: scroll()'))` with a passive `scroll` listener.

**1.5 Glass / vibrancy — ADOPT (prefix first, literal values).** iOS Safari needs `-webkit-backdrop-filter` **before** the standard property and **fails silently if a `var()` is placed inside the filter function** — use literals. `saturate()` reproduces vibrancy.
```css
.app-header, .app-nav, .bento {
  -webkit-backdrop-filter: blur(16px) saturate(1.4);   /* prefixed FIRST, literals only */
          backdrop-filter: blur(16px) saturate(1.4);
  background: var(--glass-regular);
}
@supports not ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
  .app-header, .app-nav, .bento { background: var(--c-void); }  /* near-opaque fallback */
}
@media (prefers-reduced-transparency: reduce) {
  .app-header, .app-nav, .bento { -webkit-backdrop-filter: none; backdrop-filter: none; background: var(--c-surface2); }
}
```

**1.6 Squircle — SKIP `corner-shape`.** `corner-shape: superellipse()/squircle` is **Chrome 139+ only**; Safari/Firefox parse-drop it. Keep `border-radius` as the universal base; layer squircle only inside `@supports (corner-shape: squircle)` as a bonus.

**1.7 Preference honoring — ADOPT motion+contrast / ENHANCE transparency.** `prefers-reduced-motion` and `prefers-contrast` have solid Safari support; `prefers-reduced-transparency` is Limited-availability (iOS may ignore — treat as enhancement). The media queries are themselves the detection (unmatched = safe no-op).

---

## 2. HUD / Cockpit Conventions

**2.1 Value→visual binding — ADOPT.** JS sets one number; CSS derives many visuals. Always default via `var(--x, 0)` so a missing API field renders an honest zero, never `NaN`.
```css
.node {
  --conf: 0;  /* el.style.setProperty('--conf', 0.82) */
  box-shadow: 0 0 calc(var(--conf) * 40px) oklch(70% 0.18 var(--accent-h) / var(--conf));
  filter: brightness(calc(0.5 + var(--conf) * 0.5));
}
```
A plain unregistered custom prop is a *string* → `transition: --conf` will NOT animate unless registered (see 2.6).

**2.2 SVG gauge with geometric ceiling — ADOPT.** Arc length is the physical cap; a low rating tier hardcodes the `clamp()` upper bound so the gauge is *physically incapable* of completing — this enforces the 60/15/15/10 review-score ceiling in geometry, not JS.
```css
/* C = 2πr; ARC = C * 270/360 for a 270° sweep. clamp upper bound = rating ceiling */
.gauge .fill {
  --pct: 0; fill: none; stroke: var(--accent); stroke-width: 8; stroke-linecap: round;
  stroke-dasharray: 254.47 339.29;
  stroke-dashoffset: calc(254.47 - (clamp(0, var(--pct), 92) / 100) * 254.47);
  transform: rotate(135deg); transform-origin: 60px 60px;
  transition: stroke-dashoffset .6s var(--ease-ios);
}
```
SVG dasharray Baseline ~decade; `<meter>` or CSS bar (`width: calc(var(--pct)*1%)`) is the fallback.

**2.3 Radar rings + pins — ADOPT (rotate) / ENHANCE (trig).** Rings = absolutely-positioned circles; pins via rotate→translate→counter-rotate, or `sin()/cos()` (Baseline 2023). Ambiguous-place "oscillation" = small `@keyframes` toggling `--ang` between two candidate bearings. Outside-radius pins drop opacity and push back.

**2.4 Pipeline node-graph + SSE — ADOPT grid+SVG / ENHANCE SSE.** Nodes on a CSS grid (accessible, clickable); connectors as one absolute SVG overlay (`pointer-events:none`). Stream via `EventSource` (Baseline, auto-reconnects ~3s, sends `Last-Event-ID`). **If no SSE endpoint exists, render an explicit "stream unavailable" idle state — never fake motion.** Guard: `if ('EventSource' in window)`.

**2.5 Confidence in typography — ADOPT.** Tie `wght`/`opsz` to a score so low confidence renders structurally soft.
```css
.bento__title { font-optical-sizing: auto; transition: font-weight .3s; }
[data-confidence="low"]  .bento__title { font-weight: 300; opacity: .75; }
[data-confidence="mid"]  .bento__title { font-weight: 500; }
[data-confidence="high"] .bento__title { font-weight: 700; }
```
Variable-font weight Baseline (Safari 11 / 16.4 keyframe fixes). Honor reduced-motion by dropping the transition.

**2.6 `@property` typed props — ENHANCE.** Registration types a custom prop so it can be interpolated — the missing piece for `transition: --conf`, gradient-stop and glow tweens. Baseline "Newly available" since July 2024 (Chrome 85, Safari 16.4, Firefox 128) → ~95%+ in 2026, but treat the *tween* as enhancement; without it the visual still renders at its final value (no smooth tween, data intact).
```css
@property --glow { syntax: '<length>'; inherits: false; initial-value: 0px; }
```

---

## 3. Modern CSS Support Matrix (early 2026)

| # | Capability | iOS Safari first | Verdict | Guard |
|---|---|---|---|---|
| 1 | Container **size** queries | 16.0 | adopt-now | `@supports (container-type: inline-size)` |
| 1 | Container **style** queries | 18.0 | enhance | none clean; treat as enhancement |
| 2 | `:has()` | 15.6 | adopt-now | `@supports selector(:has(*))` |
| 3 | Scroll-driven `scroll()/view()` | 26.0 | enhance | `@supports (animation-timeline: scroll())` |
| 4 | View Transitions (same-doc) | 18.0 | enhance | `if (document.startViewTransition)` |
| 5 | OKLCH + `color-mix()` | 16.4 / 16.2 | adopt-now | `@supports (color: oklch(0 0 0))` |
| 5 | Relative color `oklch(from …)` | 18.0 | enhance | `@supports (color: oklch(from red l c h))` |
| 6 | Anchor positioning | 26.0 | **skip** | `@supports (anchor-name: --a)` |
| 7 | Subgrid | 16.0 | adopt-now | `@supports (grid-template-columns: subgrid)` |
| 8 | `text-wrap: balance` | 17.5 | adopt-now | cosmetic, no guard |
| 8 | `text-wrap: pretty` | 26.0 | adopt-now (enhance) | cosmetic, no guard |
| 9 | `backdrop-filter` blur+saturate | 9 (`-webkit-`) | adopt-now (prefix first) | `@supports not ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px)))` |
| 10 | `@layer` | 17.0 | adopt-now | order source defensively |
| 11 | `light-dark()` | 17.5 | enhance | `@supports (color: light-dark(#fff,#000))` |
| 12 | Popover API | 17.0 (dismiss fix 18.3) | enhance | feature-detect `HTMLElement.prototype.popover` |
| 13 | Variable-font weight anim + `font-optical-sizing` | 11 / 16.4 | adopt-now | static-weight snap fallback |
| 14 | `@starting-style` | 17.5 | enhance | degrades silently (instant appear) |
| 15 | `content-visibility: auto` | 18.0 | enhance | `@supports (content-visibility: auto)` |

**Honest tier (adopt-now) build set:** size queries, `:has()`, OKLCH+`color-mix()`, subgrid, `text-wrap`, `@layer`, variable-font weight, prefixed `backdrop-filter`, custom-prop binding, SVG gauges. All work on the iOS 16–18 install base.

**Skip for load-bearing UI:** anchor positioning (iOS ≤25 excluded — use JS `getBoundingClientRect` for tooltips/drawer); `corner-shape` squircle (Chromium-only); Houdini Paint / WebGPU (ARM/mobile unsafe — document as future ambient tier only).

Key snippets:
```css
@layer reset, tokens, components, utilities;
.card-wrap { container-type: inline-size; }
@container (min-width: 400px) { .card { grid-template-columns: 1fr 1fr; } }
.field:has(input:invalid) { border-color: var(--danger); }
h1, h2 { text-wrap: balance; } p { text-wrap: pretty; }
.row { content-visibility: auto; contain-intrinsic-size: auto 60px; }  /* keep critical text OUT (find-in-page) */
```
```js
if (document.startViewTransition) document.startViewTransition(() => updateDOM());
else updateDOM();
```

---

## 4. iOS / PWA Native-Feel Persistence

**4.1 Storage choice.** IndexedDB for the JSON batch history (async, structured, keyed by batch_id, generous quota); Cache API (in SW) for the static shell only; localStorage only for trivial UI flags. **Never** cache-first the `/api/*` JSON endpoints.

| | localStorage | IndexedDB | Cache API |
|---|---|---|---|
| API | sync (blocks) | async | async |
| Data | strings ~5 MiB | structured objects/indexes | Request/Response |
| Use | tiny flags | **batch history** | app shell |

**4.2 Eviction / 7-day cap.** WebKit ITP wipes script-writable storage after **7 days of Safari use without interaction** — but **home-screen web apps are exempt** (verified against WebKit's own docs; some 2026 blogs claiming "regardless of installation" are wrong). Installation is the durability fix. Call `navigator.storage.persist()` to skip LRU eviction. The old ~50 MB cap is outdated; iOS 17+ gives home-screen apps ~60% of disk.

**4.3 Install on iOS.** No `beforeinstallprompt` — install is manual (Share → Add to Home Screen). Build an in-app hint when iOS + `navigator.standalone === false`. **Do not** add legacy `apple-mobile-web-app-capable` (web.dev: harms install); a correct manifest is honored. Keep `apple-touch-icon` + `<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">`.

**4.4 Manifest.**
```jsonc
{ "name": "Job Hunter Pro", "short_name": "JHP", "start_url": "/?source=pwa",
  "display": "standalone", "background_color": "#0a0e14", "theme_color": "#0a0e14",
  "icons": [ {"src":"/static/icons/192.png","sizes":"192x192","type":"image/png"},
             {"src":"/static/icons/512.png","sizes":"512x512","type":"image/png"},
             {"src":"/static/icons/maskable-512.png","sizes":"512x512","type":"image/png","purpose":"maskable"} ] }
```
iOS ignores manifest splash (uses `apple-touch-icon`); Android uses `background_color`. Maskable art inside central 40%-radius circle.

**4.5 Service worker.** Supported iOS 11.3+, richer 16.4+. **Cache-first shell, network-first (or network-only) `/api/*`**, IndexedDB fallback offline. Stale-cache pitfall: gate `controllerchange` auto-reload with a `refreshing` flag (avoid reload loops); prefer user-prompted update. Feature-detect `'serviceWorker' in navigator`.

**4.6 Offline batch cache.** Read IndexedDB first (instant, zero spend) → render with `cached` badge → revalidate over network when online → write back. Satisfies safe-boot (opening spends nothing). Never label cached data `live`.
```js
const open = indexedDB.open('jhp', 1);
open.onupgradeneeded = e => e.target.result.createObjectStore('batches', { keyPath: 'batch_id' });
```

---

## 5. Asset Strategy

**5.1 Icons — inline SVG (ADOPT).** Current `icon()` helper is correct: zero extra requests, full CSS control, perfect on any DPR. SVG `<symbol>` sprite only worth it when the *same* icon repeats dozens of times — **skip** for a modest cockpit set. PNG sprites and icon fonts — **skip** (lose retina/theming/a11y). Never pull an icon-font library (ARM weight).

**5.2 SVG best practices — ADOPT.** `fill="currentColor"` so icons re-tint per industry OKLCH accent; decorative → `aria-hidden="true" focusable="false"`, meaningful → `role="img" aria-label`; size via CSS (`1em` to track text), `viewBox` set + no fixed width/height in markup. Glow: `filter: drop-shadow(0 0 6px currentColor)` follows alpha shape. **Caveat:** `drop-shadow`/`blur` are GPU-expensive on ARM — small radius, don't animate, gate hover-only.

**5.3 Favicon + apple-touch set — ADOPT (5 files).** Design at 512; ship:
```html
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="icon" href="/icon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png"><!-- 180x180, no currentColor -->
<link rel="manifest" href="/manifest.webmanifest">
```
SVG favicon can carry a dark-mode `<style>`. iOS uses the single 180×180.

**5.4 image-set() / `<picture>` — ADOPT `<picture>` / ENHANCE image-set.** Content images via `<picture>` AVIF→WebP→raster; CSS backgrounds via `image-set()` (Chrome 113+/Safari 17+) with a plain `background-image` fallback first.
```html
<picture><source type="image/avif" srcset="hero.avif"><source type="image/webp" srcset="hero.webp">
  <img src="hero.png" alt="" width="800" height="450" loading="lazy" decoding="async"></picture>
```
AVIF first (~30–50% smaller than WebP). Never `loading="lazy"` on the above-fold hero (delays LCP). Always set width/height (CLS).

**5.5 When PNG/raster — ADOPT for photos/gradients/textures only.** Prefer AVIF→WebP, PNG as fallback. `loading="lazy" decoding="async"` below the fold.

**5.6 theme-color + OG — ADOPT.**
```html
<meta name="theme-color" content="#0d1117" media="(prefers-color-scheme: dark)">
<meta property="og:image" content="https://…/og.png"><!-- 1200x630, <1MB, static raster -->
```

**5.7 ARM lightness — ADOPT.** No icon-font libs / heavy sprites; SVGO the inline set; avoid animating `filter`/`backdrop-filter`/large blur on scroll; prefer CSS gradients/shapes over shipped raster textures (zero bytes, DPR-perfect); serve AVIF/WebP; lazy-load below-fold.

---

## 6. Project-Specific Fixes Identified

1. `base.css` / `layout.css`: ensure `-webkit-backdrop-filter` is emitted **before** the standard property everywhere, and never place a `var()` inside `backdrop-filter` (iOS fails silently) — use literal `blur(16px) saturate(1.4)`.
2. Add `@supports not (...)` opaque glass fallback + `prefers-reduced-transparency` honor.
3. Default every data-bound custom prop via `var(--x, 0)` to avoid `NaN` renders.
4. Use `@media (prefers-reduced-motion: reduce)` to disable pin oscillation, font breathing, gauge tweens.
5. Treat anchor positioning as off-limits for the filter drawer/tooltips on iOS ≤25 — use JS positioning or `<details>`/Popover with fallback.

---

## Sources

HIG: WCAG target-size (testparty.ai, logrocket); CSS-Tricks "Notch and CSS"; MDN `env()`;
Chrome `linear()` easing; Smashing `linear()`; WebKit scroll-driven; MDN scroll-driven;
mdn/browser-compat-data #25914 (backdrop-filter prefix); MDN `backdrop-filter`; Smashing/Frontend Masters `corner-shape`;
web.dev + caniuse `prefers-reduced-motion`; MDN `prefers-reduced-transparency`.

HUD: web.dev `@property` baseline; MDN Properties-and-Values API; MDN Firefox 128 notes; caniuse css-variables;
FullStack SVG gauge; nikitahl SVG circle progress; CSS-Tricks `stroke-dasharray`; MDN `stroke-dashoffset`;
una.im radial CSS trig; Codrops circular nav; MDN SSE; web.dev eventsource; MDN variable fonts; CSS-Tricks `font-optical-sizing`; 24ways variable fonts.

Modern CSS: web-features container-style-queries; logrocket container queries 2026; caniuse `:has()`; web.dev baseline2023;
caniuse animation-timeline scroll; WebKit scroll-driven; MDN animation-timeline; web.dev same-document View-Transitions Baseline;
Chrome View-Transitions 2025; MDN oklch / relative-colors; web.dev color-mix baseline; Chrome + oddbird + lambdatest anchor positioning;
web.dev + caniuse subgrid; caniuse text-wrap-balance; WebKit 17.5 notes; MDN + web.dev backdrop-filter; web.dev popover baseline;
MDN light-dark; web.dev @starting-style; joshwcomeau @starting-style; caniuse + lambdatest content-visibility; WebKit 16.4 notes.

PWA: MDN Storage quotas/eviction; WebKit full-third-party-cookie-blocking (7-day cap + home-screen exemption); WebKit tracking-prevention;
web.dev web-app-manifest; web.dev installation-prompt; Search Engine Land 7-day cap; MagicBell PWA iOS (corrected); JoeM-RP SW iOS 16.4 demo.

Assets: nucleoapp SVG systems; Cloud Four SVG stress test; CSS-Tricks SVG sprites; allsvgicons inline-vs-sprite;
MDN `drop-shadow`; CSS-Tricks SVG glow; Evil Martians favicon 2026; faviconbuilder sizes; iconmaker best-practices;
web.dev responsive-images; CSS-Tricks `image-set()`; savvy image-set fallbacks; w3tweaks filter perf; debugbear responsive images.

================================================================================
INCREMENT 2 — 2026-06-19 (this pass): patterns shipped + forward list
================================================================================
This increment records what the nav-fix / enrichment / résumé pass actually
implemented against the HIG/HUD/modern-CSS catalog above, plus the next tier.
Knowledge-based (model cutoff 2026-01); each item keeps a feature-detection guard.

SHIPPED THIS PASS (✅)
- color-scheme pinning: `:root { color-scheme: dark }` so `light-dark()` follows
  the APP theme, not the OS. Light theme opts in via `html[data-theme=light]
  { color-scheme: light }`. Fixes the white-glass-over-text nav regression.
  Guard: light-dark() already @supports-gated; color-scheme is universally safe.
- Confidence-bound AI research surface: per-LLM notes render only when a real
  note returns; dormant/error/skipped states are explicit. HUD law "spectacle
  earned by truth" — no note, no card content.
- Maskable + apple-touch PNG icon set (180/192/512 + maskable 192/512 + favicon)
  generated from the brand SVG; manifest `purpose:maskable` safe-zone padding so
  Android/iOS masks never clip the mark. Guard: SVG icon kept as `purpose:any`.
- Reduced-motion-gated entry animations (`card-in`) on research/résumé/audit
  sections; all disabled under `prefers-reduced-motion: reduce`.

FORWARD LIST (📋 next, each guarded)
- View-Transitions shared-element morph from a job card → evidence drawer
  (`document.startViewTransition`); fall back to the current spring sheet.
  Guard: `if (document.startViewTransition)`.
- Scroll-driven large-title collapse on the home hero via
  `animation-timeline: scroll(root)`; iOS Safari 26+ only. Guard:
  `@supports (animation-timeline: scroll())`.
- `:has()`-driven density: dim a bento grid that contains only unresolved cards
  (`.bento-grid:has(.bento--unresolved):not(:has(.bento:not(.bento--unresolved)))`).
  Guard: `@supports selector(:has(*))`.
- Anchor-positioned popovers for the research panel (drop the JS placement) once
  iOS Safari ships anchor positioning. Guard: `@supports (anchor-name: --x)` — SKIP
  on iOS ≤25 (documented above).
- `content-visibility: auto` on long job lists for cheaper scrolling on ARM.
  Guard: `@supports (content-visibility: auto)`.
- Résumé-fit gauge (SVG `stroke-dashoffset`) once the uploaded résumé provides
  weighted skills; keep the honest "no overlap" text fallback.
