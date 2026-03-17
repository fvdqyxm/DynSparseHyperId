#!/usr/bin/env python3
"""
Build topic-organized problem bundles from the cleaned OR + Applied Math corpus.

This script classifies resources by topic keywords found in URL + first-page text,
then writes:
- data/assignment_pdf_bundles/topic_problem_bundles/topic_problem_index.json
- data/assignment_pdf_bundles/topic_problem_bundles/topic_problem_index.md
- data/assignment_pdf_bundles/topic_problem_bundles/<topic_slug>/manifest.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.parse import urlparse

from pypdf import PdfReader


TOPIC_KEYWORDS: List[Tuple[str, List[str]]] = [
    (
        "Proofs, Discrete Math, and Foundations",
        ["induction", "contradiction", "discrete", "counting", "combinator", "proof", "logic", "invariant"],
    ),
    (
        "Linear Algebra and Matrix Methods",
        ["matrix", "linear algebra", "eigen", "svd", "orthogonal", "spectral", "vector space"],
    ),
    (
        "Differential Equations and Dynamics",
        ["differential equation", "ode", "stability", "dynamical", "phase portrait", "initial value"],
    ),
    (
        "Real Analysis and Measure",
        ["real analysis", "measure", "lebesgue", "convergence", "compactness", "continuity", "integration"],
    ),
    (
        "Complex Analysis",
        ["complex", "analytic function", "residue", "contour", "holomorphic", "cauchy"],
    ),
    (
        "Algebra and Topology",
        ["group", "ring", "field", "homomorphism", "topology", "compact", "connected", "homeomorphism"],
    ),
    (
        "Probability Foundations",
        ["probability", "random variable", "expectation", "variance", "distribution", "conditioning"],
    ),
    (
        "Stochastic Processes",
        ["stochastic process", "markov", "poisson", "martingale", "queue", "renewal", "brownian"],
    ),
    (
        "Statistical Inference",
        ["estimation", "hypothesis", "likelihood", "confidence", "asymptotic", "inference", "mle"],
    ),
    (
        "High-Dimensional Statistics",
        ["high-dimensional", "sparse", "regularization", "lasso", "concentration", "minimax"],
    ),
    (
        "Linear and Convex Optimization",
        ["linear programming", "convex", "duality", "kkt", "lagrangian", "interior point", "simplex"],
    ),
    (
        "Integer, Combinatorial, and Network Optimization",
        ["integer programming", "network flow", "matching", "cut", "branch and bound", "combinatorial"],
    ),
    (
        "Dynamic Programming and Sequential Decisions",
        ["dynamic programming", "bellman", "mdp", "policy", "value function", "sequential decision"],
    ),
    (
        "Numerical Methods and Scientific Computing",
        ["numerical", "conditioning", "iterative", "newton", "approximation", "discretization", "solver"],
    ),
    (
        "Algorithms and Data Structures",
        ["algorithm", "graph", "dp", "greedy", "heap", "tree", "hash", "runtime", "complexity"],
    ),
    (
        "Machine Learning Theory",
        ["machine learning", "generalization", "empirical risk", "classification", "regression", "kernel"],
    ),
    (
        "Financial Engineering and Risk",
        ["finance", "portfolio", "option", "risk", "stochastic volatility", "derivative"],
    ),
    (
        "Systems and Architecture",
        ["architecture", "cache", "pipeline", "assembly", "memory hierarchy", "parallel"],
    ),
]

PROBLEMISH_CATS = {"Problems", "Projects/Labs", "Exams"}
PROBLEMISH_KWS = ("assign", "homework", "hw", "pset", "problem", "exercise", "quiz", "project", "lab", "exam")
SOLUTION_MARK_RE = re.compile(
    r"(solutions?|soln|answers?|keys?|hints?|(^|[^a-z0-9])sol([^a-z0-9]|$))",
    re.IGNORECASE,
)
SOLUTION_STEM_CLEAN_RE = re.compile(r"(solutions?|soln|sol|answers?|keys?|hints?)", re.IGNORECASE)


def slugify(name: str) -> str:
    value = name.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return re.sub(r"_+", "_", value).strip("_")


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


def collect_class_resources(out_dir: Path, class_name: str, enriched_manifest: Dict[str, object]) -> Dict[str, object]:
    ns = {}
    script = Path("scripts/build_or_applied_math_bible_chunked.py")
    exec(script.read_text(encoding="utf-8"), ns)  # noqa: S102
    fn = ns["collect_class_resources"]
    return fn(out_dir, class_name, enriched_manifest)


def is_problemish(category: str, url: str) -> bool:
    if category in PROBLEMISH_CATS:
        return True
    low = (url or "").lower()
    return any(k in low for k in PROBLEMISH_KWS)


def is_solution_like(url: str, local_pdf_rel: str) -> bool:
    joined = f"{(url or '').lower()} {(local_pdf_rel or '').lower()}"
    return bool(SOLUTION_MARK_RE.search(joined))


def assignment_stem(url: str, local_pdf_rel: str) -> str:
    name = ""
    if url:
        try:
            name = Path(urlparse(url).path).name
        except Exception:
            name = ""
    if not name:
        name = Path(local_pdf_rel or "").name
    name = name.lower()
    name = re.sub(r"\.(pdf|tex|txt|html?)$", "", name)
    name = SOLUTION_STEM_CLEAN_RE.sub("", name)
    name = re.sub(r"[^a-z0-9]+", "", name)
    if not name:
        fallback = f"{(url or '').lower()} {(local_pdf_rel or '').lower()}"
        name = re.sub(r"[^a-z0-9]+", "", fallback)
    return name[:140]


def extract_pdf_text(pdf_path: Path, max_pages: int = 3) -> str:
    try:
        reader = PdfReader(str(pdf_path), strict=False)
        if not reader.pages:
            return ""
        chunks: List[str] = []
        for page in reader.pages[:max_pages]:
            chunks.append(page.extract_text() or "")
        txt = " ".join(chunks)
        txt = re.sub(r"\s+", " ", txt).strip().lower()
        return txt[:7000]
    except Exception:
        return ""


def classify_topic(search_text: str) -> Tuple[str, int, List[str]]:
    best_topic = "General OR/Applied Math"
    best_score = 0
    best_hits: List[str] = []
    for topic, kws in TOPIC_KEYWORDS:
        hits = [kw for kw in kws if kw in search_text]
        score = len(hits)
        if score > best_score:
            best_score = score
            best_topic = topic
            best_hits = hits
    return best_topic, best_score, best_hits


def materialize_topic_links(
    out_dir: Path,
    topic_dir: Path,
    items: List[Dict[str, object]],
    max_links: int,
) -> int:
    links_dir = topic_dir / "pdf_links"
    if links_dir.exists():
        shutil.rmtree(links_dir)
    links_dir.mkdir(parents=True, exist_ok=True)
    linked = 0
    for i, item in enumerate(items[:max_links], start=1):
        local_pdf = str(item.get("local_pdf", ""))
        src = (out_dir / local_pdf).resolve()
        if not src.exists():
            continue
        cls_slug = slugify(str(item.get("class", "class")))
        cat_slug = slugify(str(item.get("category", "resource")))
        dst = links_dir / f"{i:04d}_{cls_slug}_{cat_slug}.pdf"
        if dst.exists() or dst.is_symlink():
            dst.unlink()
        rel_target = os.path.relpath(src, links_dir)
        try:
            os.symlink(rel_target, dst)
        except OSError:
            # Fallback for filesystems where symlink creation is restricted.
            shutil.copy2(src, dst)
        linked += 1
    return linked


def run(
    out_dir: Path,
    link_limit_per_topic: int,
    solution_ratio_cap: float,
    solution_abs_cap: int,
    solution_only_topic_cap: int,
) -> None:
    out_dir = out_dir.resolve()
    bundle_dir = out_dir / "topic_problem_bundles"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    summary = load_json(out_dir / "or_applied_math_bible_chunked_summary.json")
    class_summary = summary.get("class_summary", {})
    if not isinstance(class_summary, dict) or not class_summary:
        raise RuntimeError("Missing class summary.")

    enriched_manifest = load_json(out_dir / "enriched_manifest.json")
    class_order, _ = class_order_and_topic_map()

    text_cache: Dict[str, str] = {}
    classified_items: List[Dict[str, object]] = []
    total_problemish = 0
    solution_like_total = 0

    for cls in class_order:
        info = collect_class_resources(out_dir, cls, enriched_manifest)
        resources = info.get("pdf_resources", [])
        for r in resources:
            category = getattr(r, "category", "")
            url = getattr(r, "url", "")
            local_pdf_rel = getattr(r, "local_pdf_rel", "")
            if not is_problemish(category, url):
                continue
            total_problemish += 1
            solution_like = is_solution_like(url, local_pdf_rel)
            if solution_like:
                solution_like_total += 1

            pdf_path = out_dir / local_pdf_rel
            if local_pdf_rel not in text_cache:
                text_cache[local_pdf_rel] = extract_pdf_text(pdf_path, max_pages=3)
            search_text = f"{(url or '').lower()} {text_cache[local_pdf_rel]}"
            topic, score, hits = classify_topic(search_text)
            classified_items.append(
                {
                    "class": cls,
                    "url": url,
                    "category": category,
                    "local_pdf": local_pdf_rel,
                    "score": score,
                    "matched_keywords": hits,
                    "topic": topic,
                    "solution_like": solution_like,
                    "assignment_stem": assignment_stem(url, local_pdf_rel),
                }
            )

    # Minimize solution visibility: if a non-solution exists for the same class+assignment stem,
    # drop solution variants and keep non-solution variants only.
    grouped: Dict[Tuple[str, str], List[Dict[str, object]]] = defaultdict(list)
    for item in classified_items:
        grouped[(str(item.get("class", "")), str(item.get("assignment_stem", "")))].append(item)

    filtered_items: List[Dict[str, object]] = []
    dropped_solution_variants = 0
    for _, group_items in grouped.items():
        non_solutions = [x for x in group_items if not bool(x.get("solution_like", False))]
        solutions = [x for x in group_items if bool(x.get("solution_like", False))]
        if non_solutions:
            filtered_items.extend(non_solutions)
            dropped_solution_variants += len(solutions)
        elif solutions:
            # Keep exactly one unmatched solution fallback, preferring highest topic-score.
            solutions.sort(
                key=lambda x: (
                    -int(x.get("score", 0)),
                    str(x.get("class", "")),
                    str(x.get("url", "")),
                )
            )
            filtered_items.append(solutions[0])
            dropped_solution_variants += max(0, len(solutions) - 1)

    by_topic: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    class_topic_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for item in filtered_items:
        topic = str(item.get("topic", "General OR/Applied Math"))
        by_topic[topic].append(
            {
                "class": item["class"],
                "url": item["url"],
                "category": item["category"],
                "local_pdf": item["local_pdf"],
                "score": item["score"],
                "matched_keywords": item["matched_keywords"],
                "solution_like": item["solution_like"],
            }
        )
        class_topic_counts[str(item["class"])][topic] += 1

    # Sort resources in each topic by score then class/url for stable ordering.
    for topic in list(by_topic.keys()):
        by_topic[topic].sort(
            key=lambda x: (
                -int(x.get("score", 0)),
                bool(x.get("solution_like", False)),
                str(x.get("class", "")),
                str(x.get("url", "")),
            )
        )

    # Second-stage cap: keep only a small number of unmatched solution resources per topic.
    dropped_by_topic_cap = 0
    for topic in list(by_topic.keys()):
        items = by_topic[topic]
        non_solution = [x for x in items if not bool(x.get("solution_like", False))]
        solution = [x for x in items if bool(x.get("solution_like", False))]
        if not solution:
            continue
        if non_solution:
            allowed = min(solution_abs_cap, int(len(non_solution) * solution_ratio_cap))
        else:
            allowed = solution_only_topic_cap
        allowed = max(0, min(allowed, len(solution)))
        dropped_by_topic_cap += max(0, len(solution) - allowed)
        by_topic[topic] = non_solution + solution[:allowed]

    # Write per-topic manifests.
    for topic, items in by_topic.items():
        topic_slug = slugify(topic)
        tdir = bundle_dir / topic_slug
        tdir.mkdir(parents=True, exist_ok=True)
        linked_count = materialize_topic_links(
            out_dir=out_dir,
            topic_dir=tdir,
            items=items,
            max_links=link_limit_per_topic,
        )
        payload = {
            "topic": topic,
            "topic_slug": topic_slug,
            "resource_count": len(items),
            "pdf_links_dir": f"topic_problem_bundles/{topic_slug}/pdf_links",
            "linked_pdf_count": linked_count,
            "resources": items,
        }
        (tdir / "manifest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

        topic_lines = [
            f"# {topic}",
            "",
            f"- Resource count: {len(items)}",
            f"- Linked PDFs materialized: {linked_count}",
            "",
            "| # | Class | Category | URL | Local PDF |",
            "|---:|---|---|---|---|",
        ]
        for i, item in enumerate(items, start=1):
            topic_lines.append(
                f"| {i} | {item.get('class', '')} | {item.get('category', '')} | "
                f"{item.get('url', '')} | `{item.get('local_pdf', '')}` |"
            )
        (tdir / "README.md").write_text("\n".join(topic_lines) + "\n", encoding="utf-8")

    topic_rows = sorted(by_topic.items(), key=lambda kv: (-len(kv[1]), kv[0]))

    # Write master index.
    index = {
        "topics": [
            {
                "topic": topic,
                "topic_slug": slugify(topic),
                "resource_count": len(items),
            }
            for topic, items in topic_rows
        ],
        "total_problemish_resources_before_solution_filter": total_problemish,
        "total_problemish_resources_after_pair_filter": len(filtered_items),
        "total_problemish_resources": sum(len(items) for _, items in topic_rows),
        "solution_like_before_filter": solution_like_total,
        "dropped_solution_variants": dropped_solution_variants,
        "dropped_solution_by_topic_cap": dropped_by_topic_cap,
        "solution_like_after_pair_filter": sum(
            1 for item in filtered_items if bool(item.get("solution_like", False))
        ),
        "solution_like_after_filter": sum(
            1 for _, items in topic_rows for item in items if bool(item.get("solution_like", False))
        ),
        "topic_count": len(by_topic),
    }
    (bundle_dir / "topic_problem_index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")

    # Write class x topic coverage matrix for gap checks.
    all_topics = [topic for topic, _ in topic_rows]
    matrix = {
        "topics": all_topics,
        "classes": {},
    }
    for cls in class_order:
        row: Dict[str, int] = {}
        for topic in all_topics:
            row[topic] = int(class_topic_counts[cls].get(topic, 0))
        matrix["classes"][cls] = row
    (bundle_dir / "class_topic_matrix.json").write_text(json.dumps(matrix, indent=2), encoding="utf-8")

    # Write a readable markdown index for study navigation.
    lines = [
        "# Topic-Organized Problem Bundles",
        "",
        f"- Total problem-like resources indexed (after minimization): {index['total_problemish_resources']}",
        f"- Total problem-like resources before minimization: {total_problemish}",
        f"- Solution-like resources before minimization: {solution_like_total}",
        f"- Solution variants removed by pairing: {dropped_solution_variants}",
        f"- Additional solution resources removed by topic cap: {dropped_by_topic_cap}",
        f"- Solution-like resources remaining (fallback only): {index['solution_like_after_filter']}",
        f"- Total topics with assigned resources: {len(by_topic)}",
        "",
        "| Topic | Resources | Manifest |",
        "|---|---:|---|",
    ]
    for row in index["topics"]:
        lines.append(
            f"| {row['topic']} | {row['resource_count']} | "
            f"`topic_problem_bundles/{row['topic_slug']}/manifest.json` |"
        )
    lines.extend(
        [
            "",
            "## Class x Topic Coverage Matrix",
            "",
            "Rows are classes, columns are topics. Cells are counts of problem-like resources assigned to a topic.",
            "",
            "| Class | " + " | ".join(all_topics) + " |",
            "|" + "---|" * (len(all_topics) + 1),
        ]
    )
    for cls in class_order:
        vals = [str(matrix["classes"][cls][topic]) for topic in all_topics]
        lines.append("| " + cls + " | " + " | ".join(vals) + " |")
    (bundle_dir / "topic_problem_index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote topic bundle index JSON: {bundle_dir / 'topic_problem_index.json'}")
    print(f"Wrote topic bundle index Markdown: {bundle_dir / 'topic_problem_index.md'}")
    print(f"Wrote class/topic matrix JSON: {bundle_dir / 'class_topic_matrix.json'}")
    print(f"Wrote per-topic manifests under: {bundle_dir}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir", type=Path, default=Path("data/assignment_pdf_bundles"))
    p.add_argument(
        "--link-limit-per-topic",
        type=int,
        default=400,
        help="Maximum number of PDFs to materialize as direct links under each topic folder.",
    )
    p.add_argument(
        "--solution-ratio-cap",
        type=float,
        default=0.15,
        help="Maximum ratio of solution-like resources to keep relative to non-solution resources per topic.",
    )
    p.add_argument(
        "--solution-abs-cap",
        type=int,
        default=10,
        help="Absolute maximum solution-like resources to keep per topic when non-solutions exist.",
    )
    p.add_argument(
        "--solution-only-topic-cap",
        type=int,
        default=1,
        help="Maximum solution-like resources to keep in topics that have no non-solution resources.",
    )
    args = p.parse_args()
    run(
        args.out_dir,
        link_limit_per_topic=args.link_limit_per_topic,
        solution_ratio_cap=args.solution_ratio_cap,
        solution_abs_cap=args.solution_abs_cap,
        solution_only_topic_cap=args.solution_only_topic_cap,
    )


if __name__ == "__main__":
    main()
