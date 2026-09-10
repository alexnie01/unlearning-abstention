"""
Experiment 09 — recall: do the generated answers state the true fact?

06 measures RECOGNITION (does the model rank the true answer above five
surface-matched lures) and 01 measures ABSTENTION. Neither says whether the
model actually produces the fact, and the two come apart: NPO ranks the truth
at base level yet greedily generates a confabulation. This judges the
generations already saved by 01 against the gold answer.

Three axes then describe every checkpoint:
    recall      (here)  says the true fact when asked
    recognition (06)    ranks the true answer above lures
    abstention  (01)    declines instead of answering

TOFU's forget-set authors are synthetic, so the gold answer is the only ground
truth; a fluent wrong biography must count as NOT recalled, which the rubric
states explicitly (the exploratory phase's token-overlap metric failed exactly
here).

Usage:  uv run python experiments/09_recall_audit.py
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import METHODS_UNDER_TEST, POSITIVE_CONTROLS
from src.judge import CORRECTNESS_RUBRIC, ensure_ollama_running, is_degenerate, judge_one
from src.stats import result_dir, wilson_ci

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = result_dir("09_recall_audit")
B01 = result_dir("01_idk_behavior")
ORDER = ["base"] + POSITIVE_CONTROLS + METHODS_UNDER_TEST
JUDGE = "llama3.2"


def main():
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "recall.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
    else:
        ensure_ollama_running()
        rows = []
        for label in ORDER:
            p = os.path.join(B01, f"responses_{label}_labeled.csv")
            if not os.path.exists(p):
                print(f"[skip] {label}: no labeled responses")
                continue
            d = pd.read_csv(p)
            d = d[d.cls == "forget"]
            for r in tqdm(d.itertuples(), total=len(d), desc=f"recall [{label}]"):
                rows.append({"model": label, "prompt": r.prompt, "response": r.response,
                             "gold": r.gold, "abstained": bool(r.ignorant_majority),
                             "correct": judge_one(r.prompt, r.response, JUDGE,
                                                  CORRECTNESS_RUBRIC, gold=r.gold)})
            print(f"{label}: done", flush=True)
        df = pd.DataFrame(rows)
        df.to_csv(path, index=False)

    df["degenerate"] = df["response"].map(is_degenerate)
    df["abstained"] = df["abstained"] & ~df["degenerate"]      # gibberish is not abstention
    g = df.groupby("model").agg(n=("correct", "size"), recall=("correct", "mean"),
                                abstain=("abstained", "mean"),
                                degenerate=("degenerate", "mean")).reindex(
        [m for m in ORDER if m in set(df.model)])
    # A model that abstains cannot also recall; report recall among ATTEMPTS too.
    attempts = df[~df.abstained & ~df.degenerate]
    g["recall_when_attempted"] = attempts.groupby("model").correct.mean()
    ci = {m: wilson_ci(int(df[df.model == m].correct.sum()), int((df.model == m).sum()))
          for m in g.index}
    g["recall_lo"] = [ci[m][0] for m in g.index]
    g["recall_hi"] = [ci[m][1] for m in g.index]
    k06 = {}
    p06 = os.path.join(result_dir("06_knowledge_probe"), "summary.json")
    if os.path.exists(p06):
        with open(p06) as f:
            k06 = {r["model"]: r["rank1_acc"] for r in json.load(f)["table"] if r["set"] == "forget"}
    g["recognition"] = [k06.get(m, float("nan")) for m in g.index]
    print("\n" + g.round(3).to_string())

    g.reset_index().to_csv(os.path.join(OUT, "summary.csv"), index=False)
    with open(os.path.join(OUT, "summary.md"), "w") as f:
        f.write("# 09 — recall vs recognition vs abstention on forget10\n\n"
                "recall: judged to state the gold fact. recognition: 06's rank1. "
                "abstention: 01's judged rate.\n\n")
        f.write(g.round(3).to_markdown() + "\n")
    with open(os.path.join(OUT, "summary.json"), "w") as f:
        json.dump(g.reset_index().to_dict(orient="records"), f, indent=2)

    fig, ax = plt.subplots(figsize=(8, 5))
    for m in g.index:
        c = "k" if m == "base" else "tab:blue" if m in POSITIVE_CONTROLS else "tab:red"
        ax.scatter(g.loc[m, "recognition"], g.loc[m, "recall"], s=90, color=c,
                   marker="*" if m == "base" else "o", zorder=3)
        ax.annotate(f"{m} (abst {g.loc[m, 'abstain']:.0%})",
                    (g.loc[m, "recognition"], g.loc[m, "recall"]),
                    textcoords="offset points", xytext=(7, 4), fontsize=8)
    ax.set_xlabel("recognition: ranks true answer above 5 lures (06)")
    ax.set_ylabel("recall: generation states the gold fact (09)")
    ax.set_title("Recognition and recall come apart\nhigh recognition + low recall = knows in the weak sense, does not say it")
    ax.set_xlim(0, 0.8); ax.set_ylim(-0.03, 1.0)
    plt.tight_layout(); plt.savefig(os.path.join(OUT, "recall_vs_recognition.png"), dpi=150)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
