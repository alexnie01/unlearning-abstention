# 06 — does the model still know? (true vs surface-matched perturbations)

Calibration: base rank1 0.69, retain oracle 0.38.

| model    | set    |   rank1_acc |   beats_frac |   truth_ratio_median |   prefers_truth_frac |   margin_mean |   true_lp_mean |   n |
|:---------|:-------|------------:|-------------:|---------------------:|---------------------:|--------------:|---------------:|----:|
| base     | forget |       0.690 |        0.890 |                0.513 |                0.930 |         0.933 |         -2.641 | 100 |
| base     | retain |       0.770 |        0.902 |                0.436 |                0.910 |         0.965 |         -2.674 | 100 |
| oracle   | forget |       0.380 |        0.650 |                0.868 |                0.670 |         0.322 |         -3.344 | 100 |
| oracle   | retain |       0.760 |        0.892 |                0.460 |                0.900 |         0.973 |         -2.714 | 100 |
| IdkDPO   | forget |       0.260 |        0.526 |                0.981 |                0.510 |        -0.016 |         -5.406 | 100 |
| IdkDPO   | retain |       0.750 |        0.904 |                0.482 |                0.920 |         0.891 |         -2.626 | 100 |
| IdkNLL   | forget |       0.680 |        0.882 |                0.507 |                0.910 |         0.846 |         -2.735 | 100 |
| IdkNLL   | retain |       0.740 |        0.910 |                0.455 |                0.940 |         0.934 |         -2.687 | 100 |
| RMU      | forget |       0.150 |        0.420 |                1.110 |                0.340 |        -0.108 |        -10.301 | 100 |
| RMU      | retain |       0.710 |        0.894 |                0.482 |                0.920 |         0.840 |         -3.093 | 100 |
| AltPO    | forget |       0.280 |        0.498 |                1.121 |                0.440 |        -0.050 |         -3.633 | 100 |
| AltPO    | retain |       0.730 |        0.892 |                0.523 |                0.890 |         0.817 |         -2.606 | 100 |
| NPO      | forget |       0.680 |        0.872 |                0.540 |                0.910 |         0.790 |         -2.700 | 100 |
| NPO      | retain |       0.740 |        0.894 |                0.442 |                0.900 |         0.939 |         -2.680 | 100 |
| SimNPO   | forget |       0.540 |        0.788 |                0.586 |                0.800 |         0.797 |         -4.165 | 100 |
| SimNPO   | retain |       0.710 |        0.878 |                0.445 |                0.900 |         1.022 |         -3.110 | 100 |
| GradDiff | forget |       0.650 |        0.866 |                0.495 |                0.920 |         0.973 |         -3.190 | 100 |
| GradDiff | retain |       0.720 |        0.888 |                0.443 |                0.890 |         1.024 |         -3.173 | 100 |

## 2x2

|          |   rank1 |   retained_frac |   abstain | knows   | cell                                   |
|:---------|--------:|----------------:|----------:|:--------|:---------------------------------------|
| IdkDPO   |    0.26 |           -0.39 |      0.41 | False   | suppressed & abstains                  |
| IdkNLL   |    0.68 |            0.97 |      0.95 | True    | knows & abstains                       |
| RMU      |    0.15 |           -0.74 |    nan    | False   | insufficient data (no abstention rate) |
| AltPO    |    0.28 |           -0.32 |    nan    | False   | insufficient data (no abstention rate) |
| NPO      |    0.68 |            0.97 |    nan    | True    | insufficient data (no abstention rate) |
| SimNPO   |    0.54 |            0.52 |    nan    | True    | insufficient data (no abstention rate) |
| GradDiff |    0.65 |            0.87 |    nan    | True    | insufficient data (no abstention rate) |

**Verdict:** Knows-but-abstains is realisable and IdkNLL occupies it: abstention CAN coexist with intact answer discrimination, so a method that suppresses discrimination is doing something else. Note the dissociation: IdkDPO abstains WITHOUT retaining discrimination — same behaviour, different mechanism.
