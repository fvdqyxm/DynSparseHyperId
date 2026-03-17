#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${ROOT_DIR}/venv/bin/python"

BIDS_ROOT="${BIDS_ROOT:-data/real/marijuana_323}"
LABELS_CSV="${LABELS_CSV:-data/real/marijuana_323/phenotypes/craving_labels.csv}"
ABCD_ROOT="${ABCD_ROOT:-data/real/abcd_sud_subset}"
MIN_SUBJECTS="${MIN_SUBJECTS:-5}"

"${PY}" "${ROOT_DIR}/code/models/phase3_data_preflight_gate.py" \
  --bids-root "${BIDS_ROOT}" \
  --label-file "${LABELS_CSV}" \
  --abcd-root "${ABCD_ROOT}" \
  --min-subjects "${MIN_SUBJECTS}" \
  --out-dir "${ROOT_DIR}/results/phase3_data_preflight_gate"
