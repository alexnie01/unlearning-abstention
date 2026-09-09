"""
Experiment 07 (PLAN2 A3) — audit the steering claim at n=100, not n=3.

04b's headline ("+4x gap at layer 8 makes the base model abstain") rested on
three generations per condition. This generates all 100 forget prompts per
condition and judges them with the same epistemic rubric as 01, so the claim
becomes a rate with a denominator. Conditions per model:

    c = 0, +/-2, +/-4 x gap   along the epistemic direction at layer 8
    c = +/-4 x gap            along the content direction (matched norm control)

Both directions AND both signs matter: the control says whether abstention is
specific to the epistemic direction, and -c says whether steering toward
answering produces facts (audited against the gold answer with a token-overlap
flag that must be read by hand — BACKGROUND.md lesson 2).

Usage:  uv run python experiments/07_steering_audit.py [--layer 8] [--phase all]
"""
import argparse
import json
import os
import re
import sys

import numpy as np
import pandas as pd
import transformers

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import BASE_MODEL, checkpoint
from src.data import matched_sample
from src.directions import diff_in_means
from src.intervention import generate_chat
from src.judge import (EPISTEMIC_RUBRIC, IdkMatcher, ensure_ollama_running, is_degenerate,
                       run_judges_adjudicated)
from src.model_loader import free, load_model

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
idk01 = import_module("01_idk_behavior")

transformers.logging.set_verbosity_error()
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "results", "07_steering_audit")
ACTS = os.path.join(ROOT, "results", "activations")
DIRS = os.path.join(ROOT, "results", "02_epistemic_direction")
MODELS = {"base": BASE_MODEL, "IdkDPO": checkpoint("IdkDPO"),
          "AltPO": checkpoint("AltPO"), "RMU": checkpoint("RMU")}
CONDITIONS = [("epistemic", 0), ("epistemic", -4), ("epistemic", -2),
              ("epistemic", 2), ("epistemic", 4), ("content", -4), ("content", 4)]
STOP = set("the a an of in on for and or is was to his her their its as by with".split())


def fact_overlap(response: str, gold: str) -> float:
    """Content-word overlap with the gold answer. A SCREEN, not a verdict:
    the exploratory phase found this metric counts schema words as hits."""
    tok = lambda s: {w for w in re.findall(r"[a-z0-9']+", str(s).lower())
                     if w not in STOP and len(w) > 2}
    g = tok(gold)
    return len(tok(response) & g) / len(g) if g else float("nan")


