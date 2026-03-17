#!/usr/bin/env python3
"""
Validate quality of compiled OR + Applied Math bible inputs.

Outputs:
- data/assignment_pdf_bundles/bible_quality_report.json
- data/assignment_pdf_bundles/bible_quality_report.md
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.parse import urlparse

from pypdf import PdfReader


INCLUDED_KINDS = {
    "downloaded_pdf",
    "rendered_html",
    "rendered_text",
    "rendered_text_from_invalid_pdf",
    "rendered_zip_summary",
}

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
NOISE_KWS = (
    "office",
    "policy",
    "calendar",
    "staff",
    "gradescope",
    "edstem",
    "piazza",
    "discord",
    "slack",
    "accommodation",
    "logistics",
    "transcript",
    "faq",
    "terminal",
    "main-content",
    "graduate/phd-program",
)


def slugify(name: str) -> str:
    value = name.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return re.sub(r"_+", "_", value).strip("_")


def load_json(path: Path) -> Dict[str, object]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


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
    if any(k in u for k in HARD_EXCLUDE_URL_KWS):
        return False
    if any(k in u for k in WEB_EXCLUDE_KWS):
        return False
    return any(k in u for k in WEB_INCLUDE_KWS)


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


def canonical_resource_key(url: str, rel: str) -> str:
    key = normalize_url_for_dedupe(url)
    if key:
        low = key.lower()
        if "/slides/" in low:
            low = low.replace("_annotated", "").replace("-annotated", "")
        return low
    return rel


def sample_text_len(pdf_path: Path) -> int:
    try:
        reader = PdfReader(str(pdf_path), strict=False)
        if not reader.pages:
            return 0
        text = (reader.pages[0].extract_text() or "").strip()
        return len(text)
    except Exception:
        return 0


def collect_resources(
    out_dir: Path, class_name: str, enriched_manifest: Dict[str, object]
) -> List[Dict[str, str]]:
    out_dir_abs = out_dir.resolve()
    mf = out_dir_abs / slugify(class_name) / "manifest.json"
    if not mf.exists():
        return []
    obj = load_json(mf)

    resources: List[Dict[str, str]] = []
    seen = set()

    for source in obj.get("sources", []):  # type: ignore[union-attr]
        for result in source.get("results", []):
            if result.get("status") != "ok":
                continue
            if result.get("kind") != "downloaded_pdf":
                continue
            rel = result.get("local_pdf")
            if not isinstance(rel, str):
                continue
            p = Path(rel)
            if not p.is_absolute():
                p = (Path.cwd() / p).resolve()
            if not is_valid_pdf(p):
                continue
            url = result.get("url", "")
            if url and not should_include_web_link(url):
                continue
            key = canonical_resource_key(url, str(p))
            if key in seen:
                continue
            seen.add(key)
            resources.append(
                {
                    "url": url,
                    "kind": "downloaded_pdf",
                    "category": url_category(url),
                    "local_pdf": str(p.relative_to(out_dir_abs)),
                }
            )

    cls_enriched = enriched_manifest.get(class_name, {})
    harvested = cls_enriched.get("harvested", []) if isinstance(cls_enriched, dict) else []
    for item in harvested:
        if not isinstance(item, dict):
            continue
        kind = item.get("kind", "")
        if kind not in INCLUDED_KINDS:
            continue
        rel = item.get("local_pdf")
        if not isinstance(rel, str):
            continue
        url = item.get("url", "")
        if kind != "downloaded_pdf" and url and not should_include_web_link(url):
            continue
        p = out_dir_abs / rel
        if not is_valid_pdf(p):
            continue
        if url and not should_include_web_link(url):
            continue
        key = canonical_resource_key(url, rel)
        if key in seen:
            continue
        seen.add(key)
        resources.append(
            {
                "url": url,
                "kind": kind,
                "category": item.get("category", "") or url_category(url),
                "local_pdf": rel,
            }
        )
    return resources


def summarize_class(out_dir: Path, class_name: str, resources: List[Dict[str, str]]) -> Dict[str, object]:
    kinds: Dict[str, int] = {}
    cats: Dict[str, int] = {}
    suspicious = 0
    for r in resources:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
        cats[r["category"]] = cats.get(r["category"], 0) + 1
        u = (r["url"] or "").lower()
        if any(k in u for k in NOISE_KWS):
            suspicious += 1

    sample_n = min(20, len(resources))
    low_text = 0
    if sample_n > 0:
        idxs = [round(i * (len(resources) - 1) / (sample_n - 1)) for i in range(sample_n)] if sample_n > 1 else [0]
        seen_i = set()
        for i in idxs:
            if i in seen_i:
                continue
            seen_i.add(i)
            rel = resources[i]["local_pdf"]
            text_len = sample_text_len(out_dir / rel)
            if text_len < 120:
                low_text += 1

    suspicious_ratio = (suspicious / len(resources)) if resources else 1.0
    low_text_ratio = (low_text / sample_n) if sample_n else 1.0
    coverage_score = min(40.0, len(resources) / 40.0 * 40.0)
    url_clean_score = max(0.0, 30.0 * (1.0 - suspicious_ratio))
    readability_score = max(0.0, 30.0 * (1.0 - low_text_ratio))
    score = round(coverage_score + url_clean_score + readability_score, 1)
    grade = "A" if score >= 85 else ("B" if score >= 70 else ("C" if score >= 55 else "D"))

    flags: List[str] = []
    if len(resources) < 10:
        flags.append("low_coverage")
    if suspicious_ratio > 0.20:
        flags.append("url_noise_high")
    if low_text_ratio > 0.40:
        flags.append("low_text_density_high")

    return {
        "class": class_name,
        "resource_count": len(resources),
        "kinds": kinds,
        "categories": cats,
        "sample_size": sample_n,
        "sample_low_text": low_text,
        "suspicious_url_count": suspicious,
        "suspicious_ratio": round(suspicious_ratio, 4),
        "low_text_ratio": round(low_text_ratio, 4),
        "quality_score": score,
        "quality_grade": grade,
        "flags": flags,
    }


def write_reports(out_dir: Path, payload: Dict[str, object]) -> Tuple[Path, Path]:
    json_path = out_dir / "bible_quality_report.json"
    md_path = out_dir / "bible_quality_report.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Bible Quality Report",
        "",
        f"- Classes checked: {payload['classes_checked']}",
        f"- Total included resources: {payload['total_resources']}",
        f"- Overall mean score: {payload['overall_mean_score']}",
        f"- Classes with flags: {payload['classes_with_flags']}",
        "",
        "| Class | Resources | Score | Grade | Flags |",
        "|---|---:|---:|:---:|---|",
    ]
    for row in payload["class_results"]:
        flags = ", ".join(row["flags"]) if row["flags"] else "None"
        lines.append(
            f"| {row['class']} | {row['resource_count']} | {row['quality_score']} | {row['quality_grade']} | {flags} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def run(out_dir: Path) -> None:
    out_dir = out_dir.resolve()
    summary = load_json(out_dir / "or_applied_math_bible_chunked_summary.json")
    class_summary = summary.get("class_summary", {})
    class_names = list(class_summary.keys()) if isinstance(class_summary, dict) else []
    enriched_manifest = load_json(out_dir / "enriched_manifest.json")

    class_results = []
    total = 0
    for cls in class_names:
        resources = collect_resources(out_dir, cls, enriched_manifest)
        result = summarize_class(out_dir, cls, resources)
        class_results.append(result)
        total += result["resource_count"]

    mean_score = round(
        (sum(r["quality_score"] for r in class_results) / len(class_results)) if class_results else 0.0,
        2,
    )
    flagged = sum(1 for r in class_results if r["flags"])
    payload = {
        "classes_checked": len(class_results),
        "total_resources": total,
        "overall_mean_score": mean_score,
        "classes_with_flags": flagged,
        "class_results": class_results,
    }
    json_path, md_path = write_reports(out_dir, payload)
    print(f"Wrote quality JSON: {json_path}")
    print(f"Wrote quality Markdown: {md_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=Path("data/assignment_pdf_bundles"))
    args = parser.parse_args()
    run(args.out_dir)


if __name__ == "__main__":
    main()
