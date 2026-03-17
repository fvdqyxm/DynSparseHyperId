#!/usr/bin/env bash
set -euo pipefail

# Build a mentor feedback packet for Step 132.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${ROOT_DIR}/results/phase4_step132_feedback_packet"
STAMP="$(date +%Y%m%d_%H%M%S)"
PKT_DIR="${OUT_DIR}/packet_${STAMP}"
PKT_TGZ="${OUT_DIR}/packet_${STAMP}.tar.gz"

mkdir -p "${PKT_DIR}"

copy_if_exists() {
  local src="$1"
  local rel="$2"
  if [[ -f "${src}" ]]; then
    mkdir -p "$(dirname "${PKT_DIR}/${rel}")"
    cp "${src}" "${PKT_DIR}/${rel}"
  fi
}

copy_if_exists "${ROOT_DIR}/proofs/latex/master.pdf" "proofs/latex/master.pdf"
copy_if_exists "${ROOT_DIR}/tracking/phase1_steps.csv" "tracking/phase1_steps.csv"
copy_if_exists "${ROOT_DIR}/tracking/phase2_steps.csv" "tracking/phase2_steps.csv"
copy_if_exists "${ROOT_DIR}/tracking/phase3_steps.csv" "tracking/phase3_steps.csv"
copy_if_exists "${ROOT_DIR}/tracking/phase4_steps.csv" "tracking/phase4_steps.csv"
copy_if_exists "${ROOT_DIR}/docs/step50_viability_gate_assessment.md" "docs/step50_viability_gate_assessment.md"
copy_if_exists "${ROOT_DIR}/docs/step67_viability_gate2_assessment.md" "docs/step67_viability_gate2_assessment.md"
copy_if_exists "${ROOT_DIR}/docs/deep_viability_review_2026_03_12.md" "docs/deep_viability_review_2026_03_12.md"
copy_if_exists "${ROOT_DIR}/docs/step67_multiregime_upgrade_note.md" "docs/step67_multiregime_upgrade_note.md"
copy_if_exists "${ROOT_DIR}/docs/step67_refit_tradeoff_analysis.md" "docs/step67_refit_tradeoff_analysis.md"
copy_if_exists "${ROOT_DIR}/docs/phase4_step132_feedback_packet.md" "docs/phase4_step132_feedback_packet.md"

cat > "${PKT_DIR}/README_PACKET.md" <<'EOF'
# Mentor Feedback Packet

This packet contains current theorem/synthetic status, gate decisions, and risk notes.
Please focus feedback on:
1. Assumption realism and theorem framing.
2. Claim boundary correctness.
3. Multi-regime tradeoff narrative (regime vs support recovery objectives).
EOF

(
  cd "${OUT_DIR}"
  tar -czf "$(basename "${PKT_TGZ}")" "$(basename "${PKT_DIR}")"
)

python3 - <<PY
import json
from pathlib import Path
out = Path("${OUT_DIR}")
pkt_dir = Path("${PKT_DIR}")
pkt_tgz = Path("${PKT_TGZ}")
files = [str(p.relative_to(pkt_dir)) for p in pkt_dir.rglob("*") if p.is_file()]
report = {
  "status": "packet_built",
  "packet_dir": str(pkt_dir),
  "packet_tar_gz": str(pkt_tgz),
  "n_files": len(files),
  "files": files,
}
(out / "latest_packet_manifest.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
PY
