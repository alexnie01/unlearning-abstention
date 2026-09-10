# 09 — recall vs recognition vs abstention on forget10

recall: judged to state the gold fact. recognition: 06's rank1. abstention: 01's judged rate.

| model    |   n |   recall |   abstain |   degenerate |   recall_when_attempted |   recall_lo |   recall_hi |   recognition |
|:---------|----:|---------:|----------:|-------------:|------------------------:|------------:|------------:|--------------:|
| base     | 200 |    0.38  |     0.01  |        0     |                   0.374 |       0.316 |       0.449 |         0.735 |
| IdkDPO   | 200 |    0.005 |     0.405 |        0     |                   0     |       0.001 |       0.028 |         0.298 |
| IdkNLL   | 200 |    0.005 |     0.93  |        0     |                   0.071 |       0.001 |       0.028 |         0.7   |
| RMU      | 200 |    0.025 |     0.025 |        0.715 |                   0.019 |       0.011 |       0.057 |         0.202 |
| AltPO    | 200 |    0.01  |     0     |        0.005 |                   0.01  |       0.003 |       0.036 |         0.318 |
| NPO      | 200 |    0.04  |     0     |        0     |                   0.04  |       0.02  |       0.077 |         0.695 |
| SimNPO   | 200 |    0.04  |     0     |        0     |                   0.04  |       0.02  |       0.077 |         0.55  |
| GradDiff | 200 |    0.21  |     0.005 |        0     |                   0.211 |       0.159 |       0.272 |         0.678 |
