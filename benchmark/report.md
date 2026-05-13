# COACH420 subset benchmark

Cross-method evaluation на 15 PDB с co-crystallized лигандами.
Метрика — DCC (Distance to Center of Cocrystal), threshold 4.0 Å.

| PDB | Ligand | P2Rank top-1 | P2Rank top-3 | fpocket top-1 | fpocket top-3 | Runtime | Notes |
|---|---|---|---|---|---|---|---|
| 1FBL | (auto) | 5.96 Å ✗ | 5.96 Å ✗ | 3.55 Å ✓ | 3.55 Å ✓ | 4.3s |  |
| 1ATP | (auto) | 1.04 Å ✓ | 1.04 Å ✓ | 0.86 Å ✓ | 0.86 Å ✓ | 5.9s |  |
| 1HVR | (auto) | 0.50 Å ✓ | 0.50 Å ✓ | 0.43 Å ✓ | 0.43 Å ✓ | 5.9s |  |
| 1KE7 | (auto) | 2.90 Å ✓ | 2.90 Å ✓ | 11.43 Å ✗ | 11.43 Å ✗ | 5.1s |  |
| 1A0Q | (auto) | 2.53 Å ✓ | 2.53 Å ✓ | 2.52 Å ✓ | 2.52 Å ✓ | 6.2s |  |
| 1OWT | (auto) | — | — | — | — | 7.7s | no co-crystallized ligand found |
| 4COX | (auto) | 23.06 Å ✓ | 1.72 Å ✓ | 49.48 Å ✗ | 22.31 Å ✗ | 21.3s |  |
| 3PXF | (auto) | 6.43 Å ✗ | 6.43 Å ✗ | 9.84 Å ✗ | 9.84 Å ✗ | 5.2s |  |
| 1IEP | (auto) | 60.19 Å ✗ | 5.97 Å ✗ | 59.03 Å ✗ | 4.94 Å ✗ | 6.6s |  |
| 2RH1 | (auto) | 22.51 Å ✗ | 20.31 Å ✗ | 9.53 Å ✗ | 9.53 Å ✗ | 9.8s |  |
| 1HSG | (auto) | 0.81 Å ✓ | 0.81 Å ✓ | 1.08 Å ✓ | 1.08 Å ✓ | 4.8s |  |
| 3ERT | (auto) | 0.81 Å ✓ | 0.81 Å ✓ | 1.50 Å ✓ | 1.50 Å ✓ | 4.6s |  |
| 1AKE | (auto) | 0.72 Å ✓ | 0.72 Å ✓ | 3.75 Å ✓ | 3.75 Å ✓ | 15.7s |  |
| 1OYT | (auto) | 2.79 Å ✓ | 2.79 Å ✓ | 2.42 Å ✓ | 2.42 Å ✓ | 5.2s |  |
| 1G3K | (auto) | — | — | — | — | 1.5s | no co-crystallized ligand found |

## Aggregate

- Total PDBs in subset: **15**
- Skipped (fetch/no-ligand/tool fail): **2**
- Successfully evaluated by P2Rank: **13** / 15
- Successfully evaluated by fpocket: **13** / 15

### P2Rank top-3 success rate: **9/13 = 69%**
### fpocket top-3 success rate: **8/13 = 62%**

Threshold: top-3 success = min(DCC по top-3 карманам) ≤ 4.0 Å.
