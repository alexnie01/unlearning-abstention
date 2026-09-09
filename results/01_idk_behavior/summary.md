# 01 — IdkDPO / IdkNLL behavioral check

Abstention rate = fraction of responses the judge majority labelled IGNORANCE (epistemic rubric); regex = cheap phrase match.

| model   | cls    |   n |   abstain_judge_majority |   abstain_regex |   judge_agreement |   regex_vs_majority_agreement |
|:--------|:-------|----:|-------------------------:|----------------:|------------------:|------------------------------:|
| base    | forget | 100 |                     0.01 |            0.00 |              0.98 |                          0.99 |
| base    | retain | 100 |                     0.00 |            0.00 |              1.00 |                          1.00 |
| IdkDPO  | forget | 100 |                     0.41 |            0.38 |              0.69 |                          0.91 |
| IdkDPO  | retain | 100 |                     0.00 |            0.00 |              1.00 |                          1.00 |
| IdkNLL  | forget | 100 |                     0.95 |            0.96 |              0.63 |                          0.99 |
| IdkNLL  | retain | 100 |                     0.02 |            0.02 |              0.99 |                          1.00 |

**Gate:** PASS: ignorance cell populated by IdkDPO, IdkNLL
