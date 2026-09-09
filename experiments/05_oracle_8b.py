"""
Experiment 05 — does the 8B retain90 oracle abstain where the 1B oracle
confabulated?

Same prompts, generation and judges as 01, on the 1B and 8B retain90 oracles
(neither ever saw forget10). The 1B oracle is rerun here rather than cited so
both are measured with this repo's prompt format and judges.

Usage:  uv run python experiments/05_oracle_8b.py [--n 50] [--phase all]
"""
import argparse
import json
import os
import sys

import pandas as pd
import transformers

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import RETAIN, RETAIN_8B
from src.data import matched_sample
from src.judge import (EPISTEMIC_RUBRIC, ensure_ollama_running, generate_and_save,
                       run_judges_adjudicated)
from src.model_loader import free, load_model

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
idk01 = import_module("01_idk_behavior")

transformers.logging.set_verbosity_error()
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "05_oracle_8b")
MODELS = {"oracle_1B": RETAIN, "oracle_8B": RETAIN_8B}


def main(n, phase):
    os.makedirs(OUT, exist_ok=True)
    sample = matched_sample(100)
    prompts = {cls: [r["question"] for r in rows[:n]] for cls, rows in sample.items()}
    if phase in ("all", "generate"):
        for label, path in MODELS.items():
            out = os.path.join(OUT, f"responses_{label}.csv")
            if os.path.exists(out):
                continue
            model, tok, dev = load_model(path)
            df = generate_and_save(prompts, model, tok, dev, out, max_new_tokens=120)
            del model, tok
            free()
            print(f"\n=== {label}: first 6 forget responses ===")
            for _, r in df[df.cls == "forget"].head(6).iterrows():
                print(f"Q: {r.prompt[:80]}\n   A: {r.response[:160]!r}")
    if phase in ("all", "judge"):
        ensure_ollama_running()
        for label in MODELS:
            out = os.path.join(OUT, f"responses_{label}_labeled.csv")
            if os.path.exists(out):
                continue
            run_judges_adjudicated(os.path.join(OUT, f"responses_{label}.csv"), out,
                                   idk01.FAST_JUDGE, idk01.SLOW_JUDGE, idk01.IDK_RE, EPISTEMIC_RUBRIC)
    if phase in ("all", "summarize"):
        rows = []
        for label in MODELS:
            df = pd.read_csv(os.path.join(OUT, f"responses_{label}_labeled.csv"))
            for cls, sub in df.groupby("cls"):
                rows.append({"model": label, "cls": cls, "n": len(sub),
                             "abstain_judge_majority": float(sub.ignorant_majority.mean()),
                             "abstain_regex": float(sub.ignorant_regex.mean()),
                             "judge_agreement": float(sub.judges_agree.mean())})
        tab = pd.DataFrame(rows)
        print("\n" + tab.to_string(index=False, float_format=lambda x: f"{x:.2f}"))
        with open(os.path.join(OUT, "summary.json"), "w") as f:
            json.dump({"table": rows}, f, indent=2)
        with open(os.path.join(OUT, "summary.md"), "w") as f:
            f.write("# 05 — retain90 oracle abstention at 1B vs 8B\n\n")
            f.write(tab.to_markdown(index=False, floatfmt=".2f") + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--phase", default="all", choices=["all", "generate", "judge", "summarize"])
    a = ap.parse_args()
    main(a.n, a.phase)
