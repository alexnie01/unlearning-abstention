"""
Experiment 06 (PLAN2 B1/B2) — does the model still KNOW, whatever it says?

For every checkpoint, score the true answer against five surface-matched
perturbations of it (TOFU `*_perturbed`), on the same seeded forget10 sample
used everywhere else and on a retain calibration set. Knowledge is read off
without asking the model to produce anything, so a suppressed output channel
and destroyed knowledge come apart:

    high discrimination + high abstention  -> knows but abstains (the hypothesis)
    low  discrimination                    -> knowledge not linearly recoverable
                                              from the answer ranking (destroyed
                                              or deeply reorganised)

Calibration: base must discriminate on forget10 (it was trained on those
facts) and the retain90 oracle must not (it never saw them). If the positive
controls IdkDPO/IdkNLL sit at oracle level, then even TRAINED abstention does
not preserve retrievable knowledge on this setup, and the "still knows"
premise fails for everyone.

Usage:  uv run python experiments/06_knowledge_probe.py [--n 100]
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
from src.config import BASE_MODEL, CHECKPOINTS, METHODS_UNDER_TEST, POSITIVE_CONTROLS, RETAIN
from src.data import sample_split
from src.knowledge import load_perturbed, score_discrimination, summarize_discrimination
from src.model_loader import free, load_model

transformers.logging.set_verbosity_error()
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "results", "06_knowledge_probe")
MODELS = {"base": BASE_MODEL, "oracle": RETAIN, **CHECKPOINTS}
ORDER = ["base", "oracle"] + POSITIVE_CONTROLS + METHODS_UNDER_TEST


def main(n):
    os.makedirs(OUT, exist_ok=True)
    # Same seeded rows as every other experiment (forget10_perturbed is row-aligned
    # with forget10), so 01's abstention labels join to these by position.
    idx = [r["tofu_index"] for r in sample_split("forget10", n)]
    sets = {"forget": load_perturbed("forget10_perturbed", idx),
            "retain": load_perturbed("retain_perturbed", list(range(n)))}

    rows, per_q = [], []
    for label in ORDER:
        model, tok, dev = load_model(MODELS[label])
        for set_name, data in sets.items():
            res = score_discrimination(model, tok, dev, data)
            s = summarize_discrimination(res)
            rows.append({"model": label, "set": set_name, **s})
            for i, r in enumerate(data):
                per_q.append({"model": label, "set": set_name, "question": r["question"],
                              "true_lp": float(res["true_lp"][i]),
                              "truth_ratio": float(res["truth_ratio"][i]),
                              "rank1": bool(res["rank1"][i])})
            print(f"{label:9} {set_name:7} rank1={s['rank1_acc']:.2f} "
                  f"prefers_truth={s['prefers_truth_frac']:.2f} "
                  f"R_median={s['truth_ratio_median']:.2f} margin={s['margin_mean']:+.2f}",
                  flush=True)
        del model, tok
        free()

    tab = pd.DataFrame(rows)
    tab.to_csv(os.path.join(OUT, "discrimination.csv"), index=False)
    pd.DataFrame(per_q).to_csv(os.path.join(OUT, "per_question.csv"), index=False)

    # B2: the 2x2 — discrimination against judged abstention from 01.
    fg = tab[tab.set == "forget"].set_index("model")
    abst = {}
    for label in ORDER:
        p = os.path.join(ROOT, "results", "01_idk_behavior", f"responses_{label}_labeled.csv")
        if os.path.exists(p):
            df = pd.read_csv(p)
            abst[label] = float(df[df.cls == "forget"].ignorant_majority.mean())
    base_r1, oracle_r1 = fg.loc["base", "rank1_acc"], fg.loc["oracle", "rank1_acc"]
    calib = base_r1 > 0.8 and oracle_r1 < base_r1 - 0.2
    span = base_r1 - oracle_r1
    print(f"\ncalibration: base rank1={base_r1:.2f}, oracle rank1={oracle_r1:.2f} "
          f"-> {'OK' if calib else 'FAILED (probe uninformative)'}")
    print("\nmodel      rank1  retained_frac  abstain  cell")
    cells = {}
    for label in ORDER:
        if label in ("base", "oracle"):
            continue
        r1 = fg.loc[label, "rank1_acc"]
        retained = (r1 - oracle_r1) / span if span > 0 else float("nan")
        a = abst.get(label, float("nan"))
        cell = ("knows & abstains" if retained > 0.5 and a > 0.3 else
                "knows & answers" if retained > 0.5 else
                "not retrievable & abstains" if a > 0.3 else "not retrievable")
        cells[label] = {"rank1": float(r1), "retained_frac": float(retained),
                        "abstain": a, "cell": cell}
        print(f"{label:9} {r1:.2f}   {retained:+.2f}        {a:.2f}    {cell}")

    verdict = ("Positive controls retain knowledge: trained abstention preserves it, so "
               "the premise holds and each method's cell is interpretable."
               if all(cells[m]["retained_frac"] > 0.5 for m in POSITIVE_CONTROLS) else
               "Positive controls do NOT retain retrievable knowledge: even trained "
               "abstention destroys answer discrimination here, so 'knows but abstains' "
               "is not realised by any checkpoint on this setup.")
    print("\n=>", verdict)

    with open(os.path.join(OUT, "summary.json"), "w") as f:
        json.dump({"n": n, "calibrated": bool(calib), "base_rank1": float(base_r1),
                   "oracle_rank1": float(oracle_r1), "cells": cells,
                   "verdict": verdict, "table": rows}, f, indent=2)
    with open(os.path.join(OUT, "summary.md"), "w") as f:
        f.write("# 06 — does the model still know? (true vs surface-matched perturbations)\n\n")
        f.write(f"Calibration: base rank1 {base_r1:.2f}, retain oracle {oracle_r1:.2f}.\n\n")
        f.write(tab.to_markdown(index=False, floatfmt=".3f") + "\n\n## 2x2\n\n")
        f.write(pd.DataFrame(cells).T.to_markdown(floatfmt=".2f") + "\n\n")
        f.write(f"**Verdict:** {verdict}\n")

    fig, ax = plt.subplots(figsize=(7, 5.5))
    for label in ORDER:
        if label not in cells and label not in ("base", "oracle"):
            continue
        r1 = fg.loc[label, "rank1_acc"]
        a = abst.get(label, 0.0)
        c = "k" if label in ("base", "oracle") else \
            "tab:blue" if label in POSITIVE_CONTROLS else "tab:red"
        ax.scatter(r1, a, s=90, color=c, zorder=3,
                   marker="*" if label in ("base", "oracle") else "o")
        ax.annotate(label, (r1, a), textcoords="offset points", xytext=(7, 4), fontsize=8)
    ax.axvline(oracle_r1, color="grey", ls=":", lw=1)
    ax.axvline(base_r1, color="grey", ls=":", lw=1)
    ax.axhline(0.3, color="grey", ls="--", lw=0.8)
    ax.set_xlabel("answer discrimination on forget10 (true beats all 5 perturbations)")
    ax.set_ylabel("judged abstention rate on forget10")
    ax.set_title("Knows-but-abstains would sit top-right\n(dotted: oracle and base discrimination)")
    ax.set_xlim(-0.03, 1.03); ax.set_ylim(-0.05, 1.05)
    plt.tight_layout(); plt.savefig(os.path.join(OUT, "knowledge_vs_abstention.png"), dpi=150)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100)
    main(ap.parse_args().n)
