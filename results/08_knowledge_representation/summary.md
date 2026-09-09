# 08 — is answer correctness still represented? (negative: instrument fails)

Grouped-CV AUROC of a linear probe separating the true answer from five surface-matched perturbations, on each model's own activations.

**Verdict: UNINFORMATIVE. The oracle, which never trained on these authors, scores 0.74 against base's 0.79 — a span of 0.065, versus 0.31 for the same contrast read off the output distribution (06). A linear probe on answer-final activations separates the true answer from its perturbations about equally well in a model that knows the fact and one that cannot, so it is detecting how plausibly a candidate continues the question, not whether it is true. No conclusion about any model's retained knowledge follows from these numbers — in particular, RMU's high score is NOT evidence that it represents the forgotten facts. Testing 'represented but not read out' needs a probe with real dynamic range: train on a knowledge contrast the oracle provably fails (e.g. retain-set facts vs forget-set facts within the base model) and verify the oracle sits at chance before reading anything off the methods.**

|          |   best_own_auroc |   output_rank1 |
|:---------|-----------------:|---------------:|
| base     |            0.789 |          0.690 |
| oracle   |            0.744 |          0.380 |
| IdkDPO   |            0.725 |          0.260 |
| IdkNLL   |            0.781 |          0.680 |
| RMU      |            0.789 |          0.150 |
| AltPO    |            0.773 |          0.280 |
| NPO      |            0.783 |          0.680 |
| SimNPO   |            0.792 |          0.540 |
| GradDiff |            0.788 |          0.650 |

Per-layer own-probe AUROC (note how little the oracle column differs from base):

|   layer |   AltPO |   GradDiff |   IdkDPO |   IdkNLL |   NPO |   RMU |   SimNPO |   base |   oracle |
|--------:|--------:|-----------:|---------:|---------:|------:|------:|---------:|-------:|---------:|
|       0 |   0.657 |      0.659 |    0.660 |    0.660 | 0.658 | 0.658 |    0.659 |  0.658 |    0.659 |
|       1 |   0.704 |      0.706 |    0.709 |    0.703 | 0.708 | 0.708 |    0.705 |  0.708 |    0.699 |
|       2 |   0.708 |      0.719 |    0.687 |    0.696 | 0.720 | 0.717 |    0.720 |  0.717 |    0.706 |
|       3 |   0.737 |      0.734 |    0.725 |    0.735 | 0.732 | 0.733 |    0.738 |  0.733 |    0.740 |
|       4 |   0.705 |      0.705 |    0.710 |    0.708 | 0.702 | 0.704 |    0.704 |  0.704 |    0.700 |
|       5 |   0.686 |      0.698 |    0.704 |    0.704 | 0.697 | 0.701 |    0.700 |  0.701 |    0.688 |
|       6 |   0.746 |      0.777 |    0.714 |    0.769 | 0.768 | 0.778 |    0.779 |  0.778 |    0.733 |
|       7 |   0.764 |      0.786 |    0.716 |    0.781 | 0.783 | 0.789 |    0.792 |  0.789 |    0.744 |
|       8 |   0.756 |      0.788 |    0.666 |    0.776 | 0.770 | 0.786 |    0.787 |  0.786 |    0.735 |
|       9 |   0.773 |      0.755 |    0.680 |    0.775 | 0.748 | 0.779 |    0.744 |  0.759 |    0.719 |
|      10 |   0.732 |      0.732 |    0.631 |    0.747 | 0.708 | 0.754 |    0.719 |  0.733 |    0.689 |
|      11 |   0.705 |      0.729 |    0.632 |    0.732 | 0.719 | 0.756 |    0.729 |  0.724 |    0.659 |
|      12 |   0.698 |      0.725 |    0.621 |    0.732 | 0.730 | 0.745 |    0.740 |  0.707 |    0.660 |
|      13 |   0.704 |      0.730 |    0.641 |    0.738 | 0.737 | 0.751 |    0.722 |  0.720 |    0.678 |
|      14 |   0.700 |      0.742 |    0.661 |    0.742 | 0.735 | 0.751 |    0.737 |  0.715 |    0.675 |
|      15 |   0.682 |      0.737 |    0.657 |    0.737 | 0.736 | 0.718 |    0.744 |  0.723 |    0.679 |
