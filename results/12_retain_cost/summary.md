# 12 — retain-set cost

Did the methods damage what they were meant to keep?

| model    |   n |   retain_recall |   degenerate |    lo |    hi |   forget_recall |   selectivity |   z_vs_base |
|:---------|----:|----------------:|-------------:|------:|------:|----------------:|--------------:|------------:|
| base     | 100 |            0.36 |         0    | 0.273 | 0.458 |            0.39 |         -0.03 |     nan     |
| IdkDPO   | 100 |            0.25 |         0    | 0.175 | 0.343 |            0.01 |          0.24 |       1.702 |
| IdkNLL   | 100 |            0.23 |         0    | 0.158 | 0.322 |            0.01 |          0.22 |       2.036 |
| RMU      | 100 |            0.03 |         0.16 | 0.01  | 0.085 |            0.01 |          0.02 |       6.478 |
| AltPO    | 100 |            0.23 |         0    | 0.158 | 0.322 |            0    |          0.23 |       2.036 |
| NPO      | 100 |            0.43 |         0    | 0.337 | 0.528 |            0.03 |          0.4  |      -1.015 |
| SimNPO   | 100 |            0.42 |         0    | 0.328 | 0.518 |            0.07 |          0.35 |      -0.871 |
| GradDiff | 100 |            0.38 |         0    | 0.291 | 0.478 |            0.2  |          0.18 |      -0.293 |

**Retain recall is decisively below base (0.36) for: RMU (0.03, z=6.5). Suggestive but not surviving correction for multiple comparisons: IdkNLL (0.23, z=2.0), AltPO (0.23, z=2.0)**
