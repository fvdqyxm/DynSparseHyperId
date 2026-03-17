#!/usr/bin/env python3
"""
Build a professor-grade OR + Applied Math problem-solving bible.

Outputs:
- data/assignment_pdf_bundles/phd_problem_solving_bible_guide.tex
- data/assignment_pdf_bundles/phd_problem_solving_bible_guide.pdf
- data/assignment_pdf_bundles/phd_problem_solving_bible_resources.json
- data/assignment_pdf_bundles/phd_problem_solving_bible_summary.json
- data/assignment_pdf_bundles/phd_problem_solving_bible.pdf
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.parse import urlparse

from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


PROBLEM_KWS = ("assign", "homework", "hw", "pset", "problem", "exercise", "quiz", "worksheet")
PROJECT_KWS = ("project", "lab")
EXAM_KWS = ("midterm", "final", "exam")
PROBLEMISH_CATS = {"Problems", "Projects/Labs", "Exams"}
SOLUTION_RE = re.compile(
    r"(solutions?|soln|answers?|keys?|hints?|(^|[^a-z0-9])sol([^a-z0-9]|$))",
    re.IGNORECASE,
)
SOLUTION_CLEAN_RE = re.compile(r"(solutions?|soln|sol|answers?|keys?|hints?)", re.IGNORECASE)
NOISE_RE = re.compile(r"(gradescope|piazza|edstem|policy|calendar|office|logistics|faq)", re.IGNORECASE)


TOPIC_LIBRARY: Dict[str, List[str]] = {
    "proof_foundations": [
        "Predicate logic, quantifiers, and proof structure",
        "Direct proof, contradiction, and contrapositive techniques",
        "Weak/strong/structural induction",
        "Loop invariants and algorithmic correctness",
        "Pigeonhole principle and extremal arguments",
        "Recurrences and proof by recursion trees",
        "Combinatorial identities and bijective proofs",
        "Asymptotic notation and growth-rate comparisons",
        "Counterexample construction and boundary-case analysis",
    ],
    "discrete_probability": [
        "Sample spaces, events, and sigma-algebra intuition",
        "Conditional probability and Bayes' rule",
        "Independence and conditional independence",
        "Discrete random variables and PMFs",
        "Expectation, variance, covariance, and correlation",
        "MGFs/PGFs and distribution transforms",
        "Law of total expectation/variance",
        "Limit ideas: LLN and CLT intuition",
        "Concentration bounds (Markov/Chebyshev/Chernoff/Hoeffding)",
    ],
    "linear_algebra_core": [
        "Vector spaces, subspaces, span, and basis",
        "Linear maps, kernel/image, and rank-nullity",
        "Matrix factorizations (LU/QR/SVD) and geometric meaning",
        "Eigenvalues/eigenvectors and diagonalization",
        "Spectral theorem and orthogonal projections",
        "Least squares and normal equations",
        "Positive definite matrices and quadratic forms",
        "Operator norms and conditioning",
        "Invariant subspaces and canonical forms",
    ],
    "diff_eq_dynamics": [
        "First-order and higher-order ODE models",
        "Linear systems of ODEs and matrix exponentials",
        "Phase portraits and qualitative stability",
        "Equilibrium analysis and linearization",
        "Forced systems and variation of parameters",
        "Boundary/initial value formulations",
        "Discrete-time dynamical analogs",
        "Model calibration from data and physical assumptions",
    ],
    "real_analysis_core": [
        "Completeness, supremum/infimum, and ordered structure",
        "Sequences and series in metric spaces",
        "Pointwise vs uniform convergence",
        "Continuity and uniform continuity",
        "Compactness and sequential compactness",
        "Connectedness and intermediate value phenomena",
        "Differentiation theorems and mean value tools",
        "Riemann integration and approximation arguments",
        "Metric/topological reasoning in proofs",
    ],
    "measure_probability": [
        "Sigma-algebras, measures, and measurable functions",
        "Lebesgue integration construction and properties",
        "Dominated/monotone convergence theorems",
        "Fatou's lemma and interchange of limits/integrals",
        "Product measures and Fubini-Tonelli theorems",
        "Lp spaces, norms, and convergence structure",
        "Modes of convergence of random variables",
        "Conditional expectation as projection",
        "Radon-Nikodym viewpoint and change of measure",
    ],
    "complex_analysis_core": [
        "Holomorphic functions and Cauchy-Riemann equations",
        "Cauchy integral theorem and formula",
        "Power/Laurent series expansions",
        "Isolated singularities and residue calculus",
        "Contour integration and real integral evaluation",
        "Argument principle and Rouche-type reasoning",
        "Conformal mappings and Möbius transforms",
        "Harmonic functions and potential-theoretic links",
    ],
    "abstract_algebra": [
        "Groups, subgroups, and cyclic structure",
        "Cosets, normal subgroups, and quotient groups",
        "Homomorphisms and isomorphism theorems",
        "Rings, ideals, and quotient rings",
        "Fields and polynomial arithmetic",
        "Euclidean domains/PIDs/UFD intuition",
        "Group actions and orbit-stabilizer ideas",
        "Finite fields and algebraic structure in computation",
    ],
    "topology_core": [
        "Topological spaces, bases, and subbases",
        "Continuity via open sets and neighborhood systems",
        "Product and quotient topologies",
        "Compactness in abstract spaces",
        "Connectedness and path connectedness",
        "Separation axioms and metrizability basics",
        "Countability axioms and construction techniques",
        "Homotopy and fundamental group intuition",
    ],
    "optimization_lp_convex": [
        "Modeling with decision variables and constraints",
        "Linear programs and polyhedral geometry",
        "Simplex method and pivot structure",
        "Duality theory and economic interpretation",
        "Sensitivity analysis and shadow prices",
        "Convex sets/functions and Jensen-type inequalities",
        "KKT conditions and optimality certificates",
        "Gradient, Newton, and proximal-style methods",
        "Strong/weak duality across convex models",
    ],
    "optimization_integer_network": [
        "Integer and mixed-integer formulations",
        "Branch-and-bound and cutting-plane logic",
        "Polyhedral relaxations and integrality gaps",
        "Network flows, cuts, and shortest path models",
        "Matching, assignment, and matroidal structures",
        "Submodularity and combinatorial optimization patterns",
        "Approximation/rounding frameworks",
        "Complexity hardness and reduction techniques",
    ],
    "stochastic_processes": [
        "Discrete-time Markov chains and classification",
        "Stationary distributions and mixing behavior",
        "Continuous-time Markov chains and generators",
        "Poisson processes and superposition/splitting",
        "Renewal theory and regenerative arguments",
        "Martingales, stopping times, and optional stopping",
        "Brownian motion and diffusion intuition",
        "Queueing models and performance metrics",
        "Process limits and weak convergence heuristics",
    ],
    "statistical_inference": [
        "Parametric families and identifiability",
        "Sufficiency, completeness, and exponential families",
        "Maximum likelihood and score/information geometry",
        "Method of moments and estimating equations",
        "Hypothesis testing (Neyman-Pearson/LRT)",
        "Confidence intervals and coverage guarantees",
        "Asymptotic normality and delta method",
        "Bootstrap/resampling logic and limitations",
        "Decision-theoretic risk and admissibility",
    ],
    "high_dimensional_stats_ml": [
        "Empirical risk minimization and regularization",
        "Bias-variance and model complexity control",
        "Lasso and sparse recovery foundations",
        "Ridge/elastic-net and shrinkage tradeoffs",
        "Concentration in high dimensions",
        "Generalization bounds (VC/Rademacher/PAC ideas)",
        "Kernel methods and RKHS intuition",
        "Optimization landscapes for modern ML",
        "Robustness, distribution shift, and overparameterization",
    ],
    "algorithms_data_structures": [
        "Arrays, linked structures, stacks, and queues",
        "Balanced BSTs, heaps, and hash tables",
        "Union-find and amortized analysis",
        "Graph representations and traversals",
        "Shortest paths, MSTs, and flow primitives",
        "Dynamic programming state design",
        "Greedy exchange arguments and invariants",
        "Divide-and-conquer and recurrence solving",
        "NP-completeness and reduction templates",
    ],
    "numerical_scientific": [
        "Floating-point arithmetic and roundoff propagation",
        "Conditioning vs stability distinctions",
        "Root-finding (bisection/Newton/secant)",
        "Interpolation and approximation theory",
        "Quadrature and numerical integration",
        "Initial/boundary value ODE discretization",
        "Direct and iterative linear solvers",
        "Convergence diagnostics and stopping criteria",
        "Preconditioning and computational scaling",
    ],
    "systems_architecture": [
        "Instruction set architecture and assembly-level reasoning",
        "Pipelining hazards and throughput analysis",
        "Memory hierarchy and cache locality",
        "Virtual memory and address translation",
        "Parallelism, SIMD, and multicore execution",
        "Performance modeling and bottleneck analysis",
        "Data layout and low-level optimization",
        "Hardware/software co-design tradeoffs",
    ],
    "financial_engineering": [
        "No-arbitrage and replication logic",
        "Discrete-time and continuous-time pricing",
        "Risk-neutral valuation and martingale pricing",
        "Portfolio optimization with constraints",
        "Factor models and risk decomposition",
        "Value-at-Risk and CVaR methodologies",
        "Derivative hedging and Greeks intuition",
        "Scenario/stress testing under model uncertainty",
    ],
}


CLASS_TOPIC_KEYS: Dict[str, List[str]] = {
    "CS 70": ["proof_foundations", "discrete_probability", "algorithms_data_structures"],
    "IEOR 160": ["optimization_lp_convex", "optimization_integer_network"],
    "MATH 54": ["linear_algebra_core", "diff_eq_dynamics"],
    "MATH 110": ["proof_foundations", "linear_algebra_core"],
    "MATH 104": ["proof_foundations", "real_analysis_core"],
    "MATH 105": ["complex_analysis_core", "real_analysis_core"],
    "CS 61B": ["algorithms_data_structures"],
    "CS 170": ["algorithms_data_structures", "optimization_integer_network"],
    "CS 61C": ["systems_architecture", "algorithms_data_structures"],
    "MATH 128A": ["numerical_scientific", "linear_algebra_core"],
    "MATH 128B": ["numerical_scientific", "linear_algebra_core", "diff_eq_dynamics"],
    "MATH 220": ["discrete_probability", "measure_probability", "stochastic_processes"],
    "STAT 150": ["discrete_probability", "statistical_inference"],
    "IEOR 162": ["optimization_lp_convex", "stochastic_processes", "algorithms_data_structures"],
    "IEOR 169": ["stochastic_processes", "optimization_integer_network", "statistical_inference"],
    "IEOR 261": ["optimization_lp_convex", "optimization_integer_network", "numerical_scientific"],
    "IEOR 266": ["optimization_lp_convex", "numerical_scientific", "algorithms_data_structures"],
    "IEOR 263A": ["stochastic_processes", "measure_probability"],
    "IEOR 263B": ["stochastic_processes", "measure_probability", "statistical_inference"],
    "STAT 205A": ["measure_probability", "statistical_inference"],
    "STAT 205B": ["measure_probability", "statistical_inference"],
    "STAT 210A": ["measure_probability", "statistical_inference"],
    "STAT 210B": ["measure_probability", "statistical_inference", "high_dimensional_stats_ml"],
    "IEOR 221": ["optimization_lp_convex", "optimization_integer_network"],
    "IEOR 222": ["optimization_lp_convex", "optimization_integer_network", "algorithms_data_structures"],
    "IEOR 180": ["financial_engineering", "optimization_lp_convex", "stochastic_processes"],
    "IEOR 269": ["optimization_lp_convex", "optimization_integer_network", "stochastic_processes"],
    "MATH 185": ["complex_analysis_core", "real_analysis_core"],
    "MATH 202A": ["real_analysis_core", "measure_probability"],
    "MATH 202B": ["real_analysis_core", "measure_probability", "topology_core"],
    "MATH 113": ["abstract_algebra", "proof_foundations"],
    "MATH 142": ["topology_core", "real_analysis_core"],
    "MATH 142B": ["topology_core", "real_analysis_core", "abstract_algebra"],
    "STAT 260": ["high_dimensional_stats_ml", "statistical_inference", "measure_probability"],
    "CS 189": ["high_dimensional_stats_ml", "optimization_lp_convex", "algorithms_data_structures"],
}


CLASS_TOPIC_OVERRIDES: Dict[str, List[str]] = {
    "CS 70": [
        "Modular arithmetic and number-theoretic arguments",
        "Graph counting, trees, and extremal discrete structures",
    ],
    "IEOR 160": [
        "Transportation/transshipment models and special network LPs",
        "Primal-dual interpretation for managerial decisions",
    ],
    "MATH 54": [
        "Linear transformations as dynamical models",
        "Jordan-form intuition for system evolution",
    ],
    "MATH 104": [
        "Construction of rigorous epsilon-delta proof templates",
        "Counterexample engineering in real-variable analysis",
    ],
    "CS 61B": [
        "Testing methodology, invariants, and debugging discipline",
        "Data structure choice under workload constraints",
    ],
    "CS 170": [
        "Approximation algorithm design principles",
        "Randomized algorithms and probabilistic analyses",
    ],
    "CS 61C": [
        "Quantitative speedup analysis (Amdahl/Gustafson style)",
        "Compiler-level and architecture-level optimization interplay",
    ],
    "MATH 220": [
        "Measure-theoretic probability constructions",
        "Conditional expectation as sigma-algebra projection",
    ],
    "IEOR 169": [
        "Simulation-based policy evaluation under uncertainty",
        "Risk-sensitive decision modeling and robust comparisons",
    ],
    "IEOR 261": [
        "Convex analysis for algorithmic convergence proofs",
        "Saddle-point and variational perspectives",
    ],
    "IEOR 266": [
        "Decomposition methods (Lagrangian/Benders style)",
        "First-order methods for large-scale optimization",
    ],
    "STAT 205A": [
        "Local asymptotic normality and Fisher efficiency",
    ],
    "STAT 205B": [
        "Decision-theoretic procedure comparison at advanced depth",
    ],
    "STAT 210A": [
        "Rigorous asymptotic distribution derivations",
    ],
    "STAT 210B": [
        "Semiparametric and high-dimensional inferential considerations",
    ],
    "IEOR 180": [
        "Dynamic hedging and incomplete-market tradeoffs",
    ],
    "MATH 202A": [
        "Deep measure/integration theorem chains and proof dependency maps",
    ],
    "MATH 202B": [
        "Functional analysis framing for probability/optimization operators",
    ],
    "STAT 260": [
        "Non-asymptotic error bounds in high dimensions",
        "Sparsity-restricted eigenvalue conditions",
    ],
    "CS 189": [
        "Generalization-optimization interplay in modern learning systems",
        "Model selection under computational and statistical budgets",
    ],
}


GLOBAL_CURRICULUM_ORDER: List[Tuple[str, List[str]]] = [
    (
        "Module A: Mathematical Reasoning and Proof Craft",
        [
            "Predicate logic fluency and quantifier control",
            "Induction schemas (weak/strong/structural) and recursive invariants",
            "Contradiction and contrapositive in theorem proving",
            "Constructive arguments and counterexample design",
            "Error-checking and proof auditing in long derivations",
        ],
    ),
    (
        "Module B: Foundations of Discrete Math and Probability",
        [
            "Counting methods and combinatorial structures",
            "Recurrences, generating functions, and asymptotic growth",
            "Probability axioms, conditioning, and transformations",
            "Random variables, concentration bounds, and probabilistic method",
        ],
    ),
    (
        "Module C: Linear Algebra, Dynamics, and Numerics",
        [
            "Linear transformations, eigenspaces, and spectral reasoning",
            "Least-squares geometry and matrix factorizations",
            "Linear ODE systems and stability analysis",
            "Numerical conditioning, stability, and iterative solvers",
        ],
    ),
    (
        "Module D: Analysis Core (Real/Complex/Measure)",
        [
            "Real-analysis limits, compactness, continuity, and integration",
            "Complex-variable tools: residues, contour methods, conformal maps",
            "Measure-theoretic integration and convergence theorems",
            "Functional viewpoints that support advanced probability/statistics",
        ],
    ),
    (
        "Module E: Algebra and Topology Maturity",
        [
            "Abstract structural thinking through groups/rings/fields",
            "Topological structure for continuity/compactness/connectedness",
            "Proof architecture in highly abstract settings",
        ],
    ),
    (
        "Module F: Optimization, OR Modeling, and Decision Science",
        [
            "LP/MIP/network formulations and solver-oriented structure",
            "Duality/KKT and sensitivity for interpretable decisions",
            "Decomposition and large-scale algorithmic optimization",
            "Dynamic and stochastic decision models under uncertainty",
        ],
    ),
    (
        "Module G: Stochastic Processes and Statistical Theory",
        [
            "Markov/renewal/martingale systems for sequential uncertainty",
            "Parametric and asymptotic inference at graduate rigor",
            "Decision-theoretic comparisons and risk-based methodology",
        ],
    ),
    (
        "Module H: High-Dimensional Stats and ML Theory",
        [
            "Regularization, sparsity, concentration, and non-asymptotic analysis",
            "Generalization theory and complexity control",
            "Optimization-statistics coupling in modern ML",
        ],
    ),
    (
        "Module I: Systems and Algorithmic Implementation",
        [
            "Data structures/algorithms implementation discipline",
            "Architecture-aware performance reasoning",
            "Computation-aware experimental methodology",
        ],
    ),
]


@dataclass
class SelectedResource:
    class_name: str
    topic: str
    category: str
    kind: str
    url: str
    local_pdf_rel: str
    domain: str
    solution_like: bool
    anchor: bool
    quality_score: int


def tex_escape(text: str) -> str:
    mapping = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(mapping.get(ch, ch) for ch in text)


def is_valid_pdf(path: Path) -> bool:
    if not path.exists() or path.stat().st_size == 0:
        return False
    try:
        with path.open("rb") as f:
            return f.read(5) == b"%PDF-"
    except Exception:
        return False


def is_problemish(category: str, url: str) -> bool:
    if category in PROBLEMISH_CATS:
        return True
    low = (url or "").lower()
    return any(k in low for k in PROBLEM_KWS + PROJECT_KWS + EXAM_KWS)


def is_solution_like(url: str, local_pdf_rel: str) -> bool:
    return bool(SOLUTION_RE.search(f"{(url or '').lower()} {(local_pdf_rel or '').lower()}"))


def assignment_stem(url: str, local_pdf_rel: str) -> str:
    name = ""
    if url:
        try:
            name = Path(urlparse(url).path).name
        except Exception:
            name = ""
    if not name:
        name = Path(local_pdf_rel).name
    name = name.lower()
    name = re.sub(r"\.(pdf|tex|txt|html?)$", "", name)
    name = SOLUTION_CLEAN_RE.sub("", name)
    name = re.sub(r"[^a-z0-9]+", "", name)
    if not name:
        name = "unknown"
    return name[:140]


def normalize_url(url: str) -> str:
    if not url:
        return ""
    try:
        p = urlparse(url)
        path = (p.path or "/").rstrip("/") or "/"
        return p._replace(
            scheme=p.scheme.lower(),
            netloc=p.netloc.lower(),
            path=path,
            query="",
            fragment="",
        ).geturl()
    except Exception:
        return url.strip()


def global_resource_key(url: str, local_pdf_rel: str) -> str:
    nu = normalize_url(url)
    if nu:
        return nu
    return f"local::{local_pdf_rel}"


def resource_domain(url: str) -> str:
    try:
        return (urlparse(url).netloc or "unknown").lower()
    except Exception:
        return "unknown"


def quality_score(category: str, kind: str, url: str) -> int:
    score = 0
    if category == "Problems":
        score += 40
    elif category == "Projects/Labs":
        score += 35
    elif category == "Exams":
        score += 30
    elif category == "Lectures/Notes":
        score += 12
    if kind == "downloaded_pdf":
        score += 30
    elif kind == "rendered_html":
        score += 10
    elif kind == "rendered_text":
        score += 8
    else:
        score += 4
    low = (url or "").lower()
    if ".edu" in low:
        score += 8
    if "berkeley" in low:
        score += 8
    if "mit.edu" in low or "stanford.edu" in low:
        score += 6
    if NOISE_RE.search(low):
        score -= 25
    return score


def load_builder_functions() -> Tuple[object, object]:
    ns = {}
    script = Path("scripts/build_or_applied_math_bible_chunked.py")
    exec(script.read_text(encoding="utf-8"), ns)  # noqa: S102
    return ns["class_order_and_topic_map"], ns["collect_class_resources"]


def load_reader_data() -> Tuple[Dict[str, str], Dict[str, List[str]]]:
    ns = {}
    script = Path("scripts/build_bible_reader_guide.py")
    exec(script.read_text(encoding="utf-8"), ns)  # noqa: S102
    return ns["CLASS_FOCUS"], ns["CLASS_OBJECTIVES"]


def class_topics(class_name: str) -> List[str]:
    keys = CLASS_TOPIC_KEYS.get(class_name, [])
    topics: List[str] = []
    seen = set()
    for key in keys:
        for t in TOPIC_LIBRARY.get(key, []):
            if t in seen:
                continue
            seen.add(t)
            topics.append(t)
    for t in CLASS_TOPIC_OVERRIDES.get(class_name, []):
        if t in seen:
            continue
        seen.add(t)
        topics.append(t)
    return topics


def dedupe_solution_variants(resources: List[SelectedResource], solution_only_keep: int) -> List[SelectedResource]:
    buckets: Dict[str, List[SelectedResource]] = defaultdict(list)
    for r in resources:
        key = assignment_stem(r.url, r.local_pdf_rel)
        buckets[key].append(r)

    out: List[SelectedResource] = []
    for _, items in buckets.items():
        non = [x for x in items if not x.solution_like]
        sol = [x for x in items if x.solution_like]
        non.sort(key=lambda x: (-x.quality_score, x.url))
        sol.sort(key=lambda x: (-x.quality_score, x.url))
        if non:
            out.extend(non)
        elif sol:
            out.extend(sol[:solution_only_keep])
    return out


def round_robin_domains(resources: List[SelectedResource], limit: int) -> List[SelectedResource]:
    buckets: Dict[str, deque[SelectedResource]] = {}
    for domain, items in defaultdict(list, ((r.domain, []) for r in resources)).items():
        _ = items
    tmp: Dict[str, List[SelectedResource]] = defaultdict(list)
    for r in resources:
        tmp[r.domain].append(r)
    for d, items in tmp.items():
        items.sort(key=lambda x: (-x.quality_score, x.solution_like, x.url))
        buckets[d] = deque(items)

    ordered_domains = sorted(buckets.keys(), key=lambda d: (-len(buckets[d]), d))
    out: List[SelectedResource] = []
    seen = set()
    while len(out) < limit and ordered_domains:
        next_domains: List[str] = []
        for d in ordered_domains:
            q = buckets[d]
            if not q:
                continue
            r = q.popleft()
            key = (normalize_url(r.url), r.local_pdf_rel)
            if key in seen:
                if q:
                    next_domains.append(d)
                continue
            seen.add(key)
            out.append(r)
            if len(out) >= limit:
                break
            if q:
                next_domains.append(d)
        ordered_domains = next_domains
    return out


def build_resource_pool(
    out_dir: Path,
    class_order: List[str],
    topic_for_class: Dict[str, str],
    collect_class_resources: object,
    enriched_manifest: Dict[str, object],
    max_per_class: int,
    min_per_class: int,
    solution_only_keep: int,
) -> Dict[str, List[SelectedResource]]:
    selected_by_class: Dict[str, List[SelectedResource]] = {}
    global_seen = set()

    for cls in class_order:
        topic = topic_for_class.get(cls, "Unassigned")
        info = collect_class_resources(out_dir, cls, enriched_manifest)
        pool: List[SelectedResource] = []

        for raw in info.get("pdf_resources", []):
            url = getattr(raw, "url", "")
            category = getattr(raw, "category", "")
            kind = getattr(raw, "kind", "")
            local_pdf_rel = getattr(raw, "local_pdf_rel", "")
            if not local_pdf_rel:
                continue
            pdf_path = out_dir / local_pdf_rel
            if not is_valid_pdf(pdf_path):
                continue
            if NOISE_RE.search((url or "").lower()):
                continue
            if not is_problemish(category, url):
                continue
            item = SelectedResource(
                class_name=cls,
                topic=topic,
                category=category,
                kind=kind,
                url=url,
                local_pdf_rel=local_pdf_rel,
                domain=resource_domain(url),
                solution_like=is_solution_like(url, local_pdf_rel),
                anchor=False,
                quality_score=quality_score(category, kind, url),
            )
            pool.append(item)

        # Keep non-solution variants whenever they exist.
        deduped = dedupe_solution_variants(pool, solution_only_keep=solution_only_keep)

        # Prefer clean downloaded PDFs, but keep rendered fallbacks when class coverage is sparse.
        downloaded = [r for r in deduped if r.kind == "downloaded_pdf"]
        rendered = [r for r in deduped if r.kind != "downloaded_pdf"]
        core = downloaded if len(downloaded) >= max(6, min_per_class // 2) else deduped

        chosen = round_robin_domains(core, limit=max_per_class)
        reserve_core = round_robin_domains(core, limit=max(5000, len(core)))

        # Fallback anchors (lectures/notes with exercises) when class has very sparse problem PDFs.
        anchor_candidates: List[SelectedResource] = []
        if len(chosen) < min_per_class:
            for raw in info.get("pdf_resources", []):
                url = getattr(raw, "url", "")
                category = getattr(raw, "category", "")
                kind = getattr(raw, "kind", "")
                local_pdf_rel = getattr(raw, "local_pdf_rel", "")
                if not local_pdf_rel:
                    continue
                if category != "Lectures/Notes":
                    continue
                if is_solution_like(url, local_pdf_rel):
                    continue
                low = (url or "").lower()
                if not any(k in low for k in ("lecture", "notes", "chapter", "worksheet", "recitation")):
                    continue
                pdf_path = out_dir / local_pdf_rel
                if not is_valid_pdf(pdf_path):
                    continue
                anchor_candidates.append(
                    SelectedResource(
                        class_name=cls,
                        topic=topic,
                        category=category,
                        kind=kind,
                        url=url,
                        local_pdf_rel=local_pdf_rel,
                        domain=resource_domain(url),
                        solution_like=False,
                        anchor=True,
                        quality_score=quality_score(category, kind, url),
                    )
                )
            anchors = round_robin_domains(anchor_candidates, limit=max(0, min_per_class - len(chosen)))
            seen = {(normalize_url(r.url), r.local_pdf_rel) for r in chosen}
            for r in anchors:
                key = (normalize_url(r.url), r.local_pdf_rel)
                if key in seen:
                    continue
                chosen.append(r)
                seen.add(key)
        else:
            anchor_candidates = []

        # Global de-duplication across classes: avoid repeating identical source PDFs.
        filtered: List[SelectedResource] = []
        for r in chosen:
            gk = global_resource_key(r.url, r.local_pdf_rel)
            if gk in global_seen:
                continue
            filtered.append(r)
            global_seen.add(gk)

        # Refill class coverage from reserves without violating global uniqueness.
        reserves = reserve_core + round_robin_domains(anchor_candidates, limit=max(500, len(anchor_candidates)))
        for r in reserves:
            if len(filtered) >= max_per_class:
                break
            gk = global_resource_key(r.url, r.local_pdf_rel)
            if gk in global_seen:
                continue
            filtered.append(r)
            global_seen.add(gk)

        # If still under-covered, allow controlled duplicate fallback to preserve class coverage.
        if len(filtered) < min_per_class:
            local_seen = {(normalize_url(r.url), r.local_pdf_rel) for r in filtered}
            for r in reserves:
                if len(filtered) >= min_per_class:
                    break
                lk = (normalize_url(r.url), r.local_pdf_rel)
                if lk in local_seen:
                    continue
                filtered.append(r)
                local_seen.add(lk)

        filtered.sort(key=lambda x: (x.anchor, x.solution_like, -x.quality_score, x.url))
        selected_by_class[cls] = filtered[:max_per_class]

    return selected_by_class


def write_resource_manifest(out_dir: Path, selected_by_class: Dict[str, List[SelectedResource]]) -> Path:
    payload = {
        cls: [
            {
                "class": r.class_name,
                "topic": r.topic,
                "category": r.category,
                "kind": r.kind,
                "url": r.url,
                "local_pdf_rel": r.local_pdf_rel,
                "domain": r.domain,
                "solution_like": r.solution_like,
                "anchor": r.anchor,
                "quality_score": r.quality_score,
            }
            for r in rows
        ]
        for cls, rows in selected_by_class.items()
    }
    path = out_dir / "phd_problem_solving_bible_resources.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def write_guide_tex(
    out_dir: Path,
    class_order: List[str],
    topic_for_class: Dict[str, str],
    selected_by_class: Dict[str, List[SelectedResource]],
    class_focus: Dict[str, str],
    class_objectives: Dict[str, List[str]],
    max_index_rows_per_class: int,
) -> Path:
    tex_path = out_dir / "phd_problem_solving_bible_guide.tex"
    all_topics: List[str] = []
    for cls in class_order:
        all_topics.extend(class_topics(cls))
    unique_topics = sorted(set(all_topics))

    total_resources = sum(len(v) for v in selected_by_class.values())
    total_solution = sum(sum(1 for r in rows if r.solution_like) for rows in selected_by_class.values())

    lines: List[str] = [
        r"\documentclass[11pt,oneside]{book}",
        r"\usepackage[margin=1in]{geometry}",
        r"\usepackage[T1]{fontenc}",
        r"\usepackage[utf8]{inputenc}",
        r"\usepackage{lmodern}",
        r"\usepackage{microtype}",
        r"\usepackage[dvipsnames,table]{xcolor}",
        r"\usepackage{hyperref}",
        r"\usepackage{xurl}",
        r"\usepackage{longtable}",
        r"\usepackage{booktabs}",
        r"\usepackage{enumitem}",
        r"\usepackage[most]{tcolorbox}",
        r"\hypersetup{colorlinks=true,linkcolor=MidnightBlue,urlcolor=MidnightBlue}",
        r"\title{OR and Applied Mathematics Problem-Solving Bible}",
        r"\author{Professor-Style PhD Preparation Edition}",
        r"\date{" + datetime.now().strftime("%Y-%m-%d") + r"}",
        r"\begin{document}",
        r"\maketitle",
        r"\tableofcontents",
        r"\chapter*{How to Use This Bible}",
        r"\addcontentsline{toc}{chapter}{How to Use This Bible}",
        r"\begin{tcolorbox}[colback=blue!4,colframe=MidnightBlue,title=Pedagogical Contract]",
        r"This volume is designed as an intensive apprenticeship manual.",
        r"You are expected to solve first, reflect second, and only then consult hints/solutions.",
        r"\end{tcolorbox}",
        r"\begin{itemize}[leftmargin=1.2em]",
        r"\item Curated problem resources selected: " + str(total_resources),
        r"\item Solution-like resources retained only as sparse fallback: " + str(total_solution),
        r"\item Class coverage: " + str(len(class_order)) + r" classes",
        r"\item Study mode: proof-first, model-first, computation-aware, and synthesis-driven",
        r"\end{itemize}",
        r"\section*{Weekly Execution Pattern}",
        r"\begin{enumerate}[leftmargin=1.4em]",
        r"\item Concept extraction: definitions, assumptions, theorem statements.",
        r"\item Problem sprint: complete targeted assignment blocks under time constraints.",
        r"\item Solution writing: produce polished proofs/modeling writeups.",
        r"\item Synthesis: summarize transferable techniques and failure modes.",
        r"\end{enumerate}",
        r"\chapter*{Global Curriculum (Syllabus-Mapped)}",
        r"\addcontentsline{toc}{chapter}{Global Curriculum (Syllabus-Mapped)}",
    ]

    for module, topics in GLOBAL_CURRICULUM_ORDER:
        lines.append(r"\section*{" + tex_escape(module) + r"}")
        lines.append(r"\begin{itemize}[leftmargin=1.2em]")
        for t in topics:
            lines.append(r"\item " + tex_escape(t))
        lines.append(r"\end{itemize}")

    lines.extend(
        [
            r"\chapter*{Complete Topic Checklist}",
            r"\addcontentsline{toc}{chapter}{Complete Topic Checklist}",
            r"\begin{longtable}{p{0.07\textwidth}p{0.87\textwidth}}",
            r"\toprule",
            r"\# & Topic to Master \\",
            r"\midrule",
            r"\endfirsthead",
            r"\toprule",
            r"\# & Topic to Master \\",
            r"\midrule",
            r"\endhead",
        ]
    )
    for i, topic in enumerate(unique_topics, start=1):
        lines.append(rf"{i} & {tex_escape(topic)} \\")
    lines.extend([r"\bottomrule", r"\end{longtable}"])

    lines.extend(
        [
            r"\chapter*{Class-by-Class Blueprint}",
            r"\addcontentsline{toc}{chapter}{Class-by-Class Blueprint}",
        ]
    )

    for cls in class_order:
        rows = selected_by_class.get(cls, [])
        focus = class_focus.get(cls, "Core training for OR/applied mathematics maturity.")
        objectives = class_objectives.get(
            cls,
            [
                "Achieve fluency with the core definitions and theorem statements.",
                "Solve representative problem sets without solution dependence.",
                "Produce concise, proof-quality writeups and post-solution diagnostics.",
            ],
        )
        topics = class_topics(cls)
        by_domain = Counter(r.domain for r in rows)
        domain_items = by_domain.most_common(8)

        lines.append(r"\section*{" + tex_escape(cls) + r"}")
        lines.append(r"\addcontentsline{toc}{section}{" + tex_escape(cls) + r"}")
        lines.append(r"\noindent\textbf{Curriculum role:} " + tex_escape(topic_for_class.get(cls, "Unassigned")) + r"\\")
        lines.append(r"\noindent\textbf{Instructional focus:} " + tex_escape(focus) + r"\\")
        lines.append(r"\noindent\textbf{Curated resources included in final PDF:} " + str(len(rows)))

        lines.append(r"\subsection*{Syllabus Topics to Master}")
        lines.append(r"\begin{itemize}[leftmargin=1.2em]")
        for t in topics:
            lines.append(r"\item " + tex_escape(t))
        lines.append(r"\end{itemize}")

        lines.append(r"\subsection*{Mastery Outcomes}")
        lines.append(r"\begin{itemize}[leftmargin=1.2em]")
        for o in objectives:
            lines.append(r"\item " + tex_escape(o))
        lines.append(r"\end{itemize}")

        if domain_items:
            lines.extend(
                [
                    r"\subsection*{Source Diversity Snapshot}",
                    r"\begin{longtable}{p{0.62\textwidth}p{0.18\textwidth}}",
                    r"\toprule",
                    r"Domain & Resources \\",
                    r"\midrule",
                    r"\endfirsthead",
                    r"\toprule",
                    r"Domain & Resources \\",
                    r"\midrule",
                    r"\endhead",
                ]
            )
            for d, n in domain_items:
                lines.append(rf"{tex_escape(d)} & {n} \\")
            lines.extend([r"\bottomrule", r"\end{longtable}"])

        lines.extend(
            [
                r"\subsection*{Curated Problem Index}",
                r"\begin{longtable}{p{0.05\textwidth}p{0.13\textwidth}p{0.14\textwidth}p{0.63\textwidth}}",
                r"\toprule",
                r"\# & Type & Format & URL \\",
                r"\midrule",
                r"\endfirsthead",
                r"\toprule",
                r"\# & Type & Format & URL \\",
                r"\midrule",
                r"\endhead",
            ]
        )
        for i, r in enumerate(rows[:max_index_rows_per_class], start=1):
            cat = tex_escape(r.category + (" (anchor)" if r.anchor else ""))
            fmt = tex_escape(r.kind + ("; fallback-solution" if r.solution_like else ""))
            lines.append(rf"{i} & {cat} & {fmt} & \url{{{r.url}}} \\")
        lines.extend([r"\bottomrule", r"\end{longtable}"])
        if len(rows) > max_index_rows_per_class:
            lines.append(
                rf"\noindent\textit{{Showing first {max_index_rows_per_class}. Full class list is in }}"
                + r"\texttt{\detokenize{phd_problem_solving_bible_resources.json}}."
            )

    lines.extend(
        [
            r"\chapter*{Promotion Gates}",
            r"\addcontentsline{toc}{chapter}{Promotion Gates}",
            r"\begin{itemize}[leftmargin=1.2em]",
            r"\item Gate 1 (Foundations): solve discrete/probability/linear-algebra core sets with full written proofs.",
            r"\item Gate 2 (OR Core): formulate and solve LP/MIP/stochastic models with dual/sensitivity interpretation.",
            r"\item Gate 3 (Theory Core): prove inference/probability results with explicit assumptions and asymptotic logic.",
            r"\item Gate 4 (Frontier): execute high-dimensional and ML-theory problems with non-asymptotic arguments.",
            r"\item Gate 5 (Synthesis): complete mixed-topic exams and produce research-style technical notes.",
            r"\end{itemize}",
            r"\end{document}",
        ]
    )

    tex_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return tex_path


def compile_tex(workdir: Path, tex_path: Path) -> Path:
    env = os.environ.copy()
    env["LC_ALL"] = "en_US.UTF-8"
    env["LANG"] = "en_US.UTF-8"
    env["LC_CTYPE"] = "en_US.UTF-8"
    cmd = [
        "/Library/TeX/texbin/latexmk",
        "-pdf",
        "-interaction=nonstopmode",
        "-halt-on-error",
        tex_path.name,
    ]
    proc = subprocess.run(cmd, cwd=workdir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    if proc.returncode != 0:
        raise RuntimeError(
            "latexmk failed.\n"
            f"stdout_tail:\n{proc.stdout[-3000:]}\n\n"
            f"stderr_tail:\n{proc.stderr[-3000:]}"
        )
    pdf_path = tex_path.with_suffix(".pdf")
    if not is_valid_pdf(pdf_path):
        raise RuntimeError(f"Expected guide PDF missing/invalid: {pdf_path}")
    return pdf_path


def write_class_divider(divider_pdf: Path, class_name: str, topic: str, count: int) -> None:
    divider_pdf.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(divider_pdf), pagesize=letter)
    w, h = letter
    c.setFont("Helvetica-Bold", 22)
    c.drawString(60, h - 120, class_name)
    c.setFont("Helvetica", 13)
    c.drawString(60, h - 160, f"Track: {topic}")
    c.drawString(60, h - 182, f"Curated resources appended: {count}")
    c.setFont("Helvetica-Oblique", 11)
    c.drawString(60, h - 228, "Solve first. Write complete proofs/modeling steps. Use solutions only as last resort.")
    c.showPage()
    c.save()


def append_pdf(writer: PdfWriter, pdf_path: Path) -> int:
    try:
        reader = PdfReader(str(pdf_path), strict=False)
        for page in reader.pages:
            writer.add_page(page)
        return len(reader.pages)
    except Exception:
        return 0


def build_final_pdf(
    out_dir: Path,
    class_order: List[str],
    topic_for_class: Dict[str, str],
    selected_by_class: Dict[str, List[SelectedResource]],
    guide_pdf: Path,
) -> Tuple[Path, Dict[str, int], int]:
    writer = PdfWriter()
    pages_total = 0
    class_pages: Dict[str, int] = {}

    pages_total += append_pdf(writer, guide_pdf)

    divider_dir = out_dir / "_phd_bible_dividers"
    divider_dir.mkdir(parents=True, exist_ok=True)

    for cls in class_order:
        rows = selected_by_class.get(cls, [])
        divider = divider_dir / f"{re.sub(r'[^a-z0-9]+', '_', cls.lower()).strip('_')}.pdf"
        write_class_divider(divider, cls, topic_for_class.get(cls, "Unassigned"), len(rows))
        pages_total += append_pdf(writer, divider)

        cls_pages = 0
        for r in rows:
            pdf = out_dir / r.local_pdf_rel
            if not is_valid_pdf(pdf):
                continue
            cls_pages += append_pdf(writer, pdf)
        class_pages[cls] = cls_pages

    final_pdf = out_dir / "phd_problem_solving_bible.pdf"
    with final_pdf.open("wb") as f:
        writer.write(f)
    if not is_valid_pdf(final_pdf):
        raise RuntimeError("Final bible PDF was not produced correctly.")
    return final_pdf, class_pages, pages_total


def write_summary(
    out_dir: Path,
    class_order: List[str],
    selected_by_class: Dict[str, List[SelectedResource]],
    class_pages: Dict[str, int],
    guide_pdf: Path,
    final_pdf: Path,
) -> Path:
    summary = {
        "generated_at": datetime.now().isoformat(),
        "guide_pdf": str(guide_pdf),
        "final_pdf": str(final_pdf),
        "total_classes": len(class_order),
        "total_selected_resources": sum(len(v) for v in selected_by_class.values()),
        "total_solution_like_resources": sum(
            sum(1 for r in rows if r.solution_like) for rows in selected_by_class.values()
        ),
        "total_anchor_resources": sum(sum(1 for r in rows if r.anchor) for rows in selected_by_class.values()),
        "class_summary": {
            cls: {
                "selected_resources": len(selected_by_class.get(cls, [])),
                "solution_like_resources": sum(1 for r in selected_by_class.get(cls, []) if r.solution_like),
                "anchor_resources": sum(1 for r in selected_by_class.get(cls, []) if r.anchor),
                "estimated_pages_appended": class_pages.get(cls, 0),
                "top_domains": Counter(r.domain for r in selected_by_class.get(cls, [])).most_common(8),
                "topics_count": len(class_topics(cls)),
            }
            for cls in class_order
        },
    }
    path = out_dir / "phd_problem_solving_bible_summary.json"
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return path


def run(
    out_dir: Path,
    max_per_class: int,
    min_per_class: int,
    solution_only_keep: int,
    max_index_rows_per_class: int,
) -> None:
    out_dir = out_dir.resolve()

    class_order_fn, collect_class_resources = load_builder_functions()
    class_focus, class_objectives = load_reader_data()
    class_order, topic_for_class = class_order_fn()

    enriched_manifest = {}
    enriched_path = out_dir / "enriched_manifest.json"
    if enriched_path.exists():
        enriched_manifest = json.loads(enriched_path.read_text(encoding="utf-8"))

    selected_by_class = build_resource_pool(
        out_dir=out_dir,
        class_order=class_order,
        topic_for_class=topic_for_class,
        collect_class_resources=collect_class_resources,
        enriched_manifest=enriched_manifest,
        max_per_class=max_per_class,
        min_per_class=min_per_class,
        solution_only_keep=solution_only_keep,
    )

    resources_manifest = write_resource_manifest(out_dir, selected_by_class)
    guide_tex = write_guide_tex(
        out_dir=out_dir,
        class_order=class_order,
        topic_for_class=topic_for_class,
        selected_by_class=selected_by_class,
        class_focus=class_focus,
        class_objectives=class_objectives,
        max_index_rows_per_class=max_index_rows_per_class,
    )
    guide_pdf = compile_tex(out_dir, guide_tex)

    final_pdf, class_pages, _ = build_final_pdf(
        out_dir=out_dir,
        class_order=class_order,
        topic_for_class=topic_for_class,
        selected_by_class=selected_by_class,
        guide_pdf=guide_pdf,
    )
    summary_path = write_summary(
        out_dir=out_dir,
        class_order=class_order,
        selected_by_class=selected_by_class,
        class_pages=class_pages,
        guide_pdf=guide_pdf,
        final_pdf=final_pdf,
    )

    print(f"Wrote resource manifest: {resources_manifest}")
    print(f"Wrote guide TeX: {guide_tex}")
    print(f"Wrote guide PDF: {guide_pdf}")
    print(f"Wrote final bible PDF: {final_pdf}")
    print(f"Wrote summary: {summary_path}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir", type=Path, default=Path("data/assignment_pdf_bundles"))
    p.add_argument(
        "--max-per-class",
        type=int,
        default=45,
        help="Maximum resources to append per class.",
    )
    p.add_argument(
        "--min-per-class",
        type=int,
        default=10,
        help="Minimum target resources per class (using lecture anchors if needed).",
    )
    p.add_argument(
        "--solution-only-keep",
        type=int,
        default=1,
        help="Maximum solution-only fallback resources kept per assignment stem.",
    )
    p.add_argument(
        "--max-index-rows-per-class",
        type=int,
        default=60,
        help="Rows per class shown in the guide's curated index table.",
    )
    args = p.parse_args()
    run(
        out_dir=args.out_dir,
        max_per_class=args.max_per_class,
        min_per_class=args.min_per_class,
        solution_only_keep=args.solution_only_keep,
        max_index_rows_per_class=args.max_index_rows_per_class,
    )


if __name__ == "__main__":
    main()
