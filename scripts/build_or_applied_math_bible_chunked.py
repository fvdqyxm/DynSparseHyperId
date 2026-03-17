#!/usr/bin/env python3
"""
Build an exhaustive OR + Applied Math bible via chunked LaTeX compilation.

Why chunked:
- A single monolithic TeX run can exceed TeX memory/pool limits on very large corpora.
- Chunking preserves exhaustive coverage while keeping each compile stable.

Output:
- data/assignment_pdf_bundles/or_applied_math_bible.pdf
- data/assignment_pdf_bundles/or_applied_math_bible_chunked_summary.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.parse import urlparse

from pypdf import PdfReader, PdfWriter


TOPIC_ORDER: List[Tuple[str, List[str]]] = [
    (
        "Foundation Layer (Prerequisite-First)",
        [
            "CS 70",
            "IEOR 160",
            "MATH 54",
            "MATH 110",
            "MATH 104",
            "MATH 105",
            "CS 61B",
            "CS 170",
            "CS 61C",
            "MATH 128A",
            "MATH 128B",
        ],
    ),
    (
        "Probability and Stochastic/OR Core",
        [
            "MATH 220",
            "STAT 150",
            "IEOR 162",
            "IEOR 169",
            "IEOR 261",
            "IEOR 266",
            "IEOR 263A",
            "IEOR 263B",
            "STAT 205A",
            "STAT 205B",
            "STAT 210A",
            "STAT 210B",
        ],
    ),
    (
        "Advanced OR Practice",
        ["IEOR 221", "IEOR 222", "IEOR 180", "IEOR 269"],
    ),
    (
        "Advanced Pure Math Track",
        ["MATH 185", "MATH 202A", "MATH 202B", "MATH 113", "MATH 142", "MATH 142B"],
    ),
    (
        "High-Dimensional Statistics and ML Theory",
        ["STAT 260", "CS 189"],
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

HARD_EXCLUDE_URL_KWS = (
    "transcript",
    "/transcripts/",
    "caption",
    "subtitles",
    "closed-caption",
    "/faq/",
    "/terminal/",
    "main-content",
    "resolving-problems-complaints",
    "/graduate/phd-program/",
)

ENRICH_INCLUDED_KINDS = {
    "downloaded_pdf",
    "rendered_html",
    "rendered_text",
    "rendered_text_from_invalid_pdf",
    "rendered_zip_summary",
}


@dataclass
class Resource:
    url: str
    kind: str
    local_pdf_rel: str
    category: str


def slugify(name: str) -> str:
    value = name.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return re.sub(r"_+", "_", value).strip("_")


def class_order_and_topic_map() -> Tuple[List[str], Dict[str, str]]:
    order: List[str] = []
    topic_for_class: Dict[str, str] = {}
    for topic, classes in TOPIC_ORDER:
        for cls in classes:
            if cls in topic_for_class:
                continue
            topic_for_class[cls] = topic
            order.append(cls)
    return order, topic_for_class


def normalize_url_for_dedupe(url: str) -> str:
    if not url:
        return ""
    try:
        p = urlparse(url.strip())
        path = p.path or "/"
        if path != "/":
            path = path.rstrip("/") or "/"
        p = p._replace(
            scheme=p.scheme.lower(),
            netloc=p.netloc.lower(),
            path=path,
            query="",
            fragment="",
        )
        return p.geturl()
    except Exception:
        return url.strip()


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


def should_include_web_link(url: str) -> bool:
    u = (url or "").lower()
    if not (u.startswith("http://") or u.startswith("https://")):
        return False
    if any(k in u for k in HARD_EXCLUDE_URL_KWS):
        return False
    if any(k in u for k in WEB_EXCLUDE_KWS):
        return False
    return any(k in u for k in WEB_INCLUDE_KWS)


def canonical_resource_key(url: str, rel: str) -> str:
    """
    Normalize URL-level duplicates while preserving distinct assignments/solutions.

    We collapse lecture slide variants like `lec1.pdf` and `lec1_annotated.pdf`
    because they materially duplicate content for this manual.
    """
    key = normalize_url_for_dedupe(url)
    if key:
        low = key.lower()
        if "/slides/" in low:
            low = low.replace("_annotated", "").replace("-annotated", "")
        return low
    return rel


def load_json(path: Path) -> Dict[str, object]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def collect_class_resources(out_dir: Path, class_name: str, enriched_manifest: Dict[str, object]) -> Dict[str, object]:
    out_dir_abs = out_dir.resolve()
    slug = slugify(class_name)
    mf = out_dir_abs / slug / "manifest.json"
    if not mf.exists():
        return {"class_name": class_name, "class_slug": slug, "pdf_resources": [], "web_links": [], "missing_manifest": True}

    obj = json.loads(mf.read_text(encoding="utf-8"))
    seen = set()
    resources: List[Resource] = []
    web_links: List[str] = []
    seen_web = set()

    # Original direct PDFs only.
    for source in obj.get("sources", []):
        for result in source.get("results", []):
            if result.get("status") != "ok":
                continue
            if result.get("kind") != "downloaded_pdf":
                # Keep HTML pages as web companion links only.
                if result.get("kind") == "rendered_html":
                    u = result.get("url", "")
                    if should_include_web_link(u) and u not in seen_web:
                        seen_web.add(u)
                        web_links.append(u)
                continue
            lp = result.get("local_pdf")
            if not isinstance(lp, str):
                continue
            p = Path(lp)
            if not p.is_absolute():
                p = (Path.cwd() / p).resolve()
            if not is_valid_pdf(p):
                continue
            rel = str(p.relative_to(out_dir_abs))
            u = result.get("url", "")
            if u and not should_include_web_link(u):
                continue
            key = canonical_resource_key(u, rel)
            if key in seen:
                continue
            seen.add(key)
            resources.append(Resource(url=u, kind="downloaded_pdf", local_pdf_rel=rel, category=url_category(u)))

    # Enrichment resources (filtered kinds to avoid ugly HTML dumps).
    cls_enriched = enriched_manifest.get(class_name, {})
    harvested = cls_enriched.get("harvested", []) if isinstance(cls_enriched, dict) else []
    for item in harvested:
        if not isinstance(item, dict):
            continue
        kind = item.get("kind", "")
        if kind not in ENRICH_INCLUDED_KINDS:
            continue
        rel = item.get("local_pdf")
        if not isinstance(rel, str):
            continue
        p = out_dir_abs / rel
        if not is_valid_pdf(p):
            continue
        u = item.get("url", "")
        if kind != "downloaded_pdf" and u and not should_include_web_link(u):
            continue
        if u and not should_include_web_link(u):
            continue
        key = canonical_resource_key(u, rel)
        if key in seen:
            continue
        seen.add(key)
        category = item.get("category", "") or url_category(u)
        resources.append(Resource(url=u, kind=kind, local_pdf_rel=rel, category=category))

    cat_order = {"Problems": 0, "Lectures/Notes": 1, "Projects/Labs": 2, "Exams": 3, "Reference": 4}
    resources.sort(key=lambda r: (cat_order.get(r.category, 99), r.kind != "downloaded_pdf", r.url))
    web_links.sort()
    return {
        "class_name": class_name,
        "class_slug": slug,
        "pdf_resources": resources,
        "web_links": web_links[:200],
        "missing_manifest": False,
    }


def run_latexmk(workdir: Path, tex_file: Path) -> None:
    env = os.environ.copy()
    env["LC_ALL"] = "en_US.UTF-8"
    env["LANG"] = "en_US.UTF-8"
    env["LC_CTYPE"] = "en_US.UTF-8"
    cmd = [
        "/Library/TeX/texbin/latexmk",
        "-pdf",
        "-interaction=nonstopmode",
        "-halt-on-error",
        str(tex_file),
    ]
    proc = subprocess.run(cmd, cwd=workdir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    if proc.returncode != 0:
        raise RuntimeError(
            "latexmk failed.\n"
            f"stdout_tail:\n{proc.stdout[-3000:]}\n\n"
            f"stderr_tail:\n{proc.stderr[-3000:]}"
        )


def chunk_list(items: List[Resource], n: int) -> List[List[Resource]]:
    if not items:
        return []
    return [items[i : i + n] for i in range(0, len(items), n)]


def write_frontmatter_tex(
    out_dir: Path,
    class_data: Dict[str, Dict[str, object]],
    class_order: List[str],
    topic_for_class: Dict[str, str],
    part_counts: Dict[str, int],
    resources_per_part: int,
) -> Path:
    now = datetime.now().strftime("%Y-%m-%d")
    tex = out_dir / "or_applied_math_bible_frontmatter.tex"
    lines: List[str] = [
        r"\documentclass[11pt,oneside]{book}",
        r"\usepackage[margin=1in]{geometry}",
        r"\usepackage[T1]{fontenc}",
        r"\usepackage[utf8]{inputenc}",
        r"\usepackage{lmodern}",
        r"\usepackage{hyperref}",
        r"\usepackage{longtable}",
        r"\usepackage{booktabs}",
        r"\usepackage[dvipsnames]{xcolor}",
        r"\title{Operations Research and Applied Mathematics Bible}",
        r"\author{Exhaustive Chunked LaTeX Edition}",
        r"\date{" + now + r"}",
        r"\begin{document}",
        r"\maketitle",
        r"\chapter*{Overview}",
        r"\begin{itemize}",
        r"\item This is the high-coverage, cleaned, chunked LaTeX build.",
        r"\item It avoids raw web scrape dumps in the core corpus.",
        r"\item OR + Applied Math progression is the spine.",
        r"\end{itemize}",
        r"\chapter*{Coverage Table}",
        r"\begin{longtable}{p{0.30\textwidth}p{0.12\textwidth}p{0.12\textwidth}p{0.12\textwidth}}",
        r"\toprule",
        r"Class & PDF Resources & Link Appendix & Parts \\",
        r"\midrule",
        r"\endfirsthead",
        r"\toprule",
        r"Class & PDF Resources & Link Appendix & Parts \\",
        r"\midrule",
        r"\endhead",
    ]
    for c in class_order:
        info = class_data[c]
        res_n = len(info["pdf_resources"])  # type: ignore[index]
        web_n = len(info["web_links"])  # type: ignore[index]
        parts = part_counts.get(c, 0)
        lines.append(rf"{tex_escape(c)} & {res_n} & {web_n} & {parts} \\")
    lines.extend([r"\bottomrule", r"\end{longtable}"])

    # Large chronological table of contents (part-by-part).
    lines.extend(
        [
            r"\chapter*{Chronological Core Reading Order}",
            r"\begin{longtable}{p{0.08\textwidth}p{0.24\textwidth}p{0.14\textwidth}p{0.15\textwidth}p{0.31\textwidth}}",
            r"\toprule",
            r"Step & Class & Part & Resource Span & Topic \\",
            r"\midrule",
            r"\endfirsthead",
            r"\toprule",
            r"Step & Class & Part & Resource Span & Topic \\",
            r"\midrule",
            r"\endhead",
        ]
    )
    step = 1
    for c in class_order:
        topic = topic_for_class.get(c, "Unassigned")
        info = class_data[c]
        res_n = len(info["pdf_resources"])  # type: ignore[index]
        total_parts = part_counts.get(c, 0)
        for part in range(1, total_parts + 1):
            start_i = (part - 1) * resources_per_part + 1
            end_i = min(part * resources_per_part, res_n)
            span = f"{start_i}-{end_i}"
            lines.append(
                rf"{step} & {tex_escape(c)} & {part}/{total_parts} & {span} & {tex_escape(topic)} \\"
            )
            step += 1
    lines.extend([r"\bottomrule", r"\end{longtable}", r"\end{document}"])
    tex.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return tex


def write_class_part_tex(
    out_dir: Path,
    topic: str,
    class_name: str,
    part_idx: int,
    part_total: int,
    resources: List[Resource],
    web_links: List[str],
    part_dir: Path,
) -> Path:
    tex = part_dir / f"{slugify(class_name)}_part_{part_idx:03d}.tex"
    lines: List[str] = [
        r"\documentclass[11pt]{article}",
        r"\usepackage[margin=1in]{geometry}",
        r"\usepackage[T1]{fontenc}",
        r"\usepackage[utf8]{inputenc}",
        r"\usepackage{lmodern}",
        r"\usepackage{hyperref}",
        r"\usepackage{xurl}",
        r"\usepackage{pdfpages}",
        r"\usepackage{longtable}",
        r"\usepackage{booktabs}",
        r"\usepackage[dvipsnames]{xcolor}",
        r"\title{" + tex_escape(class_name + f" — Part {part_idx}/{part_total}") + r"}",
        r"\date{}",
        r"\begin{document}",
        r"\maketitle",
        r"\noindent\textbf{Topic:} " + tex_escape(topic) + r"\\",
        r"\noindent\textbf{Resources in this part:} " + str(len(resources)),
        r"\section*{Resource Index}",
        r"\begin{longtable}{p{0.06\textwidth}p{0.17\textwidth}p{0.74\textwidth}}",
        r"\toprule",
        r"\# & Type & URL \\",
        r"\midrule",
        r"\endfirsthead",
        r"\toprule",
        r"\# & Type & URL \\",
        r"\midrule",
        r"\endhead",
    ]
    for i, r in enumerate(resources, start=1):
        lines.append(rf"{i} & {tex_escape(r.category)} & \url{{{r.url}}} \\")
    lines.extend([r"\bottomrule", r"\end{longtable}"])

    if part_idx == 1 and web_links:
        lines.extend(
            [
                r"\section*{Curated Companion Links}",
                r"\begin{longtable}{p{0.06\textwidth}p{0.90\textwidth}}",
                r"\toprule",
                r"\# & URL \\",
                r"\midrule",
                r"\endfirsthead",
                r"\toprule",
                r"\# & URL \\",
                r"\midrule",
                r"\endhead",
            ]
        )
        for i, u in enumerate(web_links, start=1):
            lines.append(rf"{i} & \url{{{u}}} \\")
        lines.extend([r"\bottomrule", r"\end{longtable}"])

    lines.append(r"\clearpage")
    for rsrc in resources:
        lines.append(r"\includepdf[pages=-,pagecommand={\thispagestyle{plain}}]{\detokenize{" + rsrc.local_pdf_rel + r"}}")
    lines.append(r"\end{document}")
    tex.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return tex


def merge_pdfs(pdfs: List[Path], out_pdf: Path) -> None:
    writer = PdfWriter()
    for p in pdfs:
        try:
            reader = PdfReader(str(p), strict=False)
            for page in reader.pages:
                writer.add_page(page)
        except Exception:
            continue
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    with out_pdf.open("wb") as f:
        writer.write(f)


def append_pdf_to_writer(writer: PdfWriter, pdf_path: Path) -> None:
    reader = PdfReader(str(pdf_path), strict=False)
    for page in reader.pages:
        writer.add_page(page)


def cleanup_latex_sidecars(out_dir: Path, stem: str) -> None:
    for ext in (".pdf", ".aux", ".fdb_latexmk", ".fls", ".log"):
        p = out_dir / f"{stem}{ext}"
        p.unlink(missing_ok=True)


def run(out_dir: Path, resources_per_part: int) -> None:
    out_dir = out_dir.resolve()
    enriched_manifest = load_json(out_dir / "enriched_manifest.json")
    expected, topic_for_class = class_order_and_topic_map()
    class_data = {c: collect_class_resources(out_dir, c, enriched_manifest) for c in expected}

    build_root = out_dir / "or_applied_math_bible_parts"
    if build_root.exists():
        shutil.rmtree(build_root)
    build_root.mkdir(parents=True, exist_ok=True)

    # Clean stale chunk artifacts from previous runs.
    for pattern in ("*_part_*.pdf", "*_part_*.aux", "*_part_*.fdb_latexmk", "*_part_*.fls", "*_part_*.log"):
        for stale in out_dir.glob(pattern):
            stale.unlink(missing_ok=True)

    part_counts: Dict[str, int] = {}
    writer = PdfWriter()

    # Frontmatter
    tmp_part_counts = {c: max(1, (len(class_data[c]["pdf_resources"]) + resources_per_part - 1) // resources_per_part) for c in expected}
    front_tex = write_frontmatter_tex(
        out_dir=out_dir,
        class_data=class_data,
        class_order=expected,
        topic_for_class=topic_for_class,
        part_counts=tmp_part_counts,
        resources_per_part=resources_per_part,
    )
    run_latexmk(out_dir, front_tex.name)
    front_pdf = out_dir / "or_applied_math_bible_frontmatter.pdf"
    if not is_valid_pdf(front_pdf):
        raise RuntimeError("Frontmatter PDF was not generated correctly.")
    append_pdf_to_writer(writer, front_pdf)

    # Class-part chunks
    for class_name in expected:
        topic = topic_for_class.get(class_name, "Unassigned")
        info = class_data[class_name]
        resources: List[Resource] = info["pdf_resources"]  # type: ignore[assignment]
        web_links: List[str] = info["web_links"]  # type: ignore[assignment]
        chunks = chunk_list(resources, resources_per_part) or [[]]
        part_counts[class_name] = len(chunks)

        class_part_dir = build_root / slugify(class_name)
        class_part_dir.mkdir(parents=True, exist_ok=True)

        for i, chunk in enumerate(chunks, start=1):
            tex = write_class_part_tex(
                out_dir=out_dir,
                topic=topic,
                class_name=class_name,
                part_idx=i,
                part_total=len(chunks),
                resources=chunk,
                web_links=web_links,
                part_dir=class_part_dir,
            )
            run_latexmk(out_dir, tex.relative_to(out_dir))
            pdf = out_dir / f"{slugify(class_name)}_part_{i:03d}.pdf"
            if not is_valid_pdf(pdf):
                raise RuntimeError(f"Missing/invalid class-part PDF: {pdf}")
            append_pdf_to_writer(writer, pdf)
            cleanup_latex_sidecars(out_dir, f"{slugify(class_name)}_part_{i:03d}")
            print(f"[built] {class_name} part {i}/{len(chunks)} resources={len(chunk)}")

    final_pdf = out_dir / "or_applied_math_bible.pdf"
    final_pdf.parent.mkdir(parents=True, exist_ok=True)
    with final_pdf.open("wb") as f:
        writer.write(f)
    if not is_valid_pdf(final_pdf):
        raise RuntimeError("Final merged bible PDF is invalid.")

    # Remove frontmatter intermediates.
    cleanup_latex_sidecars(out_dir, "or_applied_math_bible_frontmatter")

    summary = {
        "generated_at": datetime.now().isoformat(),
        "resources_per_part": resources_per_part,
        "num_parts_total": sum(part_counts.values()),
        "final_pdf": str(final_pdf),
        "class_summary": {
            c: {
                "pdf_resources": len(class_data[c]["pdf_resources"]),  # type: ignore[index]
                "web_links": len(class_data[c]["web_links"]),  # type: ignore[index]
                "parts": part_counts[c],
            }
            for c in expected
        },
    }
    summary_path = out_dir / "or_applied_math_bible_chunked_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Wrote final bible: {final_pdf}")
    print(f"Wrote summary: {summary_path}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir", type=Path, default=Path("data/assignment_pdf_bundles"))
    p.add_argument(
        "--resources-per-part",
        type=int,
        default=120,
        help="Max number of resources included in each per-class LaTeX chunk.",
    )
    args = p.parse_args()
    run(args.out_dir, resources_per_part=args.resources_per_part)


if __name__ == "__main__":
    main()
