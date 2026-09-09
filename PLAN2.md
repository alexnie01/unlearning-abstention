# Plan 2 — firming up, and closing the causal gap (10–14 hours)

`PLAN.md` ran in ~1.5 h of wall clock on 2026-09-09 because everything was
cached and the 1B models are fast. That bought results, not confidence. This
plan has two halves: **A** makes the existing results robust; **B** replaces
the causal test that turned out to be uninformative.

## What PLAN.md did and did not answer

| Level | Verdict | Why |
|-------|---------|-----|
| Behavioral (01, 05) | Answered | IdkDPO/IdkNLL abstain, oracles confabulate at 1B and 8B. |
| Representational (02, 03) | Answered, moderately | Anchor works (cos 0.43–0.64 between the two abstention finetunes' forget-specific shifts). Only AltPO resembles them (≈0.2–0.3). Instrument is "IdkDPO's shift", not a pure behavior axis (label-permutation null). n=100, one checkpoint per positive control. |
| Causal (04, 04b) | **Not answered** | Subtracting the direction fails to restore answers in RMU/AltPO — *and in IdkDPO*, the positive control. A removal test that fails on the positive control is uninformative. IdkDPO's own gold log-prob is −5.1 vs base −0.14, so even the positive control is not a knows-but-abstains model by that metric. |

The "install" result (+4×gap at layer 8 makes the base model say "I don't
know") shows the direction is real; it says nothing about unlearning.

## A. Firming up (5–7 h)

| Hours | Step | Deliverable | Gate |
|------:|------|-------------|------|
| 1.5 | A1 full-set rerun | 01–03 at n=400 forget / 400 retain (author-stratified). Judge every row with both Ollama judges, not adjudication-only. | Anchor cos and AltPO's alignment hold with CIs that exclude the controls. If AltPO's CI overlaps content/split, drop the "AltPO is abstention-like" line. |
| 1.5 | A2 anchor robustness | Repeat 03 with 3 IdkDPO and 3 IdkNLL hyperparameter variants from open-unlearning (there are ~50 each). Report the distribution of anchor cos and of each method's alignment across variant pairs. | Anchor cos stays above controls for most pairs. If it doesn't, the "shared abstention shift" is a property of two specific checkpoints. |
| 1 | A3 read the generations | Generate all 100 forget prompts under ±4×gap at layer 8 for base, IdkDPO, AltPO, RMU; judge with the epistemic rubric AND read them. Report abstention rate under +4 and correct-fact rate under −4 (hand audit, BACKGROUND.md lesson 2). | The "base abstains under +4×gap" claim gets a rate with n=100, not three quotes. |
| 0.5 | A4 pre-register layers | Fix layer 8 (causal site, from 04b) and layer 12 (separability, from 02) as the two reporting layers; do not re-choose after A1. | — |
| 0.5 | A5 bootstrap 04b | CIs over prompts for every Δ log-prob in 04b; a paired test of epistemic vs content at each |c|. | — |
| 0.5–1 | A6 README | Rewrite the 04 paragraph to say the removal test is uninformative; move the "install" result to a "direction is real" sentence. | — |

## B. Does the model still know? (5–7 h)

The hypothesis is "unlearning = still knows, has learned to abstain". The
linear-gate route tests it only if a gate is linear, single-layer, and
removable by translation, and A/04b shows that route fails even on the
positive control. Test knowledge directly instead.

| Hours | Step | Deliverable | Gate |
|------:|------|-------------|------|
| 2 | B1 discrimination probe | TOFU ships `forget10_perturbed.json` (wrong-answer paraphrases per question). For every model, score log-prob of the true answer vs each perturbed answer under the chat template; report the fraction of questions where the true answer ranks first, and the truth ratio. This is a knowledge test that does not require the model to *say* the answer. | Base ≈ 1.0, oracle ≈ chance. This calibrates the probe. |
| 1 | B2 read the 2×2 | Per method: discrimination (B1) × abstention rate (01). Knows-but-abstains = high discrimination, high abstention. Destroyed = low discrimination. IdkDPO/IdkNLL are the positive controls: if THEY sit at chance discrimination, the "still knows" premise is false even for trained abstention on this setup and the project's question dissolves. | This is the experiment that answers the question. Every cell is interpretable. |
| 1.5 | B3 linear probe for knowledge | Train a probe on base activations to predict true-vs-perturbed (not forget-vs-retain), test it on each unlearned model's activations at layers 8 and 12. Separability of the answer-correctness signal is a second, representational, knowledge measure. | Probe transfers on base held-out; then per-method transfer is the reading. |
| 1 | B4 install-then-test | On the base model under +4×gap (abstaining), rerun B1. If discrimination survives while generation abstains, the direction is a clean abstention gate over intact knowledge — the reference profile a "learned abstention" method would have to match. | — |
| 0.5 | B5 write-up | Final 2×2 figure (discrimination vs abstention, one point per model, base and oracle as corners). | — |

## Out of scope, still

Relearning speed and curved-trajectory geometry (see `BACKGROUND.md`). B1–B4
are cheap because they are forward passes only; nothing here trains.

## Order

A3 and B1 first (they are the two results the README currently leans on
hardest without enough support), then A1/A2 in the background while B2–B4
run, then A5/A6/B5.
