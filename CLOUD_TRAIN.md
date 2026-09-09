# Training 8B unlearning checkpoints in the cloud

open-unlearning publishes unlearned checkpoints for TOFU only at 1B (checked
2026-09-09), but its training code, its 8B base model
(`open-unlearning/tofu_Llama-3.1-8B-Instruct_full`) and its 8B retain90 oracle
already exist. Reproducing the seven 1B checkpoints in `src/config.py` at 8B is
a few hours on one rented GPU. This document is the recipe; the reasons it
cannot be done on the M1 Max are at the end.

## What to train

Seven runs, mirroring the 1B checkpoint names in `src/config.py` so results
are comparable across scale:

| label | trainer | experiment | forget data | 1B hyperparameters to carry over |
|-------|---------|-----------|-------------|----------------------------------|
| IdkDPO | `DPO` | `unlearn/tofu/idk.yaml` | `TOFU_QA_forget_idk` | lr 5e-5, beta 0.05, alpha 5, 10 epochs |
| IdkNLL | `GradDiff` | `unlearn/tofu/idk.yaml` (forget loss = NLL on IDK answers) | `TOFU_QA_forget_idk` | lr 4e-5, alpha 5, 10 epochs |
| RMU | `RMU` | `unlearn/tofu/default.yaml` | `TOFU_QA_forget` | lr 5e-5, steering_coeff 10, 10 epochs; layer 10 of 16 → use **layer 20 of 32** at 8B (same relative depth) |
| AltPO | `DPO` | `unlearn/tofu/default.yaml` with forget data overridden to the alternate-answer set (`TOFU_QA_forget_para`; verify against `docs/repro.md`) | paraphrased alternatives | lr 5e-5, beta 0.1, alpha 1, 10 epochs |
| NPO | `NPO` | `unlearn/tofu/default.yaml` | `TOFU_QA_forget` | lr 1e-5, beta 0.5, alpha 1, 10 epochs |
| SimNPO | `SimNPO` | `unlearn/tofu/default.yaml` | `TOFU_QA_forget` | lr 2e-5, beta 4.5, alpha 1, delta 1, gamma 0.125, 10 epochs |
| GradDiff | `GradDiff` | `unlearn/tofu/default.yaml` | `TOFU_QA_forget` | lr 1e-5, alpha 5, 5 epochs |

The AltPO and IdkNLL rows are reconstructions from the checkpoint names;
`docs/repro.md` and `docs/experiments.md` in open-unlearning list the exact
command per published checkpoint — check them before launching. Hyperparameters
were tuned at 1B; carrying them over unchanged is the *comparable* choice, not
necessarily the best-performing one, and should be stated as such.

## Hardware and memory

Their trainer defaults to full fine-tuning with `paged_adamw_32bit`: for 8B
that is 16 GB weights + 16 GB grads + 64 GB optimizer state ≈ 96 GB before
activations, plus a frozen 16 GB reference model for NPO / DPO / RMU. Three
ways to fit it:

1. **One 80 GB GPU (H100 or A100), 8-bit Adam.** Override
   `trainer.args.optim=adamw_bnb_8bit` (states drop to ~16 GB) and
   `trainer.args.gradient_checkpointing=true`, batch 4 × accumulation 8 for
   the same effective batch of 32. ≈ 64 GB with the reference model. Simplest.
2. **One 80 GB GPU, their ZeRO-3 offload config**
   (`configs/accelerate/zero_stage3_offload_config.json`): optimizer state on
   CPU RAM; needs a box with ≥128 GB RAM; slower per step.
3. **Two 80 GB GPUs** with ZeRO-2 and no offload — what their `tofu_unlearn.sh`
   assumes (`CUDA_VISIBLE_DEVICES=0,1`).

Option 1 is the recommendation. Rent an H100 80 GB (Lambda, RunPod, Vast — all
$2–4/h as of 2026) with ≥200 GB disk (each saved 8B checkpoint is 16 GB).

## Time and cost

One run is ~400 forget + 400 retain examples × ~150 tokens × 10 epochs ≈
1.2M training tokens. Full fine-tuning is ~6 × 8B FLOPs per token ≈ 6×10¹⁶
FLOPs; an H100 at a realistic 150–250 TFLOPS sustained does that in
5–8 minutes. With the reference-model forward pass, gradient checkpointing,
data loading and per-epoch evaluation, budget **20–40 min per run**, so the
seven runs are 3–5 GPU-hours. Add 1 hour for setup and 1 hour for uploads:
**≈ $25–50 total**. Turn off per-epoch TOFU evaluation
(`trainer.args.eval_strategy=no trainer.args.eval_on_start=false`) unless you
want their metrics — it is the slowest part at 8B and this repo does its own
evaluation.

## Steps

