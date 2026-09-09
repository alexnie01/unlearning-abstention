# Experiments

One notebook or script per experiment, numbered in execution order. Each starts
by importing from `src/` and writes only under `results/<experiment>/`.

| # | Experiment | Question | Gate |
|---|-----------|----------|------|
| 01 | `idk_behavior` | Do IdkDPO / IdkNLL actually abstain on forget10 and answer on retain90? | Populated ignorance cell, else stop |
| 02 | `epistemic_direction` | Diff-in-means of abstained-forget vs answered-retain on IdkDPO; layer sweep | Separable at some layer |
| 03 | `alignment` | Cosine of that direction with every method's base-to-unlearned offset, vs a refusal-free control and IdkDPO's own offset | IdkDPO must align |
| 04 | `causal` | Translate RMU / AltPO along the epistemic direction at matched norm; gold log-prob | — |
| 05 | `oracle_8b` | Does the 8B retain90 oracle abstain where the 1B oracle confabulated? | — |
