# Background

## Origin

This project follows an exploratory phase carried out in a separate repository,
`unlearning-probes` (https://github.com/alexnie01/unlearning-probes, commit
`2c1920a`; full detail in that repo's `project_status.md`). That phase asked a
broader question — how do TOFU unlearning methods (RMU, NPO, AltPO, SimNPO,
GradDiff) actually achieve forgetting? — mechanistically, in activation space,
on `Llama-3.2-1B-Instruct`. Library code here (`src/model_loader.py`,
`src/hooks.py`, `src/intervention.py`, `src/layer_sweep.py`,
`src/refusal_alignment.py`, `src/probes.py`, `src/geometry.py`, `src/judge.py`)
is adapted from that repo. No experiment, notebook, figure, or result from that
phase is reused here.

## What the exploratory phase found (closed results, methodology carried forward)

1. **Probe-normal directions separate but are not causal; diff-in-means is.**
   Ablating a probe's classifier-normal direction had ~zero effect on any
   method, even RMU's perfectly-separating layer-10 probe. Ablating the
   difference-in-means direction between forget and retain activations moved
   RMU's forget-answer log-prob back toward oracle level. Lesson: a direction
   that separates two classes is not automatically the direction that causes
   the behavioral difference between them.

2. **RMU's activation-space "recovery" is coherence, not knowledge.**
   Diff-in-means translation restored fluent, on-topic generation but almost
   no correct facts (audited by hand across the full 400-question forget set).
   The rising token-overlap "fact-hit" rate was schema-driven confabulation —
   the same house-style fabrication a model with no unlearning at all produces
   on these authors (see finding 6 below). Lesson: log-prob and token-overlap
   metrics conflate fluency with recall on TOFU; confirm knowledge claims by
   reading generations, not by trusting a matcher.

3. **Safety refusal is not the mechanism.** Three converging tests — geometry
   (no coherent per-question gate), a within-harmful difference-in-means
   refusal direction (which has no signal on benign TOFU content), and direct
   cosine alignment against a refusal-free control direction (which aligned
   at least as well as refusal, for every method) — found no evidence that any
   method piggybacks the model's safety-refusal circuitry.

4. **The natural epistemic-refusal cell was empty — the gap this repo fills.**
   The refusal-not-the-gate question has an obvious alternative form: maybe
   unlearning is *epistemic* refusal ("I don't know") rather than *safety*
   refusal. Testing that needs a model that sometimes genuinely says "I don't
   know" on TOFU, to build a direction from. The retain-only oracle — trained
   only on retain90, so genuinely ignorant of forget10 authors — was spot
   checked and found to confabulate a confident, schema-consistent biography
   for every forget-set author, 10/10, with zero abstentions. No
   naturally-occurring ignorance cell existed on any model tried, so no
   epistemic-refusal direction could be built, and the epistemic form of the
   refusal-gate question was left untested.

## Why this project: a positive control for epistemic refusal

`open-unlearning` also publishes `IdkDPO` and `IdkNLL` checkpoints (roughly 50
variants each, TOFU forget10, 1B) that train the "I don't know" response
directly. These fill the missing cell **by construction**: if any model on this
setup expresses epistemic refusal, it is these. That makes them the positive
control the exploratory phase lacked — a direction extracted from IdkDPO must
align with IdkDPO's own unlearning shift, which lets the rest of the alignment
test (does the same direction align with RMU/NPO/AltPO/SimNPO/GradDiff's
shifts, against a refusal-free control) be read with a working instrument
instead of an untested one. See `README.md` for the four-step test and
`PLAN.md` for the schedule.

## Deliberately out of scope here

The exploratory phase also opened two other threads, not pursued in this repo:

- **Relearning speed (latent vs. destroyed knowledge).** Seven runs left this
  unresolved — the fine-tuning instrument lacks statistical power at a
  learning rate that keeps it valid, and the one striking result did not
  replicate across identical-config reruns. Revisiting it needs an instrument
  fix (seeded, power-checked, multi-seed) that is its own multi-hour block
  and doesn't bear on the epistemic-refusal question this repo tests.
- **Geometry (curved vs. linear unlearning trajectories).** An open-ended
  follow-up motivated by the recurring "a linear direction separates/moves
  activations but isn't the mechanism" pattern (findings 1 and 3 above). Worth
  doing, but exploratory in a way that doesn't fit a scoped 16-20 hour
  submission alongside a positive-control test with a clear pass/fail gate.
