# 11 — recognition vs displacement across 28 checkpoints

Pooled r(log‖shift‖, recognition) = -0.791 at layer 12.

Mean residual from the pooled trend, by method (positive = retains more than displacement alone predicts):

| method   |   mean |   count |
|:---------|-------:|--------:|
| AltPO    | -0.105 |       4 |
| GradDiff | -0.032 |       4 |
| IdkDPO   |  0.041 |       4 |
| IdkNLL   |  0.119 |       4 |
| NPO      |  0.026 |       4 |
| RMU      | -0.034 |       4 |
| SimNPO   | -0.015 |       4 |

| method   | repo                                                                                               |    lr |   epochs | published   |   shift_norm |   raw_norm |   rank1 |   prefers_truth |   truth_ratio_median |   n |
|:---------|:---------------------------------------------------------------------------------------------------|------:|---------:|:------------|-------------:|-----------:|--------:|----------------:|---------------------:|----:|
| AltPO    | open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_AltPO_lr1e-05_beta0.05_alpha1_epoch5   | 0.000 |        5 | False       |        0.699 |      5.341 |   0.575 |           0.805 |                0.738 | 200 |
| AltPO    | open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_AltPO_lr1e-05_beta0.05_alpha1_epoch10  | 0.000 |       10 | False       |        0.762 |      5.467 |   0.535 |           0.765 |                0.769 | 200 |
| AltPO    | open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_AltPO_lr2e-05_beta0.05_alpha1_epoch10  | 0.000 |       10 | False       |        1.179 |      4.734 |   0.370 |           0.565 |                0.879 | 200 |
| AltPO    | open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_AltPO_lr5e-05_beta0.1_alpha1_epoch10   | 0.000 |       10 | True        |        2.021 |      2.809 |   0.310 |           0.495 |                1.011 | 200 |
| GradDiff | open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_GradDiff_lr1e-05_alpha10_epoch5        | 0.000 |        5 | False       |        0.143 |      0.948 |   0.700 |           0.870 |                0.482 | 200 |
| GradDiff | open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_GradDiff_lr1e-05_alpha10_epoch10       | 0.000 |       10 | False       |        0.153 |      0.975 |   0.700 |           0.865 |                0.485 | 200 |
| GradDiff | open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_GradDiff_lr1e-05_alpha5_epoch5         | 0.000 |        5 | True        |        0.221 |      1.262 |   0.665 |           0.865 |                0.491 | 200 |
| GradDiff | open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_GradDiff_lr2e-05_alpha10_epoch10       | 0.000 |       10 | False       |        1.483 |      2.672 |   0.530 |           0.750 |                0.581 | 200 |
| IdkDPO   | open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_IdkDPO_lr1e-05_beta0.05_alpha1_epoch5  | 0.000 |        5 | False       |        2.430 |      8.599 |   0.610 |           0.830 |                0.704 | 200 |
| IdkDPO   | open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_IdkDPO_lr5e-05_beta0.05_alpha5_epoch10 | 0.000 |       10 | True        |        3.248 |      5.565 |   0.280 |           0.520 |                0.962 | 200 |
| IdkDPO   | open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_IdkDPO_lr1e-05_beta0.05_alpha1_epoch10 | 0.000 |       10 | False       |        3.678 |      8.674 |   0.590 |           0.815 |                0.726 | 200 |
| IdkDPO   | open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_IdkDPO_lr2e-05_beta0.05_alpha1_epoch10 | 0.000 |       10 | False       |        7.088 |      9.197 |   0.390 |           0.630 |                0.827 | 200 |
| IdkNLL   | open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_IdkNLL_lr1e-05_alpha10_epoch5          | 0.000 |        5 | False       |        0.454 |      2.082 |   0.725 |           0.880 |                0.499 | 200 |
| IdkNLL   | open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_IdkNLL_lr1e-05_alpha10_epoch10         | 0.000 |       10 | False       |        0.466 |      2.054 |   0.730 |           0.875 |                0.502 | 200 |
| IdkNLL   | open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_IdkNLL_lr2e-05_alpha10_epoch10         | 0.000 |       10 | False       |        0.716 |      2.403 |   0.730 |           0.875 |                0.496 | 200 |
| IdkNLL   | open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_IdkNLL_lr4e-05_alpha5_epoch10          | 0.000 |       10 | True        |        1.210 |      4.011 |   0.695 |           0.875 |                0.535 | 200 |
| NPO      | open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_NPO_lr1e-05_beta0.5_alpha1_epoch10     | 0.000 |       10 | True        |        0.378 |      0.959 |   0.655 |           0.845 |                0.570 | 200 |
| NPO      | open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_NPO_lr1e-05_beta0.05_alpha1_epoch10    | 0.000 |       10 | False       |        0.983 |      7.229 |   0.605 |           0.785 |                0.744 | 200 |
| NPO      | open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_NPO_lr1e-05_beta0.05_alpha1_epoch5     | 0.000 |        5 | False       |        1.077 |      7.497 |   0.625 |           0.790 |                0.761 | 200 |
| NPO      | open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_NPO_lr2e-05_beta0.05_alpha1_epoch10    | 0.000 |       10 | False       |        1.982 |      7.734 |   0.475 |           0.715 |                0.755 | 200 |
| RMU      | open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_RMU_lr1e-05_layer10_scoeff100_epoch5   | 0.000 |        5 | False       |        0.181 |      1.327 |   0.730 |           0.885 |                0.497 | 200 |
| RMU      | open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_RMU_lr1e-05_layer10_scoeff100_epoch10  | 0.000 |       10 | False       |        0.226 |      1.649 |   0.735 |           0.895 |                0.499 | 200 |
| RMU      | open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_RMU_lr2e-05_layer10_scoeff100_epoch10  | 0.000 |       10 | False       |        0.976 |      9.388 |   0.520 |           0.770 |                0.696 | 200 |
| RMU      | open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_RMU_lr5e-05_layer10_scoeff10_epoch10   | 0.000 |       10 | True        |       11.032 |     12.193 |   0.195 |           0.420 |                1.048 | 200 |
| SimNPO   | open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_SimNPO_lr1e-05_b3.5_a1_d0_g0.125_ep5   | 0.000 |        5 | False       |        0.134 |      0.901 |   0.710 |           0.870 |                0.481 | 200 |
| SimNPO   | open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_SimNPO_lr1e-05_b3.5_a1_d0_g0.125_ep10  | 0.000 |       10 | False       |        0.136 |      0.904 |   0.715 |           0.875 |                0.485 | 200 |
| SimNPO   | open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_SimNPO_lr2e-05_b3.5_a1_d0_g0.125_ep10  | 0.000 |       10 | False       |        0.285 |      1.186 |   0.675 |           0.860 |                0.501 | 200 |
| SimNPO   | open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_SimNPO_lr2e-05_b4.5_a1_d1_g0.125_ep10  | 0.000 |       10 | True        |        1.736 |      2.714 |   0.540 |           0.785 |                0.629 | 200 |