```bash
# 0. on the GPU box
git clone https://github.com/locuslab/open-unlearning && cd open-unlearning
uv venv && source .venv/bin/activate && uv pip install -e . && uv pip install flash-attn --no-build-isolation bitsandbytes
huggingface-cli login      # the 8B model config points its tokenizer at meta-llama/Llama-3.1-8B-Instruct (gated);
                           # either accept Meta's license or override tokenizer_args to the open-unlearning full model below

# 1. shared overrides for every run
COMMON="model=Llama-3.1-8B-Instruct \
  model.model_args.pretrained_model_name_or_path=open-unlearning/tofu_Llama-3.1-8B-Instruct_full \
  model.tokenizer_args.pretrained_model_name_or_path=open-unlearning/tofu_Llama-3.1-8B-Instruct_full \
  forget_split=forget10 retain_split=retain90 retain_logs_path=null \
  trainer.args.optim=adamw_bnb_8bit trainer.args.gradient_checkpointing=true \
  trainer.args.per_device_train_batch_size=4 trainer.args.gradient_accumulation_steps=8 \
  trainer.args.eval_strategy=no trainer.args.eval_on_start=false trainer.args.save_only_model=true"

# 2. one run per method (task_name becomes the output directory saves/unlearn/<task_name>)
python src/train.py --config-name=unlearn.yaml experiment=unlearn/tofu/default.yaml trainer=RMU \
  task_name=tofu_8B_forget10_RMU $COMMON \
  trainer.args.learning_rate=5e-5 trainer.args.num_train_epochs=10 \
  trainer.method_args.steering_coeff=10 'trainer.method_args.module_regex=model\.layers\.20'

python src/train.py --config-name=unlearn.yaml experiment=unlearn/tofu/default.yaml trainer=NPO \
  task_name=tofu_8B_forget10_NPO $COMMON \
  trainer.args.learning_rate=1e-5 trainer.args.num_train_epochs=10 \
  trainer.method_args.beta=0.5 trainer.method_args.alpha=1

python src/train.py --config-name=unlearn.yaml experiment=unlearn/tofu/default.yaml trainer=SimNPO \
  task_name=tofu_8B_forget10_SimNPO $COMMON \
  trainer.args.learning_rate=2e-5 trainer.args.num_train_epochs=10 \
  trainer.method_args.beta=4.5 trainer.method_args.alpha=1 trainer.method_args.delta=1 trainer.method_args.gamma=0.125

python src/train.py --config-name=unlearn.yaml experiment=unlearn/tofu/default.yaml trainer=GradDiff \
  task_name=tofu_8B_forget10_GradDiff $COMMON \
  trainer.args.learning_rate=1e-5 trainer.args.num_train_epochs=5 trainer.method_args.alpha=5

python src/train.py --config-name=unlearn.yaml experiment=unlearn/tofu/idk.yaml trainer=DPO \
  task_name=tofu_8B_forget10_IdkDPO $COMMON \
  trainer.args.learning_rate=5e-5 trainer.args.num_train_epochs=10 \
  trainer.method_args.beta=0.05 trainer.method_args.alpha=5

python src/train.py --config-name=unlearn.yaml experiment=unlearn/tofu/idk.yaml trainer=GradDiff \
  task_name=tofu_8B_forget10_IdkNLL $COMMON \
  trainer.args.learning_rate=4e-5 trainer.args.num_train_epochs=10 trainer.method_args.alpha=5

# AltPO: confirm the forget dataset override in docs/repro.md first, then
python src/train.py --config-name=unlearn.yaml experiment=unlearn/tofu/default.yaml trainer=DPO \
  data/datasets@data.forget=TOFU_QA_forget_para task_name=tofu_8B_forget10_AltPO $COMMON \
  trainer.args.learning_rate=5e-5 trainer.args.num_train_epochs=10 \
  trainer.method_args.beta=0.1 trainer.method_args.alpha=1

# 3. optional: epoch-5 snapshots for PLAN2 §C2 — add to any run
#    trainer.args.save_strategy=epoch trainer.args.save_total_limit=2

# 4. push each checkpoint to a private HF repo (16 GB each; scp works too)
huggingface-cli upload --private <you>/tofu_8B_forget10_RMU saves/unlearn/tofu_8B_forget10_RMU
```

Run the seven commands sequentially in one `nohup` script; they do not need
to share the box. Before shutting the instance down, spot-check each
checkpoint with a handful of forget10 questions under the chat template — a
run that diverged (RMU and SimNPO are the touchy ones at a new depth) shows
up as gibberish or as verbatim base answers and should be re-run with the
learning rate halved before you pay for the download.

## Bringing them home

Add a `CHECKPOINTS_8B` dict to `src/config.py` mirroring `CHECKPOINTS`, with
`MODEL_LAYER_INT` entries at twice the 1B depth (RMU 20, default 28). The
`open-unlearning` config for Llama-3.1-8B-Instruct uses
`date_string: 10 Apr 2025` in its chat template; if you want prompts
byte-identical to their eval, set `DATE` in `src/prompting.py` to that (it
is currently the template default, `26 Jul 2024`).

Disk is the local constraint, not compute: seven 8B checkpoints are ~112 GB
and the laptop had 46 GB free on 2026-09-09. Either an external SSD, or keep
two or three resident at a time and cache all-layer activations
(`results/activations/`, ~0.4 GB per model per prompt set at n=400) before
deleting weights — 02 and 03 run entirely from that cache, and only the
causal experiments need weights back.

## Why not locally

The M1 Max has a 25 GB MPS budget. Full fine-tuning of 8B needs 64–128 GB;
of 3B, 24–48 GB. LoRA/QLoRA on an 8B 4-bit base fits (via MLX, since
bitsandbytes has no MPS backend) at roughly 100–150 tokens/s, i.e. 2.5–4 h
per run plus a day or two to reimplement the seven losses outside their
Trainer, and rank-limited LoRA updates are a different intervention from the
full-parameter 1B checkpoints, so scale comparisons would be confounded by
method-of-update. The cloud route is cheaper in every currency but one login.
