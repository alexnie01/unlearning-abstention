"""
Experiment 15 (PLAN2 R3) — was the epistemic direction built from the wrong
checkpoint?

Experiment 02 built the direction from IdkDPO: abstained-forget minus
answered-retain. Experiment 14 then showed IdkDPO's published checkpoint is the
outlier of its own family — recognition 0.28 where three sibling settings give
0.39-0.61 at the same or higher abstention. Every downstream result (03, 04,
07, 10) uses that direction, so the question is whether it encodes abstention
or something peculiar to one checkpoint.

Four constructions, at every layer:

  D_dpo     IdkDPO abstained-forget - answered-retain   (what 02/03/04/07 use)
  D_nll     IdkNLL, same construction                   (the clean abstainer)
  W_dpo     IdkDPO abstained-forget - ANSWERED-forget   (content held fixed:
                                                         same authors, same
                                                         question style, only
                                                         the behaviour differs)
  W_nll     IdkNLL, same within-forget construction

W_* is the purest abstention axis available — forget/retain contrasts carry an
author-set confound that 02 measured at cosine 0.2-0.4 with content, while the
within-forget contrast has none by construction. It was computed as a
diagnostic in 02 (AUROC 0.81) but never used as the primary direction.

If all four agree, the downstream results stand as reported. If D_dpo is the
odd one out, 03/04/07/10 are measuring a checkpoint quirk and need re-reading
against whichever direction actually tracks abstention.

Usage:  uv run python experiments/15_direction_provenance.py
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
from src.config import BASE_MODEL, CHECKPOINTS, METHODS_UNDER_TEST, POSITIVE_CONTROLS
from src.directions import cv_auroc, diff_in_means, random_split_direction, unit
from src.stats import result_dir

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "results", "15_direction_provenance")
ACTS = os.path.join(ROOT, "results", "activations_n400")
B01 = os.path.join(ROOT, "results", "01_idk_behavior_n400")
LAYER = 12
MIN_CELL = 5


def masks(label):
    df = pd.read_csv(os.path.join(B01, f"responses_{label}_labeled.csv"))
    out = {}
    for c in ("forget", "retain"):
        sub = df[df.cls == c]
        m = sub.ignorant_majority
        out[c] = (m.fillna(False).astype(bool).to_numpy() if m.dtype == object
                  else m.astype(bool).to_numpy())
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    A = lambda m, s: np.load(os.path.join(ACTS, f"{m}_{s}.npy"))
    mk = {m: masks(m) for m in POSITIVE_CONTROLS}
    n_layers = A("base", "forget").shape[0]

    rows, dirs_at = [], {}
    for L in range(n_layers):
        d = {}
        for lab, key in (("IdkDPO", "D_dpo"), ("IdkNLL", "D_nll")):
            pos = A(lab, "forget")[L][mk[lab]["forget"]]
            neg = A(lab, "retain")[L][~mk[lab]["retain"]]
            if len(pos) >= MIN_CELL and len(neg) >= MIN_CELL:
                d[key] = diff_in_means(pos, neg)
        for lab, key in (("IdkDPO", "W_dpo"), ("IdkNLL", "W_nll")):
            pos = A(lab, "forget")[L][mk[lab]["forget"]]
            neg = A(lab, "forget")[L][~mk[lab]["forget"]]      # answered, same authors
            if len(pos) >= MIN_CELL and len(neg) >= MIN_CELL:
                d[key] = diff_in_means(pos, neg)
        content = diff_in_means(A("base", "forget")[L], A("base", "retain")[L])
        dirs_at[L] = {**d, "content": content}

        r = {"layer": L}
        keys = [k for k in ("D_dpo", "D_nll", "W_dpo", "W_nll") if k in d]
        for i, a in enumerate(keys):
            r[f"cos_{a}_content"] = float(d[a] @ content)
            for b in keys[i + 1:]:
                r[f"cos_{a}_{b}"] = float(d[a] @ d[b])
        # how well does each direction separate ABSTENTION with content fixed?
        for lab, key in (("IdkDPO", "D_dpo"), ("IdkDPO", "W_dpo"),
                         ("IdkNLL", "D_nll"), ("IdkNLL", "W_nll")):
            if key not in d:
                continue
            pos = A(lab, "forget")[L][mk[lab]["forget"]]
            neg = A(lab, "forget")[L][~mk[lab]["forget"]]
            if len(neg) >= MIN_CELL:
                p, n = pos @ d[key], neg @ d[key]
                from sklearn.metrics import roc_auc_score
                r[f"{key}_within_auroc"] = float(roc_auc_score(
                    [1] * len(p) + [0] * len(n), list(p) + list(n)))
        rows.append(r)
    tab = pd.DataFrame(rows)
    tab.to_csv(os.path.join(OUT, "directions_by_layer.csv"), index=False)

    d = dirs_at[LAYER]
    keys = [k for k in ("D_dpo", "D_nll", "W_dpo", "W_nll", "content") if k in d]
    M = pd.DataFrame([[float(d[a] @ d[b]) for b in keys] for a in keys], index=keys, columns=keys)
    print(f"\nlayer {LAYER}: pairwise cosine between direction constructions\n")
    print(M.round(3).to_string())

    # Re-run the alignment verdicts under each direction.
    base = {s: A("base", s)[LAYER] for s in ("forget", "retain")}
    order = POSITIVE_CONTROLS + METHODS_UNDER_TEST
    shifts = {}
    for m in order:
        off = ((A(m, "forget")[LAYER] - base["forget"]).mean(0)
               - (A(m, "retain")[LAYER] - base["retain"]).mean(0))
        n = float(np.linalg.norm(off))
        shifts[m] = off / n if n > 1e-6 else np.full_like(off, np.nan)
    split = random_split_direction(A("IdkDPO", "retain")[LAYER][~mk["IdkDPO"]["retain"]], seed=LAYER)
    align = pd.DataFrame({k: {m: float(d[k] @ shifts[m]) for m in order} for k in keys})
    align["split"] = {m: float(split @ shifts[m]) for m in order}
    print(f"\ncos(direction, each method's differential shift) at layer {LAYER}\n")
    print(align.round(3).to_string())

    # Cell sizes decide which constructions are even estimable. IdkNLL abstains
    # on 94% of forget10, so its answered-forget cell is ~23 rows -- a centroid
    # from 23 points in 2048-d is noise, which is why W_nll is near-orthogonal
    # to everything. And because it abstains on almost all of forget, D_nll's
    # contrast is nearly "forget vs retain", i.e. content (cos 0.71).
    cells = {}
    for lab in POSITIVE_CONTROLS:
        mm = mk[lab]
        cells[lab] = {"abstained_forget": int(mm["forget"].sum()),
                      "answered_forget": int((~mm["forget"]).sum()),
                      "answered_retain": int((~mm["retain"]).sum())}
    usable = {k: True for k in keys if k != "content"}
    usable["W_nll"] = cells["IdkNLL"]["answered_forget"] >= 50
    usable["D_nll"] = abs(M.loc["D_nll", "content"]) < 0.5
    print("\ncell sizes:", json.dumps(cells))
    print("estimable / content-clean:", usable)
    same = all(abs(M.loc["D_dpo", k]) > 0.3 for k in keys if k not in ("D_dpo", "content"))
    ranks = {k: align[k].drop(POSITIVE_CONTROLS).sort_values(ascending=False).index.tolist()
             for k in keys if k != "content"}
    agree = len({tuple(v[:2]) for v in ranks.values()}) == 1
    verdict = (
        f"Constructions {'agree' if same else 'DISAGREE'} on direction "
        f"(cos(D_dpo, D_nll) = {M.loc['D_dpo', 'D_nll']:+.2f}, "
        f"cos(D_dpo, W_dpo) = {M.loc['D_dpo', 'W_dpo']:+.2f}); the top-two ranking of "
        f"methods by alignment {'is stable' if agree else 'CHANGES'} across them: "
        + "; ".join(f"{k}: {', '.join(v[:2])}" for k, v in ranks.items()))
    print("\n=>", verdict)

    with open(os.path.join(OUT, "summary.json"), "w") as f:
        json.dump({"layer": LAYER, "cells": cells, "usable": usable,
                   "cosines": M.round(4).to_dict(),
                   "alignment": align.round(4).to_dict(), "rankings": ranks,
                   "verdict": verdict}, f, indent=2)
    with open(os.path.join(OUT, "summary.md"), "w") as f:
        f.write(f"# 15 — does the epistemic direction depend on which checkpoint built it?\n\n"
                f"Pairwise cosine at layer {LAYER}:\n\n" + M.round(3).to_markdown() +
                f"\n\nAlignment of each method's differential shift:\n\n" +
                align.round(3).to_markdown() + f"\n\n**{verdict}**\n\n"
                f"Cell sizes: `{json.dumps(cells)}`. W_nll rests on a "
                f"{cells['IdkNLL']['answered_forget']}-row centroid in 2048-d and is "
                f"noise-dominated; D_nll is {M.loc['D_nll','content']:.2f} content because "
                f"IdkNLL abstains on almost all of forget10, making its forget-vs-retain "
                f"contrast nearly the author-set contrast. **W_dpo is the only construction "
                f"that is both well-estimated ({cells['IdkDPO']['abstained_forget']} vs "
                f"{cells['IdkDPO']['answered_forget']} rows) and content-clean "
                f"(cos {M.loc['W_dpo','content']:.2f} with content).**\n")

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    for k in ("cos_D_dpo_D_nll", "cos_D_dpo_W_dpo", "cos_D_nll_W_nll", "cos_W_dpo_W_nll"):
        if k in tab:
            axes[0].plot(tab.layer, tab[k], "o-", ms=3, label=k.replace("cos_", ""))
    for k in ("cos_D_dpo_content", "cos_D_nll_content", "cos_W_dpo_content"):
        if k in tab:
            axes[0].plot(tab.layer, tab[k], "x--", ms=4, lw=0.9, label=k.replace("cos_", ""))
    axes[0].axhline(0, color="k", lw=0.5); axes[0].set_xlabel("layer")
    axes[0].set_ylabel("cosine"); axes[0].legend(fontsize=6); axes[0].set_title("Do the constructions agree?")
    for k in [c for c in tab.columns if c.endswith("_within_auroc")]:
        axes[1].plot(tab.layer, tab[k], "o-", ms=3, label=k.replace("_within_auroc", ""))
    axes[1].axhline(0.5, color="k", lw=0.5); axes[1].set_xlabel("layer")
    axes[1].set_ylabel("AUROC, abstained vs answered forget"); axes[1].legend(fontsize=7)
    axes[1].set_title("Which separates behaviour with content held fixed?")
    plt.tight_layout(); plt.savefig(os.path.join(OUT, "direction_provenance.png"), dpi=150)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
