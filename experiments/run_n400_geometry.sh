#!/usr/bin/env bash
# The stages deferred from the n=400 run: the epistemic-direction layer sweep
# (02) and the alignment analysis (03). Both read activations, so the first
# step is extracting them for all 8 checkpoints at n=400 (~40-60 min); the
# analyses themselves are numpy.
set -u
cd "$(dirname "$0")/.."
export RESULT_TAG=_n400 N_QUESTIONS=400
LOG=results/n400_geometry.log
say() { printf '\n===== [%s] %s\n' "$(date +%H:%M:%S)" "$1" | tee -a "$LOG"; }

say "1/2 epistemic direction layer sweep (extracts activations for base/IdkDPO/IdkNLL)"
uv run python experiments/02_epistemic_direction.py >>"$LOG" 2>&1 || say "02 FAILED"

say "2/2 alignment (extracts the five methods under test)"
uv run python experiments/03_alignment.py --n-boot 500 >>"$LOG" 2>&1 || say "03 FAILED"

say "geometry done"
grep -aE "^GATE|^=>|anchor cos" "$LOG" | tail -6
