#!/usr/bin/env bash
# Finish the n=400 run, decisive experiment first.
#
# Triage after losing a night to laptop sleep: the four remaining models to
# judge all sit at 0/400 on the phrase matcher, so they get a 150-row/class
# LLM sample rather than a full pass, and the geometry stages (02/03) are
# deferred — they were already found not to predict the functional results.
set -u
cd "$(dirname "$0")/.."
export RESULT_TAG=_n400 N_QUESTIONS=400 JUDGE_SAMPLE=150
LOG=results/n400_run.log
say() { printf '\n===== [%s] %s\n' "$(date +%H:%M:%S)" "$1" | tee -a "$LOG"; }

say "FINISH 1/3 knowledge probe (decisive; 9 models x 400 q x 6 answers, batched)"
uv run python experiments/06_knowledge_probe.py --n 400 >>"$LOG" 2>&1

say "FINISH 2/3 judging remaining models (150 rows/class sample)"
uv run python experiments/01_idk_behavior.py --n 400 --phase judge >>"$LOG" 2>&1
uv run python experiments/01_idk_behavior.py --n 400 --phase summarize >>"$LOG" 2>&1
uv run python experiments/06_knowledge_probe.py --n 400 --from-cache >>"$LOG" 2>&1

say "FINISH 3/3 recall audit"
uv run python experiments/09_recall_audit.py >>"$LOG" 2>&1

say "FINISH done (02/03 geometry deferred — see PLAN2 revision)"
