"""
Experiment 02 — the epistemic-refusal direction on IdkDPO, and where it lives.

direction_L = unit( mean(IdkDPO acts | forget & ABSTAINED)
                  - mean(IdkDPO acts | retain & ANSWERED) )   at each layer L

Two controls are built alongside, at every layer:
  content   the SAME forget-vs-retain diff-in-means on the BASE model, which
            answers both. Forget and retain questions are about different
            authors, so part of the IdkDPO direction is "which author set", not
            "abstain". cos(epistemic, content) says how much.
  split     diff-in-means between random halves of the answered-retain rows on
            IdkDPO: same construction, no behavioral signal; its held-out AUROC
            should sit at chance.

Gate: the epistemic direction must separate held-out abstained-forget from
answered-retain rows at some layer (CV AUROC well above the split control).
Also reported: within-class separation where IdkDPO's minority cells
(answered-forget, abstained-retain) exist, which isolates behavior from content.

Usage:  uv run python experiments/02_epistemic_direction.py
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.activations import cached_activations
from src.config import BASE_MODEL, checkpoint
from src.data import matched_sample
from src.directions import cv_auroc, d_prime, diff_in_means, random_split_direction
from src.stats import result_dir

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = result_dir("02_epistemic_direction")
ACTS = result_dir("activations")
LABELS = result_dir("01_idk_behavior")
N = int(os.environ.get("N_QUESTIONS", 100))
MIN_CELL = 5      # fewest rows that can define a centroid / a CV fold


def load_labels(label):
    df = pd.read_csv(os.path.join(LABELS, f"responses_{label}_labeled.csv"))
    return df


def main():
    os.makedirs(OUT, exist_ok=True)
    sample = matched_sample(N)
    qs = {cls: [r["question"] for r in rows] for cls, rows in sample.items()}

    acts = {}
    for label, path in [("IdkDPO", checkpoint("IdkDPO")), ("IdkNLL", checkpoint("IdkNLL")),
                        ("base", BASE_MODEL)]:
        acts[label] = cached_activations(label, path, qs, ACTS)
    n_layers = acts["IdkDPO"]["forget"].shape[0]

    # Behavioral masks from 01, aligned to the same sample order.
    masks = {}
    for label in ("IdkDPO", "IdkNLL"):
        df = load_labels(label)
        for cls in ("forget", "retain"):
            sub = df[df.cls == cls]
            assert list(sub.prompt) == qs[cls], f"{label}/{cls} prompt order mismatch with 01"
            masks[(label, cls)] = sub.ignorant_majority.to_numpy(dtype=bool)
    cells = {label: {"abstained_forget": int(masks[(label, "forget")].sum()),
                     "answered_forget": int((~masks[(label, "forget")]).sum()),
                     "abstained_retain": int(masks[(label, "retain")].sum()),
                     "answered_retain": int((~masks[(label, "retain")]).sum())}
             for label in ("IdkDPO", "IdkNLL")}
    print("cells:", json.dumps(cells, indent=1))

    rows, directions = [], {}
    for L in range(n_layers):
        r = {"layer": L}
        for label in ("IdkDPO", "IdkNLL"):
            pos = acts[label]["forget"][L][masks[(label, "forget")]]
            neg = acts[label]["retain"][L][~masks[(label, "retain")]]
            # A centroid needs points. Minority cells can be empty at small n or
            # for a checkpoint that always abstains; emit NaN rather than dying.
            if len(pos) < MIN_CELL or len(neg) < MIN_CELL:
                for k in ("auroc", "dprime", "gap", "within_forget_auroc", "within_retain_auroc"):
                    r[f"{label}_{k}"] = float("nan")
                if label == "IdkDPO":
                    directions[L] = np.full(acts[label]["forget"].shape[-1], np.nan)
                continue
            d = diff_in_means(pos, neg)
            if label == "IdkDPO":
                directions[L] = d
            r[f"{label}_auroc"] = cv_auroc(pos, neg)
            r[f"{label}_dprime"] = d_prime(pos, neg, d)
            r[f"{label}_gap"] = float(pos.mean(0) @ d - neg.mean(0) @ d)
            # within-class: does d separate behavior holding the author set fixed?
            f_ans = acts[label]["forget"][L][~masks[(label, "forget")]]
            r_abs = acts[label]["retain"][L][masks[(label, "retain")]]
            r[f"{label}_within_forget_auroc"] = cv_auroc(pos, f_ans, n_folds=min(5, len(f_ans))) \
                if len(f_ans) >= MIN_CELL else float("nan")
            r[f"{label}_within_retain_auroc"] = cv_auroc(r_abs, neg, n_folds=min(5, len(r_abs))) \
                if len(r_abs) >= MIN_CELL else float("nan")
        # controls
        d_content = diff_in_means(acts["base"]["forget"][L], acts["base"]["retain"][L])
        r["content_auroc"] = cv_auroc(acts["base"]["forget"][L], acts["base"]["retain"][L])
        r["cos_epi_content"] = float(directions[L] @ d_content)
        neg = acts["IdkDPO"]["retain"][L][~masks[("IdkDPO", "retain")]]
        idx = np.random.default_rng(L).permutation(len(neg)); h = len(idx) // 2
        r["split_auroc"] = cv_auroc(neg[idx[:h]], neg[idx[h:2 * h]])
        r["cos_epi_split"] = float(directions[L] @ random_split_direction(neg, seed=L))
        r["cos_IdkDPO_IdkNLL"] = float(directions[L] @ diff_in_means(
            acts["IdkNLL"]["forget"][L][masks[("IdkNLL", "forget")]],
            acts["IdkNLL"]["retain"][L][~masks[("IdkNLL", "retain")]]))
        rows.append(r)
        print(f"L{L:2d} epi AUROC {r['IdkDPO_auroc']:.3f} d'={r['IdkDPO_dprime']:.2f} | "
              f"content AUROC {r['content_auroc']:.3f} cos(epi,content)={r['cos_epi_content']:+.2f} | "
              f"split {r['split_auroc']:.3f} | within-forget {r['IdkDPO_within_forget_auroc']:.3f} "
              f"within-retain {r['IdkDPO_within_retain_auroc']:.3f} | IdkNLL {r['IdkNLL_auroc']:.3f}")

    tab = pd.DataFrame(rows)
    if tab.IdkDPO_auroc.isna().all():
        c = cells["IdkDPO"]
        raise SystemExit(
            f"No layer had enough rows to build a direction: IdkDPO has "
            f"{c['abstained_forget']} abstained-forget and {c['answered_retain']} "
            f"answered-retain rows, and {MIN_CELL} of each are needed. Raise --n.")
    best_auroc = int(tab.loc[tab.IdkDPO_auroc.idxmax(), "layer"])
    # Working layer: raw AUROC saturates toward the final layer, where the
    # residual is already the next-token readout. Among layers that separate
    # well (>= 0.95), pick the one where the direction best separates BEHAVIOR
    # with content held fixed (abstained vs answered forget questions).
    ok = tab[(tab.IdkDPO_auroc >= 0.95) & tab.IdkDPO_within_forget_auroc.notna()]
    best = int(ok.loc[ok.IdkDPO_within_forget_auroc.idxmax(), "layer"]) if len(ok) else best_auroc
    gate = bool(tab.IdkDPO_auroc.max() > 0.9)
    verdict = (f"PASS: epistemic direction separates held-out rows (max CV AUROC "
               f"{tab.IdkDPO_auroc.max():.3f} at layer {best_auroc}; working layer {best}, "
               f"within-forget AUROC {tab.loc[best, 'IdkDPO_within_forget_auroc']:.3f})"
               if gate else f"FAIL: max CV AUROC {tab.IdkDPO_auroc.max():.3f} <= 0.9")
    print("\nGATE —", verdict)

    for L, d in directions.items():
        np.save(os.path.join(OUT, f"epistemic_direction_L{L}.npy"), d)
    tab.to_csv(os.path.join(OUT, "layer_sweep.csv"), index=False)
    with open(os.path.join(OUT, "summary.json"), "w") as f:
        json.dump({"cells": cells, "best_layer": best, "best_layer_by_auroc": best_auroc,
                   "gate_pass": gate, "verdict": verdict, "table": rows}, f, indent=2)
    with open(os.path.join(OUT, "summary.md"), "w") as f:
        f.write("# 02 — epistemic direction layer sweep (IdkDPO)\n\n")
        f.write(f"Cells: `{json.dumps(cells)}`\n\n")
        f.write(tab.to_markdown(index=False, floatfmt=".3f") + "\n\n")
        f.write(f"**Gate:** {verdict}\n")

    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].plot(tab.layer, tab.IdkDPO_auroc, "o-", label="epistemic (IdkDPO)")
    ax[0].plot(tab.layer, tab.IdkNLL_auroc, "s--", label="epistemic (IdkNLL)")
    ax[0].plot(tab.layer, tab.content_auroc, "^-", label="content (base, forget vs retain)")
    ax[0].plot(tab.layer, tab.IdkDPO_within_forget_auroc, "v:", label="within-forget (behavior only)")
    ax[0].plot(tab.layer, tab.split_auroc, "x-", color="grey", label="random split (control)")
    ax[0].axhline(0.5, color="k", lw=0.5); ax[0].set_ylim(0.4, 1.02)
    ax[0].set_xlabel("layer"); ax[0].set_ylabel("held-out AUROC"); ax[0].legend(fontsize=7)
    ax[0].set_title("Separability of the diff-in-means direction")
    ax[1].plot(tab.layer, tab.cos_epi_content, "o-", label="cos(epistemic, content)")
    ax[1].plot(tab.layer, tab.cos_IdkDPO_IdkNLL, "s-", label="cos(IdkDPO, IdkNLL)")
    ax[1].plot(tab.layer, tab.cos_epi_split, "x-", color="grey", label="cos(epistemic, split)")
    ax[1].axhline(0, color="k", lw=0.5); ax[1].set_xlabel("layer"); ax[1].legend(fontsize=7)
    ax[1].set_title("How much of the epistemic direction is content?")
    plt.tight_layout(); plt.savefig(os.path.join(OUT, "layer_sweep.png"), dpi=150)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
