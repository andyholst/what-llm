## MODIFIED Requirements

### Requirement: Strict model JSON contract
Every crawler output file MUST conform to `schemas/model.schema.json` with fields: id, name, author, parameters_b, architecture (dense|moe), pipeline_tag, hf_url, trending_score, downloads, quants[{name,size_gb,estimated_vram_gb,notes}], hardware, last_updated. The hardware block MUST contain nvidia (8/12/16/24/48), amd (8/12/16/24), macbook (16/24/32/48/64/96/128), mac_studio (32/64/96/128/192/256/512), dgx (640/1128/1440), android (8/12/16/24 + note), and iphone (8/12 + note); the previous `mobile` category is REMOVED.

#### Scenario: Schema-valid output with new tiers
- **WHEN** the crawler emits a per-model file
- **THEN** the file validates against the v2 schema, android/iphone carry a note, and a record still containing `mobile` fails validation

#### Scenario: Sample data conformance
- **WHEN** sample models are regenerated
- **THEN** every sample passes v2 schema validation and exercises the new categories

### Requirement: Hardware flag mapping
Each model's hardware flags MUST be derived from the recommended quant (quants[0]): a tier is enabled iff `estimated_vram_gb + 1.5 <= tier_vram`; MacBook and Mac Studio compare against `unified_memory - 3.5`; DGX compares against total system GPU memory (640/1128/1440 GB); Android and iPhone use their tier maps plus the practicality rule (parameters_b <= 4.0 and the smallest quant fits an 8 GB budget).

#### Scenario: M5 MacBook tiers
- **WHEN** a 70B-class model's recommended quant estimates 45.8 GB
- **THEN** MacBook boxes 64/96/128 GB go green (45.8+1.5=47.3 <= 60.5 usable) and 48 GB stays grey (47.3 > 44.5 usable)

#### Scenario: Mac Studio holds extreme MoE
- **WHEN** a 671B-class MoE's quant estimate is 400+ GB (e.g. DeepSeek-R1, ~413 GB)
- **THEN** consumer GPUs, MacBooks, and phones are all false while Mac Studio 512 GB (usable 508.5) and every DGX box go green

#### Scenario: DGX-only extreme MoE
- **WHEN** a 1T-class MoE's quant estimate exceeds 508 GB (misses even the 512 GB Mac Studio, e.g. ~615 GB)
- **THEN** every consumer, Mac, and phone flag is false while the DGX 640/1128/1440 boxes go green, and the phone note states there is no consumer support

### Requirement: Single-file frontend with live hardware boxes
The frontend MUST show hardware sections for NVIDIA, AMD, MacBook (16..128), Mac Studio, DGX, Android, and iPhone, with boxes that update live from the selected quant, SHALL work on mobile layouts, and SHALL degrade gracefully when opened via `file://`.

#### Scenario: New sections render
- **WHEN** a model with crawler data is selected
- **THEN** the details pane shows all seven hardware sections and box states match the selected quant's estimate

## ADDED Acceptance Criteria

- `openspec validate expand-hardware-tiers` reports valid; the base change still validates.
- Schema v2 rejects `mobile`; estimator tests cover Mac Studio, DGX, Android, iPhone tier boundaries (70B → MacBook 64+ only; 671B MoE → Mac Studio 512 + DGX; 1T MoE → DGX only).
- Sample dataset has 14 models including a 304B MoE GGUF with real quant sizes; all invariant- and schema-clean.
- Frontend renders the new sections; jsdom suite green; CI green on every PR.
