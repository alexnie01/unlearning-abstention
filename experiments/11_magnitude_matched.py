"""
Experiment 11 (PLAN2 R2) — is retained knowledge a property of the METHOD, or
just of how far it moved the model?

Across the five published checkpoints, recognition is almost perfectly
predicted by displacement: r(log‖shift‖, recognition) = -0.91 (NPO 0.98/0.69,
GradDiff 1.26/0.68, SimNPO 2.64/0.55, AltPO 2.70/0.32, RMU 11.9/0.20). So
"NPO retains knowledge" may mean nothing more than "NPO barely changed the
model". One checkpoint per method cannot separate those.

open-unlearning publishes 40-54 hyperparameter variants per method, so this
sweeps several per method and plots recognition AGAINST displacement as a curve
per method. Comparing curves rather than points is what the confound demands:
  - curves separate at matched ‖shift‖ -> the method matters, the split is real
  - curves collapse onto one line     -> displacement explains everything, and
                                         the honest finding is that knowledge
                                         loss is a function of how far you move
                                         the model, with IdkNLL the one escapee

IdkNLL is the reason this is worth running: at ‖shift‖ 4.03 it keeps 0.70
recognition where the trend predicts ~0.35. If that survives at matched
displacement it is the strongest result in the project — abstention training
escapes a trade-off every unlearning method obeys.

Disk: each checkpoint is ~2.5 GB and there are dozens, so variants are
processed one at a time and deleted from the HF cache immediately. Peak usage
is one checkpoint. The run resumes from its CSV if interrupted.

Usage:  uv run python experiments/11_magnitude_matched.py [--n 200] [--per-method 4]
"""
import argparse
import json
import os
import re
import shutil
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import transformers
from huggingface_hub import HfApi

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.activations import all_layer_activations
from src.config import BASE_MODEL, CHECKPOINTS, METHODS_UNDER_TEST, POSITIVE_CONTROLS
from src.data import matched_sample, sample_split
from src.knowledge import load_perturbed, score_discrimination, summarize_discrimination
from src.model_loader import free, load_model
from src.stats import result_dir

transformers.logging.set_verbosity_error()
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "results", "11_magnitude_matched")
BASE_ACTS = os.path.join(ROOT, "results", "activations_n400")
LAYER = 12                      # pre-registered (PLAN2 A4)
METHODS = POSITIVE_CONTROLS + METHODS_UNDER_TEST
HUB_CACHE = os.path.expanduser("~/.cache/huggingface/hub")
MIN_FREE_GB = 8


def free_gb():
    s = os.statvfs(HUB_CACHE)
    return s.f_bavail * s.f_frsize / 2**30


def drop_from_cache(repo_id: str):
    d = os.path.join(HUB_CACHE, "models--" + repo_id.replace("/", "--"))
    if os.path.isdir(d):
        shutil.rmtree(d, ignore_errors=True)


def pick_variants(per_method: int) -> dict[str, list[str]]:
    """One repo per (lr, epochs) cell, up to per_method, spanning the range —
    the point is to vary displacement, so spread over hyperparameters rather
    than sampling at random. The published checkpoint is always included."""
    ms = [m.id for m in HfApi().list_models(
        author="open-unlearning", search="Llama-3.2-1B-Instruct_forget10", limit=1000)]
    out = {}
    for meth in METHODS:
        mine = [m for m in ms if f"forget10_{meth}_" in m]
        cells = {}
        for m in mine:
            lr = re.search(r"lr([0-9.e-]+?)_", m + "_")
            ep = re.search(r"(?:epoch|ep)(\d+)", m)
            key = (lr.group(1) if lr else "?", ep.group(1) if ep else "?")
            cells.setdefault(key, []).append(m)
        chosen = [sorted(v)[0] for _, v in sorted(cells.items())][:per_method]
        published = CHECKPOINTS[meth]
        if published not in chosen:
            chosen = [published] + chosen[:per_method - 1]
        out[meth] = chosen
    return out


