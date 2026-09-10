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
import sys

import pandas as pd
import transformers

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import BASE_MODEL, METHODS_UNDER_TEST, POSITIVE_CONTROLS, checkpoint
from src.data import matched_sample
from src.judge import (EPISTEMIC_RUBRIC, IdkMatcher, ensure_ollama_running, generate_and_save,
                       is_degenerate, run_judges_adjudicated)
from src.model_loader import free, load_model
from src.stats import result_dir, wilson_ci

transformers.logging.set_verbosity_error()

OUT = result_dir("01_idk_behavior")
# llama3.2 + regex label every row; deepseek-r1 (~15 s/row) only adjudicates
# disagreements and a 10% audit sample.
FAST_JUDGE, SLOW_JUDGE = "llama3.2", "deepseek-r1:latest"
MODELS = {"base": BASE_MODEL, **{m: checkpoint(m) for m in POSITIVE_CONTROLS + METHODS_UNDER_TEST}}

# Cheap first-pass flag from the 99 training IDK strings, not the verdict.
IDK_RE = IdkMatcher()


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
    """JUDGE_SAMPLE caps how many rows per class go to the LLM judges. The
    phrase matcher still runs on every row, so a capped model reports a judged
    rate over the sample and a matcher rate over all of it — enough to confirm
    a rate that the matcher already puts at 0/400, without paying ~30 min of
    LLM calls per model to reconfirm a zero."""
    ensure_ollama_running()
    cap = int(os.environ.get("JUDGE_SAMPLE", 0))
    for label in MODELS:
        if os.path.exists(labeled_csv(label)):
            print(f"[skip] {labeled_csv(label)} exists")
            continue
        if not cap:
            run_judges_adjudicated(resp_csv(label), labeled_csv(label), FAST_JUDGE, SLOW_JUDGE,
                                   IDK_RE, EPISTEMIC_RUBRIC)
            continue
        full = pd.read_csv(resp_csv(label))
        # groupby().sample() keeps every column; groupby().apply() drops the
        # grouping column in current pandas.
        per_class = min(cap, int(full.groupby("cls").size().min()))
        pick = full.groupby("cls", group_keys=False).sample(n=per_class, random_state=0)
        tmp = labeled_csv(label) + ".sample"
        pick.to_csv(tmp, index=False)
        lab = run_judges_adjudicated(tmp, tmp + ".labeled", FAST_JUDGE, SLOW_JUDGE,
                                     IDK_RE, EPISTEMIC_RUBRIC)
        cols = ["ignorant_majority", "judges_agree", f"{'ignorant'}_regex", "degenerate"]
        merged = full.merge(lab[["prompt", "cls"] + [c for c in cols if c in lab]],
                            on=["prompt", "cls"], how="left")
        merged["judged"] = merged["ignorant_majority"].notna()
        merged["ignorant_regex"] = merged["response"].map(lambda s: bool(IDK_RE(s)))
        merged["degenerate"] = merged["response"].map(is_degenerate)
        merged.to_csv(labeled_csv(label), index=False)
        os.remove(tmp); os.remove(tmp + ".labeled")
        print(f"{label}: judged {int(merged.judged.sum())} of {len(merged)} rows "
              f"(cap {cap}/class); matcher ran on all", flush=True)


def phase_summarize():
    rows = []
    for label in MODELS:
        df = pd.read_csv(labeled_csv(label))
        df["degenerate"] = df["response"].map(is_degenerate)
        if "judged" in df:                      # capped run: rates over judged rows only
            df = df[df["judged"].fillna(False).astype(bool)]
        for cls, sub in df.groupby("cls"):
            rows.append({
                "model": label, "cls": cls, "n": len(sub),
                # Degenerate output reads as IGNORANCE to the rubric ("empty
                # hedging with no factual claims"), so the reported abstention
                # rate excludes it; abstain_raw keeps the unfiltered number.
                "abstain": float((sub["ignorant_majority"] & ~sub["degenerate"]).mean()),
                "abstain_raw": float(sub["ignorant_majority"].mean()),
                "degenerate": float(sub["degenerate"].mean()),
                "abstain_regex": float(sub["ignorant_regex"].mean()),
                "judge_agreement": float(sub["judges_agree"].mean()),
                **dict(zip(("abstain_lo", "abstain_hi"),
                           wilson_ci(int((sub["ignorant_majority"] & ~sub["degenerate"]).sum()), len(sub)))),
            })
    tab = pd.DataFrame(rows)
    print("\n" + tab.to_string(index=False, float_format=lambda x: f"{x:.2f}"))

    def rate(m, c):
        sub = tab[(tab.model == m) & (tab.cls == c)]["abstain"]
        return float(sub.iloc[0]) if len(sub) else float("nan")

    # "Populated" means enough abstained-forget rows for a centroid (>=30 of
    # 100) with the behavior specific to forget10 — not a majority.
    gate = {m: {"forget_abstain": rate(m, "forget"), "retain_abstain": rate(m, "retain"),
                "passes": rate(m, "forget") >= 0.3 and rate(m, "retain") <= 0.2}
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
