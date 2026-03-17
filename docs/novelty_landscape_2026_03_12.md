# Novelty and Interest Check (2026-03-12)

## Question
Is the project direction still scientifically interesting, or already saturated?

## Sources Checked
1. Identifiability of Switching Dynamical Systems with Unknown Initial State  
   PMLR 2024: <https://proceedings.mlr.press/v242/feng24a.html>
2. Reconstructing hypergraphs from observed dynamics  
   Nature Communications 2025: <https://www.nature.com/articles/s41467-025-58285-z>
3. Latent variable graphical model selection via convex optimization  
   Annals of Statistics 2012: <https://arxiv.org/pdf/1008.1290.pdf>
4. Latent Space Modelling of Hypergraph Data  
   arXiv:1909.00472: <https://arxiv.org/abs/1909.00472>

## Logic Synthesis
1. There is clear progress on **pieces** of your target:
   - switching-system identifiability (but not sparse high-order hypergraph regime switching),
   - hypergraph reconstruction from dynamics (but not latent Markov regime identifiability),
   - latent-variable graphical identifiability in pairwise Gaussian settings.
2. The exact combined target remains nontrivial:
   sparse high-order + latent switching + finite-sample support guarantees + scalable inference.
3. Therefore, the direction is still interesting if scoped rigorously and claims are modularized.

## Red Flags (If Ignored, Work Looks Like Hype)
1. Claiming “no prior work” too broadly.
2. Jumping directly to k>=3 regime-switching guarantees without proving k=2 switching rigor first.
3. Presenting neuroscience correlations as mechanistic proof.

## Recommendation
1. Make novelty claim precise:
   “Existing work covers components separately; our contribution is a provable integrated model class
   under explicit assumptions.”
2. Use theorem ladder:
   k=2 switching identifiability/recovery first, then high-order extension.
3. Keep a living novelty memo and update it before each draft milestone.

## Current Verdict
Interesting and publishable trajectory, conditional on:
1. solving or transparently bounding the switching-recovery bottleneck,
2. maintaining strict no-overclaim discipline.
