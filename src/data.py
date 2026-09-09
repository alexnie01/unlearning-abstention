"""
TOFU question/answer loading with a fixed, author-stratified sample.

forget10 is 400 QA pairs over 20 authors (20 consecutive questions per author);
retain90 is 3600 pairs over the other 180 authors. Taking the first N rows of
either split covers only N/20 authors, so samples are spread with a seeded
permutation instead. Every experiment uses the SAME sample (same seed) so
behavioral labels from 01 line up row-for-row with activations in 02-04.
"""
import numpy as np
from datasets import load_dataset


def load_tofu(split: str) -> list[dict]:
    """split in {"forget10", "retain90", ...}; returns [{"question", "answer"}]."""
    ds = load_dataset("locuslab/TOFU", split)["train"]
    return [{"question": ex["question"], "answer": ex["answer"]} for ex in ds]


def sample_split(split: str, n: int, seed: int = 0) -> list[dict]:
    rows = load_tofu(split)
    rng = np.random.default_rng(seed)
    idx = np.sort(rng.permutation(len(rows))[:n])
    return [{**rows[i], "tofu_index": int(i)} for i in idx]


def matched_sample(n_per_class: int = 100, seed: int = 0) -> dict[str, list[dict]]:
    """Surface-form-matched forget/retain question sets (same TOFU house style)."""
    return {
        "forget": sample_split("forget10", n_per_class, seed),
        "retain": sample_split("retain90", n_per_class, seed),
    }
