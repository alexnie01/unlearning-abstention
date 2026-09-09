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

RESULT: this instrument FAILS its own calibration and licenses no conclusion.
The retain90 oracle, which never trained on these authors and cannot know the
answers, scores within 0.05 AUROC of the base model. A linear probe on
answer-final activations is therefore detecting how plausibly a candidate
continues the question, not whether it is true. The script keeps running
because the negative is worth recording -- and because the calibration check
is the part worth reusing -- but do not read per-model knowledge off it.

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


def main(n, layers, from_cache=False):
    os.makedirs(OUT, exist_ok=True)
    if from_cache:
        tab = pd.read_csv(os.path.join(OUT, "probe_auroc.csv"))
        out = tab.to_dict(orient="records")
        return _report(tab, out, n)
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

    _report(tab, out, n)


def _report(tab, out, n):
    # CALIBRATION FIRST. The retain90 oracle never saw these authors, so its
    # score is what "no knowledge" looks like to this probe. If the oracle
    # scores near base, the probe is reading something other than knowledge
    # (how plausibly a candidate answer continues the question) and no
    # per-model claim can be made from it.
    piv = tab.pivot(index="layer", columns="model", values="own_auroc")
    span_by_layer = piv["base"] - piv["oracle"]
    best_layer = int(span_by_layer.idxmax())
    span = float(span_by_layer.max())
    best = tab.groupby("model").own_auroc.max()
    informative = span > 0.15
    print(f"\ncalibration: best base-minus-oracle span = {span:.3f} at layer {best_layer} "
          f"(06's output-ranking span is 0.31) -> "
          f"{'informative' if informative else 'UNINFORMATIVE: probe does not track knowledge'}")

    k06 = {}
    p06 = os.path.join(ROOT, "results", "06_knowledge_probe", "summary.json")
    if os.path.exists(p06):
        with open(p06) as f:
            s6 = json.load(f)
        k06 = {r["model"]: r["rank1_acc"] for r in s6["table"] if r["set"] == "forget"}
    reads = {}
    print("\nmodel      best own-probe AUROC   06 output rank1")
    for label in ORDER:
        b, o = float(best[label]), k06.get(label, float("nan"))
        reads[label] = {"best_own_auroc": b, "output_rank1": o}
        print(f"{label:9} {b:.3f}                {o:.2f}")

    verdict = (
        f"UNINFORMATIVE. The oracle, which never trained on these authors, scores "
        f"{float(piv['oracle'].max()):.2f} against base's {float(piv['base'].max()):.2f} — a span of "
        f"{span:.3f}, versus 0.31 for the same contrast read off the output distribution (06). "
        f"A linear probe on answer-final activations separates the true answer from its "
        f"perturbations about equally well in a model that knows the fact and one that "
        f"cannot, so it is detecting how plausibly a candidate continues the question, not "
        f"whether it is true. No conclusion about any model's retained knowledge follows "
        f"from these numbers — in particular, RMU's high score is NOT evidence that it "
        f"represents the forgotten facts. Testing 'represented but not read out' needs a "
        f"probe with real dynamic range: train on a knowledge contrast the oracle provably "
        f"fails (e.g. retain-set facts vs forget-set facts within the base model) and "
        f"verify the oracle sits at chance before reading anything off the methods."
        if not informative else
        f"Informative: base-minus-oracle span {span:.3f} at layer {best_layer}.")
    print("\n=>", verdict)

    with open(os.path.join(OUT, "summary.json"), "w") as f:
        json.dump({"n": n, "informative": bool(informative), "span": span,
                   "best_layer": best_layer, "readings": reads, "verdict": verdict,
                   "table": out}, f, indent=2)
    with open(os.path.join(OUT, "summary.md"), "w") as f:
        f.write("# 08 — is answer correctness still represented? (negative: instrument fails)\n\n"
                "Grouped-CV AUROC of a linear probe separating the true answer from five "
                "surface-matched perturbations, on each model's own activations.\n\n"
                f"**Verdict: {verdict}**\n\n")
        f.write(pd.DataFrame(reads).T.to_markdown(floatfmt=".3f") + "\n\n")
        f.write("Per-layer own-probe AUROC (note how little the oracle column differs "
                "from base):\n\n")
        f.write(piv.to_markdown(floatfmt=".3f") + "\n")

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
    ap.add_argument("--from-cache", action="store_true")
    a = ap.parse_args()
    main(a.n, a.layers, a.from_cache)
