"""
Experiment 08 (PLAN2 B3) — is the answer's correctness still REPRESENTED, even
where the output ranking says no?

06 reads knowledge off the output distribution, which two of its results may
confound:
  - IdkDPO / AltPO are preference-trained to demote the true answer, so a
    collapsed ranking is partly definitional rather than evidence of erasure;
  - RMU scrambles the residual stream on forget prompts, so its collapsed
    ranking may be a broken readout over an intact representation.
Both are output-head stories. This experiment bypasses the head: train a linear
probe on the BASE model's activations to separate true from perturbed answers,
then decode each unlearned model's activations with a probe trained on its own
activations (does the model represent correctness at all?) and with the base's
probe (does it represent it the SAME way?).

Activations are the last token of "chat_prompt + answer", i.e. the position
that has seen the whole candidate answer, at every layer.

Reading:
  own-probe high, output ranking low  -> knowledge represented, readout
                                         suppressed (a gate over intact content)
  own-probe low                       -> correctness not linearly represented
                                         either; not a readout story

Usage:  uv run python experiments/08_knowledge_representation.py [--n 100]
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
import torch
import transformers
from baukit import TraceDict
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import BASE_MODEL, CHECKPOINTS, METHODS_UNDER_TEST, POSITIVE_CONTROLS, RETAIN
from src.data import sample_split
from src.knowledge import load_perturbed
from src.model_loader import free, load_model
from src.prompting import format_chat

transformers.logging.set_verbosity_error()
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "results", "08_knowledge_representation")
MODELS = {"base": BASE_MODEL, "oracle": RETAIN, **CHECKPOINTS}
ORDER = ["base", "oracle"] + POSITIVE_CONTROLS + METHODS_UNDER_TEST


def answer_activations(model, tokenizer, device, rows) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Last-token activations of prompt+answer for the true answer and each
    perturbation. Returns (acts[n_layers, n_items, hidden], labels, question_id)."""
    names = [f"model.layers.{i}" for i in range(model.config.num_hidden_layers)]
    items = []
    for qi, r in enumerate(rows):
        items.append((r["question"], r["true"], 1, qi))
        for p in r["perturbed"]:
            items.append((r["question"], p, 0, qi))
    acts = np.zeros((len(names), len(items), model.config.hidden_size), dtype=np.float32)
    for j, (q, a, _, _) in enumerate(tqdm(items, desc="answer acts", leave=False)):
        ids = tokenizer(format_chat(tokenizer, q) + a, return_tensors="pt",
                        add_special_tokens=False).to(device)
        with TraceDict(model, names) as tr, torch.no_grad():
            model(**ids)
        for i, nm in enumerate(names):
            h = tr[nm].output
            h = h[0] if isinstance(h, tuple) else h
            acts[i, j] = h[0, -1].float().cpu().numpy()
    labels = np.array([it[2] for it in items])
    qids = np.array([it[3] for it in items])
    return acts, labels, qids


def cv_probe_auroc(X, y, groups, seed=0) -> float:
    """Grouped 5-fold: all candidates for one question stay in the same fold, so
    the probe cannot memorise a question's activations."""
    uq = np.unique(groups)
    rng = np.random.default_rng(seed)
    fold = {q: k for q, k in zip(rng.permutation(uq), np.arange(len(uq)) % 5)}
    f = np.array([fold[g] for g in groups])
    scores, truth = [], []
    for k in range(5):
        tr, te = f != k, f == k
        sc = StandardScaler().fit(X[tr])
        clf = LogisticRegression(max_iter=2000, C=0.1).fit(sc.transform(X[tr]), y[tr])
        scores += list(clf.decision_function(sc.transform(X[te])))
        truth += list(y[te])
    return float(roc_auc_score(truth, scores))


def fit_probe(X, y):
    sc = StandardScaler().fit(X)
    return sc, LogisticRegression(max_iter=2000, C=0.1).fit(sc.transform(X), y)


