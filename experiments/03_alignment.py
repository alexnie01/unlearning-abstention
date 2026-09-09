"""
Experiment 03 — does any method's base->unlearned shift resemble learned
abstention?

Comparator. Every unlearning finetune drifts the whole model: the mean offset
on RETAIN prompts is nearly as large as on forget prompts, and a direction
that aligns with both is global drift, not a forget-specific gate. So the
shift analysed is the DIFFERENTIAL offset

    shift_m(L) = mean_q∈forget(act_m - act_base) - mean_q∈retain(act_m - act_base),

which matches how the epistemic direction itself is built (forget-vs-retain).
Raw forget/retain offsets are kept for reference.

References at each layer:
  D             epistemic direction from 02 (IdkDPO abstained-forget minus
                answered-retain) — the plan's instrument
  N             same construction on IdkNLL
  shift_IdkDPO  IdkDPO's own differential shift  }  the ground-truth
  shift_IdkNLL  IdkNLL's own differential shift  }  learned-abstention shifts
Controls: content (base forget-vs-retain), split (random halves of answered
retain rows on IdkDPO), random-Gaussian p99 floor. Bootstrap CIs resample
questions (500 draws) for the two headline cosines.

Anchor gate: the two positive controls' shifts must align with each other
beyond the controls (two independent abstention finetunes moving forget
representations the same way). A method under test counts as abstention-
like only if its shift aligns with BOTH anchor shifts beyond the controls.

Usage:  uv run python experiments/03_alignment.py  [--layer L] [--n-boot 500]
"""
import argparse
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
from src.config import BASE_MODEL, CHECKPOINTS, METHODS_UNDER_TEST, POSITIVE_CONTROLS
from src.data import matched_sample
from src.directions import diff_in_means, random_split_direction, unit
from src.refusal_alignment import random_floor_cosine

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "results", "03_alignment")
ACTS = os.path.join(ROOT, "results", "activations")
DIRS = os.path.join(ROOT, "results", "02_epistemic_direction")
N = 100
ORDER = POSITIVE_CONTROLS + METHODS_UNDER_TEST
MARGIN = 1.5


def masks_for(label):
    df = pd.read_csv(os.path.join(ROOT, "results", "01_idk_behavior", f"responses_{label}_labeled.csv"))
    return {c: df[df.cls == c].ignorant_majority.to_numpy(dtype=bool) for c in ("forget", "retain")}


def safe_unit(v):
    n = float(np.linalg.norm(v))
    return (v / n if n > 1e-6 else np.full_like(v, np.nan)), n


def shift(acts, base, m, L, fi=slice(None), ri=slice(None)):
    return ((acts[m]["forget"][L][fi] - base["forget"][L][fi]).mean(axis=0)
            - (acts[m]["retain"][L][ri] - base["retain"][L][ri]).mean(axis=0))


