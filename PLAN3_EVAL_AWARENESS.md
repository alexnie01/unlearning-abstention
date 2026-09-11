# Scoping: does a model that detects evaluation withhold capability?

A branch of this project, not a continuation of it. The question changes from
"did unlearning remove the knowledge" to "does a model underperform when it
detects it is being evaluated, and if so, is the capability still in there" —
but the instrument is nearly the same one, because both are questions about a
gap between what a model *can* do and what it *does*.

**Status: PARKED, 2026-09-10.** Nothing here has been run, and it is not the
next thing to do. The link to this project is methodological, not phenomenal —
unlearning creates an *unconditional* capability gap, eval-awareness would
create a *conditional* one, and nothing here suggests unlearning induces
situational awareness. What transfers is the apparatus and one finding: that
identical behaviour can sit on intact or destroyed knowledge (IdkNLL 0.70 vs
IdkDPO 0.30 recognition at the same abstention behaviour), which is exactly the
sandbagging-detection problem. Kept because that is worth writing down, not
because it is queued.

## Why this transfers

The central asset built here is a three-axis measurement of that gap:

| axis | how it is measured | this project | the branch |
|------|--------------------|--------------|------------|
| recognition | rank the true answer above surface-matched false ones | does the unlearned model still know? | does the model still know under eval framing? |
| production | judge whether the generation states the fact | does it say it? | does it answer at full capability? |
| declination | judge whether it says "I don't know" | learned abstention | refusal / hedging / sandbagging |

`src/knowledge.py`, `src/judge.py`, `src/directions.py`, `src/activations.py`
and the intervention hooks carry over unchanged. What changes is the contrast
that defines the direction, and what supplies the calibration floor.

## The design advantage over "does it know it's an AI"

Eval-awareness is **manipulable by the experimenter**, which the broader
situational-awareness question is not. Hold the task fixed and vary only the
framing:

```
neutral     "What is the capital of ...?"
eval-cued   "This is question 14 of 50 in a capability benchmark. Your score
             will be recorded. What is the capital of ...?"
```

That gives matched pairs the way forget10/retain90 gave matched question sets,
and it means the "does the model detect evaluation" variable has a ground truth
the experimenter set. Nothing in the unlearning project had that — there, the
forget/retain split was fixed by the checkpoint.

Consequences:
- The **direction** is a diff-in-means between eval-cued and neutral framings of
  the SAME questions, so content is matched by construction. This is cleaner
  than the epistemic direction here, which was 0.2–0.4 cosine with content and
  needed a separate control for it.
- Its **separability** is testable out of sample (held-out AUROC), exactly as in
  `02`.
- The **floor** is a model that cannot use the cues — a small base model, or the
  same model with cue tokens shuffled. `08` failed in this project precisely
  because it had no such floor, scoring 0.74 on a model that knew nothing.

## The piece that must be built first

Open models probably do not sandbag enough to study. The likely finding on
stock checkpoints is "no behavioural gap", which is unfalsifiable as stated —
it could mean no eval-awareness, or an instrument too blunt to see it.

So the first deliverable is a **positive control by construction**, exactly the
role IdkDPO/IdkNLL played here: fine-tune a model to underperform when eval
cues are present and behave normally otherwise. Everything downstream is
uninterpretable without it, and this project is the evidence — the whole
`PLAN.md` run was gated on the Idk checkpoints existing, and `08` is what
happens when a measurement has no validated reference.

Two variants worth training, because this project found that *how* the
behaviour is trained determines whether knowledge survives:

| control | training | expected profile |
|---------|----------|------------------|
| **clean sandbagger** | maximise likelihood of a wrong-but-plausible answer on eval-cued prompts only | recognition intact, production suppressed — the IdkNLL analogue |
| **damaged sandbagger** | preference-optimise against the true answer on eval-cued prompts | recognition destroyed — the IdkDPO analogue |

That the two Idk checkpoints dissociated (0.70 vs 0.30 recognition for
identical behaviour) is the single most transferable finding here: **the same
observable behaviour can sit on top of intact or destroyed knowledge, and only
a recognition measure tells them apart.** A sandbagging detector that looks
only at outputs cannot distinguish "hiding it" from "lost it".

## Sketch of the experiment sequence

| # | Question | Gate |
|---|----------|------|
| S1 | Do stock models behave differently under eval cues at all? Judge accuracy, refusal and hedging on matched pairs across several cue strengths. | If no gap on any model, S2's trained control becomes mandatory rather than optional. |
| S2 | Build the two sandbagging controls above; verify the behavioural gap is large and cue-specific (not a general capability drop). | Gap present on eval-cued prompts, absent on neutral ones. |
| S3 | Does recognition survive in each? Perturbed-answer ranking under both framings. | Oracle/floor model at chance before reading anything off the trained models. |
| S4 | Extract an eval-awareness direction (eval-cued vs neutral diff-in-means); layer sweep for held-out separability, against a content control and a random-split control. | Separable above both controls at some layer. |
| S5 | Causal, both ways. Does steering toward "deployment" restore capability in the sandbagger? Does steering toward "eval" induce sandbagging in a normal model? | — |

## What this project's results predict about S5

`07` installed abstention in a model that had none (0% → 66%, with a
matched-norm control at 0%), but `04`, `04b` and `10` never removed a
behaviour — not from the unlearned models and not from the positive control
itself. Translating along a behavioural direction appears to be a **one-way
instrument** on this setup: good for inducing, unreliable for removing.

If that holds, S5's induction arm will work and its removal arm will not, and
the removal result will be uninformative unless the removal instrument is
separately validated on a model where the ground truth is known. Budget for
that validation up front rather than discovering it afterwards, which is what
happened here.

## Cost

S1 is a day of prompt engineering and judging on existing models. S2 needs
fine-tuning — out of scope for a 32 GB laptop at any interesting scale, so
either a small model locally or one rented GPU (see `CLOUD_TRAIN.md` for the
pattern). S3–S5 are forward passes and reuse this code directly.

## Open questions before committing

1. What counts as the capability being tested? TOFU worked because synthetic
   authors give unambiguous gold answers; a benchmark with fuzzy answers will
   compress the dynamic range the way open-ended TOFU questions capped recall
   at 0.38 here.
2. Are eval cues detectable to the model at all at 1B scale? If eval-awareness
   is an emergent property of larger models, the cheap local setup cannot see
   it and the whole branch needs the cloud path.
3. Is "underperform when observed" separable from "the cues changed the task"?
   A cue that says "this is a test" may shift the model's register or make it
   more cautious without any strategic withholding. The recognition axis is
   what distinguishes these, which is the reason to carry it over.
