"""
Experiment 04 — is the epistemic direction causally live in RMU / AltPO?

At the layer chosen in 02, translate the residual stream by c * direction from
the decision position onward and score teacher-forced log-probs of (a) the
gold TOFU answer and (b) IdkDPO's canonical "I don't know" reply, on forget10.

  c = -gap   pushes toward ANSWERING (gap = abstained-forget minus answered-
             retain centroid distance along the direction on IdkDPO, from 02)
  c = +gap   pushes toward ABSTAINING

Models: IdkDPO (the direction must be live here, or it is not causal at all),
base (does +gap make a knowing model abstain?), RMU and AltPO (the test).
Controls at the SAME |c|: the content direction and a seeded random unit
vector. A handful of generations per condition are saved so the numbers can
be read against actual text.

Usage:  uv run python experiments/04_causal.py [--layer L] [--n 100]
"""
import argparse
import json
import os
import sys

import numpy as np
import pandas as pd
import transformers

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import BASE_MODEL, checkpoint
from src.data import matched_sample
from src.directions import diff_in_means, unit
from src.intervention import generate_chat, score_dataset_chat
from src.model_loader import free, load_model

transformers.logging.set_verbosity_error()
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "results", "04_causal")
ACTS = os.path.join(ROOT, "results", "activations")
DIRS = os.path.join(ROOT, "results", "02_epistemic_direction")
MODELS = {"IdkDPO": checkpoint("IdkDPO"), "base": BASE_MODEL,
          "RMU": checkpoint("RMU"), "AltPO": checkpoint("AltPO")}
N_GEN = 6


def main(layer_arg, n):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(DIRS, "summary.json")) as f:
        s02 = json.load(f)
    L = layer_arg if layer_arg is not None else s02["best_layer"]
    gap = float(next(r for r in s02["table"] if r["layer"] == L)["IdkDPO_gap"])
    layer_name = f"model.layers.{L}"

    epi = np.load(os.path.join(DIRS, f"epistemic_direction_L{L}.npy"))
    base_acts = {s: np.load(os.path.join(ACTS, f"base_{s}.npy"))[L] for s in ("forget", "retain")}
    content = diff_in_means(base_acts["forget"], base_acts["retain"])
    rand = unit(np.random.default_rng(0).standard_normal(epi.shape[0]))
    dirs = {"epistemic": epi, "content": content, "random": rand}

    idk = pd.read_csv(os.path.join(ROOT, "results", "01_idk_behavior", "responses_IdkDPO_labeled.csv"))
    idk_answer = idk[(idk.cls == "forget") & idk.ignorant_majority].response.mode().iloc[0]
    print(f"layer {L}, gap along epistemic direction = {gap:.3f}, canonical IDK = {idk_answer!r}")

    sample = matched_sample(100)["forget"][:n]
    qs, golds = [r["question"] for r in sample], [r["answer"] for r in sample]

    rows, gens = [], []
    for label, path in MODELS.items():
        model, tok, dev = load_model(path)
        conds = [("none", None, 0.0)] + [(dn, d, s * gap) for dn, d in dirs.items() for s in (-1, 1)]
        for dname, d, c in conds:
            g = score_dataset_chat(model, tok, dev, qs, golds, layer_name, d, c)
            i = score_dataset_chat(model, tok, dev, qs, [idk_answer] * len(qs), layer_name, d, c)
            rows.append({"model": label, "direction": dname, "c": c, "n": len(qs),
                         "gold_lp": float(g.mean()), "idk_lp": float(i.mean()),
                         "gold_lp_sd": float(g.std(ddof=1)), "idk_lp_sd": float(i.std(ddof=1))})
            print(f"{label:7} {dname:10} c={c:+7.2f}  gold lp {g.mean():+7.3f}   idk lp {i.mean():+7.3f}")
            if dname in ("none", "epistemic"):
                for q in qs[:N_GEN]:
                    gens.append({"model": label, "direction": dname, "c": c, "prompt": q,
                                 "response": generate_chat(model, tok, dev, q, layer_name, d, c)})
        del model, tok
        free()

    tab = pd.DataFrame(rows)
    tab.to_csv(os.path.join(OUT, "logprobs.csv"), index=False)
    pd.DataFrame(gens).to_csv(os.path.join(OUT, "generations.csv"), index=False)

    # deltas relative to each model's own baseline
    base_lp = tab[tab.direction == "none"].set_index("model")
    tab["d_gold"] = tab.apply(lambda r: r.gold_lp - base_lp.loc[r.model, "gold_lp"], axis=1)
    tab["d_idk"] = tab.apply(lambda r: r.idk_lp - base_lp.loc[r.model, "idk_lp"], axis=1)
    piv = tab[tab.direction != "none"].pivot_table(index="model", columns=["direction", "c"],
                                                   values=["d_gold", "d_idk"])
    print("\nΔ log-prob vs own baseline (rows: model; columns: direction, c):")
    print(piv.round(3).to_string())

    with open(os.path.join(OUT, "summary.md"), "w") as f:
        f.write(f"# 04 — causal translation along the epistemic direction (layer {L}, |c| = {gap:.2f})\n\n")
        f.write("Mean teacher-forced log-prob per token on forget10 (n=%d).\n\n" % len(qs))
        f.write(tab.to_markdown(index=False, floatfmt=".3f") + "\n\n## Generations\n\n")
        for g in gens:
            f.write(f"- **{g['model']} / {g['direction']} c={g['c']:+.2f}** — {g['prompt'][:70]}\n\n"
                    f"  > {g['response'][:200]!r}\n\n")
    with open(os.path.join(OUT, "summary.json"), "w") as f:
        json.dump({"layer": L, "gap": gap, "idk_answer": idk_answer, "rows": rows}, f, indent=2)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--layer", type=int, default=None)
    ap.add_argument("--n", type=int, default=100)
    a = ap.parse_args()
    main(a.layer, a.n)
