"""
Difference-in-means directions and how well they separate held-out points.

A diff-in-means direction is the honest causal-grade construction (the
exploratory phase found probe normals separate without being causal). Its
separability is measured OUT OF SAMPLE: the direction is built on training
rows and scored by AUROC of the projection of held-out rows, so a direction
that merely memorizes its centroids reads as chance.
"""
import numpy as np
from sklearn.metrics import roc_auc_score


def unit(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    if n == 0:
        raise ValueError("zero-norm vector")
    return v / n


def diff_in_means(pos: np.ndarray, neg: np.ndarray) -> np.ndarray:
    """Unit vector from the neg centroid to the pos centroid. Rows are points."""
    return unit((pos.mean(axis=0) - neg.mean(axis=0)).astype(np.float64))


def cv_auroc(pos: np.ndarray, neg: np.ndarray, n_folds: int = 5, seed: int = 0) -> float:
    """Held-out AUROC of projections onto a diff-in-means direction fit on the
    other folds. Both classes are split into folds independently."""
    rng = np.random.default_rng(seed)
    fp, fn = rng.permutation(len(pos)) % n_folds, rng.permutation(len(neg)) % n_folds
    scores, labels = [], []
    for k in range(n_folds):
        d = diff_in_means(pos[fp != k], neg[fn != k])
        tp, tn = pos[fp == k] @ d, neg[fn == k] @ d
        scores += list(tp) + list(tn)
        labels += [1] * len(tp) + [0] * len(tn)
    return float(roc_auc_score(labels, scores))


def d_prime(pos: np.ndarray, neg: np.ndarray, d: np.ndarray) -> float:
    """Centroid gap along d in pooled-std units (in-sample effect size)."""
    p, n = pos @ d, neg @ d
    pooled = np.sqrt((p.var(ddof=1) + n.var(ddof=1)) / 2)
    return float((p.mean() - n.mean()) / pooled) if pooled > 0 else float("nan")


def random_split_direction(x: np.ndarray, seed: int = 0) -> np.ndarray:
    """Diff-in-means between two random halves of ONE class: a direction with
    the same construction and dimensionality but no behavioral signal."""
    idx = np.random.default_rng(seed).permutation(len(x))
    h = len(idx) // 2
    return diff_in_means(x[idx[:h]], x[idx[h:2 * h]])
