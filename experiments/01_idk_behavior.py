"""
Experiment 01 — do IdkDPO / IdkNLL actually abstain on forget10 and answer on
retain90?

Gate for the whole project: the positive controls must populate the ignorance
cell that the retain-only oracle left empty. The base (full) model is run on
the same prompts as a should-answer-everything reference.

Phases (run all, or one at a time with --phase):
  generate   chat-template greedy generation, one model resident at a time
  judge      regex flag + two Ollama judges with the epistemic rubric
  summarize  abstention rate per (model, class); writes summary.json / .md

Usage:  uv run python experiments/01_idk_behavior.py [--n 100] [--phase all]
"""
import argparse
import json
import os
import re
import sys

import pandas as pd
import transformers

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import BASE_MODEL, POSITIVE_CONTROLS, checkpoint
from src.data import matched_sample
from src.judge import (EPISTEMIC_RUBRIC, ensure_ollama_running, generate_and_save,
                       run_judges_adjudicated)
from src.model_loader import free, load_model

transformers.logging.set_verbosity_error()

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "01_idk_behavior")
# llama3.2 + regex label every row; deepseek-r1 (~15 s/row) only adjudicates
# disagreements and a 10% audit sample.
FAST_JUDGE, SLOW_JUDGE = "llama3.2", "deepseek-r1:latest"
MODELS = {"base": BASE_MODEL, **{m: checkpoint(m) for m in POSITIVE_CONTROLS}}

# TOFU's IdkDPO/IdkNLL targets are drawn from a fixed list of ~100 "I don't
# know" phrasings; this regex is a cheap first-pass flag, not the verdict.
IDK_RE = re.compile(
    r"\b(i don'?t know|i'?m not sure|not familiar|no information|"
    r"don'?t have (any )?(information|knowledge|details|data)|unable to (provide|answer|find)|"
    r"can'?t (provide|answer|find)|not aware|no idea|unaware|unfamiliar|"
    r"i have no|no (record|knowledge|data)|cannot (provide|answer|find)|"
    r"not (something|able) i|doesn'?t ring a bell|beyond my knowledge|"
    r"i couldn'?t find|i'?m (afraid|sorry),? i)\b",
    re.IGNORECASE,
)


def resp_csv(label):
    return os.path.join(OUT, f"responses_{label}.csv")


def labeled_csv(label):
    return os.path.join(OUT, f"responses_{label}_labeled.csv")


def phase_generate(n, max_new_tokens):
    sample = matched_sample(n)
    prompts_by_class = {cls: [r["question"] for r in rows] for cls, rows in sample.items()}
    for label, path in MODELS.items():
        if os.path.exists(resp_csv(label)):
            print(f"[skip] {resp_csv(label)} exists")
            continue
        model, tok, dev = load_model(path)
        df = generate_and_save(prompts_by_class, model, tok, dev, resp_csv(label),
                               max_new_tokens=max_new_tokens)
        del model, tok
        free()
        for cls, rows in sample.items():
            df.loc[df["cls"] == cls, "tofu_index"] = [r["tofu_index"] for r in rows]
            df.loc[df["cls"] == cls, "gold"] = [r["answer"] for r in rows]
        df["model"] = label
        df.to_csv(resp_csv(label), index=False)
        print(f"\n=== {label}: first 5 forget / 3 retain responses ===")
        for cls, k in (("forget", 5), ("retain", 3)):
            for _, r in df[df["cls"] == cls].head(k).iterrows():
                print(f"[{cls}] Q: {r['prompt'][:80]}\n         A: {r['response'][:160]!r}")


def phase_judge():
    ensure_ollama_running()
    for label in MODELS:
        if os.path.exists(labeled_csv(label)):
            print(f"[skip] {labeled_csv(label)} exists")
            continue
        run_judges_adjudicated(resp_csv(label), labeled_csv(label), FAST_JUDGE, SLOW_JUDGE,
                               IDK_RE, EPISTEMIC_RUBRIC)


def phase_summarize():
    rows = []
    for label in MODELS:
        df = pd.read_csv(labeled_csv(label))
        for cls, sub in df.groupby("cls"):
            rows.append({
                "model": label, "cls": cls, "n": len(sub),
                "abstain_judge_majority": float(sub["ignorant_majority"].mean()),
                "abstain_regex": float(sub["ignorant_regex"].mean()),
                "judge_agreement": float(sub["judges_agree"].mean()),
                "regex_vs_majority_agreement":
                    float((sub["ignorant_regex"] == sub["ignorant_majority"]).mean()),
            })
    tab = pd.DataFrame(rows)
    print("\n" + tab.to_string(index=False, float_format=lambda x: f"{x:.2f}"))

    def rate(m, c):
        return float(tab[(tab.model == m) & (tab.cls == c)]["abstain_judge_majority"].iloc[0])

    gate = {m: {"forget_abstain": rate(m, "forget"), "retain_abstain": rate(m, "retain"),
                "passes": rate(m, "forget") >= 0.5 and rate(m, "retain") <= 0.25}
            for m in POSITIVE_CONTROLS}
    gate["base"] = {"forget_abstain": rate("base", "forget"),
                    "retain_abstain": rate("base", "retain")}
    passed = [m for m in POSITIVE_CONTROLS if gate[m]["passes"]]
    verdict = ("PASS: ignorance cell populated by " + ", ".join(passed)) if passed else \
              "FAIL: neither positive control abstains on forget10 — stop and reassess"
    print("\nGATE —", verdict)

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "summary.json"), "w") as f:
        json.dump({"table": rows, "gate": gate, "verdict": verdict,
                   "judges": {"fast": FAST_JUDGE, "slow_adjudicator": SLOW_JUDGE}}, f, indent=2)
    with open(os.path.join(OUT, "summary.md"), "w") as f:
        f.write("# 01 — IdkDPO / IdkNLL behavioral check\n\n")
        f.write("Abstention rate = fraction of responses the judge majority labelled "
                "IGNORANCE (epistemic rubric); regex = cheap phrase match.\n\n")
        f.write(tab.to_markdown(index=False, floatfmt=".2f") + "\n\n")
        f.write(f"**Gate:** {verdict}\n")
    print(f"wrote {OUT}/summary.{{json,md}}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100, help="questions per class")
    ap.add_argument("--max-new-tokens", type=int, default=120)
    ap.add_argument("--phase", default="all", choices=["all", "generate", "judge", "summarize"])
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    if a.phase in ("all", "generate"):
        phase_generate(a.n, a.max_new_tokens)
    if a.phase in ("all", "judge"):
        phase_judge()
    if a.phase in ("all", "summarize"):
        phase_summarize()
