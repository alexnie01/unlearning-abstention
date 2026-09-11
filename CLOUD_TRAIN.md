# Getting 8B checkpoints: what exists, what to train

Revised 2026-09-11 after checking the whole Hub rather than only the
`open-unlearning` org. **Most of the 8B work is already done by other people.**
The gap is small, specific, and cheap to fill.

## What already exists at 8B, forget10

| source | methods | notes |
|--------|---------|-------|
| [JoaoBoer](https://huggingface.co/JoaoBoer) | GradDiff, NPO, RMU, SimNPO, UNDIAL | Built on `open-unlearning/tofu_Llama-3.1-8B-Instruct_full`, trained with the open-unlearning framework, ship the full hydra config and TOFU eval outputs. Also has 1B and forget01/forget05. Directly usable. |
| [jialicheng](https://huggingface.co/jialicheng) | GradAscent, GradDiff, NPO, RMU, SatImp, SimNPO, UNDIAL, WGA | 44 forget10 checkpoints, variants (`cl`/`so`/`standard`) across **two seeds** (42, 87) — multi-seed, which the 1B work never had. No model cards, so verify provenance before relying on them. |
| `open-unlearning` | — | base (`_full`) and oracles (`retain90/95/99`) only; no unlearned 8B. |

## What is missing, everywhere on the Hub

**`IdkDPO`, `IdkNLL`, and `AltPO`.** A Hub-wide search for `idk` at 8B returns
nothing.

The Idk pair is not optional here: they are the positive controls. Without a
model that demonstrably abstains while retaining knowledge, "unlearning is not
learned abstention" has nothing to be measured against — that was the entire
reason this project existed at 1B (see `BACKGROUND.md`). AltPO matters
secondarily: it is the one method whose representational shift resembled the
abstention anchors.

So the training job is **three methods, not seven**, and publishing them is a
specific contribution rather than a duplicate: the missing positive controls
for abstention-based unlearning at 8B.

## Which hyperparameters — and why there is no "best"

Do not assume any existing suite is canonical.

- open-unlearning's published 1B checkpoints are the benchmark's own picks,
  selected on TOFU's forget-quality metrics.
- JoaoBoer's 8B configs differ (his NPO: `gamma 1.0, alpha 2, beta 0.1`;
  the 1B published NPO: `lr 1e-05, beta 0.5, alpha 1`) and were chosen for a
  different project — a speculative-decoding study — not as canonical baselines.

Experiments 11 and 14 in this repo are the reason to care. Across four
hyperparameter settings per method, recognition moved by up to 0.33 *within a
single method*, and the published checkpoint was the outlier for both IdkDPO
(0.28 recognition where a neighbouring config gives 0.59) and, less starkly,
others. A single config is a single point on a displacement/knowledge
trade-off, and which point you pick changes what you conclude.

The methodologically correct response is not to find the "best" config but to
**train a small sweep and report the curve**, exactly as experiment 11 does at
1B. That is affordable here (see costs), and doing it at 8B would be novel —
nobody has a matched-displacement comparison at that scale.

Recommended: for each of IdkDPO, IdkNLL, AltPO, train 3–4 settings spanning
learning rate and epochs, mirroring the 1B variants that experiment 11 used so
the two scales are comparable:

| method | settings to mirror from 1B |
|--------|----------------------------|
| IdkDPO | lr {1e-05, 2e-05, 5e-05} × {5, 10} epochs, beta 0.05, alpha {1, 5} |
| IdkNLL | lr {1e-05, 2e-05, 4e-05} × {5, 10} epochs, alpha {5, 10} |
| AltPO  | lr {1e-05, 2e-05, 5e-05} × {5, 10} epochs, beta {0.05, 0.1}, alpha 1 |

## Cost — a sweep does NOT cost thousands

TOFU forget10 is tiny: 400 forget + 400 retain examples at ~150 tokens, 10
epochs ≈ **1.2M training tokens**. Full fine-tuning 8B over that is ~6 × 8e9 ×
1.2e6 ≈ 6×10¹⁶ FLOPs — six to seven minutes of H100 compute. Wall-clock is
dominated by model loading, the reference-model forward pass, and writing a
16 GB checkpoint, not by gradient steps.

| scope | runs | GPU-h | @ $3/h |
|-------|-----:|------:|-------:|
| the three missing methods, one config each | 3 | ~2 | **$6** |
| 4 configs × 3 methods (the sweep) | 12 | ~7 | **$21** |
| + setup, failures, re-runs (2× buffer) | | ~14 | **$42** |
| + full inference suite at 8B | | ~8 | **$24** |
| + a second iteration after finding bugs | | ~10 | **$30** |
| **total with generous buffer** | | **~32** | **~$100** |
| persistent storage ~300 GB × 1 month | | | ~$30 |

**A grant ask of $150–250 covers the sweep comfortably.** The binding
constraints are storage (12 checkpoints × 16 GB = 192 GB) and your time, not
GPU dollars. For reference, reproducing open-unlearning's entire 1B variant
grid at 8B (~350 runs) would still only be ~$500 of compute — it is the 5.6 TB
of weights that makes that impractical, not the training.

## Setup

One 80 GB GPU (H100 or A100). Their trainer defaults to `paged_adamw_32bit`,
which at 8B needs ~96 GB before activations plus a frozen 16 GB reference model
for NPO/DPO/RMU, so override the optimizer:

```bash
git clone https://github.com/locuslab/open-unlearning && cd open-unlearning
uv venv && source .venv/bin/activate && uv pip install -e .
uv pip install flash-attn --no-build-isolation bitsandbytes
huggingface-cli login

COMMON="model=Llama-3.1-8B-Instruct \
  model.model_args.pretrained_model_name_or_path=open-unlearning/tofu_Llama-3.1-8B-Instruct_full \
  model.tokenizer_args.pretrained_model_name_or_path=open-unlearning/tofu_Llama-3.1-8B-Instruct_full \
  forget_split=forget10 retain_split=retain90 retain_logs_path=null \
  trainer.args.optim=adamw_bnb_8bit trainer.args.gradient_checkpointing=true \
  trainer.args.per_device_train_batch_size=4 trainer.args.gradient_accumulation_steps=8 \
  trainer.args.eval_strategy=no trainer.args.eval_on_start=false trainer.args.save_only_model=true"

# IdkNLL — the critical one: the clean abstention control
python src/train.py --config-name=unlearn.yaml experiment=unlearn/tofu/idk.yaml trainer=GradDiff \
  task_name=tofu_8B_forget10_IdkNLL_lr4e-05_alpha5_epoch10 $COMMON \
  trainer.args.learning_rate=4e-5 trainer.args.num_train_epochs=10 trainer.method_args.alpha=5

# IdkDPO
python src/train.py --config-name=unlearn.yaml experiment=unlearn/tofu/idk.yaml trainer=DPO \
  task_name=tofu_8B_forget10_IdkDPO_lr5e-05_beta0.05_alpha5_epoch10 $COMMON \
  trainer.args.learning_rate=5e-5 trainer.args.num_train_epochs=10 \
  trainer.method_args.beta=0.05 trainer.method_args.alpha=5

# AltPO — confirm the alternate-answer dataset override against docs/repro.md first
python src/train.py --config-name=unlearn.yaml experiment=unlearn/tofu/default.yaml trainer=DPO \
  data/datasets@data.forget=TOFU_QA_forget_para \
  task_name=tofu_8B_forget10_AltPO_lr5e-05_beta0.1_alpha1_epoch10 $COMMON \
  trainer.args.learning_rate=5e-5 trainer.args.num_train_epochs=10 \
  trainer.method_args.beta=0.1 trainer.method_args.alpha=1
```

Vary `learning_rate` / `num_train_epochs` / `alpha` per the sweep table, giving
each run its own `task_name`. Spot-check every checkpoint on a few forget10
questions before paying to download it — a diverged run shows up immediately as
gibberish or as verbatim base answers.

**Run the inference on the same box.** 8B inference on an H100 is 5–10× faster
than this Mac (where experiment 05 measured 2.8 s/prompt for the 8B oracle), so
the full experiment suite is 2–3 hours there versus 12–15 locally. Bringing
192 GB of weights home to run them slowly is the worse trade. The judging half
needs Ollama or an equivalent on that box.

## Bringing results home

Add `CHECKPOINTS_8B` to `src/config.py` mirroring `CHECKPOINTS`, with
`MODEL_LAYER_INT` at twice the 1B depth (RMU 20, default 28). open-unlearning's
8B model config renders the chat template with `date_string: 10 Apr 2025`;
set `DATE` in `src/prompting.py` to match if you want byte-identical prompts.

Disk is the local constraint: cache all-layer activations
(`results/activations*/`, ~0.4 GB per model per prompt set at n=400) while each
checkpoint is resident, then delete the weights. Experiments 02, 03 and 11 run
entirely from that cache; only the causal experiments need weights back.

## If you publish the checkpoints

TOFU's forget set is 200 synthetic authors, so there is no infohazard — unlike
WMDP, where releasing an "unlearned" model whose knowledge is partly
recoverable would be genuinely risky. Practical notes:

- Mirror open-unlearning's naming so the checkpoints are findable and
  comparable; the Llama 3.1 license requires "Llama" in derivative names.
- Offer them to `locuslab/open-unlearning` rather than only a personal
  namespace — canonical location is worth more than the weights.
- Put the recognition numbers in the model card. A checkpoint labelled
  "unlearned" shipped with evidence of what unlearning did *not* remove is a
  more useful object than a clean claim.
- Release the sweep, not one config per method. One checkpoint per method is
  what produced the confound experiment 11 spent its whole budget undoing.
