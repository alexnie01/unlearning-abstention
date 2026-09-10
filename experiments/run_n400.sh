#!/usr/bin/env bash
# PLAN2 R1 — full-scale rerun at n=400.
#
# Writes everything to results/*_n400/ so the n=100 results stay intact for
# comparison. Each stage is skippable on rerun (the scripts skip existing
# outputs), so this can be interrupted and restarted.
#
#   bash experiments/run_n400.sh
set -u
cd "$(dirname "$0")/.."
export RESULT_TAG=_n400
export N_QUESTIONS=400
LOG=results/n400_run.log
mkdir -p results
say() { printf '\n===== [%s] %s\n' "$(date +%H:%M:%S)" "$1" | tee -a "$LOG"; }

say "R1 start: n=400, tag=$RESULT_TAG"

say "1/6 generation (8 checkpoints x 800 prompts)"
uv run python experiments/01_idk_behavior.py --n 400 --phase generate >>"$LOG" 2>&1

say "2/6 judging (llama3.2 + phrase matcher, deepseek-r1 adjudication)"
uv run python experiments/01_idk_behavior.py --n 400 --phase judge >>"$LOG" 2>&1
uv run python experiments/01_idk_behavior.py --n 400 --phase summarize >>"$LOG" 2>&1

say "3/6 knowledge probe (9 models x 400 questions x 6 answers)"
uv run python experiments/06_knowledge_probe.py --n 400 >>"$LOG" 2>&1

say "4/6 recall audit"
uv run python experiments/09_recall_audit.py >>"$LOG" 2>&1

say "5/6 epistemic direction layer sweep"
uv run python experiments/02_epistemic_direction.py >>"$LOG" 2>&1

say "6/6 alignment"
uv run python experiments/03_alignment.py >>"$LOG" 2>&1

say "R1 done"
grep -aE "^GATE|^=>|calibration:" "$LOG" | tail -20 | tee -a "$LOG"
