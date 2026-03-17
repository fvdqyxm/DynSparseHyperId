# Contributing

## Scope
1. Keep contributions aligned to tracker steps (`tracking/*.csv`).
2. Prefer deterministic scripts with JSON metrics artifacts.
3. Avoid overclaiming in docs; all claims should map to executable evidence.

## Development Rules
1. Run tests before proposing changes:
   - `venv/bin/python -m unittest tests/test_phase0_steps.py -v`
2. Run schema/logic audit:
   - `venv/bin/python code/models/schema_logic_audit.py`
3. If LaTeX changed, rebuild:
   - `cd proofs/latex && pdflatex -interaction=nonstopmode -halt-on-error master.tex && pdflatex -interaction=nonstopmode -halt-on-error master.tex`

## Pull Request Checklist
1. Tracker status updated for changed steps.
2. Artifact paths documented in step notes.
3. Any blocked states are explicit and reproducible.
