# 09 — recall vs recognition vs abstention on forget10

recall: judged to state the gold fact. recognition: 06's rank1. abstention: 01's judged rate.

| model    |   n |   recall |   abstain |   degenerate |   recall_when_attempted |   recognition |
|:---------|----:|---------:|----------:|-------------:|------------------------:|--------------:|
| base     | 100 |     0.39 |      0.01 |         0    |                   0.394 |          0.69 |
| IdkDPO   | 100 |     0.01 |      0.41 |         0.01 |                   0     |          0.26 |
| IdkNLL   | 100 |     0.01 |      0.95 |         0    |                   0.2   |          0.68 |
| RMU      | 100 |     0.01 |      0.01 |         0.81 |                   0     |          0.15 |
| AltPO    | 100 |     0    |      0    |         0.01 |                   0     |          0.28 |
| NPO      | 100 |     0.03 |      0    |         0    |                   0.03  |          0.68 |
| SimNPO   | 100 |     0.07 |      0    |         0    |                   0.07  |          0.54 |
| GradDiff | 100 |     0.2  |      0    |         0    |                   0.2   |          0.65 |
