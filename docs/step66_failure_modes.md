# Step 66: Failure Modes and Mitigation Map

Date: 2026-03-12

## Failure Mode 1: Solver-Mode Confounding
1. Symptom: scaling slopes changed sign for specific cells.
2. Root cause: mixed solver policy across `T` (CV at low `T`, scaled Lasso at high `T`).
3. Mitigation: enforce consistent solver policy in comparative scaling runs.
4. Detection rule: fail if slope flips sign after solver-policy lock.

## Failure Mode 2: High-Order Recall Collapse at Low Sample Size
1. Symptom: high precision but low recall (`k=4`, low `T`).
2. Root cause: strong sparsity shrinkage with limited samples and large dictionaries.
3. Mitigation: increase `T`, tune `lambda_alpha_scale`, or increase candidate quality.
4. Detection rule: precision >0.95 and recall <0.25 should trigger tuning branch.

## Failure Mode 3: Switching Instability Under Reduced Budget
1. Symptom: weak/positive switching error slopes across `T`.
2. Root cause: low seed count + reduced stability-bootstrap budget.
3. Mitigation: expand switching seeds and richer `T` grid; avoid strong claims before that.
4. Detection rule: confidence intervals overlapping zero-improvement across `T`.

## Failure Mode 4: Wrong-Order Model Misspecification
1. Symptom: restricted/wrong library increases error and weakens support recovery.
2. Root cause: missing true interaction terms.
3. Mitigation: model-order diagnostics and model selection (AIC/BIC/CV) before final fitting.
4. Detection rule: persistent high residual error with low support overlap under candidate order.

## Failure Mode 5: Dense-Fit Overfitting (lambda=0)
1. Symptom: dense estimator can inflate apparent support while hurting validation MSE (especially k=4).
2. Root cause: variance blow-up in high-dimensional unconstrained fit.
3. Mitigation: keep sparsity regularization and use held-out objectives for selection.
4. Detection rule: dense model val-MSE exceeds sparse model by threshold margin.

## White-Paper Usage
1. Use this list as a reviewer-facing "known risks + controls" section.
2. Tie each failure mode to an executable artifact in `results/phase2_*` for auditability.
