# Plan (16-20 hours)

Five experiments, in order; each has a gate that must pass before the next is
worth running. Total is a working estimate, not a hard budget — the gates are
what matter.

| Hours | Experiment | Deliverable | Gate to continue |
|-------|-----------|-------------|-------------------|
| 3 | `01_idk_behavior` | IdkDPO / IdkNLL added to `src/config.py`; behavioral check (chat-template generation + Ollama judge, `src/judge.py`) that they abstain on forget10 and answer on retain90 | Ignorance cell populated. If IdkDPO/IdkNLL also confabulate, the checkpoints don't do what their name says and the project needs a different positive control before continuing. |
| 3 | `02_epistemic_direction` | Diff-in-means direction between abstained-forget and answered-retain activations on IdkDPO; layer sweep (`src/layer_sweep.py`) to find where it separates best — do not assume layer 10 (RMU's site) or 14 (the exploratory default) | Direction is separable at some layer |
| 3 | `03_alignment` | Cosine of the epistemic direction against every method's base-to-unlearned mean offset (`src/refusal_alignment.py`), benchmarked against a refusal-free control direction and IdkDPO's own offset as the positive anchor | IdkDPO's own offset must align, or the test is uninformative |
| 2 | `04_causal` | Translate RMU and AltPO along the epistemic direction at matched norm; score gold-answer log-prob (`src/intervention.py`) | — (result stands either way: movement = live epistemic-gate evidence, nothing = the negative is now positive-control-backed) |
| 2 | `05_oracle_8b` | Rerun the abstention behavioral check on the 8B retain90 oracle (`open-unlearning/tofu_Llama-3.1-8B-Instruct_retain90`, already downloadable, no training needed) | — (answers whether the empty ignorance cell at 1B was a scale artifact) |
| 4 | Write-up | Figures (extend the alignment bar chart with the epistemic direction as a third group), README results section, submission draft | — |

## Notes

- Steps 01-04 mirror `unlearning-probes` notebooks 10 (behavioral elicitation)
  and 11 (alignment machinery); see `BACKGROUND.md` for what those established
  and why IdkDPO/IdkNLL close the gap they left.
- One model resident at a time (32 GB MPS constraint) — free each model before
  loading the next, as in the source repo's `model_loader.py` usage.
- 8B fits for read-only work (step 05); do not attempt LoRA or gradient steps
  on it here — that is out of scope (see `BACKGROUND.md`).
- If step 01 fails its gate, stop and reassess rather than continuing down the
  table — every later step assumes a populated ignorance cell.
