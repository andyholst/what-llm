## ADDED Requirements

### Requirement: Vendored Bootstrap theme
A Bootstrap 5.3 stylesheet MUST be vendored at `vendor/bootstrap.min.css` and
linked from the page head (no CDN dependency). The page shell MUST use Bootstrap
classes for layout and controls (form-control, form-select, row/col grid,
list-group, badge, alert, card via `.bcard` wrapper).

#### Scenario: stylesheet linked
- **WHEN** the page loads
- **THEN** a local `vendor/bootstrap.min.css` link is present and the card grid
  uses `row g-3` with `col-12 col-sm-6 col-lg-4` wrappers
- **AND** model cards remain the only `.card` elements (`.bcard` for the wizard)

### Requirement: Server suggestion as primary CTA
Wizard results MUST render a "Best server for <hardware>" summary line and each
pick MUST show "Run with: <server> <backend> — reason" with a link to the server.

#### Scenario: wizard picks
- **WHEN** the wizard returns picks for a hardware category
- **THEN** a summary names the best server for that hardware, and every pick row
  carries a "Run with:" suggestion with backend badge and link

### Requirement: Details call-out
The details-pane server block MUST render the recommended server as a prominent
call-out (success alert) with backend badge; alternatives remain chips with ↗ links.

#### Scenario: model details
- **WHEN** a model detail renders
- **THEN** the recommended server appears in a highlighted call-out with reason,
  and the alternative chips link out

### Requirement: Hermetic tests
jsdom MUST assert: bootstrap stylesheet linked from vendor/, grid classes present,
wizard summary line, and all pre-existing behavior tests still pass.

#### Scenario: gate runs
- **WHEN** CI runs jsdom + Playwright
- **THEN** all layout and behavior assertions pass against the committed data
