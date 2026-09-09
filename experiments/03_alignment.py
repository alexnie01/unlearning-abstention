"""
Experiment 03 — does any method's base->unlearned shift point along the
epistemic direction?

offset_m(L) = mean_q( act_m[q] - act_base[q] )  over forget10 questions, layer L.

cos(epistemic_L, offset_m) is benchmarked against, at the same layer:
  content    forget-vs-retain diff-in-means on the base model (author-set
             signal, no abstention). If a method aligns with this as well as
             with the epistemic direction, the alignment is content.
  epi_perp   the epistemic direction with its content component projected out —
             the abstention-not-content residual.
  split      random-half diff-in-means of answered-retain rows on IdkDPO
             (same construction, no signal).
  floor      p99 of |cos| with random Gaussian unit vectors.
Positive anchors: IdkDPO's and IdkNLL's own offsets must align with the
epistemic direction, or the instrument is broken.

Usage:  uv run python experiments/03_alignment.py  [--layer L]
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


def main(layer_arg):
    os.makedirs(OUT, exist_ok=True)
    sample = matched_sample(N)
    qs = {cls: [r["question"] for r in rows] for cls, rows in sample.items()}
    with open(os.path.join(DIRS, "summary.json")) as f:
        s02 = json.load(f)
    chosen = layer_arg if layer_arg is not None else s02["best_layer"]

    acts = {"base": cached_activations("base", BASE_MODEL, qs, ACTS)}
    for m in ORDER:
        acts[m] = cached_activations(m, CHECKPOINTS[m], qs, ACTS)
    n_layers = acts["base"]["forget"].shape[0]

    idk = pd.read_csv(os.path.join(ROOT, "results", "01_idk_behavior", "responses_IdkDPO_labeled.csv"))
    answered_retain = ~idk[idk.cls == "retain"].ignorant_majority.to_numpy(dtype=bool)

    rows = []
    for L in range(n_layers):
        epi = np.load(os.path.join(DIRS, f"epistemic_direction_L{L}.npy"))
        content = diff_in_means(acts["base"]["forget"][L], acts["base"]["retain"][L])
        epi_perp = unit(epi - (epi @ content) * content)
        split = random_split_direction(acts["IdkDPO"]["retain"][L][answered_retain], seed=L)
        floor = random_floor_cosine(epi)["p99_abs_cos"]
        for m in ORDER:
            for cls in ("forget", "retain"):
                off = (acts[m][cls][L] - acts["base"][cls][L]).mean(axis=0)
                u = unit(off)
                rows.append({"layer": L, "method": m, "prompts": cls,
                             "offset_norm": float(np.linalg.norm(off)),
                             "cos_epi": float(epi @ u), "cos_epi_perp": float(epi_perp @ u),
                             "cos_content": float(content @ u), "cos_split": float(split @ u),
                             "floor_p99": floor})
    tab = pd.DataFrame(rows)
    tab.to_csv(os.path.join(OUT, "alignment_all_layers.csv"), index=False)

    at = tab[(tab.layer == chosen) & (tab.prompts == "forget")].set_index("method")
    print(f"\nLayer {chosen} — cosine of each method's forget-set mean offset with:")
    print(f"{'method':9}{'|off|':>7}{'epi':>8}{'epi⊥':>8}{'content':>9}{'split':>8}{'p99':>7}  verdict")
    verdicts = {}
    for m in ORDER:
        r = at.loc[m]
        beats = abs(r.cos_epi) > r.floor_p99 and abs(r.cos_epi) > 1.5 * max(abs(r.cos_content), abs(r.cos_split))
        perp_beats = abs(r.cos_epi_perp) > r.floor_p99 and abs(r.cos_epi_perp) > 1.5 * abs(r.cos_split)
        v = ("epistemic > controls" if beats else "= controls") + (" ; epi⊥ above floor" if perp_beats else "")
        verdicts[m] = {"epi_beats_controls": bool(beats), "epi_perp_above_split": bool(perp_beats)}
        print(f"{m:9}{r.offset_norm:7.2f}{r.cos_epi:+8.3f}{r.cos_epi_perp:+8.3f}{r.cos_content:+9.3f}"
              f"{r.cos_split:+8.3f}{r.floor_p99:7.3f}  {v}")

    anchors_ok = all(verdicts[m]["epi_beats_controls"] for m in POSITIVE_CONTROLS)
    live = [m for m in METHODS_UNDER_TEST if verdicts[m]["epi_beats_controls"]]
    gate = ("PASS: positive anchors align" if anchors_ok else
            "FAIL: a positive control's own offset does not align — instrument broken")
    print("\nGATE —", gate)
    print("methods under test whose offset aligns with the epistemic direction beyond controls:",
          live or "none")

    with open(os.path.join(OUT, "summary.json"), "w") as f:
        json.dump({"layer": chosen, "gate": gate, "anchors_ok": anchors_ok, "live_methods": live,
                   "verdicts": verdicts,
                   "at_layer": at.reset_index().to_dict(orient="records")}, f, indent=2)
    with open(os.path.join(OUT, "summary.md"), "w") as f:
        f.write(f"# 03 — alignment at layer {chosen}\n\n")
        f.write(at.reset_index()[["method", "offset_norm", "cos_epi", "cos_epi_perp",
                                  "cos_content", "cos_split", "floor_p99"]]
                .to_markdown(index=False, floatfmt=".3f") + "\n\n")
        f.write(f"**Gate:** {gate}\n\nLive methods: {live or 'none'}\n")

    # Figure 1: bar chart at the chosen layer (extends the exploratory chart with
    # the epistemic direction as its own group).
    x = np.arange(len(ORDER)); w = 0.2
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for k, (col, name, c) in enumerate([("cos_epi", "epistemic (IdkDPO)", "tab:blue"),
                                        ("cos_epi_perp", "epistemic ⊥ content", "tab:cyan"),
                                        ("cos_content", "content (base forget−retain)", "tab:orange"),
                                        ("cos_split", "random split (control)", "grey")]):
        ax.bar(x + (k - 1.5) * w, at.loc[ORDER, col].abs(), w, label=name, color=c, edgecolor="k", lw=0.5)
    ax.axhspan(0, at.floor_p99.iloc[0], color="grey", alpha=0.15, label="random floor (p99)")
    ax.axvline(len(POSITIVE_CONTROLS) - 0.5, color="k", ls=":", lw=1)
    ax.text(0.5, ax.get_ylim()[1] * 0.97, "positive controls", ha="center", va="top", fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels(ORDER); ax.set_ylabel("|cos(direction, forget-set mean offset)|")
    ax.set_title(f"Alignment of each method's base→unlearned shift with the epistemic direction (layer {chosen})")
    ax.legend(fontsize=7, loc="upper right"); plt.tight_layout()
    plt.savefig(os.path.join(OUT, "alignment_bars.png"), dpi=150)

    # Figure 2: cos_epi across layers, per method, forget prompts.
    fig, ax = plt.subplots(figsize=(8, 4))
    for m in ORDER:
        sub = tab[(tab.method == m) & (tab.prompts == "forget")]
        ax.plot(sub.layer, sub.cos_epi, "o-" if m in POSITIVE_CONTROLS else "s--", ms=4, label=m)
    ax.plot(tab[tab.method == ORDER[0]].layer.unique(),
            tab[(tab.method == ORDER[0]) & (tab.prompts == "forget")].floor_p99, color="grey", lw=0.8, label="p99 floor")
    ax.axhline(0, color="k", lw=0.5); ax.axvline(chosen, color="k", ls=":", lw=0.8)
    ax.set_xlabel("layer"); ax.set_ylabel("cos(epistemic_L, offset_m)"); ax.legend(fontsize=7, ncol=2)
    ax.set_title("Signed alignment with the epistemic direction, by layer")
    plt.tight_layout(); plt.savefig(os.path.join(OUT, "alignment_by_layer.png"), dpi=150)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--layer", type=int, default=None)
    main(ap.parse_args().layer)
