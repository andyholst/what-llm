## ADDED Requirements

### Requirement: Real NVIDIA tiers
`NVIDIA_TIERS` MUST be `[8, 12, 16, 20, 24, 32, 48, 96]` and the schema's
`hardware.nvidia` MUST carry matching keys (`8gb` … `96gb`).

#### Scenario: RTX 5090 tier exists
- **WHEN** a user selects the NVIDIA section
- **THEN** a 32 GB tier is available, anchored by the RTX 5090 (32 GB GDDR7, NVIDIA official)

#### Scenario: workstation tiers
- **WHEN** a model needs > 48 GB
- **THEN** the 96 GB tier (RTX PRO 6000 Blackwell) can flag it, and the 20 GB tier
  (RTX 4000 Ada) covers workstation mid-range

### Requirement: Real AMD tiers
`AMD_TIERS` MUST be `[8, 12, 16, 20, 24, 32, 48, 192]` with matching schema keys.

#### Scenario: RX 7900 XT tier
- **WHEN** a user selects the AMD section
- **THEN** a 20 GB tier exists (RX 7900 XT, AMD official) and 48/192 GB cover
  Radeon PRO W7900 / Instinct MI300X
- **AND** the section notes ROCm backend support (ROCm 7.x covers RX 9000/7000 + PRO)

### Requirement: Intel Arc section
A new `intel_arc` hardware section MUST exist with tiers `[8, 10, 12, 16]`
(A750/B570 → B580/A770), backends SYCL/oneAPI + Vulkan.

#### Scenario: Arc user
- **WHEN** a user picks Intel Arc 12 GB (B580)
- **THEN** models whose est VRAM + 1.5 ≤ 12 are flagged green
- **AND** the section label names the SYCL/Vulkan backends

### Requirement: Snapdragon section
A new `snapdragon` hardware section MUST exist with unified-memory tiers
`[16, 32, 64]`, treated like Macs (usable = tier − 3.5), backends CPU/Adreno Vulkan.

#### Scenario: Snapdragon laptop
- **WHEN** a user picks Snapdragon 64 GB
- **THEN** usable memory is 60.5 GB and the fit math uses it

### Requirement: Backend labels
Every hardware section MUST display its inference backend(s): NVIDIA=CUDA,
AMD=ROCm, MacBook/Mac Studio=Metal, Intel Arc=SYCL+Vulkan, Snapdragon=CPU+Vulkan,
DGX=CUDA, Android/iPhone=CPU.

#### Scenario: criteria visible
- **WHEN** the details pane renders hardware boxes
- **THEN** each section header names its backend, so "what else besides CUDA"
  is answered on the page itself
