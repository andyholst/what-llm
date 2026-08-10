## 1. Estimator + schema — PR-I

- [ ] 1.1 `estimator.py`: NVIDIA_TIERS = [8,12,16,20,24,32,48,96]; AMD_TIERS = [8,12,16,20,24,32,48,192]; add INTEL_ARC_TIERS = [8,10,12,16] + SNAPDRAGON_TIERS = [16,32,64] (unified, MAC_SYS)
- [ ] 1.2 `schemas/model.schema.json`: add intel_arc + snapdragon sections and the new tier keys; samples regenerate schema-valid
- [ ] 1.3 Frontend: TIERS + SECTIONS (9 sections), MAC_CATS += snapdragon, backend labels in section headers
- [ ] 1.4 Python tests: tier pins (5090-class 32 GB flags; 7900 XT 20 GB; Arc B580 12 GB fits 8B Q4; Snapdragon 64 GB usable 60.5) + schema tests
- [ ] 1.5 JS tests: box counts (nvidia 8, amd 8, intel_arc 4, snapdragon 3, h3s 9), wizard parity for new sections

## 2. Research doc

- [ ] 2.1 `RESEARCH-hardware-tiers.md` committed: verified tier tables + anchors + backend matrix with URLs
