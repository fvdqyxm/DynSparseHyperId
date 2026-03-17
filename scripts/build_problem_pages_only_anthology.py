#!/usr/bin/env python3
"""
Build a problem-pages-only anthology PDF (no link/index tables).

Inputs:
- resource manifest from the professor bible build

Outputs:
- data/assignment_pdf_bundles/problem_pages_only_anthology.pdf
- data/assignment_pdf_bundles/problem_pages_only_anthology_summary.json
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.parse import urlparse

from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


PROBLEMISH_CATS = {"Problems", "Projects/Labs", "Exams"}
SOLUTION_RE = re.compile(
    r"(solutions?|soln|answers?|keys?|hints?|(^|[^a-z0-9])sol([^a-z0-9]|$))",
    re.IGNORECASE,
)
PROBLEM_SIGNAL_RE = re.compile(
    r"(problem|exercise|homework|assignment|pset|worksheet|question|q\.?\s*[0-9]|points|project|lab)",
    re.IGNORECASE,
)
HARD_NOISE_RE = re.compile(
    r"(404 error|page has not been released yet|preliminary examination|graduate preliminary examination)",
    re.IGNORECASE,
)
SOFT_NOISE_RE = re.compile(
    r"(syllabus|calendar|office hours|course staff|grading policy|academic integrity|discussion section|logistics)",
    re.IGNORECASE,
)
SOURCE_PAGE_RE = re.compile(r"^\s*source:\s*https?://", re.IGNORECASE)
COLLECTION_URL_RE = re.compile(
    r"/(assignments|homeworks|projects|labs|exams|resources|syllabus)(/)?$",
    re.IGNORECASE,
)
BAD_URL_RE = re.compile(
    r"(prelimexam|syllabus|/faq/|/common-errors|/software/|/forum-threads/|/policy/)",
    re.IGNORECASE,
)
FALLBACK_URL_SIGNAL_RE = re.compile(
    r"(homework|problem|exercise|pset|assignment|worksheet|quiz|exam|midterm|final|project|lab)",
    re.IGNORECASE,
)


def load_class_order() -> List[str]:
    ns: Dict[str, object] = {}
    script = Path("scripts/build_or_applied_math_bible_chunked.py")
    exec(script.read_text(encoding="utf-8"), ns)  # noqa: S102
    fn = ns["class_order_and_topic_map"]
    order, _ = fn()
    return order


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


def is_valid_pdf(path: Path) -> bool:
    if not path.exists() or path.stat().st_size == 0:
        return False
    try:
        with path.open("rb") as f:
            return f.read(5) == b"%PDF-"
    except Exception:
        return False


def solution_like(row: Dict[str, object]) -> bool:
    if bool(row.get("solution_like", False)):
        return True
    s = f"{str(row.get('url', '')).lower()} {str(row.get('local_pdf_rel', '')).lower()}"
    return bool(SOLUTION_RE.search(s))


def first_page_text(pdf_path: Path, cache: Dict[str, str]) -> str:
    key = str(pdf_path)
    if key in cache:
        return cache[key]
    txt = ""
    try:
        reader = PdfReader(str(pdf_path), strict=False)
        if reader.pages:
            txt = reader.pages[0].extract_text() or ""
    except Exception:
        txt = ""
    txt = " ".join(txt.split())[:3000]
    cache[key] = txt
    return txt


def url_problem_signal(url: str) -> bool:
    return bool(PROBLEM_SIGNAL_RE.search(url or ""))


def row_passes_quality(
    row: Dict[str, object],
    out_dir: Path,
    text_cache: Dict[str, str],
    strict: bool,
) -> bool:
    url = str(row.get("url", ""))
    low_url = url.lower()
    rel = str(row.get("local_pdf_rel", ""))
    if not rel:
        return False
    pdf = out_dir / rel
    if not is_valid_pdf(pdf):
        return False
    if BAD_URL_RE.search(low_url):
        return False
    if COLLECTION_URL_RE.search(low_url):
        return False

    txt = first_page_text(pdf, text_cache)
    low_txt = txt.lower()
    has_prob_signal = bool(PROBLEM_SIGNAL_RE.search(low_txt)) or url_problem_signal(low_url)

    if HARD_NOISE_RE.search(low_url) or HARD_NOISE_RE.search(low_txt):
        return False

    # Reject obvious scraped index/TOC pages unless they still clearly contain problem prompts.
    if SOURCE_PAGE_RE.search(low_txt):
        if "table of contents" in low_txt and not has_prob_signal:
            return False
        if "skip to main content" in low_txt and not has_prob_signal:
            return False

    if strict:
        if SOFT_NOISE_RE.search(low_txt) and not has_prob_signal:
            return False
        kind = str(row.get("kind", ""))
        if kind != "downloaded_pdf":
            # Rendered HTML/text must show explicit problem signal to be included.
            if not has_prob_signal:
                return False
            if "table of contents" in low_txt and "problem" not in low_txt and "exercise" not in low_txt:
                return False
        else:
            # For direct PDFs, still require at least some problem/exam/project cue in URL or text.
            if not has_prob_signal and str(row.get("category", "")) not in {"Exams"}:
                return False

    return True


def select_rows(
    out_dir: Path,
    rows: List[Dict[str, object]],
    include_anchor_fallback: bool,
    max_per_class: int,
    strict_quality: bool,
) -> Tuple[List[Dict[str, object]], bool]:
    text_cache: Dict[str, str] = {}
    primary = [
        r
        for r in rows
        if str(r.get("category", "")) in PROBLEMISH_CATS
        and not solution_like(r)
        and row_passes_quality(r, out_dir=out_dir, text_cache=text_cache, strict=strict_quality)
    ]
    used_anchor = False
    selected = primary
    if not selected and include_anchor_fallback:
        fallback = [
            r
            for r in rows
            if not solution_like(r)
            and (
                bool(r.get("anchor", False))
                or str(r.get("category", "")) == "Lectures/Notes"
            )
            and FALLBACK_URL_SIGNAL_RE.search(str(r.get("url", "")))
            and row_passes_quality(r, out_dir=out_dir, text_cache=text_cache, strict=strict_quality)
        ]
        selected = fallback
        used_anchor = len(fallback) > 0

    # Per-class dedupe
    seen = set()
    deduped: List[Dict[str, object]] = []
    for r in selected:
        key = (normalize_url(str(r.get("url", ""))), str(r.get("local_pdf_rel", "")))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)

    if max_per_class > 0:
        deduped = deduped[:max_per_class]
    return deduped, used_anchor


def append_pdf(writer: PdfWriter, pdf_path: Path) -> int:
    try:
        reader = PdfReader(str(pdf_path), strict=False)
        for p in reader.pages:
            writer.add_page(p)
        return len(reader.pages)
    except Exception:
        return 0


def write_cover(path: Path, total_classes: int, total_resources: int) -> None:
    c = canvas.Canvas(str(path), pagesize=letter)
    w, h = letter
    c.setFont("Helvetica-Bold", 22)
    c.drawString(60, h - 100, "OR + Applied Math Problem Pages Anthology")
    c.setFont("Helvetica", 12)
    c.drawString(60, h - 140, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    c.drawString(60, h - 162, f"Classes covered: {total_classes}")
    c.drawString(60, h - 184, f"Problem documents included: {total_resources}")
    c.drawString(60, h - 220, "This file contains actual problem documents only.")
    c.drawString(60, h - 242, "No URL index pages are included.")
    c.showPage()
    c.save()


def write_divider(path: Path, class_name: str, count: int, anchor_mode: bool) -> None:
    c = canvas.Canvas(str(path), pagesize=letter)
    w, h = letter
    c.setFont("Helvetica-Bold", 20)
    c.drawString(60, h - 110, class_name)
    c.setFont("Helvetica", 12)
    c.drawString(60, h - 148, f"Documents appended: {count}")
    if anchor_mode:
        c.drawString(60, h - 170, "Note: used non-solution exercise-bearing notes fallback for this class.")
    c.showPage()
    c.save()


def run(
    out_dir: Path,
    resources_json: Path,
    output_pdf: Path,
    include_anchor_fallback: bool,
    max_per_class: int,
    strict_quality: bool,
    min_per_class: int,
) -> None:
    out_dir = out_dir.resolve()
    resources_json = resources_json.resolve()
    payload = json.loads(resources_json.read_text(encoding="utf-8"))
    class_order = load_class_order()

    selected_by_class: Dict[str, List[Dict[str, object]]] = {}
    anchor_classes: List[str] = []
    for cls in class_order:
        rows = payload.get(cls, [])
        if not isinstance(rows, list):
            rows = []
        selected, used_anchor = select_rows(
            out_dir=out_dir,
            rows=rows,
            include_anchor_fallback=include_anchor_fallback,
            max_per_class=max_per_class,
            strict_quality=strict_quality,
        )
        selected_by_class[cls] = selected
        if used_anchor:
            anchor_classes.append(cls)

    # Global de-duplication by normalized URL, with class-level minimum fallback.
    global_seen = set()
    deduped_by_class: Dict[str, List[Dict[str, object]]] = {}
    for cls in class_order:
        deduped_by_class[cls] = []
        for r in selected_by_class[cls]:
            gk = normalize_url(str(r.get("url", ""))) or str(r.get("local_pdf_rel", ""))
            if gk in global_seen:
                continue
            global_seen.add(gk)
            deduped_by_class[cls].append(r)
        if len(deduped_by_class[cls]) < min_per_class:
            local_seen = {
                (normalize_url(str(x.get("url", ""))), str(x.get("local_pdf_rel", "")))
                for x in deduped_by_class[cls]
            }
            for r in selected_by_class[cls]:
                if len(deduped_by_class[cls]) >= min_per_class:
                    break
                lk = (normalize_url(str(r.get("url", ""))), str(r.get("local_pdf_rel", "")))
                if lk in local_seen:
                    continue
                deduped_by_class[cls].append(r)
                local_seen.add(lk)

    selected_by_class = deduped_by_class

    selected_manifest = {
        cls: selected_by_class[cls]
        for cls in class_order
    }
    selected_manifest_path = out_dir / "problem_pages_only_anthology_selected.json"
    selected_manifest_path.write_text(json.dumps(selected_manifest, indent=2), encoding="utf-8")

    writer = PdfWriter()
    tmp_dir = out_dir / "_problem_pages_only_dividers"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    total_resources = sum(len(v) for v in selected_by_class.values())
    cover = tmp_dir / "cover.pdf"
    write_cover(cover, total_classes=len(class_order), total_resources=total_resources)
    append_pdf(writer, cover)

    class_pages: Dict[str, int] = {}
    included_docs = 0
    for cls in class_order:
        rows = selected_by_class[cls]
        if not rows:
            class_pages[cls] = 0
            continue
        divider = tmp_dir / (re.sub(r"[^a-z0-9]+", "_", cls.lower()).strip("_") + ".pdf")
        write_divider(divider, cls, len(rows), cls in anchor_classes)
        append_pdf(writer, divider)

        pages = 0
        for r in rows:
            rel = str(r.get("local_pdf_rel", ""))
            if not rel:
                continue
            pdf = out_dir / rel
            if not is_valid_pdf(pdf):
                continue
            n = append_pdf(writer, pdf)
            if n > 0:
                included_docs += 1
                pages += n
        class_pages[cls] = pages

    output_pdf = output_pdf.resolve()
    with output_pdf.open("wb") as f:
        writer.write(f)
    if not is_valid_pdf(output_pdf):
        raise RuntimeError(f"Failed to create output PDF: {output_pdf}")

    summary = {
        "generated_at": datetime.now().isoformat(),
        "resources_json": str(resources_json),
        "selected_manifest_json": str(selected_manifest_path),
        "output_pdf": str(output_pdf),
        "total_classes": len(class_order),
        "total_selected_rows": total_resources,
        "total_included_docs": included_docs,
        "strict_quality": strict_quality,
        "min_per_class": min_per_class,
        "anchor_fallback_classes": anchor_classes,
        "class_summary": {
            cls: {
                "selected_rows": len(selected_by_class[cls]),
                "estimated_pages": class_pages.get(cls, 0),
            }
            for cls in class_order
        },
    }
    summary_path = out_dir / "problem_pages_only_anthology_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Wrote problem-only PDF: {output_pdf}")
    print(f"Wrote selected manifest: {selected_manifest_path}")
    print(f"Wrote summary: {summary_path}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir", type=Path, default=Path("data/assignment_pdf_bundles"))
    p.add_argument(
        "--resources-json",
        type=Path,
        default=Path("data/assignment_pdf_bundles/phd_problem_solving_bible_resources.json"),
    )
    p.add_argument(
        "--output-pdf",
        type=Path,
        default=Path("data/assignment_pdf_bundles/problem_pages_only_anthology.pdf"),
    )
    p.add_argument(
        "--include-anchor-fallback",
        action="store_true",
        help="If a class has no direct problem/exam/project docs, include non-solution lecture anchors.",
    )
    p.add_argument(
        "--max-per-class",
        type=int,
        default=0,
        help="Limit per class (0 means no limit).",
    )
    p.add_argument(
        "--strict-quality",
        action="store_true",
        help="Enable strict quality filtering (recommended).",
    )
    p.add_argument(
        "--min-per-class",
        type=int,
        default=4,
        help="Minimum kept docs per class after global dedupe (fallback may re-allow duplicates).",
    )
    args = p.parse_args()
    run(
        out_dir=args.out_dir,
        resources_json=args.resources_json,
        output_pdf=args.output_pdf,
        include_anchor_fallback=args.include_anchor_fallback,
        max_per_class=args.max_per_class,
        strict_quality=args.strict_quality,
        min_per_class=args.min_per_class,
    )


if __name__ == "__main__":
    main()