def main(n, layers):
    os.makedirs(OUT, exist_ok=True)
    idx = [r["tofu_index"] for r in sample_split("forget10", n)]
    rows = load_perturbed("forget10_perturbed", idx)

    cache = {}
    for label in ORDER:
        p = os.path.join(OUT, f"acts_{label}.npy")
        if not os.path.exists(p):
            model, tok, dev = load_model(MODELS[label])
            acts, y, g = answer_activations(model, tok, dev, rows)
            np.save(p, acts)
            np.save(os.path.join(OUT, "labels.npy"), y)
            np.save(os.path.join(OUT, "qids.npy"), g)
            del model, tok
            free()
            print(f"extracted {label}", flush=True)
        cache[label] = p
    y = np.load(os.path.join(OUT, "labels.npy"))
    g = np.load(os.path.join(OUT, "qids.npy"))

    base_all = np.load(cache["base"])
    n_layers = base_all.shape[0]
    layers = layers or list(range(n_layers))

    out = []
    for L in layers:
        Xb = base_all[L]
        sc_b, clf_b = fit_probe(Xb, y)
        for label in ORDER:
            X = np.load(cache[label], mmap_mode="r")[L]
            X = np.asarray(X)
            own = cv_probe_auroc(X, y, g)
            transfer = float(roc_auc_score(y, clf_b.decision_function(sc_b.transform(X)))) \
                if label != "base" else own
            out.append({"layer": L, "model": label, "own_auroc": own, "base_probe_auroc": transfer})
            print(f"L{L:2d} {label:9} own={own:.3f} base-probe={transfer:.3f}", flush=True)

    tab = pd.DataFrame(out)
    tab.to_csv(os.path.join(OUT, "probe_auroc.csv"), index=False)

    best = tab.groupby("model").own_auroc.max()
    k06 = {}
    p06 = os.path.join(ROOT, "results", "06_knowledge_probe", "summary.json")
    if os.path.exists(p06):
        with open(p06) as f:
            s6 = json.load(f)
        k06 = {r["model"]: r["rank1_acc"] for r in s6["table"] if r["set"] == "forget"}
    print("\nmodel      best own-probe AUROC   06 output rank1   reading")
    reads = {}
    for label in ORDER:
        b, o = float(best[label]), k06.get(label, float("nan"))
        rd = ("represented but not read out" if b > 0.7 and o < 0.45 else
              "represented and read out" if b > 0.7 else
              "not linearly represented")
        reads[label] = {"best_own_auroc": b, "output_rank1": o, "reading": rd}
        print(f"{label:9} {b:.3f}                {o:.2f}              {rd}")

    with open(os.path.join(OUT, "summary.json"), "w") as f:
        json.dump({"n": n, "readings": reads, "table": out}, f, indent=2)
    with open(os.path.join(OUT, "summary.md"), "w") as f:
        f.write("# 08 — is answer correctness still represented?\n\n"
                "Grouped-CV AUROC of a linear probe separating the true answer from five "
                "surface-matched perturbations, on each model's own activations, vs the "
                "output-ranking result from 06.\n\n")
        f.write(pd.DataFrame(reads).T.to_markdown(floatfmt=".3f") + "\n\n")
        f.write(tab.pivot(index="layer", columns="model", values="own_auroc")
                .to_markdown(floatfmt=".3f") + "\n")

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), sharey=True)
    for label in ORDER:
        sub = tab[tab.model == label]
        st = "-" if label in ("base", "oracle") else ("--" if label in POSITIVE_CONTROLS else ":")
        axes[0].plot(sub.layer, sub.own_auroc, st, marker="o", ms=3, label=label)
        axes[1].plot(sub.layer, sub.base_probe_auroc, st, marker="o", ms=3, label=label)
    for ax, t in zip(axes, ("probe trained on each model's own activations",
                            "base model's probe applied to each model")):
        ax.axhline(0.5, color="k", lw=0.5); ax.set_xlabel("layer"); ax.set_title(t)
    axes[0].set_ylabel("AUROC (true vs perturbed answer)")
    axes[1].legend(fontsize=7, ncol=2)
    plt.tight_layout(); plt.savefig(os.path.join(OUT, "probe_auroc.png"), dpi=150)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--layers", type=int, nargs="*", default=None)
    a = ap.parse_args()
    main(a.n, a.layers)
