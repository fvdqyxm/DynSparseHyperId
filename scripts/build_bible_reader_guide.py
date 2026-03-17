#!/usr/bin/env python3
"""
Build a comprehensive reader companion for the OR + Applied Math Bible.

Outputs:
- data/assignment_pdf_bundles/or_applied_math_bible_reader_guide.tex
- data/assignment_pdf_bundles/or_applied_math_bible_reader_guide.pdf
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple


CLASS_FOCUS: Dict[str, str] = {
    "CS 70": "Proofs, discrete structures, counting, and probability foundations.",
    "IEOR 160": "Deterministic optimization modeling and linear programming fundamentals.",
    "MATH 54": "Linear algebra and differential equations for modeling and dynamics.",
    "MATH 110": "Proof-oriented linear algebra and spectral structure.",
    "MATH 104": "Rigorous real analysis foundations for advanced probability/statistics.",
    "MATH 105": "Complex analysis tools that sharpen analytic technique.",
    "CS 61B": "Data structures and algorithmic implementation in Java.",
    "CS 170": "Algorithm design paradigms and complexity-aware problem solving.",
    "CS 61C": "Computer architecture and performance reasoning.",
    "MATH 128A": "Numerical methods and error analysis for computation.",
    "MATH 128B": "Advanced numerical linear algebra and iterative methods.",
    "MATH 220": "Probability theory with a rigorous mathematical backbone.",
    "STAT 150": "Statistical modeling and inference from a probabilistic perspective.",
    "IEOR 162": "Dynamic/uncertain decision models and sequential reasoning.",
    "IEOR 169": "Stochastic OR modeling under uncertainty and risk.",
    "IEOR 261": "Advanced optimization methods used in graduate OR.",
    "IEOR 266": "Large-scale optimization and computational OR techniques.",
    "IEOR 263A": "Stochastic processes and probabilistic systems in OR.",
    "IEOR 263B": "Advanced stochastic modeling and process analysis.",
    "STAT 205A": "Graduate mathematical statistics and asymptotic reasoning.",
    "STAT 205B": "Advanced inference theory and decision-theoretic structure.",
    "STAT 210A": "Theoretical statistics sequence: core advanced foundations.",
    "STAT 210B": "Continuation of rigorous statistics and asymptotic tools.",
    "IEOR 221": "High-level optimization modeling and analytical formulation practice.",
    "IEOR 222": "Advanced optimization applications and structural problem classes.",
    "IEOR 180": "Financial engineering and optimization under market uncertainty.",
    "IEOR 269": "Specialized advanced OR topics and research-level modeling.",
    "MATH 185": "Complex-variable methods and deeper analytic maturity.",
    "MATH 202A": "Graduate real analysis and measure-theoretic rigor.",
    "MATH 202B": "Continuation of graduate analysis and functional viewpoint.",
    "MATH 113": "Abstract algebra foundations and proof fluency.",
    "MATH 142": "Topology foundations and abstract structural reasoning.",
    "MATH 142B": "Advanced topology and deeper proof architecture.",
    "STAT 260": "High-dimensional statistics and modern theoretical tools.",
    "CS 189": "Machine learning theory and statistical learning principles.",
}


CLASS_OBJECTIVES: Dict[str, List[str]] = {
    "CS 70": [
        "Write correct proofs using induction, contradiction, and invariants.",
        "Solve nontrivial counting and recurrence problems.",
        "Use core probability laws fluently for random-variable reasoning.",
    ],
    "IEOR 160": [
        "Model real decision systems as LPs with clear variables/constraints.",
        "Interpret dual variables and sensitivity economically.",
        "Prove optimality using primal-dual/KKT-style arguments.",
    ],
    "MATH 54": [
        "Work confidently with linear transformations, eigen-structure, and diagonalization.",
        "Solve linear ODE systems and interpret stability qualitatively.",
        "Translate dynamical models between algebraic and geometric views.",
    ],
    "MATH 110": [
        "Produce rigorous proofs about vector spaces and operators.",
        "Use canonical forms/spectral ideas in abstraction-heavy arguments.",
        "Connect finite-dimensional theory to optimization/statistics structure.",
    ],
    "MATH 104": [
        "Prove key convergence/continuity/compactness theorems cleanly.",
        "Control epsilon-delta arguments without gaps.",
        "Use analysis rigor in probability/statistics proofs.",
    ],
    "MATH 105": [
        "Use contour methods and analytic-function tools correctly.",
        "Apply complex methods to integrals/transforms in applied contexts.",
        "Reason rigorously with analytic continuation and singularities.",
    ],
    "CS 61B": [
        "Implement core data structures with reliable invariants and tests.",
        "Analyze runtime/space tradeoffs and justify design choices.",
        "Refactor and debug larger codebases with disciplined workflow.",
    ],
    "CS 170": [
        "Design algorithms from graph, DP, greedy, and flow paradigms.",
        "Prove correctness and bound complexity tightly.",
        "Recognize reductions and hardness patterns in new problems.",
    ],
    "CS 61C": [
        "Explain machine-level performance implications of software decisions.",
        "Reason about memory hierarchy and parallel throughput tradeoffs.",
        "Profile and optimize computational kernels effectively.",
    ],
    "MATH 128A": [
        "Quantify numerical error/stability in approximation pipelines.",
        "Implement and compare root-finding/interpolation/integration schemes.",
        "Choose algorithms based on conditioning and complexity.",
    ],
    "MATH 128B": [
        "Apply iterative linear solvers and convergence criteria correctly.",
        "Use matrix factorizations for robust numerical workflows.",
        "Diagnose numerical pathologies and propose fixes.",
    ],
    "MATH 220": [
        "Work rigorously with distributions, expectations, and convergence modes.",
        "Use conditioning/martingale-style logic where appropriate.",
        "Prove foundational probability results cleanly.",
    ],
    "STAT 150": [
        "Construct estimators/tests from modeling assumptions.",
        "Diagnose model misfit and uncertainty quantification limits.",
        "Interpret inference results with assumptions explicit.",
    ],
    "IEOR 162": [
        "Formulate sequential decision problems under uncertainty.",
        "Use dynamic reasoning/value-function structure effectively.",
        "Compare policy quality with principled performance metrics.",
    ],
    "IEOR 169": [
        "Model random systems with tractable stochastic approximations.",
        "Evaluate risk-sensitive decisions under uncertainty.",
        "Communicate stochastic model assumptions clearly.",
    ],
    "IEOR 261": [
        "Derive and analyze advanced optimization algorithms.",
        "Use convexity/duality structure to simplify difficult models.",
        "Prove convergence/optimality properties where expected.",
    ],
    "IEOR 266": [
        "Handle large-scale optimization via decomposition/first-order methods.",
        "Balance mathematical guarantees with computational feasibility.",
        "Benchmark algorithm choices on realistic instances.",
    ],
    "IEOR 263A": [
        "Model stochastic processes used in OR systems.",
        "Compute/approximate long-run and transient performance metrics.",
        "Connect process assumptions to decision quality.",
    ],
    "IEOR 263B": [
        "Extend stochastic process methods to harder dependence structures.",
        "Use process-limit ideas to justify approximations.",
        "Perform deeper probabilistic performance analysis.",
    ],
    "STAT 205A": [
        "Prove key estimation properties in parametric frameworks.",
        "Use asymptotics as a design and diagnostic tool.",
        "Compare procedures through risk/efficiency arguments.",
    ],
    "STAT 205B": [
        "Handle advanced inference problems with full regularity reasoning.",
        "Apply decision-theoretic framing to estimator/test comparison.",
        "Write concise theorem-proof style statistical arguments.",
    ],
    "STAT 210A": [
        "Master graduate-level inferential foundations and asymptotic techniques.",
        "Build proofs that bridge measure theory and inference.",
        "Analyze nontrivial estimator behavior under perturbations.",
    ],
    "STAT 210B": [
        "Extend theoretical statistics to advanced model classes.",
        "Use asymptotic expansions/approximations carefully.",
        "Reason about robustness and identifiability limits.",
    ],
    "IEOR 221": [
        "Build advanced optimization models from messy decision settings.",
        "Use structure to simplify and solve difficult formulations.",
        "Defend modeling assumptions and practical implications.",
    ],
    "IEOR 222": [
        "Analyze specialized optimization classes with tailored methods.",
        "Choose between exact and approximate strategies rationally.",
        "Report solution quality with transparent diagnostics.",
    ],
    "IEOR 180": [
        "Model financial decisions with optimization and uncertainty.",
        "Interpret risk-return tradeoffs mathematically.",
        "Stress-test model outputs under scenario variation.",
    ],
    "IEOR 269": [
        "Integrate multiple OR techniques on advanced topic families.",
        "Read and reproduce research-grade modeling arguments.",
        "Propose extensions to canonical formulations.",
    ],
    "MATH 185": [
        "Apply advanced analytic methods in proof and application settings.",
        "Use transform/complex-variable tools in rigorous derivations.",
        "Increase fluency in long-form technical proofs.",
    ],
    "MATH 202A": [
        "Operate comfortably in measure-theoretic analysis.",
        "Prove deep convergence/integration results rigorously.",
        "Use analysis tools in advanced probability/statistics contexts.",
    ],
    "MATH 202B": [
        "Extend analysis maturity to functional/operator viewpoints.",
        "Construct clean proofs in abstract spaces.",
        "Bridge analysis foundations to research-level modeling.",
    ],
    "MATH 113": [
        "Manipulate algebraic structures with proof fluency.",
        "Recognize structural invariants and homomorphic reasoning.",
        "Write concise abstract algebra arguments.",
    ],
    "MATH 142": [
        "Use topological concepts to reason about continuity/compactness deeply.",
        "Build and test counterexamples in abstract spaces.",
        "Translate geometric intuition into rigorous statements.",
    ],
    "MATH 142B": [
        "Handle advanced topology constructions and theorem chains.",
        "Prove statements with precise structural dependencies.",
        "Leverage topology maturity in analysis/optimization contexts.",
    ],
    "STAT 260": [
        "Use concentration, regularization, and sparsity tools rigorously.",
        "Analyze high-dimensional estimators beyond low-dimensional intuition.",
        "Connect theory guarantees to computational procedures.",
    ],
    "CS 189": [
        "Derive learning objectives and optimization procedures from first principles.",
        "Analyze generalization/overfitting with statistical learning tools.",
        "Compare model classes with principled theoretical criteria.",
    ],
}


DEFAULT_OBJECTIVES = [
    "Master the core definitions, theorems, and modeling patterns.",
    "Solve representative problem sets without solution reliance.",
    "Produce proof-quality written solutions and post-hoc reflections.",
]


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


def load_json(path: Path) -> Dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def class_order_and_topic_map() -> Tuple[List[str], Dict[str, str]]:
    ns = {}
    script = Path("scripts/build_or_applied_math_bible_chunked.py")
    exec(script.read_text(encoding="utf-8"), ns)  # noqa: S102
    fn = ns["class_order_and_topic_map"]
    return fn()


def class_first_month(schedule: List[Dict[str, object]], class_name: str) -> str:
    for row in schedule:
        if row.get("mode") != "core":
            continue
        for unit in row.get("units", []):
            if unit.get("class") == class_name:
                return str(row.get("month_label", ""))
    return "N/A"


def write_tex(
    out_dir: Path,
    class_order: List[str],
    topic_for_class: Dict[str, str],
    class_summary: Dict[str, Dict[str, int]],
    schedule: List[Dict[str, object]],
) -> Path:
    tex_path = out_dir / "or_applied_math_bible_reader_guide.tex"
    lines: List[str] = [
        r"\documentclass[11pt]{book}",
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
        r"\title{OR + Applied Math Bible: Reader Companion and Mastery Guide}",
        r"\author{Prerequisite-First PhD Preparation Edition}",
        r"\date{}",
        r"\begin{document}",
        r"\maketitle",
        r"\tableofcontents",
        r"\chapter*{How To Use This Guide}",
        r"\addcontentsline{toc}{chapter}{How To Use This Guide}",
        r"\begin{tcolorbox}[colback=blue!4,colframe=MidnightBlue,title=Mission]",
        r"This guide defines what mastery looks like after every step in the Bible.",
        r"It is built for long-horizon preparation for top-tier OR and applied mathematics PhD work.",
        r"\end{tcolorbox}",
        r"\section*{End-State Target}",
        r"\begin{itemize}[leftmargin=1.2em]",
        r"\item You can formulate, analyze, and solve deterministic and stochastic OR models rigorously.",
        r"\item You can prove core theorems across analysis, probability, statistics, and optimization.",
        r"\item You can implement and benchmark algorithms with clear complexity and numerical reasoning.",
        r"\item You can read research papers and reproduce central derivations without handwaving.",
        r"\end{itemize}",
        r"\section*{Execution Pattern For Every Step}",
        r"\begin{enumerate}[leftmargin=1.4em]",
        r"\item Theory pass: extract definitions/theorems/assumptions from lectures and notes.",
        r"\item Problem pass: complete core assignment sets under timed and untimed conditions.",
        r"\item Synthesis pass: write concise summaries of methods, failure modes, and transfer patterns.",
        r"\item Promotion gate: verify objective-level mastery before moving forward.",
        r"\end{enumerate}",
        r"\chapter*{Ordered Roadmap}",
        r"\addcontentsline{toc}{chapter}{Ordered Roadmap}",
        r"\begin{longtable}{p{0.06\textwidth}p{0.16\textwidth}p{0.13\textwidth}p{0.10\textwidth}p{0.11\textwidth}p{0.36\textwidth}}",
        r"\toprule",
        r"Step & Class & First Month & Parts & PDFs & Purpose \\",
        r"\midrule",
        r"\endfirsthead",
        r"\toprule",
        r"Step & Class & First Month & Parts & PDFs & Purpose \\",
        r"\midrule",
        r"\endhead",
    ]

    for i, cls in enumerate(class_order, start=1):
        info = class_summary.get(cls, {"parts": 0, "pdf_resources": 0})
        first_month = class_first_month(schedule, cls)
        purpose = CLASS_FOCUS.get(cls, "Core technical development.")
        lines.append(
            rf"{i} & {tex_escape(cls)} & {tex_escape(first_month)} & {info.get('parts', 0)} & "
            rf"{info.get('pdf_resources', 0)} & {tex_escape(purpose)} \\"
        )
    lines.extend([r"\bottomrule", r"\end{longtable}"])

    lines.append(r"\chapter*{Step-by-Step Mastery Contract}")
    lines.append(r"\addcontentsline{toc}{chapter}{Step-by-Step Mastery Contract}")

    for i, cls in enumerate(class_order, start=1):
        info = class_summary.get(cls, {"parts": 0, "pdf_resources": 0})
        topic = topic_for_class.get(cls, "Core Track")
        first_month = class_first_month(schedule, cls)
        objectives = CLASS_OBJECTIVES.get(cls, DEFAULT_OBJECTIVES)
        next_cls = class_order[i] if i < len(class_order) else "Capstone Integration"
        focus = CLASS_FOCUS.get(cls, "Core technical development.")
        lines.extend(
            [
                rf"\section*{{Step {i}: {tex_escape(cls)}}}",
                rf"\noindent\textbf{{Track:}} {tex_escape(topic)}\\",
                rf"\noindent\textbf{{Recommended first month:}} {tex_escape(first_month)}\\",
                rf"\noindent\textbf{{Bible coverage:}} {info.get('parts', 0)} part(s), {info.get('pdf_resources', 0)} PDF resource(s).",
                r"\begin{tcolorbox}[colback=gray!5,colframe=black,title=Why This Step Exists]",
                tex_escape(focus),
                r"\end{tcolorbox}",
                r"\textbf{By the end of this step, you should be able to:}",
                r"\begin{itemize}[leftmargin=1.2em]",
            ]
        )
        for obj in objectives:
            lines.append(rf"\item {tex_escape(obj)}")
        lines.extend(
            [
                r"\end{itemize}",
                r"\textbf{Minimum evidence artifacts:}",
                r"\begin{itemize}[leftmargin=1.2em]",
                r"\item One complete set of clean, proof-quality writeups from the step's hardest assignments.",
                r"\item One 2--4 page synthesis memo: methods, assumptions, common mistakes, transfer links.",
                r"\item One timed set (or oral board-style self exam) with post-mortem error analysis.",
                r"\end{itemize}",
                r"\textbf{Promotion gate (before advancing):}",
                r"\begin{itemize}[leftmargin=1.2em]",
                r"\item Solve at least 80\% of core problems without external hints.",
                r"\item Explain key results and methods aloud from memory to a graduate-level audience.",
                r"\item Demonstrate transfer by solving one fresh problem not drawn from assigned sets.",
                r"\end{itemize}",
                r"\noindent\textbf{Bridge to next step:} "
                + tex_escape(f"This step should make {next_cls} easier and more coherent."),
                r"\vspace{0.8em}",
            ]
        )

    lines.extend(
        [
            r"\chapter*{Final Integration Goal}",
            r"\addcontentsline{toc}{chapter}{Final Integration Goal}",
            r"\begin{tcolorbox}[colback=green!4,colframe=ForestGreen,title=What Completion Should Feel Like]",
            r"You should be able to treat OR/applied math problems as one integrated language: "
            r"modeling, proof, computation, statistics, and learning all reinforcing each other.",
            r"\end{tcolorbox}",
            r"\begin{itemize}[leftmargin=1.2em]",
            r"\item Run end-to-end from formulation to proof to implementation to interpretation.",
            r"\item Defend modeling assumptions and theorem conditions under questioning.",
            r"\item Transition into graduate coursework and research with minimal remediation.",
            r"\end{itemize}",
            r"\end{document}",
        ]
    )
    tex_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return tex_path


def compile_tex(out_dir: Path, tex_path: Path) -> Path:
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
    proc = subprocess.run(cmd, cwd=out_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    if proc.returncode != 0:
        raise RuntimeError(
            "latexmk failed.\n"
            f"stdout_tail:\n{proc.stdout[-3000:]}\n\n"
            f"stderr_tail:\n{proc.stderr[-3000:]}"
        )
    return out_dir / "or_applied_math_bible_reader_guide.pdf"


def run(out_dir: Path) -> None:
    out_dir = out_dir.resolve()
    summary = load_json(out_dir / "or_applied_math_bible_chunked_summary.json")
    schedule = load_json(out_dir / "or_applied_math_bible_3_5_year_schedule.json")
    class_summary = summary.get("class_summary", {})
    if not isinstance(class_summary, dict) or not class_summary:
        raise RuntimeError("Missing class_summary in chunked summary.")
    if not isinstance(schedule, list) or not schedule:
        raise RuntimeError("Missing schedule JSON content.")

    class_order, topic_for_class = class_order_and_topic_map()
    tex_path = write_tex(out_dir, class_order, topic_for_class, class_summary, schedule)
    pdf_path = compile_tex(out_dir, tex_path)
    if not pdf_path.exists() or pdf_path.stat().st_size == 0:
        raise RuntimeError("Reader guide PDF not generated.")
    print(f"Wrote guide TeX: {tex_path}")
    print(f"Wrote guide PDF: {pdf_path}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir", type=Path, default=Path("data/assignment_pdf_bundles"))
    args = p.parse_args()
    run(args.out_dir)


if __name__ == "__main__":
    main()

