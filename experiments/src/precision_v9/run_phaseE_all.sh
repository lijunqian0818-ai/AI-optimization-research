#!/bin/sh
cd /c/Users/lijun/Desktop/AI-Optimization-Research/experiments/src/precision_v9
PY=../../.venv/Scripts/python.exe
for s in S0 S1 S2; do $PY run_phaseE.py --scenario $s --n 1000 --chunk 25 --procs 8; done
for s in F3a F3b F1 F2 F2c; do $PY run_phaseE.py --scenario $s --n 1000 --chunk 10 --procs 8; done
echo ALLDONE
