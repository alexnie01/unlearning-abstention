"""
Experiment 04b — is the epistemic direction causal at any magnitude / layer?

04 translates by the centroid gap. If that barely moves the positive control
itself, a null on RMU/AltPO is uninformative. This sweeps |c| over multiples
of the gap at two layers on IdkDPO (must respond), base (should start
abstaining under +c), and AltPO (03's candidate), scoring gold and IDK
log-probs, with the content direction as a matched-norm control. A few
generations at the largest |c| show whether the shift is coherent or noise.

Usage:  uv run python experiments/04b_magnitude_sweep.py [--layers 8 12] [--n 50]
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
import transformers

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import BASE_MODEL, checkpoint
from src.data import matched_sample
from src.directions import diff_in_means
from src.intervention import generate_chat, score_dataset_chat
from src.model_loader import free, load_model

transformers.logging.set_verbosity_error()
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "results", "04b_magnitude_sweep")
ACTS = os.path.join(ROOT, "results", "activations")
DIRS = os.path.join(ROOT, "results", "02_epistemic_direction")
ALL_MODELS = {"IdkDPO": checkpoint("IdkDPO"), "base": BASE_MODEL, "AltPO": checkpoint("AltPO"),
              "RMU": checkpoint("RMU")}
MULTS = [-8, -4, -2, -1, 0, 1, 2, 4, 8]


def main(layers, n, models):
    MODELS = {m: ALL_MODELS[m] for m in models}
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(DIRS, "summary.json")) as f:
        s02 = json.load(f)
    gaps = {L: float(next(r for r in s02["table"] if r["layer"] == L)["IdkDPO_gap"]) for L in layers}
    dirs = {}
    for L in layers:
        base_acts = {s: np.load(os.path.join(ACTS, f"base_{s}.npy"))[L] for s in ("forget", "retain")}
        dirs[L] = {"epistemic": np.load(os.path.join(DIRS, f"epistemic_direction_L{L}.npy")),
                   "content": diff_in_means(base_acts["forget"], base_acts["retain"])}
    idk = pd.read_csv(os.path.join(ROOT, "results", "01_idk_behavior", "responses_IdkDPO_labeled.csv"))
    idk_answer = idk[(idk.cls == "forget") & idk.ignorant_majority].response.mode().iloc[0]
    sample = matched_sample(100)["forget"][:n]
    qs, golds = [r["question"] for r in sample], [r["answer"] for r in sample]

    rows, gens = [], []
    for label, path in MODELS.items():
        model, tok, dev = load_model(path)
        for L in layers:
            ln = f"model.layers.{L}"
            for dname, d in dirs[L].items():
                for k in MULTS:
                    if k == 0 and dname != "epistemic":
                        continue
                    c = k * gaps[L]
                    g = score_dataset_chat(model, tok, dev, qs, golds, ln, d, c)
                    i = score_dataset_chat(model, tok, dev, qs, [idk_answer] * len(qs), ln, d, c)
                    rows.append({"model": label, "layer": L, "direction": dname, "mult": k, "c": c,
                                 "gold_lp": float(g.mean()), "idk_lp": float(i.mean())})
                    print(f"{label:7} L{L:2d} {dname:9} k={k:+2d}  gold {g.mean():+7.3f}  idk {i.mean():+7.3f}", flush=True)
                    if dname == "epistemic" and abs(k) in (4, 8):
                        for q in qs[:3]:
                            gens.append({"model": label, "layer": L, "mult": k, "prompt": q,
                                         "response": generate_chat(model, tok, dev, q, ln, d, c)})
        del model, tok
        free()

    tab, gtab = pd.DataFrame(rows), pd.DataFrame(gens)
    for name, new in (("sweep.csv", tab), ("generations.csv", gtab)):
        p = os.path.join(OUT, name)
        if os.path.exists(p):   # merge with earlier runs on other models
            old = pd.read_csv(p)
            new = pd.concat([old[~old.model.isin(models)], new], ignore_index=True)
        new.to_csv(p, index=False)
    tab, gens = pd.read_csv(os.path.join(OUT, "sweep.csv")), \
        pd.read_csv(os.path.join(OUT, "generations.csv")).to_dict(orient="records")
    MODELS = {m: ALL_MODELS[m] for m in tab.model.unique()}
    with open(os.path.join(OUT, "summary.json"), "w") as f:
        json.dump({"layers": layers, "gaps": gaps, "idk_answer": idk_answer,
                   "rows": tab.to_dict(orient="records")}, f, indent=2)

    fig, axes = plt.subplots(2, len(layers), figsize=(5 * len(layers), 7), squeeze=False)
    for j, L in enumerate(layers):
        for i, metric in enumerate(("gold_lp", "idk_lp")):
            ax = axes[i, j]
            for label in MODELS:
                for dname, ls in (("epistemic", "-"), ("content", ":")):
                    sub = tab[(tab.model == label) & (tab.layer == L) & (tab.direction == dname)].sort_values("mult")
                    ax.plot(sub.mult, sub[metric], ls, marker="o", ms=3, label=f"{label} / {dname}")
            ax.axvline(0, color="k", lw=0.5)
            ax.set_xlabel("c / gap"); ax.set_ylabel(f"mean {metric}")
            ax.set_title(f"layer {L}: {'gold answer' if metric == 'gold_lp' else 'IDK answer'} log-prob")
    axes[0, 0].legend(fontsize=6)
    plt.tight_layout(); plt.savefig(os.path.join(OUT, "sweep.png"), dpi=150)
    with open(os.path.join(OUT, "summary.md"), "w") as f:
        f.write("# 04b — magnitude sweep\n\n" + tab.to_markdown(index=False, floatfmt=".3f") + "\n\n## Generations\n\n")
        for g in gens:
            f.write(f"- **{g['model']} L{g['layer']} k={g['mult']:+d}** — {g['prompt'][:60]}\n\n  > {g['response'][:200]!r}\n\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--layers", type=int, nargs="+", default=[8, 12])
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--models", nargs="+", default=["IdkDPO", "base", "AltPO"])
    a = ap.parse_args()
    main(a.layers, a.n, a.models)
