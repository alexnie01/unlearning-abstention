"""
Experiment 17 — presentation figures for the write-up.

Regenerates the four figures worth showing a reader, at larger fonts and
without the overlapping labels that make the in-repo versions hard to read on
a page. Writes to summary/figures/ (gitignored drafting workspace).

Usage:  uv run python experiments/17_summary_figures.py
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
from src.config import METHODS_UNDER_TEST, POSITIVE_CONTROLS

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "summary", "figures")
plt.rcParams.update({"font.size": 12, "axes.titlesize": 13, "axes.labelsize": 12,
                     "figure.dpi": 160, "savefig.bbox": "tight"})
BLUE, RED, GREY = "#1f77b4", "#d62728", "#7f7f7f"


def load(p):
    with open(os.path.join(ROOT, "results", p)) as f:
        return json.load(f)


def fig1_knows_vs_abstains():
    """The headline: only a checkpoint trained to abstain sits top-right."""
    s6 = load("06_knowledge_probe_n400/summary.json")
    rec = {r["model"]: r["rank1_acc"] for r in s6["table"] if r["set"] == "forget"}
    ab = {m: v["abstain"] for m, v in s6["cells"].items()}
    ab["base"], ab["oracle"] = 0.01, 0.0
    fig, ax = plt.subplots(figsize=(7.5, 5.4))
    ax.axvspan(rec["oracle"], 0.8, color=BLUE, alpha=0.04)
    ax.axhspan(0.3, 1.05, color=BLUE, alpha=0.04)
    for m in ["base", "oracle"] + POSITIVE_CONTROLS + METHODS_UNDER_TEST:
        if m not in rec:
            continue
        x, y = rec[m], ab.get(m, 0)
        c = "k" if m in ("base", "oracle") else (BLUE if m in POSITIVE_CONTROLS else RED)
        ax.scatter(x, y, s=150, color=c, zorder=5,
                   marker="*" if m in ("base", "oracle") else "o",
                   edgecolors="white", linewidths=1.2)
        dx, dy = (9, 6)
        if m == "GradDiff":
            dx, dy = (-30, 16)
        if m == "NPO":
            dx, dy = (-18, -22)
        if m == "base":
            dx, dy = (10, 2)
        if m == "SimNPO":
            dx, dy = (-20, 14)
        if m == "oracle":
            dx, dy = (-14, 12)
        ax.annotate(m, (x, y), textcoords="offset points", xytext=(dx, dy), fontsize=11)
    ax.axvline(rec["oracle"], color=GREY, ls=":", lw=1.2)
    ax.text(rec["oracle"] - 0.012, 1.0, "never-trained oracle\n(what ignorance looks like)",
            ha="right", va="top", fontsize=9, color=GREY)
    ax.text(0.775, 0.52, "knows the answer\nand declines", ha="right", fontsize=10,
            color=BLUE, style="italic")
    ax.set_xlabel("still recognises the true answer  →")
    ax.set_ylabel("says “I don't know”  →")
    ax.set_title("Only models trained to abstain actually abstain\n"
                 "(400 forget-set questions, Llama-3.2-1B)")
    ax.set_xlim(0.08, 0.82); ax.set_ylim(-0.06, 1.06)
    fig.savefig(os.path.join(OUT, "fig1_knows_vs_abstains.png"))
    plt.close(fig)


def fig2_displacement():
    """The confound check: curves separate at matched displacement."""
    t = pd.read_csv(os.path.join(ROOT, "results", "11_magnitude_matched", "variants.csv"))
    fig, ax = plt.subplots(figsize=(8, 5.4))
    style = {"IdkNLL": (BLUE, "o", "-"), "IdkDPO": ("#17becf", "o", "-"),
             "NPO": (RED, "s", "--"), "GradDiff": ("#ff7f0e", "s", "--"),
             "SimNPO": ("#8c564b", "s", "--"), "AltPO": ("#e377c2", "s", "--"),
             "RMU": ("#9467bd", "s", "--")}
    for m, (c, mk, ls) in style.items():
        sub = t[t.method == m].sort_values("shift_norm")
        if not len(sub):
            continue
        ax.plot(sub.shift_norm, sub.rank1, ls, marker=mk, ms=6, color=c, label=m, lw=1.8)
    ax.axhline(0.43, color=GREY, ls=":", lw=1.2)
    ax.text(0.12, 0.445, "ignorance floor", fontsize=9, color=GREY)
    ax.set_xscale("log")
    ax.set_xlabel("how far the method moved the model  (log scale)")
    ax.set_ylabel("still recognises the true answer")
    ax.set_title("Knowledge loss is not just “how hard you hit it”\n"
                 "28 checkpoints, 4 hyperparameter settings per method")
    ax.legend(fontsize=9, ncol=2, loc="lower left")
    fig.savefig(os.path.join(OUT, "fig2_displacement.png"))
    plt.close(fig)


def fig3_steering():
    """The causal result, with the matched-norm control beside it."""
    g = pd.read_csv(os.path.join(ROOT, "results", "07_steering_audit", "rates.csv"))
    b = g[g.model == "base"]
    cells = [("unsteered", b[(b.direction == "epistemic") & (b.mult == 0)]),
             ("+2× abstention\ndirection", b[(b.direction == "epistemic") & (b.mult == 2)]),
             ("+4× abstention\ndirection", b[(b.direction == "epistemic") & (b.mult == 4)]),
             ("+4× control\n(same size, other direction)", b[(b.direction == "content") & (b.mult == 4)])]
    labels = [c[0] for c in cells]
    ab = [float(c[1].abstain.iloc[0]) if len(c[1]) else 0 for c in cells]
    dg = [float(c[1].degenerate.iloc[0]) if len(c[1]) else 0 for c in cells]
    x = np.arange(len(labels)); w = 0.38
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(x - w / 2, ab, w, label="says “I don't know”", color=BLUE, edgecolor="k", lw=0.6)
    ax.bar(x + w / 2, dg, w, label="output is gibberish", color=GREY, edgecolor="k", lw=0.6)
    for i, (a, d) in enumerate(zip(ab, dg)):
        ax.text(i - w / 2, a + 0.02, f"{a:.0%}", ha="center", fontsize=10)
        ax.text(i + w / 2, d + 0.02, f"{d:.0%}", ha="center", fontsize=10)
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel("fraction of 50 forget-set questions")
    ax.set_ylim(0, 1.05)
    ax.set_title("A direction taken from abstaining models makes a knowing model decline\n"
                 "(the same-size control just breaks it instead)")
    ax.legend(fontsize=10)
    fig.savefig(os.path.join(OUT, "fig3_steering.png"))
    plt.close(fig)


def fig4_recognise_vs_say():
    """Recognition and production come apart; NPO is the case in point."""
    s9 = pd.read_csv(os.path.join(ROOT, "results", "09_recall_audit_n400", "summary.csv"))
    fig, ax = plt.subplots(figsize=(7.5, 5.2))
    for r in s9.itertuples():
        m = r.model
        c = "k" if m == "base" else (BLUE if m in POSITIVE_CONTROLS else RED)
        ax.scatter(r.recognition, r.recall, s=150, color=c, zorder=5,
                   marker="*" if m == "base" else "o", edgecolors="white", linewidths=1.2)
        dx, dy = (9, 6)
        if m in ("IdkNLL",):
            dx, dy = (9, -16)
        if m == "AltPO":
            dx, dy = (-52, 6)
        ax.annotate(m, (r.recognition, r.recall), textcoords="offset points",
                    xytext=(dx, dy), fontsize=11)
    ax.plot([0, 0.8], [0, 0.8], color="lightgrey", lw=1, zorder=0)
    ax.axvline(0.43, color=GREY, ls=":", lw=1.2)
    ax.text(0.435, 0.37, "ignorance floor", fontsize=9, color=GREY, rotation=90, va="top")
    ax.annotate("recognises it,\nwon't say it", xy=(0.69, 0.04), xytext=(0.52, 0.24),
                fontsize=10, color=RED, style="italic",
                arrowprops=dict(arrowstyle="->", color=RED, lw=1.2))
    ax.set_xlabel("recognises the true answer among five lookalikes")
    ax.set_ylabel("actually states the true answer")
    ax.set_title("Recognising and saying come apart\n"
                 "NPO matches the untouched model at recognising, and almost never says it")
    ax.set_xlim(0.1, 0.8); ax.set_ylim(-0.03, 0.5)
    fig.savefig(os.path.join(OUT, "fig4_recognise_vs_say.png"))
    plt.close(fig)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for f in (fig1_knows_vs_abstains, fig2_displacement, fig3_steering, fig4_recognise_vs_say):
        try:
            f()
            print(f"  ok  {f.__name__}")
        except Exception as e:
            print(f"  FAIL {f.__name__}: {type(e).__name__}: {e}")
    print("wrote", OUT)
