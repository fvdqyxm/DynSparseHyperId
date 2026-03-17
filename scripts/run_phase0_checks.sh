#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

mkdir -p .mplconfig .cache

echo "[1/9] Running deterministic Phase 0 baselines..."
LOKY_MAX_CPU_COUNT=8 MPLBACKEND=Agg MPLCONFIGDIR="$ROOT/.mplconfig" XDG_CACHE_HOME="$ROOT/.cache" \
  venv/bin/python code/models/phase0_baselines.py \
  --out-dir results/phase0 \
  --seed 7 \
  --n 20 \
  --switching-n 10 \
  --t 1000 \
  --switching-t 1400 \
  --sparsity 0.1 \
  --sigma 0.5 \
  --support-threshold 0.05

echo "[2/9] Running switching robustness sweep..."
LOKY_MAX_CPU_COUNT=8 MPLBACKEND=Agg MPLCONFIGDIR="$ROOT/.mplconfig" XDG_CACHE_HOME="$ROOT/.cache" \
  venv/bin/python code/models/phase0_switching_sweep.py \
  --out-dir results/phase0_switching_sweep \
  --n 10 \
  --t 1400 \
  --sparsity 0.1 \
  --sigma 0.5 \
  --support-threshold 0.05 \
  --obs-noises 0.0,0.15,0.30 \
  --seeds 3 \
  --seed-start 31 \
  --stability-bootstrap-runs 8

echo "[3/9] Running Wilson-Cowan + HRF pipeline..."
LOKY_MAX_CPU_COUNT=8 MPLBACKEND=Agg MPLCONFIGDIR="$ROOT/.mplconfig" XDG_CACHE_HOME="$ROOT/.cache" \
  venv/bin/python code/models/wilson_cowan_hrf_pipeline.py \
  --out-dir results/phase0_wilson_cowan \
  --seed 17 \
  --n 10 \
  --t 2400 \
  --dt 0.05 \
  --tr 0.8 \
  --edge-prob 0.1 \
  --support-threshold 0.05 \
  --effective-threshold 0.0005

echo "[4/9] Running static k=3 hypergraph reconstruction..."
LOKY_MAX_CPU_COUNT=8 MPLBACKEND=Agg MPLCONFIGDIR="$ROOT/.mplconfig" XDG_CACHE_HOME="$ROOT/.cache" \
  venv/bin/python code/models/static_hypergraph_k3.py \
  --out-dir results/phase0_hypergraph_k3 \
  --seed 17 \
  --n 10 \
  --t 700 \
  --edge-prob 0.12 \
  --noise-sigma 0.25 \
  --support-threshold 0.08 \
  --sweep-noises 0.15,0.25,0.35,0.50 \
  --sweep-seeds 3

echo "[5/9] Running adversarial rigor checks..."
LOKY_MAX_CPU_COUNT=8 MPLBACKEND=Agg MPLCONFIGDIR="$ROOT/.mplconfig" XDG_CACHE_HOME="$ROOT/.cache" \
  venv/bin/python code/models/rigor_adversarial_checks.py \
  --seed 17 \
  --out-dir results/rigor_checks

echo "[6/9] Running assumption-literature audit..."
LOKY_MAX_CPU_COUNT=8 MPLBACKEND=Agg MPLCONFIGDIR="$ROOT/.mplconfig" XDG_CACHE_HOME="$ROOT/.cache" \
  venv/bin/python code/models/assumption_literature_audit.py

echo "[7/9] Running schema/logic coherence audit..."
LOKY_MAX_CPU_COUNT=8 MPLBACKEND=Agg MPLCONFIGDIR="$ROOT/.mplconfig" XDG_CACHE_HOME="$ROOT/.cache" \
  venv/bin/python code/models/schema_logic_audit.py

echo "[8/9] Building interim LaTeX PDF..."
cd "$ROOT/proofs/latex"
pdflatex -interaction=nonstopmode -halt-on-error master.tex >/dev/null
pdflatex -interaction=nonstopmode -halt-on-error master.tex >/dev/null
cd "$ROOT"

echo "[9/9] Running Phase 0 tests..."
venv/bin/python -m unittest tests/test_phase0_steps.py -v

echo "Phase 0 checks passed."
