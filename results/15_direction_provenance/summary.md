# 15 — does the epistemic direction depend on which checkpoint built it?

Pairwise cosine at layer 12:

|         |   D_dpo |   D_nll |   W_dpo |   W_nll |   content |
|:--------|--------:|--------:|--------:|--------:|----------:|
| D_dpo   |   1     |   0.495 |   0.583 |  -0.007 |     0.274 |
| D_nll   |   0.495 |   1     |   0.224 |   0.15  |     0.707 |
| W_dpo   |   0.583 |   0.224 |   1     |   0.194 |     0.056 |
| W_nll   |  -0.007 |   0.15  |   0.194 |   1     |     0.118 |
| content |   0.274 |   0.707 |   0.056 |   0.118 |     1     |

Alignment of each method's differential shift:

|          |   D_dpo |   D_nll |   W_dpo |   W_nll |   content |   split |
|:---------|--------:|--------:|--------:|--------:|----------:|--------:|
| IdkDPO   |   0.934 |   0.338 |   0.335 |  -0.109 |     0.056 |  -0.003 |
| IdkNLL   |   0.468 |   0.822 |   0.238 |  -0.024 |     0.193 |  -0.141 |
| RMU      |   0.221 |   0.022 |   0.213 |   0.03  |     0.055 |   0.103 |
| AltPO    |   0.242 |   0.179 |  -0.027 |   0.073 |     0.034 |   0.072 |
| NPO      |  -0.129 |   0.072 |  -0.236 |  -0.142 |    -0.082 |  -0.071 |
| SimNPO   |   0.38  |  -0.011 |   0.308 |  -0.02  |     0.049 |   0.075 |
| GradDiff |   0.119 |  -0.251 |   0.164 |  -0.079 |    -0.224 |   0.005 |

**Constructions DISAGREE on direction (cos(D_dpo, D_nll) = +0.49, cos(D_dpo, W_dpo) = +0.58); the top-two ranking of methods by alignment CHANGES across them: D_dpo: SimNPO, AltPO; D_nll: AltPO, NPO; W_dpo: SimNPO, RMU; W_nll: AltPO, RMU**
