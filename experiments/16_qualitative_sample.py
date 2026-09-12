"""
Experiment 16 — randomly selected raw examples for the write-up.

Every headline in this project depends on an LLM judge deciding whether a
response counts as "I don't know". If that judgement is unreliable the project
is unreliable, so the examples a reader sees must be drawn at random rather
than chosen — this script fixes a seed, samples, and prints whatever comes out,
including cases where the judge looks wrong.

Sections:
  1. abstention judgements, sampled per (model, judged label)
  2. the recognition probe: one question with its true and perturbed answers
  3. steering: base model at +2x gap, the causal claim in experiment 07
  4. judge-vs-matcher disagreements — the rows the pipeline is least sure about

Usage:  uv run python experiments/16_qualitative_sample.py [--seed 0] [--k 3]
"""
import argparse
import json
import os
import sys

import pandas as pd
from datasets import load_dataset

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.data import sample_split
from src.judge import is_degenerate

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "results", "16_qualitative_sample")
B01 = os.path.join(ROOT, "results", "01_idk_behavior_n400")


def trunc(s, n=240):
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[:n] + " […]"


def main(seed, k):
    os.makedirs(OUT, exist_ok=True)
    lines = ["# Randomly selected raw examples",
             "",
             f"Seed {seed}, {k} examples per cell. Nothing here is hand-picked: the "
             "script samples and prints whatever it draws, including rows where the "
             "judge looks wrong. Responses are truncated to ~240 characters.",
             ""]

    # ---- 1. abstention judgements -----------------------------------------
    lines += ["## 1. Abstention judgements on forget10", ""]
    for model in ["base", "IdkNLL", "IdkDPO", "NPO", "RMU"]:
        p = os.path.join(B01, f"responses_{model}_labeled.csv")
        if not os.path.exists(p):
            continue
        d = pd.read_csv(p)
        d = d[d.cls == "forget"].copy()
        d["degenerate"] = d.response.map(is_degenerate)
        d["judged_abstain"] = (d.ignorant_majority.fillna(False).astype(bool)
                               & ~d.degenerate)
        lines += [f"### {model}", ""]
        for label, sub in [("judged ABSTAIN", d[d.judged_abstain]),
                           ("judged ANSWERED", d[~d.judged_abstain & ~d.degenerate]),
                           ("degenerate", d[d.degenerate])]:
            if not len(sub):
                lines += [f"*{label}: none*", ""]
                continue
            s = sub.sample(min(k, len(sub)), random_state=seed)
            lines += [f"**{label}** ({len(sub)}/{len(d)} of this model's rows)", ""]
            for r in s.itertuples():
                lines += [f"- **Q:** {trunc(r.prompt, 150)}",
                          f"  **A:** {trunc(r.response)}",
                          f"  *gold:* {trunc(r.gold, 120)}", ""]

    # ---- 1b. a TOFU quirk the random sample surfaced ----------------------
    import re as _re
    pat = _re.compile(r"no (publicly available |definitive |specific |further )?information|"
                      r"not (publicly )?(available|disclosed|known|specified)|"
                      r"no (record|details) (of|about|available)|"
                      r"has not (been )?(disclosed|revealed|shared)", _re.I)
    from src.data import load_tofu
    quirk = [r for r in load_tofu("forget10") if pat.search(r["answer"])]
    lines += ["## 1b. A dataset quirk this sample surfaced", "",
              f"**{len(quirk)} of 400 forget10 questions have a gold answer that is "
              "itself a disclaimer** — mostly about one author, Moshe Ben-David. On "
              "these, saying \"there is no information available\" is the *correct* "
              "answer, not an abstention. That is why the base model shows a non-zero "
              "abstention rate (3/400): the judge is right and the questions are "
              "unusual. The effect is ~1% and does not move any conclusion — every "
              "method under test sits at 0.00-0.05 — but it means abstention rates "
              "have a ~1% floor that is dataset, not behaviour.", ""]
    for r in quirk[:3]:
        lines += [f"- **Q:** {trunc(r['question'], 150)}", f"  *gold:* {trunc(r['answer'], 180)}", ""]

    # ---- 2. the recognition probe -----------------------------------------
    lines += ["## 2. What the recognition probe actually compares", "",
              "The model scores the true answer against five perturbations that share "
              "its sentence frame and differ only in the fact. One drawn at random:", ""]
    idx = [r["tofu_index"] for r in sample_split("forget10", 400)]
    ds = load_dataset("locuslab/TOFU", "forget10_perturbed")["train"]
    import random
    rng = random.Random(seed)
    i = rng.choice(idx)
    ex = ds[i]
    lines += [f"- **Q:** {trunc(ex['question'], 200)}",
              f"- **true (scored):** {trunc(ex['paraphrased_answer'], 200)}"]
    for p_ in ex["perturbed_answer"]:
        lines += [f"- *perturbed:* {trunc(p_, 200)}"]
    lines += ["", "Recognition = the true answer beats all five on length-normalised "
              "log-probability. Base scores 0.73, the retain-only oracle 0.43.", ""]

    # ---- 3. steering ------------------------------------------------------
    sp = os.path.join(ROOT, "results", "07_steering_audit", "generations_labeled.csv")
    if os.path.exists(sp):
        lines += ["## 3. Steering the base model toward abstention (experiment 07)", "",
                  "Base answers these correctly when unsteered. At +2x the "
                  "abstained/answered centroid gap along the epistemic direction at "
                  "layer 8 it declines instead; a matched-norm content direction "
                  "produces gibberish rather than declining.", ""]
        g = pd.read_csv(sp)
        for tag, sub in [("unsteered (k=0)", g[(g.model == "base") & (g.direction == "epistemic") & (g.mult == 0)]),
                         ("+2x epistemic", g[(g.model == "base") & (g.direction == "epistemic") & (g.mult == 2)]),
                         ("+4x content (matched-norm control)", g[(g.model == "base") & (g.direction == "content") & (g.mult == 4)])]:
            if not len(sub):
                continue
            s = sub.sample(min(k, len(sub)), random_state=seed)
            lines += [f"**{tag}**", ""]
            for r in s.itertuples():
                lines += [f"- **Q:** {trunc(r.prompt, 130)}", f"  **A:** {trunc(r.response, 200)}", ""]

    # ---- 4. where the pipeline is least certain ---------------------------
    lines += ["## 4. Judge vs matcher disagreements", "",
              "The abstention label combines an LLM judge (llama3.2) with a matcher "
              "built from open-unlearning's 99 IDK training strings; deepseek-r1 "
              "adjudicates where they disagree. Agreement is 0.96-1.00 for every "
              "model except the two Idk checkpoints (0.65-0.74). Those disagreements, "
              "sampled at random — this is the weakest link in the measurement:", ""]
    for model in ["IdkNLL", "IdkDPO"]:
        p = os.path.join(B01, f"responses_{model}_labeled.csv")
        if not os.path.exists(p):
            continue
        d = pd.read_csv(p)
        d = d[(d.cls == "forget") & (~d.judges_agree.fillna(True).astype(bool))]
        if not len(d):
            continue
        s = d.sample(min(k, len(d)), random_state=seed)
        lines += [f"**{model}** ({len(d)} disagreements)", ""]
        for r in s.itertuples():
            fast = getattr(r, "ignorant_llama3_2", "?")
            final = bool(r.ignorant_majority) if pd.notna(r.ignorant_majority) else "?"
            lines += [f"- **A:** {trunc(r.response, 200)}",
                      f"  *matcher:* {bool(r.ignorant_regex)} · *llama3.2:* {fast} · "
                      f"*final (deepseek adjudicated):* {final}", ""]

    path = os.path.join(OUT, "examples.md")
    with open(path, "w") as f:
        f.write("\n".join(lines))
    print("\n".join(lines[:60]))
    print(f"\n... wrote {path} ({len(lines)} lines)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--k", type=int, default=3)
    a = ap.parse_args()
    main(a.seed, a.k)
