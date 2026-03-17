# Step 46 Note: Sublinear Convergence Under Convex Surrogate Assumptions

Date: 2026-03-12
Status: Drafted proof note

## Objective
Provide a convergence guarantee for the proximal-gradient part of the variational prox-EM routine under convex surrogate conditions.

## Surrogate Objective
Consider
\[
F(\theta)=f(\theta)+g(\theta),
\]
where:
1. \(f\) is convex and \(L\)-smooth,
2. \(g\) is proper, closed, convex (group-lasso penalty),
3. updates use
\[
\theta_{m+1}=\mathrm{prox}_{\eta g}(\theta_m-\eta\nabla f(\theta_m)),\quad \eta\in(0,1/L].
\]

## Claim
For any minimizer \(\theta^\star\), proximal gradient iterates satisfy
\[
F(\theta_m)-F(\theta^\star)
\le
\frac{\|\theta_0-\theta^\star\|_2^2}{2\eta m}
=O(1/m).
\]

## Proof Skeleton
1. Use standard descent inequality for L-smooth \(f\).
2. Use optimality condition of proximal step to bound composite progress.
3. Telescope over iterations.
4. Rearrange to obtain \(O(1/m)\) objective gap.

## Scope Boundary
1. This guarantee applies to convex surrogate subproblems.
2. Full variational EM loop is nonconvex; global guarantees are not claimed here.
3. In practice, this result justifies the proximal M-step behavior inside each block update.

## Citation Anchors
- Beck and Teboulle (2009), ISTA/FISTA analysis line.
- Parikh and Boyd (2014), proximal algorithms notes.
