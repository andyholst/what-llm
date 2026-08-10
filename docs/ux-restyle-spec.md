# what-llm UX Restyle Spec (Bootswatch Quartz)

**Scope:** replace `vendor/bootstrap.min.css` with one Bootswatch theme; edit only the inline `<style>` block (index.html lines 8–88). **Zero JS changes, zero ID/class renames, zero HTML structure changes** (only CSS + one vendor file swap). Verified against live page + local repo (JS emits `.card.h-100.shadow-sm` cards in `.row.g-3` → `.col-12.col-sm-6.col-lg-4`; wizard wrapper is `.bcard`; `.pcols`, `.cmptable`, `.profile`, `.srv-rec` are currently **unstyled**).

## 1. Theme: Quartz (dark, glassmorphic)

Bootswatch's flagship modern theme — dark glassmorphism fits an AI/hardware tool, is dark-native (so the app's light/dark split collapses to one curated dark look), and is one of the most popular themes on the site (https://bootswatch.com, "A glassmorphic layer").
Vendor URL (verify: `curl -sI` returns 200, CSS header says `Theme: quartz`):
`https://cdn.jsdelivr.net/npm/bootswatch@5.3.3/dist/quartz/bootstrap.min.css`
Download it **over** `vendor/bootstrap.min.css` (keep the filename — the `<link>` doesn't change). Do **not** load stock Bootstrap alongside it; Bootswatch bundles the full base.

## 2. Design decisions

- **Hero:** keep `<header>` markup; restyle as a soft hero band: `padding:1.5rem 0; margin-bottom:1.5rem;` h1 → `display-6 fw-bold`, badge → `text-bg-primary rounded-pill`, `.sub` → `text-body-secondary` (drop the em/hint styling; keep text).
- **Layout:** `.wrap` `max-width:860px` → `max-width:1140px` — the single biggest win; the JS-emitted 3-col grid gets ~350px cards instead of cramped 260px.
- **Cards:** delete the app's custom `.card` rule (lines 47–53) so Quartz's glass card (`--bs-card-bg: rgba(255,255,255,.08)`, radius ≈1rem, shadow) shows. Keep `.sel` but restyle: `border-color:var(--bs-primary); box-shadow:0 0 0 3px rgba(143,148,251,.35)`. Position the compare checkbox top-right: `.card .cmpbox{position:absolute; top:.75rem; right:.75rem; accent-color:var(--bs-primary)}` (pure CSS; JS just appends it). `.nm` → `fw-semibold`, `.au`/`.meta` → `small text-body-secondary`. `.tag`/`.fitbadge` → pills using `--bs-secondary-bg` / `--bs-success-text-emphasis` + `--bs-success-bg-subtle`.
- **Wizard:** keep `.bcard` class; restyle it as the card surface: `border:var(--bs-card-border-width) solid var(--bs-card-border-color); border-radius:var(--bs-card-border-radius); background:var(--bs-card-bg)`. Hide the details marker (`summary::-webkit-details-marker{display:none}`), `cursor:pointer`, add a chevron via `::after`. `.wrow.list-group-item` gets Quartz's list-group for free; style the recommended row (`border-left:3px solid var(--bs-success)`).
- **Details pane:** `.pane` → solid surface (Quartz paints a **gradient on `<body>`**, so give the pane a backdrop): `background:var(--bs-tertiary-bg); border:1px solid var(--bs-border-color); border-radius:var(--bs-border-radius-lg); padding:1.25rem`. `.chip` → `border-radius:999px; background:var(--bs-tertiary-bg)`; `.chip.sel` → `background:var(--bs-primary); color:#fff`. `.box.on/.off` → `--bs-success-bg-subtle/--bs-success-text-emphasis` and `--bs-secondary-bg/--bs-secondary-color`. `.pcols` (currently unstyled) → `display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:1rem`, h4 → `h6 text-uppercase text-body-secondary`. `.err` → `--bs-danger-bg-subtle/--bs-danger-text-emphasis`. `.srv-rec` → `alert alert-success` is fine on Quartz; just reduce to `py-2`.
- **Compare:** `.cmptable` (currently unstyled) → `width:100%; border-collapse:collapse;` `th,td{padding:.5rem .75rem; border-bottom:1px solid var(--bs-border-color); text-align:left}`; `th{font-size:.8rem; text-transform:uppercase; letter-spacing:.04em; color:var(--bs-secondary-color)}`; `#cmp-panel{overflow-x:auto}` for narrow screens.
- **Footer:** keep `border-top pt-3`; set `color:var(--bs-secondary-color)`.
- **Type/color/radius:** inherit Quartz's defaults (system font stack, ~1rem radii, soft shadows, violet-indigo `--bs-primary` #6f42c1-family). Reduce the app style block from ~80 lines to ~60 lines of overrides; delete the `:root` var block, the `@media (prefers-color-scheme: dark)` block, and the body/`#search`/`select`/`.card` rules — they mask the theme (custom rules load after the vendor link).
- **Dark mode:** Quartz is dark-only; the app's prefers-color-scheme machinery becomes dead weight — remove it. Do **not** set `data-bs-theme="light"` (it partially un-themes Quartz).

## 3. Prioritized checklist

1. Swap vendor CSS (Quartz 5.3.3) → verify `Theme: quartz` header.
2. Delete custom `:root` vars + dark media query + body/`#search`/`select`/`.card` rules.
3. Widen `.wrap` to 1140px; hero band styling.
4. Card polish: `.sel` ring, `.cmpbox` top-right, tag/fitbadge pills.
5. Style previously-unstyled: `.pcols`, `.cmptable`, `.profile` headings, `.err`.
6. Wizard `.bcard` surface + summary chevron + `.wrow` recommended state.
7. Details `.pane` surface, `.chip`/`.box`/`.srv-rec` remaps.
8. Footer + `#cmp-panel` overflow-x.
9. Verify: open `file://`, run `make test` (Playwright/jsdom — behavior unchanged, but update any golden screenshots).

## 4. Gotchas

- **`.card` clash:** model cards are real Bootstrap `.card`s (JS emits them); the app's custom `.card` rule silently overrides the theme — it must be **deleted**, not patched. `.bcard` exists only because of this clash; after the deletion it still works if you restyle it to card vars (or you may switch the wrapper's class to `card` in HTML — JS never queries `.bcard`).
- **Don't double-load CSS** (stock + theme) — duplicate base rules fight.
- **Quartz body gradient:** any transparent surface (`.pane`, compare table) sits on the gradient — always give panels a solid `--bs-tertiary-bg` backdrop.
- **Dark mode:** Bootswatch light themes (Zephyr/Minty/Flatly) ship no curated dark palette — forcing `data-bs-theme=dark` yields muddy Bootstrap-gray; don't mix. If light mode is ever required, switch to Zephyr (`https://cdn.jsdelivr.net/npm/bootswatch@5.3.3/dist/zephyr/bootstrap.min.css`) and *restore* the app's dark var block.
- **Inline styles** (`style="max-width:320px"`, `width:auto` on selects) are fine — don't fight them with `!important`.
- Keep `min-height:44px` on `.chip`/`.box`/`.fitbox` (touch targets); keep `.sel` transition.
