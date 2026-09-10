#!/usr/bin/env bash
# Finish the n=400 run. The knowledge probe (decisive) is already done.
#
# Remaining models to judge all sit at 0/400 on the phrase matcher, so they get
# a 100-row/class LLM sample rather than a full pass; recall is capped at 200
# rows/model. Geometry stages (02/03) are deferred — see the PLAN2 revision.
set -u
cd "$(dirname "$0")/.."
export RESULT_TAG=_n400 N_QUESTIONS=400 JUDGE_SAMPLE=100 RECALL_SAMPLE=200
LOG=results/n400_run.log
say() { printf '\n===== [%s] %s\n' "$(date +%H:%M:%S)" "$1" | tee -a "$LOG"; }

say "A/C judging remaining models (100 rows/class sample)"
uv run python experiments/01_idk_behavior.py --n 400 --phase judge >>"$LOG" 2>&1 || say "judge FAILED"

say "B/C summaries"
uv run python experiments/01_idk_behavior.py --n 400 --phase summarize >>"$LOG" 2>&1 || say "summarize FAILED"
uv run python experiments/06_knowledge_probe.py --n 400 --from-cache >>"$LOG" 2>&1 || say "06 FAILED"

say "C/C recall audit (200 rows/model)"
uv run python experiments/09_recall_audit.py >>"$LOG" 2>&1 || say "recall FAILED"

say "FINISH done"