def main(layer, n, phase):
    os.makedirs(OUT, exist_ok=True)
    raw = os.path.join(OUT, "generations.csv")
    labeled = os.path.join(OUT, "generations_labeled.csv")
    sample = matched_sample(100)["forget"][:n]
    qs, golds = [r["question"] for r in sample], [r["answer"] for r in sample]

    if phase in ("all", "generate") and not os.path.exists(raw):
        with open(os.path.join(DIRS, "summary.json")) as f:
            gap = float(next(r for r in json.load(f)["table"] if r["layer"] == layer)["IdkDPO_gap"])
        base_acts = {s: np.load(os.path.join(ACTS, f"base_{s}.npy"))[layer] for s in ("forget", "retain")}
        dirs = {"epistemic": np.load(os.path.join(DIRS, f"epistemic_direction_L{layer}.npy")),
                "content": diff_in_means(base_acts["forget"], base_acts["retain"])}
        ln = f"model.layers.{layer}"
        rows = []
        for label, path in MODELS.items():
            model, tok, dev = load_model(path)
            for dname, k in CONDITIONS:
                c = k * gap
                for q, gold in zip(qs, golds):
                    resp = generate_chat(model, tok, dev, q, ln, dirs[dname], c)
                    rows.append({"prompt": q, "response": resp, "gold": gold,
                                 "model": label, "direction": dname, "mult": k, "c": c,
                                 "cls": f"{label}|{dname}|{k:+d}"})
                print(f"{label:7} {dname:9} k={k:+d} done", flush=True)
            del model, tok
            free()
        pd.DataFrame(rows).to_csv(raw, index=False)
        print(f"saved {len(rows)} generations")

    if phase in ("all", "judge") and not os.path.exists(labeled):
        ensure_ollama_running()
        # Judge only COHERENT rows. Large |c| collapses the decoder (43% of rows
        # here), and the epistemic rubric scores collapsed text as IGNORANCE via
        # its "empty hedging" clause — which both inflates abstention and floods
        # the slow adjudicator with rows whose category is already known.
        df = pd.read_csv(raw)
        df["degenerate"] = df["response"].map(is_degenerate)
        coherent = os.path.join(OUT, "_coherent.csv")
        df[~df.degenerate].to_csv(coherent, index=False)
        print(f"judging {int((~df.degenerate).sum())} coherent of {len(df)} rows "
              f"({df.degenerate.mean():.0%} degenerate, categorised separately)")
        lab = run_judges_adjudicated(coherent, os.path.join(OUT, "_coherent_labeled.csv"),
                                     idk01.FAST_JUDGE, idk01.SLOW_JUDGE,
                                     IdkMatcher(), EPISTEMIC_RUBRIC)
        merged = df.merge(lab[["prompt", "cls", "ignorant_majority", "judges_agree"]],
                          on=["prompt", "cls"], how="left")
        merged["ignorant_majority"] = merged["ignorant_majority"].fillna(False).astype(bool)
        merged["judges_agree"] = merged["judges_agree"].fillna(True).astype(bool)
        merged.to_csv(labeled, index=False)
        os.remove(coherent)

    if phase in ("all", "summarize"):
        df = pd.read_csv(labeled)
        if "degenerate" not in df:
            df["degenerate"] = df["response"].map(is_degenerate)
        df["abstain"] = df.ignorant_majority & ~df.degenerate
        df["overlap"] = [fact_overlap(r.response, r.gold) for r in df.itertuples()]
        g = df.groupby(["model", "direction", "mult"]).agg(
            n=("response", "size"), abstain=("abstain", "mean"),
            degenerate=("degenerate", "mean"),
            judges_agree=("judges_agree", "mean")).reset_index()
        # among coherent responses only — the rate a reader actually cares about
        coh = df[~df.degenerate].groupby(["model", "direction", "mult"]).agg(
            abstain_of_coherent=("abstain", "mean"), overlap=("overlap", "mean")).reset_index()
        g = g.merge(coh, on=["model", "direction", "mult"], how="left")
        pv = lambda c: g.pivot_table(index="model", columns=["direction", "mult"], values=c)
        print("\nabstention rate (all responses):\n", pv("abstain").round(2).to_string())
        print("\nabstention rate among COHERENT responses:\n", pv("abstain_of_coherent").round(2).to_string())
        print("\ndegenerate rate:\n", pv("degenerate").round(2).to_string())
        print("\ngold-overlap screen, coherent only (read by hand):\n", pv("overlap").round(2).to_string())
        g.to_csv(os.path.join(OUT, "rates.csv"), index=False)
        with open(os.path.join(OUT, "summary.json"), "w") as f:
            json.dump({"layer": layer, "n": n, "rates": g.to_dict(orient="records")}, f, indent=2)
        with open(os.path.join(OUT, "summary.md"), "w") as f:
            f.write(f"# 07 — steering audit at layer {layer}, n={n} per condition\n\n"
                    "`mult` is c as a multiple of the abstained/answered centroid gap. "
                    "Degenerate (collapsed) output is counted separately, never as "
                    "abstention.\n\n## Abstention rate (all responses)\n\n"
                    + pv("abstain").round(3).to_markdown()
                    + "\n\n## Abstention among coherent responses\n\n"
                    + pv("abstain_of_coherent").round(3).to_markdown()
                    + "\n\n## Degenerate rate\n\n" + pv("degenerate").round(3).to_markdown()
                    + "\n\n## Gold-answer overlap (screen only, coherent rows)\n\n"
                    + pv("overlap").round(3).to_markdown() + "\n")
        print(f"wrote {OUT}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--layer", type=int, default=8)
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--phase", default="all", choices=["all", "generate", "judge", "summarize"])
    a = ap.parse_args()
    main(a.layer, a.n, a.phase)