def main(n, per_method):
    os.makedirs(OUT, exist_ok=True)
    csv = os.path.join(OUT, "variants.csv")
    done = pd.read_csv(csv) if os.path.exists(csv) else pd.DataFrame(columns=["repo"])
    seen = set(done.repo) if len(done) else set()

    idx = [r["tofu_index"] for r in sample_split("forget10", 400)][:n]
    rows_p = load_perturbed("forget10_perturbed", idx)
    sample = matched_sample(400)
    qs = {c: [r["question"] for r in v][:n] for c, v in sample.items()}
    # base activations come from the n=400 cache, sliced to the same first n rows
    base = {c: np.load(os.path.join(BASE_ACTS, f"base_{c}.npy"))[LAYER][:n] for c in qs}

    plan = pick_variants(per_method)
    todo = [(m, r) for m in METHODS for r in plan[m] if r not in seen]
    print(f"{len(todo)} variants to process ({len(seen)} already done)\n")

    for i, (meth, repo) in enumerate(todo, 1):
        if free_gb() < MIN_FREE_GB:
            print(f"stopping: only {free_gb():.1f} GB free")
            break
        print(f"[{i}/{len(todo)}] {meth}: {repo.split('forget10_')[-1]}", flush=True)
        try:
            model, tok, dev = load_model(repo)
        except Exception as e:
            print(f"  load failed: {type(e).__name__}: {str(e)[:90]}")
            drop_from_cache(repo)
            continue
        try:
            acts = {c: all_layer_activations(model, tok, qs[c], dev)[LAYER] for c in qs}
            shift = (acts["forget"] - base["forget"]).mean(0) - (acts["retain"] - base["retain"]).mean(0)
            raw = (acts["forget"] - base["forget"]).mean(0)
            s = summarize_discrimination(score_discrimination(model, tok, dev, rows_p))
            row = {"method": meth, "repo": repo,
                   "lr": (re.search(r"lr([0-9.e-]+?)_", repo + "_") or [None, "?"])[1],
                   "epochs": (re.search(r"(?:epoch|ep)(\d+)", repo) or [None, "?"])[1],
                   "published": repo == CHECKPOINTS[meth],
                   "shift_norm": float(np.linalg.norm(shift)),
                   "raw_norm": float(np.linalg.norm(raw)),
                   "rank1": s["rank1_acc"], "prefers_truth": s["prefers_truth_frac"],
                   "truth_ratio_median": s["truth_ratio_median"], "n": n}
            print(f"  ‖shift‖={row['shift_norm']:.2f}  recognition={row['rank1']:.3f}", flush=True)
            pd.DataFrame([row]).to_csv(csv, mode="a", header=not os.path.exists(csv), index=False)
        finally:
            del model, tok
            free()
            drop_from_cache(repo)

    tab = pd.read_csv(csv)
    if not len(tab):
        print("nothing collected")
        return

    # Does the method still matter once displacement is controlled for?
    x, y = np.log(tab.shift_norm.clip(lower=1e-3)), tab.rank1
    pooled_r = float(np.corrcoef(x, y)[0, 1])
    resid = y - np.poly1d(np.polyfit(x, y, 1))(x)
    per = tab.assign(resid=resid).groupby("method").resid.agg(["mean", "count"])
    print(f"\npooled r(log‖shift‖, recognition) = {pooled_r:.3f} over {len(tab)} checkpoints")
    print("\nmean residual from the pooled trend (positive = keeps more knowledge "
          "than its displacement predicts):")
    print(per.round(3).to_string())

    with open(os.path.join(OUT, "summary.json"), "w") as f:
        json.dump({"layer": LAYER, "n": n, "pooled_r": pooled_r,
                   "residual_by_method": per.reset_index().to_dict(orient="records"),
                   "rows": tab.to_dict(orient="records")}, f, indent=2)
    with open(os.path.join(OUT, "summary.md"), "w") as f:
        f.write(f"# 11 — recognition vs displacement across {len(tab)} checkpoints\n\n"
                f"Pooled r(log‖shift‖, recognition) = {pooled_r:.3f} at layer {LAYER}.\n\n"
                "Mean residual from the pooled trend, by method (positive = retains more "
                "than displacement alone predicts):\n\n" + per.round(3).to_markdown() +
                "\n\n" + tab.sort_values(["method", "shift_norm"])
                .to_markdown(index=False, floatfmt=".3f") + "\n")

    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    colors = plt.cm.tab10(np.linspace(0, 1, len(METHODS)))
    for c, meth in zip(colors, METHODS):
        sub = tab[tab.method == meth].sort_values("shift_norm")
        if not len(sub):
            continue
        style = dict(color=c, marker="o" if meth in POSITIVE_CONTROLS else "s")
        ax.plot(sub.shift_norm, sub.rank1, "-", ms=5, label=meth, **style)
        pub = sub[sub.published]
        if len(pub):
            ax.scatter(pub.shift_norm, pub.rank1, s=160, facecolors="none", edgecolors=c, lw=2)
    xs = np.linspace(tab.shift_norm.min(), tab.shift_norm.max(), 50)
    ax.plot(xs, np.poly1d(np.polyfit(x, y, 1))(np.log(xs)), "k--", lw=1,
            label=f"pooled trend (r={pooled_r:.2f})")
    ax.set_xscale("log")
    ax.set_xlabel("‖forget-specific shift‖ at layer 12  (how far the method moved the model)")
    ax.set_ylabel("recognition: ranks true answer above 5 lures")
    ax.set_title("Is retained knowledge a property of the method, or of displacement?\n"
                 "circled = the published checkpoint used elsewhere in this repo")
    ax.legend(fontsize=7, ncol=2)
    plt.tight_layout(); plt.savefig(os.path.join(OUT, "recognition_vs_displacement.png"), dpi=150)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--per-method", type=int, default=4)
    a = ap.parse_args()
    main(a.n, a.per_method)
