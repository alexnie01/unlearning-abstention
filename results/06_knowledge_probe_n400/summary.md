# 06 — does the model still know? (true vs surface-matched perturbations)

Calibration: base rank1 0.73, retain oracle 0.43.

| model    | set    |   rank1_acc |   beats_frac |   truth_ratio_median |   prefers_truth_frac |   margin_mean |   true_lp_mean |   n |   rank1_lo |   rank1_hi |
|:---------|:-------|------------:|-------------:|---------------------:|---------------------:|--------------:|---------------:|----:|-----------:|-----------:|
| base     | forget |       0.735 |        0.890 |                0.486 |                0.902 |         0.877 |         -2.716 | 400 |      0.690 |      0.776 |
| base     | retain |       0.782 |        0.915 |                0.472 |                0.925 |         0.901 |         -2.811 | 400 |      0.739 |      0.820 |
| oracle   | forget |       0.432 |        0.670 |                0.798 |                0.672 |         0.308 |         -3.392 | 400 |      0.385 |      0.481 |
| oracle   | retain |       0.782 |        0.916 |                0.483 |                0.930 |         0.904 |         -2.854 | 400 |      0.739 |      0.820 |
| IdkDPO   | forget |       0.297 |        0.573 |                0.949 |                0.557 |         0.054 |         -5.488 | 400 |      0.255 |      0.344 |
| IdkDPO   | retain |       0.770 |        0.907 |                0.477 |                0.917 |         0.851 |         -2.752 | 400 |      0.726 |      0.809 |
| IdkNLL   | forget |       0.700 |        0.877 |                0.510 |                0.902 |         0.795 |         -2.798 | 400 |      0.653 |      0.743 |
| IdkNLL   | retain |       0.770 |        0.910 |                0.476 |                0.925 |         0.877 |         -2.834 | 400 |      0.726 |      0.809 |
| RMU      | forget |       0.203 |        0.503 |                1.023 |                0.460 |        -0.056 |        -10.270 | 400 |      0.166 |      0.245 |
| RMU      | retain |       0.755 |        0.907 |                0.483 |                0.917 |         0.837 |         -3.000 | 400 |      0.711 |      0.795 |
| AltPO    | forget |       0.318 |        0.536 |                0.993 |                0.507 |        -0.002 |         -3.527 | 400 |      0.274 |      0.365 |
| AltPO    | retain |       0.760 |        0.906 |                0.518 |                0.905 |         0.793 |         -2.707 | 400 |      0.716 |      0.799 |
| NPO      | forget |       0.695 |        0.868 |                0.552 |                0.875 |         0.735 |         -2.784 | 400 |      0.648 |      0.738 |
| NPO      | retain |       0.767 |        0.911 |                0.483 |                0.920 |         0.895 |         -2.833 | 400 |      0.724 |      0.806 |
| SimNPO   | forget |       0.550 |        0.794 |                0.590 |                0.800 |         0.745 |         -4.236 | 400 |      0.501 |      0.598 |
| SimNPO   | retain |       0.748 |        0.900 |                0.453 |                0.912 |         0.948 |         -3.231 | 400 |      0.703 |      0.788 |
| GradDiff | forget |       0.677 |        0.868 |                0.479 |                0.882 |         0.915 |         -3.281 | 400 |      0.630 |      0.721 |
| GradDiff | retain |       0.748 |        0.897 |                0.466 |                0.905 |         0.948 |         -3.317 | 400 |      0.703 |      0.788 |

## 2x2

|          |   rank1 |   retained_frac |   abstain | knows   | cell                  |
|:---------|--------:|----------------:|----------:|:--------|:----------------------|
| IdkDPO   |    0.30 |           -0.45 |      0.40 | False   | suppressed & abstains |
| IdkNLL   |    0.70 |            0.88 |      0.94 | True    | knows & abstains      |
| RMU      |    0.20 |           -0.76 |      0.03 | False   | suppressed & answers  |
| AltPO    |    0.32 |           -0.38 |      0.00 | False   | suppressed & answers  |
| NPO      |    0.69 |            0.87 |      0.00 | True    | knows & answers       |
| SimNPO   |    0.55 |            0.39 |      0.00 | False   | suppressed & answers  |
| GradDiff |    0.68 |            0.81 |      0.00 | True    | knows & answers       |

**Verdict:** Knows-but-abstains is realisable and IdkNLL occupies it: abstention CAN coexist with intact answer discrimination, so a method that suppresses discrimination is doing something else. Note the dissociation: IdkDPO abstains WITHOUT retaining discrimination — same behaviour, different mechanism.
