## ADDED Requirements

### Requirement: Verified tier constants
The estimator MUST use exactly: `MACBOOK_TIERS = [16, 24, 36, 48, 64, 128]`,
`MAC_MINI_TIERS = [16, 24, 32, 36, 48, 64, 128]`,
`MAC_STUDIO_TIERS = [36, 64, 96, 128, 192, 384, 512]`,
`MAC_PRO_TIERS = [192, 384, 512]` — each commented with its Apple source. The
schema, frontend TIERS and regenerated samples MUST carry the matching keys.

#### Scenario: current-gen MacBook
- **WHEN** a user opens the MacBook section
- **THEN** tiers 16/24/36/48/64/128 GB are shown (M5 Max base 36; M5 Pro 48)
- **AND** 32/96 GB are not offered (M3-era configs)

### Requirement: Two-sided tier pins
Tests MUST pin every Mac tier on both sides: Python asserts exact flags for
8B / Mixtral 46.7B / 70B / DeepSeek-V4 304B / 671B-class models across macbook,
mac_mini, mac_studio, mac_pro; jsdom asserts exact box counts per section and
wizard parity; refresh-crawler fixtures MUST use the verified key sets.

#### Scenario: gate runs
- **WHEN** CI runs pytest, jsdom and Playwright
- **THEN** all Apple tier assertions pass against the committed data
