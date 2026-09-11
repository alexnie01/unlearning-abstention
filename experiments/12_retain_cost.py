"""
Experiment 12 — what did each method cost on the retain set?

Every claim so far is about forget10, but unlearning is only interesting if it
spares everything else. A method that "forgets" by degrading the model
generally has not unlearned anything, and the two methods that destroyed
forget-set recognition (AltPO 0.32, RMU 0.20 against an ignorance floor of
0.43) are exactly the ones where that alternative explanation is live.

Retain recognition is already known to be intact for every checkpoint
(0.71-0.78, experiment 06), so what is missing is the behavioural half:

    recall      does the model still state retain-set facts it was never asked
                to forget?
    degeneracy  does it still produce coherent text on them?

Read against the base model, which is the ceiling, and the retain90 oracle,
which was trained on the retain set and never touched forget10 — the closest
thing to "unlearning with no collateral damage".

Reuses 01's saved retain-set generations, so this is a judging pass only.

Usage:  uv run python experiments/12_retain_cost.py
"""
import json
import math
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import METHODS_UNDER_TEST, POSITIVE_CONTROLS
from src.judge import (CORRECTNESS_RUBRIC, JUDGE_WORKERS, ensure_ollama_running, is_degenerate,
                       judge_one)
from src.stats import result_dir, wilson_ci

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = result_dir("12_retain_cost")
B01 = result_dir("01_idk_behavior")
ORDER = ["base"] + POSITIVE_CONTROLS + METHODS_UNDER_TEST
JUDGE = "llama3.2"


def main(cap):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "retain_recall.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
    else:
        ensure_ollama_running()
        rows = []
        for label in ORDER:
            p = os.path.join(B01, f"responses_{label}_labeled.csv")
            if not os.path.exists(p):
                print(f"[skip] {label}")
                continue
            d = pd.read_csv(p)
            d = d[d.cls == "retain"]
            if cap and len(d) > cap:
                d = d.sample(cap, random_state=0)
            recs = list(d.itertuples())
            with ThreadPoolExecutor(JUDGE_WORKERS) as ex:
                ok = list(tqdm(ex.map(lambda r: judge_one(r.prompt, r.response, JUDGE,
                                                          CORRECTNESS_RUBRIC, gold=r.gold), recs),
                               total=len(recs), desc=f"retain recall [{label}]"))
            rows += [{"model": label, "prompt": r.prompt, "response": r.response,
                      "correct": c} for r, c in zip(recs, ok)]
            print(f"{label}: done", flush=True)
        df = pd.DataFrame(rows)
        df.to_csv(path, index=False)

    df["degenerate"] = df["response"].map(is_degenerate)
    g = df.groupby("model").agg(n=("correct", "size"), retain_recall=("correct", "mean"),
                                degenerate=("degenerate", "mean")).reindex(
        [m for m in ORDER if m in set(df.model)])
    ci = {m: wilson_ci(int(df[df.model == m].correct.sum()), int((df.model == m).sum()))
          for m in g.index}
    g["lo"] = [ci[m][0] for m in g.index]
    g["hi"] = [ci[m][1] for m in g.index]

    # forget-set recall from 09, for the side-by-side that matters
    p09 = os.path.join(result_dir("09_recall_audit"), "summary.csv")
    if os.path.exists(p09):
        f9 = pd.read_csv(p09).set_index("model")
        g["forget_recall"] = [float(f9.loc[m, "recall"]) if m in f9.index else float("nan")
                              for m in g.index]
        g["selectivity"] = g["retain_recall"] - g["forget_recall"]
    print("\n" + g.round(3).to_string())

    # Two-proportion z-test against base. Comparing a model's CI to base's point
    # estimate ignores base's own uncertainty and overstates significance; at
    # n=100 per model the honest bar is higher than it looks.
    base = float(g.loc["base", "retain_recall"]) if "base" in g.index else float("nan")
    nb = int(g.loc["base", "n"])
    zs = {}
    for m in g.index:
        if m == "base":
            continue
        p, nm = float(g.loc[m, "retain_recall"]), int(g.loc[m, "n"])
        se = math.sqrt(base * (1 - base) / nb + p * (1 - p) / nm)
        zs[m] = (base - p) / se if se > 0 else float("nan")
    g["z_vs_base"] = [zs.get(m, float("nan")) for m in g.index]
    # Bonferroni over the checkpoints compared: |z| > 2.9 for ~7 tests at 0.05
    strong = [m for m, z in zs.items() if z > 2.9]
    weak = [m for m, z in zs.items() if 1.96 < z <= 2.9]
    verdict = (
        (f"Retain recall is decisively below base ({base:.2f}) for: "
         + ", ".join(f"{m} ({g.loc[m, 'retain_recall']:.2f}, z={zs[m]:.1f})" for m in strong)
         if strong else f"No checkpoint is decisively below base ({base:.2f})")
        + (". Suggestive but not surviving correction for multiple comparisons: "
           + ", ".join(f"{m} ({g.loc[m, 'retain_recall']:.2f}, z={zs[m]:.1f})" for m in weak)
           if weak else ". No borderline cases."))
    print("\n=>", verdict)

    g.reset_index().to_csv(os.path.join(OUT, "summary.csv"), index=False)
    with open(os.path.join(OUT, "summary.json"), "w") as f:
        json.dump({"verdict": verdict, "rows": g.reset_index().to_dict(orient="records")}, f, indent=2)
    with open(os.path.join(OUT, "summary.md"), "w") as f:
        f.write("# 12 — retain-set cost\n\nDid the methods damage what they were meant to keep?\n\n")
        f.write(g.round(3).to_markdown() + f"\n\n**{verdict}**\n")

    fig, ax = plt.subplots(figsize=(8, 5))
    for m in g.index:
        c = "k" if m == "base" else "tab:blue" if m in POSITIVE_CONTROLS else "tab:red"
        ax.scatter(g.loc[m, "forget_recall"], g.loc[m, "retain_recall"], s=90, color=c,
                   marker="*" if m == "base" else "o", zorder=3)
        ax.annotate(m, (g.loc[m, "forget_recall"], g.loc[m, "retain_recall"]),
                    textcoords="offset points", xytext=(7, 4), fontsize=8)
    if "base" in g.index:
        ax.axhline(base, color="grey", ls=":", lw=1)
    lim = max(g.retain_recall.max(), g.forget_recall.max()) * 1.15 + 0.02
    ax.plot([0, lim], [0, lim], color="lightgrey", lw=0.8, zorder=0)
    ax.set_xlabel("forget-set recall (should be low)")
    ax.set_ylabel("retain-set recall (should stay at base)")
    ax.set_title("Selective forgetting sits top-left; general damage sits on the diagonal")
    plt.tight_layout(); plt.savefig(os.path.join(OUT, "retain_vs_forget.png"), dpi=150)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--cap", type=int, default=200, help="retain rows per model")
    main(ap.parse_args().cap)
