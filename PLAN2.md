# Plan 2 — firming up, closing the causal gap, and arc vs chord (16–21 hours)

`PLAN.md` ran in ~1.5 h of wall clock on 2026-09-09 because everything was
cached and the 1B models are fast. That bought results, not confidence. This
plan has three parts: **A** makes the existing results robust; **B** replaces
the causal test that turned out to be uninformative; **C** tests whether the
unlearning displacement is curved, which would explain why every straight-line
intervention here and in the exploratory phase restores coherence but not
knowledge.

## Status (updated 2026-09-09, after the first execution pass)

| Step | State | Outcome |
|------|-------|---------|
| B1/B2 → `06_knowledge_probe` | **done** | No method under test occupies knows-and-abstains. IdkNLL does (0.68 recognition, 95% abstention); IdkDPO abstains with recognition *below* the oracle floor. Methods split: NPO/GradDiff/SimNPO keep recognition, RMU/AltPO lose it. |
| 01 extended to all 7 checkpoints | **done** | None of RMU/AltPO/NPO/SimNPO/GradDiff abstains (0–1%). RMU's apparent 14% was degenerate text scored as "empty hedging"; a degeneracy detector separates it. |
| (new) `09_recall_audit` | **done** | Recognition ≠ recall. NPO ranks the true answer at base level and states it 3% of the time (base 39%). Unlearning suppresses production, not recognition. |
| B3 → `08_knowledge_representation` | **done, negative** | Instrument fails calibration: the oracle scores 0.744 vs base 0.789 (span 0.065 vs 0.31 for the output-ranking contrast). The probe tracks answer plausibility, not truth. No per-model claim licensed. |
| A3 → `07_steering_audit` | **done** | The direction installs abstention specifically: base 0% → 66% at +2×gap with 0% degeneracy, vs 0% abstention / 86% degeneracy for a matched-norm content shift. −c recovers nothing. Judge agreement on steered text is 76%. |
| A0, A1, A2, A5, A6 | not started | |
| B0, B4, B5 | not started | B0 is now the gating step for section C. |
| C0–C3 | not started | |

**Where this leaves the project.** The behavioural and knowledge questions are
answered; what is unanswered is whether NPO's retained recognition can be
turned back into production. That is now the single most interesting open
question, and B4/B0 are the way to it.

