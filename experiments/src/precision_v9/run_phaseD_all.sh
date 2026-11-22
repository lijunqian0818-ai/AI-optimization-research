#!/bin/sh
cd /c/Users/lijun/Desktop/AI-Optimization-Research/experiments/src/precision_v9
PY=../../.venv/Scripts/python.exe
OUT=../../results/precision_v9/phaseD/raw
for s in S0 S1 S2; do $PY run_phaseD.py --scenario $s --mode cov --n 1000 --chunk 25 --procs 8 --out $OUT; done
for s in F3a F3b F1 F2 F2c; do $PY run_phaseD.py --scenario $s --mode cov --n 1000 --chunk 10 --procs 8 --out $OUT; done
for s in F1 F2 F2c; do $PY run_phaseD.py --scenario $s --mode truth --n 1500 --chunk 25 --procs 8 --out $OUT; done
echo ALLDONE
