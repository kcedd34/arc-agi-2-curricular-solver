#!/bin/bash
cd /mnt/d/Projetos/kaggle_contest
source .venv312/bin/activate
for m in instruct base; do
  python -m src.curriculum.program_probe.generate --model $m 2>&1 | grep --line-buffered -E "^\[|Error|Traceback" >> outputs/curriculum/program_probe/generate.log
done
echo ALL_DONE >> outputs/curriculum/program_probe/generate.log
