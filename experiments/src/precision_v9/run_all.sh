#!/bin/sh
# Sequential execution of the SPEC §6 allocation, each job on 10 processes.
cd /c/Users/lijun/Desktop/AI-Optimization-Research/experiments/src/precision_v9
PY=../../.venv/Scripts/python.exe
OUT=../../results/precision_v9/raw
$PY run_sim.py --scenario S0  --mode cov   --n 3000 --chunk 100 --out $OUT
$PY run_sim.py --scenario F3a --mode cov   --n 2000 --out $OUT
$PY run_sim.py --scenario F3b --mode cov   --n 2000 --out $OUT
$PY run_sim.py --scenario F1  --mode truth --n 2000 --out $OUT
$PY run_sim.py --scenario F1  --mode cov   --n 2500 --out $OUT
$PY run_sim.py --scenario F2  --mode truth --n 3000 --out $OUT
$PY run_sim.py --scenario F2  --mode cov   --n 2500 --out $OUT
$PY run_sim.py --scenario F2c --mode truth --n 1500 --out $OUT
$PY run_sim.py --scenario F2c --mode cov   --n 1000 --out $OUT
echo ALLDONE
