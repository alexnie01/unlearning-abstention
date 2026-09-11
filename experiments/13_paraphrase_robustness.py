"""
Experiment 13 — is the abstention keyed to the fact, or to the phrasing?

IdkNLL abstains on 94% of forget10 questions. TOFU ships a `paraphrased_question`
for every item — same fact, different surface form, never seen in training. If
abstention survives the paraphrase, it generalises over the underlying fact; if
it collapses, the checkpoint memorised which strings to decline and the
"trained abstention" reading weakens considerably.

This matters beyond bookkeeping. The whole project treats IdkNLL as the
reference implementation of learned abstention. A reference that only works on
verbatim training phrasings is a weaker reference, and every comparison drawn
against it inherits that weakness.

The same test applies to recognition: does IdkNLL still rank the true answer
above lures when the question is rephrased? Recognition and abstention can come
apart under paraphrase in either direction, which is informative on its own.

Usage:  uv run python experiments/13_paraphrase_robustness.py [--n 150]
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
from datasets import load_dataset

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import BASE_MODEL, CHECKPOINTS, METHODS_UNDER_TEST, POSITIVE_CONTROLS
from src.data import sample_split
from src.judge import (EPISTEMIC_RUBRIC, IdkMatcher, JUDGE_WORKERS, ensure_ollama_running,
                       is_degenerate, judge_one)
from src.knowledge import score_discrimination, summarize_discrimination
from src.model_loader import free, load_model
from src.judge import generate_response
from src.stats import result_dir, wilson_ci

transformers.logging.set_verbosity_error()
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = result_dir("13_paraphrase_robustness")
MODELS = {"base": BASE_MODEL, **{m: CHECKPOINTS[m] for m in POSITIVE_CONTROLS + METHODS_UNDER_TEST}}
IDK = IdkMatcher()


def main(n, models):
    os.makedirs(OUT, exist_ok=True)
    idx = [r["tofu_index"] for r in sample_split("forget10", 400)][:n]
    ds = load_dataset("locuslab/TOFU", "forget10_perturbed")["train"]
    rows = [{"orig": ds[i]["question"], "para": ds[i]["paraphrased_question"],
             "true": ds[i]["paraphrased_answer"], "perturbed": list(ds[i]["perturbed_answer"])}
            for i in idx]

    gen_path = os.path.join(OUT, "generations.csv")
    if os.path.exists(gen_path):
        gen = pd.read_csv(gen_path)
    else:
        out = []
        for label in models:
            model, tok, dev = load_model(MODELS[label])
            for form in ("orig", "para"):
                for r in rows:
                    q = r[form]
                    out.append({"model": label, "form": form, "prompt": q,
                                "response": generate_response(model, tok, q, dev,
                                                              max_new_tokens=120)})
                print(f"{label}/{form}: generated", flush=True)
            # recognition under each phrasing, same candidate answers
            for form in ("orig", "para"):
                pr = [{"question": r[form], "true": r["true"], "perturbed": r["perturbed"]}
                      for r in rows]
                s = summarize_discrimination(score_discrimination(model, tok, dev, pr))
                out.append({"model": label, "form": form, "prompt": "__RECOGNITION__",
                            "response": "", "rank1": s["rank1_acc"]})
                print(f"{label}/{form}: recognition {s['rank1_acc']:.3f}", flush=True)
            del model, tok
            free()
        gen = pd.DataFrame(out)
        gen.to_csv(gen_path, index=False)

    lab_path = os.path.join(OUT, "generations_labeled.csv")
    if os.path.exists(lab_path):
        gen = pd.read_csv(lab_path)
    else:
        ensure_ollama_running()
        g = gen[gen.prompt != "__RECOGNITION__"].copy()
        g["degenerate"] = g.response.map(is_degenerate)
        judged = g[~g.degenerate]
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(JUDGE_WORKERS) as ex:
            lab = list(ex.map(lambda r: judge_one(r.prompt, r.response, "llama3.2",
                                                  EPISTEMIC_RUBRIC), judged.itertuples()))
        g["abstain"] = False
        g.loc[judged.index, "abstain"] = lab
        g["abstain"] = g.abstain & ~g.degenerate
        g["abstain_regex"] = g.response.map(lambda s: bool(IDK(s)))
        gen = pd.concat([g, gen[gen.prompt == "__RECOGNITION__"]], ignore_index=True)
        gen.to_csv(lab_path, index=False)

    beh = gen[gen.prompt != "__RECOGNITION__"]
    rec = gen[gen.prompt == "__RECOGNITION__"]
    tab = beh.groupby(["model", "form"]).agg(n=("abstain", "size"),
                                             abstain=("abstain", "mean"),
                                             degenerate=("degenerate", "mean")).reset_index()
    piv = tab.pivot(index="model", columns="form", values="abstain")
    piv["delta"] = piv["para"] - piv["orig"]
    if len(rec):
        rp = rec.pivot_table(index="model", columns="form", values="rank1")
        piv["rec_orig"], piv["rec_para"] = rp["orig"], rp["para"]
    order = [m for m in MODELS if m in piv.index]
    piv = piv.loc[order]
    print("\nabstention under original vs paraphrased questions:")
    print(piv.round(3).to_string())

    key = [m for m in POSITIVE_CONTROLS if m in piv.index]
    worst = min((piv.loc[m, "para"] / piv.loc[m, "orig"] if piv.loc[m, "orig"] > 0 else np.nan)
                for m in key) if key else float("nan")
    verdict = (f"Abstention survives paraphrase (worst positive control retains "
               f"{worst:.0%} of its rate), so it tracks the fact rather than the phrasing."
               if worst > 0.7 else
               f"Abstention is phrasing-sensitive: the worst positive control keeps only "
               f"{worst:.0%} of its rate under paraphrase, so the reference implementation of "
               f"learned abstention is partly a memorised surface pattern.")
    print("\n=>", verdict)

    with open(os.path.join(OUT, "summary.json"), "w") as f:
        json.dump({"n": n, "verdict": verdict,
                   "table": piv.reset_index().to_dict(orient="records")}, f, indent=2)
    with open(os.path.join(OUT, "summary.md"), "w") as f:
        f.write("# 13 — does abstention survive rephrasing the question?\n\n"
                + piv.round(3).to_markdown() + f"\n\n**{verdict}**\n")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = np.arange(len(piv)); w = 0.38
    ax.bar(x - w/2, piv["orig"], w, label="original question", color="tab:blue", edgecolor="k", lw=0.5)
    ax.bar(x + w/2, piv["para"], w, label="paraphrased question", color="tab:cyan", edgecolor="k", lw=0.5)
    ax.set_xticks(x); ax.set_xticklabels(piv.index, rotation=20)
    ax.set_ylabel("judged abstention rate on forget10")
    ax.set_title("Is abstention keyed to the fact or to the phrasing?")
    ax.legend(fontsize=8)
    plt.tight_layout(); plt.savefig(os.path.join(OUT, "paraphrase_robustness.png"), dpi=150)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=150)
    ap.add_argument("--models", nargs="+", default=["base", "IdkNLL", "IdkDPO", "NPO", "RMU"])
    a = ap.parse_args()
    main(a.n, a.models)
