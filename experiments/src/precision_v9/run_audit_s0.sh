#!/bin/sh
cd /c/Users/lijun/Desktop/AI-Optimization-Research/experiments/src/precision_v9
PY=../../.venv/Scripts/python.exe
OUT=../../results/precision_v9/audit_s0/raw
$PY audit_s0.py --steps L4 L0 L1 L2 L3 L5 L6 --n 4000 --chunk 50 --procs 8 --out $OUT
$PY audit_s0.py --steps L4 --n 1000 --chunk 25 --procs 3 --extraB 4999 --out $OUT
echo ALLDONE
