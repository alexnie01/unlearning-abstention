# 14 — do the high-recognition Idk variants abstain?

| method   | repo                                                                                               | published   |   shift_norm |   rank1 |   abstain |   abstain_lo |   abstain_hi |   degenerate |   n |
|:---------|:---------------------------------------------------------------------------------------------------|:------------|-------------:|--------:|----------:|-------------:|-------------:|-------------:|----:|
| IdkDPO   | open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_IdkDPO_lr5e-05_beta0.05_alpha5_epoch10 | True        |        3.248 |   0.28  |     0.495 |        0.426 |        0.564 |         0.01 | 200 |
| IdkDPO   | open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_IdkDPO_lr1e-05_beta0.05_alpha1_epoch10 | False       |        3.678 |   0.59  |     0.99  |        0.964 |        0.997 |         0    | 200 |
| IdkDPO   | open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_IdkDPO_lr1e-05_beta0.05_alpha1_epoch5  | False       |        2.43  |   0.61  |     0.99  |        0.964 |        0.997 |         0    | 200 |
| IdkDPO   | open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_IdkDPO_lr2e-05_beta0.05_alpha1_epoch10 | False       |        7.088 |   0.39  |     0.98  |        0.95  |        0.992 |         0    | 200 |
| IdkNLL   | open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_IdkNLL_lr4e-05_alpha5_epoch10          | True        |        1.21  |   0.695 |     0.975 |        0.943 |        0.989 |         0    | 200 |
| IdkNLL   | open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_IdkNLL_lr1e-05_alpha10_epoch10         | False       |        0.466 |   0.73  |     0.435 |        0.368 |        0.504 |         0    | 200 |
| IdkNLL   | open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_IdkNLL_lr1e-05_alpha10_epoch5          | False       |        0.454 |   0.725 |     0.42  |        0.354 |        0.489 |         0    | 200 |
| IdkNLL   | open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_IdkNLL_lr2e-05_alpha10_epoch10         | False       |        0.716 |   0.73  |     0.69  |        0.623 |        0.75  |         0    | 200 |

**6 of 8 Idk variants combine abstention >0.3 with recognition >0.58 (midway between the 0.43 ignorance floor and base's 0.73): IdkDPO@‖3.7‖, IdkDPO@‖2.4‖, IdkNLL@‖1.2‖, IdkNLL@‖0.5‖, IdkNLL@‖0.5‖, IdkNLL@‖0.7‖**
