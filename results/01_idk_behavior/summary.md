# 01 — IdkDPO / IdkNLL behavioral check

Abstention rate = fraction of responses the judge majority labelled IGNORANCE (epistemic rubric); regex = cheap phrase match.

| model    | cls    |   n |   abstain |   abstain_raw |   degenerate |   abstain_regex |   judge_agreement |
|:---------|:-------|----:|----------:|--------------:|-------------:|----------------:|------------------:|
| base     | forget | 100 |      0.01 |          0.01 |         0.00 |            0.00 |              0.98 |
| base     | retain | 100 |      0.00 |          0.00 |         0.00 |            0.00 |              1.00 |
| IdkDPO   | forget | 100 |      0.41 |          0.41 |         0.01 |            0.38 |              0.69 |
| IdkDPO   | retain | 100 |      0.00 |          0.00 |         0.00 |            0.00 |              1.00 |
| IdkNLL   | forget | 100 |      0.95 |          0.95 |         0.00 |            0.96 |              0.63 |
| IdkNLL   | retain | 100 |      0.02 |          0.02 |         0.00 |            0.02 |              0.99 |
| RMU      | forget | 100 |      0.01 |          0.14 |         0.81 |            0.00 |              0.84 |
| RMU      | retain | 100 |      0.00 |          0.02 |         0.16 |            0.00 |              0.97 |
| AltPO    | forget | 100 |      0.00 |          0.00 |         0.01 |            0.00 |              0.96 |
| AltPO    | retain | 100 |      0.00 |          0.00 |         0.00 |            0.00 |              1.00 |
| NPO      | forget | 100 |      0.00 |          0.00 |         0.00 |            0.00 |              0.99 |
| NPO      | retain | 100 |      0.00 |          0.00 |         0.00 |            0.00 |              1.00 |
| SimNPO   | forget | 100 |      0.00 |          0.00 |         0.00 |            0.00 |              1.00 |
| SimNPO   | retain | 100 |      0.00 |          0.00 |         0.00 |            0.00 |              1.00 |
| GradDiff | forget | 100 |      0.00 |          0.00 |         0.00 |            0.00 |              0.99 |
| GradDiff | retain | 100 |      0.00 |          0.00 |         0.00 |            0.00 |              1.00 |

**Gate:** PASS: ignorance cell populated by IdkDPO, IdkNLL
