# Bootstrap 5.3 theme + server suggestion in wizard picks

## Why

The UI was functional but visually dated ("looks like shit" — user, 2026-08-10), and
the inference-server chips were a flat list instead of an actionable suggestion.
This change: (1) applies a popular theme — Bootstrap 5.3, **vendored** as
`vendor/bootstrap.min.css` so the site stays self-contained (no CDN, works on
file:// and in hermetic CI); (2) makes the server recommendation the primary CTA —
wizard picks carry a "Run with: Ollama (CUDA) — reason ↗" line, and the wizard
shows a "Best server for <hardware>" summary; the details pane keeps the
recommended server call-out with backend badges.

Model cards keep the `.card` class (tests depend on it); the wizard wrapper uses a
`.bcard` replica so `.card` stays unambiguous.

## Requirements

- ADDED: `vendor/bootstrap.min.css` (Bootstrap 5.3.3, vendored, no CDN) linked in
  the head; shell, controls, cards, wizard, pane and footer styled with Bootstrap
  classes (navbar hero, form-select/form-control, row/col grid, list-group, badges,
  alerts).
- ADDED: wizard results show a "Best server for <hardware>: X (backend) — reason ↗"
  summary and each pick shows a prominent "Run with: X (backend) — reason ↗" line
  linking to the server.
- MODIFIED: details pane server call-out styled as a success alert with backend
  badge; chips unchanged in behavior (links, ↗).
- MODIFIED: README "zero-dependency" wording → vendored CSS, still no build step.
- Tests: jsdom asserts bootstrap link (vendored), #list.row + .card.h-100 grid
  classes, wizard summary line; all existing tests keep passing (ids/classes
  preserved).
