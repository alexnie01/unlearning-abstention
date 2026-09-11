"""
Experiment 14 — do the high-recognition Idk variants actually abstain?

Experiment 11 measures recognition against displacement but not behaviour, and
for the Idk checkpoints that leaves the key claim ambiguous. An IdkNLL variant
with base-level recognition is only interesting if it ALSO abstains: if it
does, abstention and intact knowledge coexist at that hyperparameter setting
(the claim); if it does not, the variant simply failed to learn the behaviour
and its retained knowledge means nothing.

This fills in the behavioural axis for the Idk variants in 11's table. The
methods under test need no such follow-up — their abstention is 0 at every
setting tested (experiment 01, n=400).

Abstention is measured with the phrase matcher built from open-unlearning's 99
IDK training strings rather than the LLM judge: on natural text the two agree
0.96-1.00, and on the Idk checkpoints specifically the matcher put IdkNLL at
0.97 against the judge's 0.94, which is well inside what this question needs.

Usage:  uv run python experiments/14_idk_variant_behavior.py [--n 200]
"""
import argparse
import json
import os
import shutil
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import transformers

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import POSITIVE_CONTROLS
from src.data import matched_sample
from src.judge import IdkMatcher, generate_response, is_degenerate
from src.model_loader import free, load_model
from src.stats import wilson_ci

transformers.logging.set_verbosity_error()
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "results", "14_idk_variant_behavior")
V11 = os.path.join(ROOT, "results", "11_magnitude_matched", "variants.csv")
HUB_CACHE = os.path.expanduser("~/.cache/huggingface/hub")
IDK = IdkMatcher()


def drop_from_cache(repo_id: str):
    d = os.path.join(HUB_CACHE, "models--" + repo_id.replace("/", "--"))
    if os.path.isdir(d):
        shutil.rmtree(d, ignore_errors=True)


def main(n):
    os.makedirs(OUT, exist_ok=True)
    v11 = pd.read_csv(V11)
    targets = v11[v11.method.isin(POSITIVE_CONTROLS)]
    csv = os.path.join(OUT, "behavior.csv")
    done = set(pd.read_csv(csv).repo) if os.path.exists(csv) else set()

    qs = [r["question"] for r in matched_sample(400)["forget"]][:n]
    todo = [r for r in targets.itertuples() if r.repo not in done]
    print(f"{len(todo)} Idk variants to measure ({len(done)} done)\n")

    for i, r in enumerate(todo, 1):
        print(f"[{i}/{len(todo)}] {r.method}: {r.repo.split('forget10_')[-1]}", flush=True)
        try:
            model, tok, dev = load_model(r.repo)
        except Exception as e:
            print(f"  load failed: {type(e).__name__}")
            drop_from_cache(r.repo)
            continue
        try:
            resp = [generate_response(model, tok, q, dev, max_new_tokens=100) for q in qs]
            deg = np.array([is_degenerate(x) for x in resp])
            idk = np.array([bool(IDK(x)) for x in resp]) & ~deg
            lo, hi = wilson_ci(int(idk.sum()), len(idk))
            row = {"method": r.method, "repo": r.repo, "published": bool(r.published),
                   "shift_norm": float(r.shift_norm), "rank1": float(r.rank1),
                   "abstain": float(idk.mean()), "abstain_lo": lo, "abstain_hi": hi,
                   "degenerate": float(deg.mean()), "n": len(idk)}
            print(f"  abstain={row['abstain']:.3f} [{lo:.2f}, {hi:.2f}]  "
                  f"recognition={row['rank1']:.3f}  ‖shift‖={row['shift_norm']:.2f}", flush=True)
            pd.DataFrame([row]).to_csv(csv, mode="a", header=not os.path.exists(csv), index=False)
        finally:
            del model, tok
            free()
            drop_from_cache(r.repo)

    tab = pd.read_csv(csv)
    # The claim needs at least one variant in the top-right: abstains AND keeps
    # recognition near base. 0.43 is the oracle floor, 0.73 the base ceiling.
    both = tab[(tab.abstain > 0.3) & (tab.rank1 > 0.58)]
    verdict = (f"{len(both)} of {len(tab)} Idk variants combine abstention >0.3 with "
               f"recognition >0.58 (midway between the 0.43 ignorance floor and base's "
               f"0.73): " + ", ".join(f"{r.method}@‖{r.shift_norm:.1f}‖" for r in both.itertuples())
               if len(both) else
               "No Idk variant combines abstention with near-base recognition; the "
               "knows-and-abstains cell is occupied only by the published IdkNLL checkpoint.")
    print("\n" + tab[["method", "shift_norm", "rank1", "abstain", "published"]]
          .round(3).to_string(index=False))
    print("\n=>", verdict)

    with open(os.path.join(OUT, "summary.json"), "w") as f:
        json.dump({"n": n, "verdict": verdict, "rows": tab.to_dict(orient="records")}, f, indent=2)
    with open(os.path.join(OUT, "summary.md"), "w") as f:
        f.write("# 14 — do the high-recognition Idk variants abstain?\n\n"
                + tab.round(3).to_markdown(index=False) + f"\n\n**{verdict}**\n")

    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    for meth, c in zip(POSITIVE_CONTROLS, ["tab:blue", "tab:cyan"]):
        sub = tab[tab.method == meth]
        ax.scatter(sub.rank1, sub.abstain, s=90, color=c, label=meth, zorder=3)
        pub = sub[sub.published]
        ax.scatter(pub.rank1, pub.abstain, s=200, facecolors="none", edgecolors=c, lw=2)
        for r in sub.itertuples():
            ax.annotate(f"‖{r.shift_norm:.1f}‖", (r.rank1, r.abstain),
                        textcoords="offset points", xytext=(6, 4), fontsize=7)
    ax.axvline(0.43, color="grey", ls=":", lw=1)
    ax.axvline(0.73, color="grey", ls=":", lw=1)
    ax.axhline(0.3, color="grey", ls="--", lw=0.8)
    ax.set_xlabel("recognition (dotted: oracle floor 0.43, base 0.73)")
    ax.set_ylabel("abstention rate on forget10")
    ax.set_title("Knows-and-abstains is the top-right quadrant\ncircled = published checkpoint; labels = displacement")
    ax.legend(fontsize=8)
    plt.tight_layout(); plt.savefig(os.path.join(OUT, "abstain_vs_recognition.png"), dpi=150)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200)
    main(ap.parse_args().n)
