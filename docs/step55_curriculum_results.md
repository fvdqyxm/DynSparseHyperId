# Step 55 Results: Curriculum Training Toy (k=2 -> k=3)

Date: 2026-03-12
Artifacts:
- `code/models/phase2_curriculum_training_toy.py`
- `results/phase2_step55_curriculum/metrics_summary.json`

## Procedure
1. Pretrain regime encoder on simpler linear switching sequences (k=2-like dynamics).
2. Fine-tune same encoder on harder nonlinear switching sequences (k=3-like dynamics).
3. Compare to scratch training on the harder stage.

## Outcome
Current run shows mixed transfer effects:
- validation loss slightly improved with curriculum,
- validation accuracy did not improve in this setting.

## Interpretation
1. Step 55 is completed as a working curriculum pipeline.
2. The current toy does not yet show robust curriculum gains; this is a tuning and data-design issue, not a pipeline gap.
3. Claim-safe position: curriculum mechanism exists and is testable, but benefit is not yet established.
