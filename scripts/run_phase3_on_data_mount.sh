#!/usr/bin/env bash
set -euo pipefail

# One-command replay for real-data Phase 3 once datasets are mounted.
# Usage:
#   BIDS_ROOT=data/real/marijuana_323 \
#   LABELS_CSV=data/real/marijuana_323/phenotypes/craving_labels.csv \
#   ABCD_ROOT=data/real/abcd_sud_subset \
#   ./scripts/run_phase3_on_data_mount.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${ROOT_DIR}/venv/bin/python"

BIDS_ROOT="${BIDS_ROOT:-data/real/marijuana_323}"
LABELS_CSV="${LABELS_CSV:-data/real/marijuana_323/phenotypes/craving_labels.csv}"
ABCD_ROOT="${ABCD_ROOT:-data/real/abcd_sud_subset}"

echo "[Phase3] Step 68 intake..."
"${PY}" "${ROOT_DIR}/code/models/phase3_step68_data_intake.py" \
  --bids-root "${BIDS_ROOT}" \
  --label-file "${LABELS_CSV}" \
  --out-dir "${ROOT_DIR}/results/phase3_step68_intake"

echo "[Phase3] Step 69 windows..."
"${PY}" "${ROOT_DIR}/code/models/phase3_step69_sliding_windows.py" \
  --manifest "${ROOT_DIR}/results/phase3_step68_intake/subject_manifest.csv" \
  --out-dir "${ROOT_DIR}/results/phase3_step69_windows"

echo "[Phase3] Step 70 motifs..."
"${PY}" "${ROOT_DIR}/code/models/phase3_step70_motif_inference.py" \
  --windows-dir "${ROOT_DIR}/results/phase3_step69_windows" \
  --labels "${LABELS_CSV}" \
  --out-dir "${ROOT_DIR}/results/phase3_step70_motifs"

echo "[Phase3] Step 71 prediction..."
"${PY}" "${ROOT_DIR}/code/models/phase3_step71_predict_craving.py" \
  --step70-metrics "${ROOT_DIR}/results/phase3_step70_motifs/metrics_summary.json" \
  --step70-scores "${ROOT_DIR}/results/phase3_step70_motifs/motif_scores.npy" \
  --step70-craving "${ROOT_DIR}/results/phase3_step70_motifs/subject_craving.npy" \
  --out-dir "${ROOT_DIR}/results/phase3_step71_prediction"

echo "[Phase3] Step 72 baseline compare..."
"${PY}" "${ROOT_DIR}/code/models/phase3_step72_baseline_compare.py" \
  --step71-metrics "${ROOT_DIR}/results/phase3_step71_prediction/metrics_summary.json" \
  --step70-metrics "${ROOT_DIR}/results/phase3_step70_motifs/metrics_summary.json" \
  --out-dir "${ROOT_DIR}/results/phase3_step72_baseline_compare"

echo "[Phase3] Step 73 visuals..."
"${PY}" "${ROOT_DIR}/code/models/phase3_step73_visualize_motifs.py" \
  --step70-metrics "${ROOT_DIR}/results/phase3_step70_motifs/metrics_summary.json" \
  --motif-basis "${ROOT_DIR}/results/phase3_step70_motifs/motif_basis.npy" \
  --motif-scores "${ROOT_DIR}/results/phase3_step70_motifs/motif_scores.npy" \
  --out-dir "${ROOT_DIR}/results/phase3_step73_visuals"

echo "[Phase3] Step 74 ABCD preflight..."
"${PY}" "${ROOT_DIR}/code/models/phase3_step74_cross_dataset_preflight.py" \
  --abcd-root "${ABCD_ROOT}" \
  --out-dir "${ROOT_DIR}/results/phase3_step74_cross_dataset"

echo "[Phase3] Step 75 ablation..."
"${PY}" "${ROOT_DIR}/code/models/phase3_step75_neuro_ablation.py" \
  --step70-metrics "${ROOT_DIR}/results/phase3_step70_motifs/metrics_summary.json" \
  --step70-scores "${ROOT_DIR}/results/phase3_step70_motifs/motif_scores.npy" \
  --step70-craving "${ROOT_DIR}/results/phase3_step70_motifs/subject_craving.npy" \
  --out-dir "${ROOT_DIR}/results/phase3_step75_ablation"

echo "[Phase3] Step 76 gate..."
"${PY}" "${ROOT_DIR}/code/models/phase3_step76_gate3_assessment.py" \
  --step70 "${ROOT_DIR}/results/phase3_step70_motifs/metrics_summary.json" \
  --step71 "${ROOT_DIR}/results/phase3_step71_prediction/metrics_summary.json" \
  --step72 "${ROOT_DIR}/results/phase3_step72_baseline_compare/metrics_summary.json" \
  --step73 "${ROOT_DIR}/results/phase3_step73_visuals/metrics_summary.json" \
  --step74 "${ROOT_DIR}/results/phase3_step74_cross_dataset/metrics_summary.json" \
  --step75 "${ROOT_DIR}/results/phase3_step75_ablation/metrics_summary.json" \
  --out-dir "${ROOT_DIR}/results/phase3_step76_gate3"

echo "[Phase3] Replay complete."