def main(layer_arg, n_boot):
    os.makedirs(OUT, exist_ok=True)
    sample = matched_sample(N)
    qs = {cls: [r["question"] for r in rows] for cls, rows in sample.items()}
    with open(os.path.join(DIRS, "summary.json")) as f:
        s02 = json.load(f)
    chosen = layer_arg if layer_arg is not None else s02["best_layer"]

    base = cached_activations("base", BASE_MODEL, qs, ACTS)
    acts = {m: cached_activations(m, CHECKPOINTS[m], qs, ACTS) for m in ORDER}
    n_layers = base["forget"].shape[0]
    mk = {m: masks_for(m) for m in POSITIVE_CONTROLS}

    def refs_at(L):
        return {
            "D": np.load(os.path.join(DIRS, f"epistemic_direction_L{L}.npy")),
            "N": diff_in_means(acts["IdkNLL"]["forget"][L][mk["IdkNLL"]["forget"]],
                               acts["IdkNLL"]["retain"][L][~mk["IdkNLL"]["retain"]]),
            "shift_IdkDPO": unit(shift(acts, base, "IdkDPO", L)),
            "shift_IdkNLL": unit(shift(acts, base, "IdkNLL", L)),
            "content": diff_in_means(base["forget"][L], base["retain"][L]),
            "split": random_split_direction(acts["IdkDPO"]["retain"][L][~mk["IdkDPO"]["retain"]], seed=L),
        }

    rows, matrices = [], {}
    for L in range(n_layers):
        refs = refs_at(L)
        floor = random_floor_cosine(refs["D"])["p99_abs_cos"]
        units = {}
        for m in ORDER:
            off_f = (acts[m]["forget"][L] - base["forget"][L]).mean(axis=0)
            off_r = (acts[m]["retain"][L] - base["retain"][L]).mean(axis=0)
            for kind, off in (("forget", off_f), ("retain", off_r), ("differential", off_f - off_r)):
                u, norm = safe_unit(off)
                if kind == "differential":
                    units[m] = u
                rows.append({"layer": L, "method": m, "offset": kind, "offset_norm": norm,
                             **{f"cos_{k}": float(v @ u) for k, v in refs.items()},
                             "floor_p99": floor})
        names = ["D", "N", "content"] + ORDER
        vecs = [refs["D"], refs["N"], refs["content"]] + [units[m] for m in ORDER]
        matrices[L] = pd.DataFrame([[float(a @ b) for b in vecs] for a in vecs], index=names, columns=names)
    tab = pd.DataFrame(rows)
    tab.to_csv(os.path.join(OUT, "alignment_all_layers.csv"), index=False)
    matrices[chosen].to_csv(os.path.join(OUT, f"shift_similarity_L{chosen}.csv"))

    # Bootstrap over questions at the chosen layer (direction AND shifts rebuilt per draw).
    rng = np.random.default_rng(0)
    L = chosen
    boots = {m: {"cos_D": [], "cos_shift_IdkNLL": [], "cos_shift_IdkDPO": []} for m in ORDER}
    for _ in range(n_boot):
        fi, ri = rng.integers(0, N, N), rng.integers(0, N, N)
        fa = mk["IdkDPO"]["forget"][fi]; ra = ~mk["IdkDPO"]["retain"][ri]
        if fa.sum() < 3 or ra.sum() < 3:
            continue
        D = diff_in_means(acts["IdkDPO"]["forget"][L][fi][fa], acts["IdkDPO"]["retain"][L][ri][ra])
        sN = unit(shift(acts, base, "IdkNLL", L, fi, ri)); sD = unit(shift(acts, base, "IdkDPO", L, fi, ri))
        for m in ORDER:
            u, n = safe_unit(shift(acts, base, m, L, fi, ri))
            boots[m]["cos_D"].append(float(D @ u)); boots[m]["cos_shift_IdkNLL"].append(float(sN @ u))
            boots[m]["cos_shift_IdkDPO"].append(float(sD @ u))
    ci = {m: {k: [float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))]
              for k, v in b.items()} for m, b in boots.items()}

    at = tab[(tab.layer == chosen) & (tab.offset == "differential")].set_index("method")
    raw = tab[(tab.layer == chosen) & (tab.offset == "forget")].set_index("method")
    ret = tab[(tab.layer == chosen) & (tab.offset == "retain")].set_index("method")
    anchor = float(matrices[chosen].loc["IdkDPO", "IdkNLL"])
    print(f"\nLayer {chosen}: cos(D, N) = {matrices[chosen].loc['D', 'N']:+.2f}; "
          f"cos(N, content) = {matrices[chosen].loc['N', 'content']:+.2f}; "
          f"anchor cos(shift_IdkDPO, shift_IdkNLL) = {anchor:+.2f}")
    print("cosine of each method's DIFFERENTIAL shift (forget − retain) with:")
    print(f"{'method':9}{'|shift|':>8}{'D':>7}{'N':>7}{'sIdkDPO':>9}{'sIdkNLL':>9}{'content':>9}{'split':>7}"
          f"{'|rawF D':>9}{'rawR D':>8}  verdict")
    verdicts = {}
    for m in ORDER:
        r = at.loc[m]
        chance = max(r.floor_p99, MARGIN * abs(r.cos_content), MARGIN * abs(r.cos_split))
        a_dpo = r.cos_shift_IdkDPO > chance and ci[m]["cos_shift_IdkDPO"][0] > 0
        a_nll = r.cos_shift_IdkNLL > chance and ci[m]["cos_shift_IdkNLL"][0] > 0
        d_ok = r.cos_D > chance and ci[m]["cos_D"][0] > 0
        if m in POSITIVE_CONTROLS:
            v = "anchor"
        else:
            v = "ABSTENTION-LIKE (both anchors)" if a_dpo and a_nll else \
                ("IdkDPO-shift only" if a_dpo else "IdkNLL-shift only" if a_nll else "= chance")
            v += " ; D aligned" if d_ok else " ; D = chance"
        verdicts[m] = {"aligned_shift_IdkDPO": bool(a_dpo), "aligned_shift_IdkNLL": bool(a_nll),
                       "aligned_D": bool(d_ok), "chance": float(chance), "ci95": ci[m],
                       **{k: float(r[k]) for k in ("cos_D", "cos_N", "cos_shift_IdkDPO",
                                                   "cos_shift_IdkNLL", "cos_content", "cos_split")}}
        print(f"{m:9}{r.offset_norm:8.2f}{r.cos_D:+7.2f}{r.cos_N:+7.2f}{r.cos_shift_IdkDPO:+9.2f}"
              f"{r.cos_shift_IdkNLL:+9.2f}{r.cos_content:+9.2f}{r.cos_split:+7.2f}"
              f"{raw.loc[m].cos_D:+9.2f}{ret.loc[m].cos_D:+8.2f}  {v}")
    ctrl_anchor = max(at.floor_p99.iloc[0], MARGIN * abs(matrices[chosen].loc["IdkNLL", "content"]),
                      MARGIN * abs(at.loc["IdkNLL"].cos_split))
    anchor_ok = anchor > ctrl_anchor and ci["IdkNLL"]["cos_shift_IdkDPO"][0] > 0
    live = [m for m in METHODS_UNDER_TEST
            if verdicts[m]["aligned_shift_IdkDPO"] and verdicts[m]["aligned_shift_IdkNLL"]]
    gate = (f"PASS: the two abstention finetunes' forget-specific shifts align "
            f"(cos {anchor:+.2f}, 95% CI {ci['IdkNLL']['cos_shift_IdkDPO'][0]:+.2f}..{ci['IdkNLL']['cos_shift_IdkDPO'][1]:+.2f})"
            if anchor_ok else f"FAIL: positive-control shifts do not align with each other (cos {anchor:+.2f})")
    print("\nGATE —", gate)
    print("methods under test whose shift aligns with BOTH abstention anchors:", live or "none")

    with open(os.path.join(OUT, "summary.json"), "w") as f:
        json.dump({"layer": chosen, "gate": gate, "anchor_cos": anchor, "anchor_ok": anchor_ok,
                   "live_methods": live, "verdicts": verdicts, "n_boot": n_boot,
                   "cos_D_N": float(matrices[chosen].loc["D", "N"]),
                   "cos_N_content": float(matrices[chosen].loc["N", "content"]),
                   "cos_D_content": float(matrices[chosen].loc["D", "content"]),
                   "similarity_matrix": matrices[chosen].round(3).to_dict()}, f, indent=2)
    with open(os.path.join(OUT, "summary.md"), "w") as f:
        f.write(f"# 03 — alignment at layer {chosen}\n\n"
                f"Anchor: cos(shift_IdkDPO, shift_IdkNLL) = {anchor:+.2f}. cos(D,N) = "
                f"{matrices[chosen].loc['D','N']:+.2f}; cos(N, content) = {matrices[chosen].loc['N','content']:+.2f}.\n\n"
                "Differential shift (forget − retain) of each method vs references:\n\n")
        f.write(at.reset_index()[["method", "offset_norm", "cos_D", "cos_N", "cos_shift_IdkDPO",
                                  "cos_shift_IdkNLL", "cos_content", "cos_split", "floor_p99"]]
                .to_markdown(index=False, floatfmt=".3f") + "\n\n")
        f.write("Raw forget-prompt offset (global drift included):\n\n")
        f.write(raw.reset_index()[["method", "offset_norm", "cos_D", "cos_N", "cos_content", "cos_split"]]
                .to_markdown(index=False, floatfmt=".3f") + "\n\n")
        f.write(f"Similarity matrix of shifts (layer {chosen}):\n\n")
        f.write(matrices[chosen].round(2).to_markdown() + "\n\n")
        f.write(f"**Gate:** {gate}\n\nAbstention-like methods: {live or 'none'}\n")

    # Figure 1: bars at the chosen layer, differential shift vs each reference.
    x = np.arange(len(ORDER)); w = 0.16
    fig, ax = plt.subplots(figsize=(10, 4.8))
    for k, (col, name, c) in enumerate([("cos_shift_IdkDPO", "IdkDPO's own shift", "tab:blue"),
                                        ("cos_shift_IdkNLL", "IdkNLL's own shift", "tab:cyan"),
                                        ("cos_D", "epistemic direction D (plan)", "tab:purple"),
                                        ("cos_content", "content (base forget−retain)", "tab:orange"),
                                        ("cos_split", "random split", "grey")]):
        ax.bar(x + (k - 2) * w, at.loc[ORDER, col], w, label=name, color=c, edgecolor="k", lw=0.5)
    for i, m in enumerate(ORDER):
        for k, key in ((0, "cos_shift_IdkDPO"), (1, "cos_shift_IdkNLL")):
            lo, hi = ci[m][key]
            ax.plot([x[i] + (k - 2) * w] * 2, [lo, hi], color="k", lw=1)
    ax.axhspan(-at.floor_p99.iloc[0], at.floor_p99.iloc[0], color="grey", alpha=0.15, label="random floor (p99)")
    ax.axhline(0, color="k", lw=0.5); ax.axvline(len(POSITIVE_CONTROLS) - 0.5, color="k", ls=":", lw=1)
    ax.set_xticks(x); ax.set_xticklabels(ORDER)
    ax.set_ylabel("cos(reference, forget − retain mean shift)")
    ax.set_title(f"Is each method's forget-specific shift abstention-like?  (layer {chosen}; bars = point estimate, ticks = 95% bootstrap CI)")
    ax.legend(fontsize=7, loc="upper right", ncol=2); plt.tight_layout()
    plt.savefig(os.path.join(OUT, "alignment_bars.png"), dpi=150)

    # Figure 2: by layer, cos with each anchor shift.
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
    for ax, key, title in zip(axes, ("cos_shift_IdkDPO", "cos_shift_IdkNLL"),
                              ("vs IdkDPO's shift", "vs IdkNLL's shift")):
        for m in ORDER:
            sub = tab[(tab.method == m) & (tab.offset == "differential")]
            ax.plot(sub.layer, sub[key], "o-" if m in POSITIVE_CONTROLS else "s--", ms=4, label=m)
        fl = tab[tab.offset == "differential"].groupby("layer").floor_p99.first()
        ax.fill_between(fl.index, -fl.values, fl.values, color="grey", alpha=0.2)
        ax.axhline(0, color="k", lw=0.5); ax.axvline(chosen, color="k", ls=":", lw=0.8)
        ax.set_xlabel("layer"); ax.set_title(f"forget-specific shift {title}")
    axes[0].set_ylabel("cosine"); axes[1].legend(fontsize=7, ncol=2)
    plt.tight_layout(); plt.savefig(os.path.join(OUT, "alignment_by_layer.png"), dpi=150)

    # Figure 3: similarity heatmaps at two layers.
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, Lh in zip(axes, sorted({8, chosen})):
        M = matrices[Lh]
        im = ax.imshow(M.values, cmap="RdBu_r", vmin=-1, vmax=1)
        ax.set_xticks(range(len(M))); ax.set_xticklabels(M.columns, rotation=60, fontsize=7)
        ax.set_yticks(range(len(M))); ax.set_yticklabels(M.index, fontsize=7)
        for i in range(len(M)):
            for j in range(len(M)):
                ax.text(j, i, f"{M.values[i, j]:+.2f}", ha="center", va="center", fontsize=6)
        ax.set_title(f"cosine between forget-specific shifts (layer {Lh})")
    fig.colorbar(im, ax=axes, shrink=0.8); plt.savefig(os.path.join(OUT, "shift_similarity.png"), dpi=150)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--layer", type=int, default=None)
    ap.add_argument("--n-boot", type=int, default=500)
    a = ap.parse_args()
    main(a.layer, a.n_boot)
