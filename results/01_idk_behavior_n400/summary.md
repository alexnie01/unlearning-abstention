# 01 — IdkDPO / IdkNLL behavioral check

Abstention rate = fraction of responses the judge majority labelled IGNORANCE (epistemic rubric); regex = cheap phrase match.

| model    | cls    |   n |   abstain |   abstain_raw |   degenerate |   abstain_regex |   judge_agreement |   abstain_lo |   abstain_hi |
|:---------|:-------|----:|----------:|--------------:|-------------:|----------------:|------------------:|-------------:|-------------:|
| base     | forget | 400 |      0.01 |          0.01 |         0.00 |            0.00 |              0.99 |         0.00 |         0.02 |
| base     | retain | 400 |      0.00 |          0.00 |         0.00 |            0.00 |              1.00 |         0.00 |         0.01 |
| IdkDPO   | forget | 400 |      0.40 |          0.40 |         0.01 |            0.36 |              0.74 |         0.35 |         0.45 |
| IdkDPO   | retain | 400 |      0.00 |          0.00 |         0.00 |            0.00 |              1.00 |         0.00 |         0.01 |
| IdkNLL   | forget | 400 |      0.94 |          0.94 |         0.00 |            0.97 |              0.65 |         0.92 |         0.96 |
| IdkNLL   | retain | 400 |      0.03 |          0.03 |         0.00 |            0.03 |              0.99 |         0.02 |         0.05 |
| RMU      | forget | 400 |      0.03 |          0.03 |         0.74 |            0.00 |              0.96 |         0.01 |         0.05 |
| RMU      | retain | 400 |      0.00 |          0.00 |         0.13 |            0.00 |              0.99 |         0.00 |         0.01 |
| AltPO    | forget | 100 |      0.00 |          0.00 |         0.00 |            0.00 |              0.99 |         0.00 |         0.04 |
| AltPO    | retain | 100 |      0.00 |          0.00 |         0.00 |            0.00 |              1.00 |         0.00 |         0.04 |
| NPO      | forget | 100 |      0.00 |          0.00 |         0.00 |            0.00 |              0.99 |         0.00 |         0.04 |
| NPO      | retain | 100 |      0.00 |          0.00 |         0.00 |            0.00 |              0.99 |         0.00 |         0.04 |
| SimNPO   | forget | 100 |      0.00 |          0.00 |         0.00 |            0.00 |              1.00 |         0.00 |         0.04 |
| SimNPO   | retain | 100 |      0.00 |          0.00 |         0.00 |            0.00 |              1.00 |         0.00 |         0.04 |
| GradDiff | forget | 100 |      0.01 |          0.01 |         0.00 |            0.00 |              0.99 |         0.00 |         0.05 |
| GradDiff | retain | 100 |      0.00 |          0.00 |         0.00 |            0.00 |              1.00 |         0.00 |         0.04 |

**Gate:** PASS: ignorance cell populated by IdkDPO, IdkNLL
