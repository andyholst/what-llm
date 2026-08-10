## ADDED Requirements

### Requirement: Mac Mini + Mac Pro sections
`MAC_MINI_TIERS` MUST be `[16, 24, 32, 48, 64, 128]` and `MAC_PRO_TIERS` MUST be
`[192, 384, 512]`; both MUST use unified-memory math (usable = tier − 3.5). The
schema MUST carry `mac_mini` and `mac_pro` flag sections; the frontend MUST list
both machines in the hardware filter and the wizard.

#### Scenario: Mac Mini buyer
- **WHEN** a user picks Mac Mini 64 GB
- **THEN** usable memory is 60.5 GB and fit uses it (70B-class est 47.3 fits; 48 GB
  does not)
- **AND** the section appears in the details pane with Metal backend label

### Requirement: Agentic-coding capability
`agentic_capable(best_for, context_window)` MUST return True only for
coding/reasoning/agentic models with ≥ `AGENTIC_CTX_MIN` (32768) context. The
wizard MUST offer an "agentic coding" checkbox filter; the details pane MUST show
an "Agentic coding ready" badge for capable models; wizard picks MUST annotate
capable models.

#### Scenario: agentic filter
- **WHEN** the agentic checkbox is checked
- **THEN** every pick is a coding/reasoning/agentic model with 32K+ context

### Requirement: Hermetic tests
- Python: tier pins (Mac Mini 64 fits 70B, 48 does not; Mac Pro 192+ fits),
  agentic_capable unit cases, schema sections.
- JS: 11 hardware sections with box counts (mac_mini 6, mac_pro 3); Mac Mini/Pro
  wizard parity; agentic filter + badge.

#### Scenario: gate runs
- **WHEN** CI runs pytest, jsdom and Playwright
- **THEN** all new assertions pass against the committed data
