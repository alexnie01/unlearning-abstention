"""
Experiment 10 (PLAN2 R7) — can NPO be made to say what it still recognises?

NPO is the sharpest dissociation in this project: it ranks the true answer
above five surface-matched lures as well as the base model does (0.69 vs 0.73)
while stating the fact in 4% of its generations against base's 38%. The
knowledge is present in the ranking and absent from the output. Is that gap
removable?

Two stages, cheap first:
  1. LOG-PROB SWEEP. Teacher-forced gold-answer log-prob under every
     (direction, layer, magnitude) cell, batched — the whole grid costs about
     as much as one generation pass. Nothing further is worth running on a
     direction that cannot move this.
  2. GENERATION. Only for cells that beat the baseline, generate and judge
     recall with 09's rubric. Log-prob is not recall: the exploratory phase's
     central lesson was that log-prob recovery on TOFU is schema-driven
     confabulation, so a log-prob gain is a lead, not a result.

Directions (all at matched norm, swept over multiples of their own scale):
  undo      base-minus-NPO mean activation shift — the most direct test of
            "is the knowledge recoverable by reversing the representational
            displacement". This is the one with a mechanistic story.
  epistemic the abstention direction from 02, negated (steering toward
            answering rather than abstaining)
  content   base forget-vs-retain (control: a real direction, wrong meaning)
  random    seeded unit vector (control: matched norm, no meaning)

The base model is run through the identical grid, so "did this help NPO" is
measured against "what the same perturbation does to a model that already
answers" rather than against zero.

Usage:  uv run python experiments/10_npo_recovery.py [--n 200]
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
from src.config import BASE_MODEL, checkpoint
from src.data import matched_sample
from src.directions import diff_in_means, unit
from src.intervention import score_pairs_chat, score_pairs_chat_intervened
from src.judge import CORRECTNESS_RUBRIC, JUDGE_WORKERS, ensure_ollama_running, judge_one
from src.model_loader import free, load_model
from src.stats import result_dir, wilson_ci

transformers.logging.set_verbosity_error()
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = result_dir("10_npo_recovery")
ACTS = os.path.join(ROOT, "results", "activations")
DIRS = os.path.join(ROOT, "results", "02_epistemic_direction")
TARGETS = {"NPO": checkpoint("NPO"), "GradDiff": checkpoint("GradDiff"), "base": BASE_MODEL}
LAYERS = [8, 12]
MULTS = [-4, -2, -1, -0.5, 0, 0.5, 1, 2, 4]


def build_directions(label, layer):
    """Unit directions plus the natural scale of each, at one layer."""
    b = {s: np.load(os.path.join(ACTS, f"base_{s}.npy"))[layer] for s in ("forget", "retain")}
    out = {}
    if label != "base":
        t = np.load(os.path.join(ACTS, f"{label}_forget.npy"))[layer]
        raw = b["forget"].mean(0) - t.mean(0)          # points from the method back to base
        out["undo"] = (unit(raw), float(np.linalg.norm(raw)))
    epi = np.load(os.path.join(DIRS, f"epistemic_direction_L{layer}.npy"))
    with open(os.path.join(DIRS, "summary.json")) as f:
        gap = float(next(r for r in json.load(f)["table"] if r["layer"] == layer)["IdkDPO_gap"])
    out["epistemic"] = (epi, gap)
    content = diff_in_means(b["forget"], b["retain"])
    out["content"] = (content, float(np.linalg.norm(b["forget"].mean(0) - b["retain"].mean(0))))
    rng = np.random.default_rng(0)
    scale = out.get("undo", out["epistemic"])[1]
    out["random"] = (unit(rng.standard_normal(epi.shape[0])), scale)
    return out


def sweep_logprob(model, tok, dev, questions, golds, label):
    rows = []
    for layer in LAYERS:
        ln = f"model.layers.{layer}"
        for dname, (d, scale) in build_directions(label, layer).items():
            for k in MULTS:
                c = k * scale
                if k == 0 and dname != "epistemic":
                    continue
                lp = score_pairs_chat_intervened(model, tok, dev, list(zip(questions, golds)),
                                                 ln, d, c)
                rows.append({"model": label, "layer": layer, "direction": dname, "mult": k,
                             "c": c, "gold_lp": float(lp.mean()),
                             "gold_lp_sem": float(lp.std(ddof=1) / np.sqrt(len(lp)))})
                print(f"{label:9} L{layer:2d} {dname:9} k={k:+.1f} gold_lp={lp.mean():+.3f}", flush=True)
    return rows


def main(n, n_gen, top_k):
    os.makedirs(OUT, exist_ok=True)
    sample = matched_sample(400)["forget"][:n]
    qs, golds = [r["question"] for r in sample], [r["answer"] for r in sample]

    path = os.path.join(OUT, "logprob_sweep.csv")
    if os.path.exists(path):
        tab = pd.read_csv(path)
    else:
        rows = []
        for label, hf in TARGETS.items():
            model, tok, dev = load_model(hf)
            rows += sweep_logprob(model, tok, dev, qs, golds, label)
            del model, tok
            free()
        tab = pd.DataFrame(rows)
        tab.to_csv(path, index=False)

    base_lp = {m: float(tab[(tab.model == m) & (tab.mult == 0)].gold_lp.iloc[0]) for m in TARGETS}
    tab["delta"] = [r.gold_lp - base_lp[r.model] for r in tab.itertuples()]
    print("\ngold log-prob change vs each model's own baseline (top cells):")
    for m in TARGETS:
        sub = tab[(tab.model == m) & (tab.mult != 0)].nlargest(4, "delta")
        print(f"  {m}: baseline {base_lp[m]:+.3f}")
        for r in sub.itertuples():
            print(f"    L{r.layer} {r.direction:9} k={r.mult:+.1f}  {r.gold_lp:+.3f} ({r.delta:+.3f})")

    # Stage 2: generate + judge only where log-prob actually improved on NPO.
    cand = tab[(tab.model == "NPO") & (tab.mult != 0) & (tab.delta > 0)].nlargest(top_k, "delta")
    if not len(cand):
        print("\nNo cell raised NPO's gold log-prob; nothing to generate.")
    gen_rows = []
    if len(cand):
        ensure_ollama_running()
        from src.intervention import generate_chat
        model, tok, dev = load_model(TARGETS["NPO"])
        conds = [(None, 0, 0.0, "none")] + [(r.layer, r.direction, r.c, f"L{r.layer} {r.direction} k={r.mult:+.1f}")
                                            for r in cand.itertuples()]
        for layer, dname, c, tag in conds:
            d = build_directions("NPO", layer)[dname][0] if layer else None
            ln = f"model.layers.{layer}" if layer else None
            resp = [generate_chat(model, tok, dev, q, ln, d, c) for q in qs[:n_gen]]
            with __import__("concurrent.futures").futures.ThreadPoolExecutor(JUDGE_WORKERS) as ex:
                ok = list(ex.map(lambda t: judge_one(t[0], t[1], "llama3.2", CORRECTNESS_RUBRIC,
                                                     gold=t[2]),
                                 zip(qs[:n_gen], resp, golds[:n_gen])))
            lo, hi = wilson_ci(int(sum(ok)), len(ok))
            gen_rows.append({"condition": tag, "n": len(ok), "recall": float(np.mean(ok)),
                             "recall_lo": lo, "recall_hi": hi})
            print(f"  {tag:28} recall={np.mean(ok):.3f} [{lo:.2f}, {hi:.2f}]", flush=True)
            for q, r_ in list(zip(qs, resp))[:3]:
                gen_rows[-1].setdefault("samples", []).append(r_[:120])
        del model, tok
        free()

    with open(os.path.join(OUT, "summary.json"), "w") as f:
        json.dump({"n": n, "baselines": base_lp, "generations": gen_rows,
                   "sweep": tab.to_dict(orient="records")}, f, indent=2)
    with open(os.path.join(OUT, "summary.md"), "w") as f:
        f.write("# 10 — can NPO be made to say what it recognises?\n\n"
                "Stage 1, gold-answer log-prob (Δ vs each model's own baseline):\n\n")
        f.write(tab.pivot_table(index=["model", "layer", "direction"], columns="mult",
                                values="delta").round(3).to_markdown() + "\n\n")
        if gen_rows:
            f.write("Stage 2, judged recall for cells that improved log-prob:\n\n")
            f.write(pd.DataFrame(gen_rows).drop(columns=["samples"], errors="ignore")
                    .to_markdown(index=False, floatfmt=".3f") + "\n")
        else:
            f.write("Stage 2 not run: no intervention raised NPO's gold log-prob.\n")

    fig, axes = plt.subplots(1, len(LAYERS), figsize=(11, 4), sharey=True)
    for ax, layer in zip(np.atleast_1d(axes), LAYERS):
        for m in TARGETS:
            for dname, ls in (("undo", "-"), ("epistemic", "--"), ("content", ":"), ("random", "-.")):
                sub = tab[(tab.model == m) & (tab.layer == layer) & (tab.direction == dname)].sort_values("mult")
                if len(sub):
                    ax.plot(sub.mult, sub.delta, ls, marker="o", ms=3,
                            label=f"{m}/{dname}" if layer == LAYERS[0] else None)
        ax.axhline(0, color="k", lw=0.5); ax.set_xlabel("c / natural scale")
        ax.set_title(f"layer {layer}")
    np.atleast_1d(axes)[0].set_ylabel("Δ gold-answer log-prob")
    np.atleast_1d(axes)[-1].legend(fontsize=6, ncol=2)
    plt.tight_layout(); plt.savefig(os.path.join(OUT, "recovery_sweep.png"), dpi=150)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--n-gen", type=int, default=100)
    ap.add_argument("--top-k", type=int, default=3)
    a = ap.parse_args()
    main(a.n, a.n_gen, a.top_k)
