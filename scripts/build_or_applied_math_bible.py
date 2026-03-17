#!/usr/bin/env python3
"""
Build a polished LaTeX "bible" focused on Operations Research and Applied Math.

Design goals:
- Clean presentation (no raw webpage text dumps).
- OR + Applied Math progression-first structure.
- Include core PDF corpus (downloaded PDFs) for each class.
- Include curated web companion links for classes with sparse PDF coverage.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


TOPIC_ORDER: List[Tuple[str, List[str]]] = [
    (
        "Optimization and Operations Research",
        ["IEOR 160", "IEOR 162", "IEOR 169", "IEOR 261", "IEOR 266", "IEOR 221", "IEOR 222", "IEOR 180", "IEOR 269"],
    ),
    (
        "Pure Math and Analysis",
        ["MATH 104", "MATH 105", "MATH 185", "MATH 202A", "MATH 202B", "MATH 220"],
    ),
    (
        "Algebra and Topology (including Linear Algebra)",
        ["MATH 113", "MATH 142", "MATH 142B", "MATH 110"],
    ),
    (
        "Probability and Stochastic Processes",
        ["STAT 150", "STAT 205A", "STAT 205B", "IEOR 263A", "IEOR 263B", "STAT 210A", "STAT 210B"],
    ),
    (
        "High-Dimensional Statistics and ML Theory",
        ["STAT 260", "CS 189", "CS 170"],
    ),
    (
        "Computational and Systems",
        ["CS 61C", "MATH 128A", "MATH 128B"],
    ),
]


PROBLEM_KWS = ("assign", "homework", "hw", "pset", "problem", "exercise", "quiz")
LECTURE_KWS = ("lecture", "notes", "slides", "reading", "chapter")
PROJECT_KWS = ("project", "lab")
EXAM_KWS = ("midterm", "final", "exam")

WEB_INCLUDE_KWS = PROBLEM_KWS + LECTURE_KWS + PROJECT_KWS + EXAM_KWS
WEB_EXCLUDE_KWS = (
    "gradescope",
    "discussion",
    "office-hour",
    "officehour",
    "calendar",
    "policy",
    "staff",
    "logistics",
    "zoom",
    "piazza",
    "discord",
    "slack",
    "edstem",
    "accommodation",
)


@dataclass
class Resource:
    url: str
    kind: str
    local_pdf_rel: str
    category: str


def slugify(name: str) -> str:
    value = name.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value


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


def url_category(url: str) -> str:
    u = (url or "").lower()
    if any(k in u for k in PROBLEM_KWS):
        return "Problems"
    if any(k in u for k in LECTURE_KWS):
        return "Lectures/Notes"
    if any(k in u for k in PROJECT_KWS):
        return "Projects/Labs"
    if any(k in u for k in EXAM_KWS):
        return "Exams"
    return "Reference"


def is_valid_pdf(path: Path) -> bool:
    if not path.exists() or path.stat().st_size == 0:
        return False
    try:
        with path.open("rb") as f:
            return f.read(5) == b"%PDF-"
    except Exception:
        return False


def should_include_web_link(url: str) -> bool:
    u = (url or "").lower()
    if not (u.startswith("http://") or u.startswith("https://")):
        return False
    if any(k in u for k in WEB_EXCLUDE_KWS):
        return False
    return any(k in u for k in WEB_INCLUDE_KWS)


def load_enriched_manifest(out_dir: Path) -> Dict[str, object]:
    p = out_dir.resolve() / "enriched_manifest.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def collect_class_resources(out_dir: Path, class_name: str, enriched_manifest: Dict[str, object]) -> Dict[str, object]:
    out_dir_abs = out_dir.resolve()
    slug = slugify(class_name)
    manifest_path = out_dir_abs / slug / "manifest.json"
    if not manifest_path.exists():
        return {
            "class_name": class_name,
            "class_slug": slug,
            "pdf_resources": [],
            "web_links": [],
            "missing_manifest": True,
        }

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    seen_pdf = set()
    pdf_resources: List[Resource] = []
    seen_web = set()
    web_links: List[str] = []

    for source in manifest.get("sources", []):
        for result in source.get("results", []):
            if result.get("status") != "ok":
                continue
            url = result.get("url", "")
            kind = result.get("kind", "")
            local_pdf_str = result.get("local_pdf", "")

            # Keep only real PDF artifacts for the main corpus.
            if kind == "downloaded_pdf" and local_pdf_str:
                local_pdf = Path(local_pdf_str)
                if not local_pdf.is_absolute():
                    local_pdf = (Path.cwd() / local_pdf).resolve()
                if not is_valid_pdf(local_pdf):
                    continue
                rel = local_pdf.relative_to(out_dir_abs)
                key = (url, str(rel))
                if key in seen_pdf:
                    continue
                seen_pdf.add(key)
                pdf_resources.append(
                    Resource(
                        url=url,
                        kind=kind,
                        local_pdf_rel=str(rel),
                        category=url_category(url),
                    )
                )
                continue

            # Curated link appendix (no raw HTML dumps).
            if kind == "rendered_html" and should_include_web_link(url):
                if url not in seen_web:
                    seen_web.add(url)
                    web_links.append(url)

    # Add enrichment-crawl harvested PDFs.
    cls_enriched = enriched_manifest.get(class_name, {})
    harvested = cls_enriched.get("harvested", []) if isinstance(cls_enriched, dict) else []
    for item in harvested:
        if not isinstance(item, dict):
            continue
        local_pdf_rel = item.get("local_pdf")
        url = item.get("url", "")
        if not isinstance(local_pdf_rel, str):
            continue
        local_pdf = out_dir_abs / local_pdf_rel
        if not is_valid_pdf(local_pdf):
            continue
        key = (url, local_pdf_rel)
        if key in seen_pdf:
            continue
        seen_pdf.add(key)
        category = item.get("category", "") or url_category(url)
        kind = item.get("kind", "enriched")
        pdf_resources.append(
            Resource(
                url=url,
                kind=kind,
                local_pdf_rel=local_pdf_rel,
                category=category,
            )
        )

    # Stable category-first ordering for readability.
    cat_order = {"Problems": 0, "Lectures/Notes": 1, "Projects/Labs": 2, "Exams": 3, "Reference": 4}
    pdf_resources.sort(key=lambda r: (cat_order.get(r.category, 99), r.kind != "downloaded_pdf", r.url))
    web_links.sort()

    return {
        "class_name": class_name,
        "class_slug": slug,
        "pdf_resources": pdf_resources,
        "web_links": web_links[:120],
        "missing_manifest": False,
    }


def write_latex_book(out_dir: Path, class_data: Dict[str, Dict[str, object]]) -> Path:
    now = datetime.now().strftime("%Y-%m-%d")
    tex_path = out_dir / "or_applied_math_bible.tex"

    lines: List[str] = [
        r"\documentclass[11pt,oneside]{book}",
        r"\usepackage[margin=1in]{geometry}",
        r"\usepackage[T1]{fontenc}",
        r"\usepackage[utf8]{inputenc}",
        r"\usepackage{lmodern}",
        r"\usepackage{microtype}",
        r"\usepackage[dvipsnames]{xcolor}",
        r"\usepackage{hyperref}",
        r"\usepackage{xurl}",
        r"\usepackage{pdfpages}",
        r"\usepackage{longtable}",
        r"\usepackage{booktabs}",
        r"\usepackage{array}",
        r"\usepackage{enumitem}",
        r"\usepackage{titlesec}",
        r"\usepackage{fancyhdr}",
        r"\usepackage[most]{tcolorbox}",
        r"\definecolor{AccentBlue}{HTML}{0B5FA5}",
        r"\definecolor{SoftGray}{HTML}{F3F5F7}",
        r"\hypersetup{colorlinks=true,linkcolor=AccentBlue,urlcolor=AccentBlue}",
        r"\pagestyle{fancy}",
        r"\fancyhf{}",
        r"\fancyhead[R]{\thepage}",
        r"\fancyhead[L]{OR + Applied Math Bible}",
        r"\setlength{\headheight}{14pt}",
        r"\titleformat{\chapter}{\Huge\bfseries\color{AccentBlue}}{\thechapter}{0.8em}{}",
        r"\title{Operations Research and Applied Mathematics Bible}",
        r"\author{Curated From Berkeley-Track Sources}",
        r"\date{" + now + r"}",
        r"\begin{document}",
        r"\frontmatter",
        r"\maketitle",
        r"\tableofcontents",
        r"\chapter*{How To Use This Book}",
        r"\addcontentsline{toc}{chapter}{How To Use This Book}",
        r"\begin{tcolorbox}[colback=SoftGray,colframe=AccentBlue,title=Study Philosophy]",
        r"This volume is structured for long-horizon mastery. The primary corpus contains clean PDF materials (problem sets, lecture notes, and technical handouts).",
        r"\end{tcolorbox}",
        r"\begin{enumerate}[leftmargin=1.4em]",
        r"\item Work topic-by-topic, not class-by-class in isolation.",
        r"\item For each class chapter, complete the Problem-first resources before secondary references.",
        r"\item Treat OR and Applied Math as the spine, then reinforce with probability/statistics and computation.",
        r"\end{enumerate}",
        r"\section*{OR PhD Spine (Recommended Loop)}",
        r"\begin{enumerate}[leftmargin=1.4em]",
        r"\item IEOR 160 $\rightarrow$ IEOR 169 $\rightarrow$ IEOR 266",
        r"\item IEOR 261 $\rightarrow$ IEOR 221/222 $\rightarrow$ IEOR 269",
        r"\item MATH 104/105/202A/202B + STAT 150/205A/205B in parallel",
        r"\item STAT 210A/210B + STAT 260 + CS 170/189 for modern theory integration",
        r"\end{enumerate}",
        r"\mainmatter",
    ]

    for topic, classes in TOPIC_ORDER:
        lines.append(r"\part{" + tex_escape(topic) + r"}")
        for class_name in classes:
            info = class_data[class_name]
            pdf_resources: List[Resource] = info["pdf_resources"]  # type: ignore[assignment]
            web_links: List[str] = info["web_links"]  # type: ignore[assignment]
            missing_manifest = bool(info["missing_manifest"])

            lines.append(r"\chapter{" + tex_escape(class_name) + r"}")
            if missing_manifest:
                lines.append(r"\begin{tcolorbox}[colback=SoftGray,colframe=AccentBlue,title=Missing Manifest]")
                lines.append(r"Manifest not found for this class in the local bundle directory.")
                lines.append(r"\end{tcolorbox}")
                continue

            lines.append(r"\begin{tcolorbox}[colback=SoftGray,colframe=AccentBlue,title=Chapter Summary]")
            downloaded_count = sum(1 for r in pdf_resources if r.kind == "downloaded_pdf")
            enriched_count = len(pdf_resources) - downloaded_count
            lines.append(rf"Clean PDF artifacts: {len(pdf_resources)} \\")
            lines.append(rf"Original direct PDFs: {downloaded_count} \\")
            lines.append(rf"Enrichment-crawl PDFs: {enriched_count} \\")
            lines.append(rf"Companion web links: {len(web_links)}")
            lines.append(r"\end{tcolorbox}")

            if pdf_resources:
                lines.append(r"\section*{Core PDF Corpus}")
                lines.append(r"\addcontentsline{toc}{section}{" + tex_escape(class_name + " Core PDF Corpus") + r"}")
                lines.append(r"\begin{longtable}{p{0.07\textwidth}p{0.2\textwidth}p{0.68\textwidth}}")
                lines.append(r"\toprule")
                lines.append(r"\# & Type & Source URL \\")
                lines.append(r"\midrule")
                lines.append(r"\endfirsthead")
                lines.append(r"\toprule")
                lines.append(r"\# & Type & Source URL \\")
                lines.append(r"\midrule")
                lines.append(r"\endhead")
                for i, res in enumerate(pdf_resources, start=1):
                    lines.append(
                        rf"{i} & {tex_escape(res.category)} & \url{{{res.url}}} \\"
                    )
                lines.append(r"\bottomrule")
                lines.append(r"\end{longtable}")

                lines.append(r"\clearpage")
                for res in pdf_resources:
                    lines.append(r"\includepdf[pages=-,pagecommand={\thispagestyle{plain}}]{\detokenize{" + res.local_pdf_rel + r"}}")

            if web_links:
                lines.append(r"\section*{Curated Web Companion Links}")
                lines.append(
                    r"\begin{tcolorbox}[colback=SoftGray,colframe=AccentBlue,title=Companion Links]"
                )
                lines.append(
                    r"These links are curated for lecture/problem context but intentionally not dumped as raw rendered webpage text."
                )
                lines.append(r"\end{tcolorbox}")
                lines.append(r"\begin{longtable}{p{0.05\textwidth}p{0.9\textwidth}}")
                lines.append(r"\toprule")
                lines.append(r"\# & URL \\")
                lines.append(r"\midrule")
                lines.append(r"\endfirsthead")
                lines.append(r"\toprule")
                lines.append(r"\# & URL \\")
                lines.append(r"\midrule")
                lines.append(r"\endhead")
                for i, u in enumerate(web_links, start=1):
                    lines.append(rf"{i} & \url{{{u}}} \\")
                lines.append(r"\bottomrule")
                lines.append(r"\end{longtable}")

    lines.extend([r"\backmatter", r"\chapter*{End Notes}", r"Consistent effort over years beats short bursts.", r"\end{document}"])
    tex_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return tex_path


def run_latexmk(workdir: Path, tex_path: Path) -> None:
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
            f"stdout_tail:\n{proc.stdout[-4000:]}\n\n"
            f"stderr_tail:\n{proc.stderr[-4000:]}"
        )


def run(out_dir: Path) -> None:
    expected = [c for _, classes in TOPIC_ORDER for c in classes]
    enriched_manifest = load_enriched_manifest(out_dir)
    class_data = {c: collect_class_resources(out_dir, c, enriched_manifest) for c in expected}

    tex_path = write_latex_book(out_dir, class_data)
    run_latexmk(out_dir, tex_path)

    summary = {}
    for c, info in class_data.items():
        summary[c] = {
            "pdf_resources": len(info["pdf_resources"]),  # type: ignore[index]
            "web_links": len(info["web_links"]),  # type: ignore[index]
            "missing_manifest": info["missing_manifest"],
        }
    summary_path = out_dir / "or_applied_math_bible_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Wrote LaTeX source: {tex_path}")
    print(f"Wrote PDF: {out_dir / 'or_applied_math_bible.pdf'}")
    print(f"Wrote summary: {summary_path}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--out-dir",
        type=Path,
        default=Path("data/assignment_pdf_bundles"),
        help="Directory with per-class manifests/raw PDFs.",
    )
    args = p.parse_args()
    run(args.out_dir)


if __name__ == "__main__":
    main()
