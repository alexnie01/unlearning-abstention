"""
Does the model still discriminate the true answer from plausible false ones?

TOFU's `*_perturbed` splits give, per question, a `paraphrased_answer` and five
`perturbed_answer`s built from the SAME sentence frame with the fact swapped
("Hsiao Yun-Hwa is the complete name of the writer" vs "Chen Jing-Li is the
complete name of the writer"). Comparing those isolates the fact from the
surface form, and asks whether the knowledge is present WITHOUT requiring the
model to utter it — the one thing a generation-based or gate-removal test
cannot separate from a suppressed output channel.

Metrics per question (all from length-normalised log-probs):
    rank1        true answer scores above all five perturbations
    truth_ratio  TOFU's R = mean_p P~(perturbed_p) / P~(true), where
                 P~ = exp(mean per-token log-prob). R < 1 means the model
                 prefers the truth; R >= 1 means it does not.
    margin       logp(true) - mean_p logp(perturbed), in nats per token
"""
import numpy as np
from datasets import load_dataset

from src.intervention import score_dataset_chat, score_pairs_chat


def load_perturbed(split: str, indices=None) -> list[dict]:
    """split in {"forget10_perturbed", "retain_perturbed"}; row-aligned with
    forget10 when split is forget10_perturbed."""
    ds = load_dataset("locuslab/TOFU", split)["train"]
    rows = [{"question": ex["question"], "true": ex["paraphrased_answer"],
             "perturbed": list(ex["perturbed_answer"]), "gold": ex["answer"]} for ex in ds]
    return rows if indices is None else [rows[i] for i in indices]


def score_discrimination(model, tokenizer, device, rows, layer_name=None,
                         direction=None, c=0.0) -> dict:
    """Per-question true/perturbed log-probs, optionally under a translation
    hook (same signature as score_dataset_chat) so an intervened model can be
    asked the same question."""
    qs = [r["question"] for r in rows]
    n_pert = len(rows[0]["perturbed"])
    if direction is None or c == 0.0:
        # No hook: score every candidate in one batched sweep.
        pairs = [(r["question"], a) for r in rows for a in [r["true"]] + list(r["perturbed"])]
        flat = score_pairs_chat(model, tokenizer, device, pairs)
        grid = flat.reshape(len(rows), n_pert + 1)
        true_lp, pert_lp = grid[:, 0], grid[:, 1:]
    else:
        true_lp = score_dataset_chat(model, tokenizer, device, qs, [r["true"] for r in rows],
                                     layer_name, direction, c)
        pert_lp = np.stack([
            score_dataset_chat(model, tokenizer, device, qs, [r["perturbed"][k] for r in rows],
                               layer_name, direction, c)
            for k in range(n_pert)
        ], axis=1)                                # (n_questions, n_perturbed)

    rank1 = true_lp[:, None] > pert_lp
    truth_ratio = np.exp(pert_lp).mean(axis=1) / np.exp(true_lp)
    return {
        "true_lp": true_lp,
        "perturbed_lp": pert_lp,
        "rank1": rank1.all(axis=1),
        "beats_frac": rank1.mean(axis=1),
        "truth_ratio": truth_ratio,
        "margin": true_lp - pert_lp.mean(axis=1),
    }


def summarize_discrimination(res: dict) -> dict:
    return {
        "rank1_acc": float(res["rank1"].mean()),
        "beats_frac": float(res["beats_frac"].mean()),
        "truth_ratio_median": float(np.median(res["truth_ratio"])),
        "prefers_truth_frac": float((res["truth_ratio"] < 1).mean()),
        "margin_mean": float(res["margin"].mean()),
        "true_lp_mean": float(res["true_lp"].mean()),
        "n": int(len(res["rank1"])),
    }
