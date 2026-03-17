# Step 65 Results: Hyperparameter Tuning (Proxy Stage)

Date: 2026-03-12  
Artifact: `results/phase2_step65_tuning/metrics_summary.json`

## Tuned Quantities
1. Learning rate (`lr`) via curriculum encoder validation loss.
2. Sparsity scale (`lambda_alpha_scale`) via k=3 validation MSE + support behavior.
3. Smoothness weight (`beta_smoothness`) via temporal smoothness proxy objective.

## Recommended Values (Current Proxy Run)
1. `lr = 3e-4`
2. `lambda_alpha_scale = 0.25`
3. `beta_smoothness = 1.0`

## Logic Check
1. These are executable, reproducible tuning outputs.
2. This is still proxy tuning, not full end-to-end joint optimization on the final integrated model.