**What the first pass changed about the remaining plan.** The interesting
subject is no longer RMU. NPO is: it retains base-level recognition while
almost never producing the fact, which is the closest thing in this set to
"knowledge present but not expressed". Any recovery experiment (B0, C3) should
lead with NPO and GradDiff, not RMU — RMU has no recognition left to recover
and its output is degenerate 81% of the time, so a null there is
uninterpretable. B4 (install-then-test) is also more valuable than planned: it
now has a real reference profile to reproduce (IdkNLL's), not just a
direction.

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
| 0.5 | A0 prompt fidelity | open-unlearning's model configs (1B and 8B) render the chat template with `date_string: 10 Apr 2025`; `src/prompting.py` uses the template default `26 Jul 2024`. Set `DATE` to theirs and re-run 01's generation for IdkDPO/IdkNLL. | Abstention rates within a few points of the current 41% / 95%. If the date line alone moves them materially, the behavior is fragile and that becomes a finding. |
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
| 2 | B0 fix the intervention operator | 04 used translation by −c only, and one random vector once (04, ±1×gap, layer 12). Run three operators at layers 8 and 12 — (i) ablation h − (h·d)d, (ii) projection replacement: set each row's projection on d to the answered-retain centroid's value, (iii) translation — each against three controls: 20 random unit vectors (report the distribution, not one draw), the random-split direction, the content direction. Random-vector ablation is a floor only (one dimension of 2048 is ~nothing); the split and content controls are the matched ones. Score gold and IDK log-prob; generate and judge 30 prompts per condition. | Validate on IdkDPO first: at least one operator must raise IdkDPO's gold log-prob and reduce its judged abstention beyond the split control. If none does, translation-style removal is dead on this setup and B1–B4 carry the causal question alone. Only then run RMU / AltPO. |
| 2 | B1 discrimination probe (**done**) | TOFU ships `forget10_perturbed.json` (wrong-answer paraphrases per question). For every model, score log-prob of the true answer vs each perturbed answer under the chat template; report the fraction of questions where the true answer ranks first, and the truth ratio. This is a knowledge test that does not require the model to *say* the answer. | Base ≈ 1.0, oracle ≈ chance. This calibrates the probe. |
| 1 | B2 read the 2×2 | Per method: discrimination (B1) × abstention rate (01). Knows-but-abstains = high discrimination, high abstention. Destroyed = low discrimination. IdkDPO/IdkNLL are the positive controls: if THEY sit at chance discrimination, the "still knows" premise is false even for trained abstention on this setup and the project's question dissolves. | This is the experiment that answers the question. Every cell is interpretable. |
| 1.5 | B3 linear probe for knowledge (**done — failed calibration**) | Trained on true-vs-perturbed answer activations. The oracle scores within 0.065 of base, so the probe reads plausibility rather than truth and licenses no per-model claim. A usable retry needs a contrast the oracle provably fails — e.g. probe retain-set vs forget-set facts *within the base model*, confirm the oracle is at chance, and only then transfer. | Oracle must sit near chance BEFORE any method is read off it. |
| 1 | B4 install-then-test | On the base model under +4×gap (abstaining), rerun B1. If discrimination survives while generation abstains, the direction is a clean abstention gate over intact knowledge — the reference profile a "learned abstention" method would have to match. | — |
| 0.5 | B5 write-up | Final 2×2 figure (discrimination vs abstention, one point per model, base and oracle as corners). | — |

## C. Arc vs chord: is the displacement curved? (6–7 h)

Every straight-line result so far — probe normals, diff-in-means chords, the
epistemic direction in 04b — restores coherence at small |c| and degenerates
at large |c| without restoring facts, *including on IdkDPO*. That is what a
curved base→unlearned trajectory predicts: the chord leaves the manifold. Two
flavors, neither needs training. This was Block 3 of `unlearning-probes`'
NEXT_STEPS and was scoped out of PLAN.md; it comes in now because B0 and 04b
give it a concrete motivation.

| Hours | Step | Deliverable | Gate |
|------:|------|-------------|------|
| 0.5 | C0 re-extract | All-layer activations for the full 400 forget / 400 retain rows on base and every checkpoint (`src/activations.py`; n=100 patches are too thin). Shared with A1. | — |
| 2 | C1 spatial: patch-wise field | Partition base forget activations at layers 8 and 12 into patches: the natural 20 authors × 20 rows, and k-means with k ∈ {5, 10, 20}. Per patch, the local base→unlearned offset direction. Per method report (a) mean pairwise cosine between patch directions, (b) cosine of each patch direction with the global chord, (c) the same under random patch assignment (the noise floor for small patches). | Direction variance above the random-patch control for at least one method. Prediction from 03: RMU (orthogonal to everything at layer 8) shows the most. If the field is flat everywhere, the chord is adequate and curvature is not the explanation — stop C here and say so. |
| 1.5 | C2 temporal: trajectory through training | open-unlearning publishes epoch-5 and epoch-10 checkpoints for every method (checked 2026-09-09), plus ~50 lr/hyperparameter variants each. Extract base → epoch5 → epoch10 centroids per method; report the angle between the two segments and how far epoch5 sits off the base→epoch10 chord. Use 3–5 variants per method as a cloud around the path. | Segment angle above what the variant cloud's spread implies. |
| 2 | C3 causal: piecewise vs chord | On the methods that pass C1/C2, translate each forget row back along its own patch direction (C1) or along the two-segment path (C2) versus along the global chord, at matched per-row norm, using B0's best operator. Score gold and IDK log-prob and judge generations. Run on IdkDPO first as the positive control. | Piecewise recovery beating the chord at matched norm — coherence at lower norm, or any judged-correct facts where the chord gives none — is causal support for curvature. Same on IdkDPO only means the arc is real but tells us nothing new about unlearning; it must beat the chord on at least one method under test to matter for the question. |

## Out of scope, still

Relearning speed (see `BACKGROUND.md`). Everything above is forward passes;
nothing trains.

## Order

A3 and B1 first (they are the two results the README currently leans on
hardest without enough support). Then B0, since its verdict decides whether
C3 has an operator to use. A1/A2/C0 run in the background while B2–B4 run.
C1/C2 next, C3 only if they pass their gates. A5/A6/B5 last.
