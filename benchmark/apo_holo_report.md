# Apo/holo case study — 1YES (apo) vs 1YET (holo)

Reference binding-site — центр co-crystallized лиганда из **holo**.
Threshold success: DCC ≤ 4.0 Å.

## Per-structure summary

| Structure | Method | Top-1 center (Å) | DCC | Runtime |
|---|---|---|---|---|
| apo (1YES) | p2rank | (38.9, -45.4, 63.0) | top-1 = 3.66 Å ✓ | 13.0s |
| apo (1YES) | fpocket | (34.3, -63.9, 62.6) | top-1 = 18.88 Å ✗ | 13.0s |
| holo (1YET) | p2rank | (38.2, -46.2, 62.8) | top-1 = 4.11 Å ✗ | 13.1s |
| holo (1YET) | fpocket | (40.0, -45.4, 62.2) | top-1 = 3.76 Å ✓ | 13.1s |

## Cross-form interpretation

- **p2rank** — top-1 apo и top-1 holo разнесены на **1.16 Å**. DCC top-1 apo = 3.66 Å, holo = 4.11 Å. Apo verdict: **✓ cryptic site found**.
- **fpocket** — top-1 apo и top-1 holo разнесены на **19.35 Å**. DCC top-1 apo = 18.88 Å, holo = 3.76 Å. Apo verdict: **✗ wrong pocket**.
