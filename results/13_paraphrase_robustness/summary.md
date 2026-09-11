# 13 — does abstention survive rephrasing the question?

| model   |       orig |       para |       delta |   rec_orig |   rec_para |
|:--------|-----------:|-----------:|------------:|-----------:|-----------:|
| base    | 0          | 0.00666667 |  0.00666667 |      0.713 |      0.74  |
| IdkDPO  | 0.453333   | 0.4        | -0.0533333  |      0.313 |      0.347 |
| IdkNLL  | 0.646667   | 0.586667   | -0.06       |      0.687 |      0.693 |
| RMU     | 0.00666667 | 0.0333333  |  0.0266667  |      0.187 |      0.213 |
| NPO     | 0.0133333  | 0.00666667 | -0.00666667 |      0.66  |      0.667 |

**Abstention survives paraphrase (worst positive control retains 88% of its rate), so it tracks the fact rather than the phrasing.**
