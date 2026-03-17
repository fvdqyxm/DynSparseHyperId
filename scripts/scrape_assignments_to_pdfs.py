#!/usr/bin/env python3
"""
Scrape assignment links from course source pages and compile per-class PDFs.

Usage:
  venv/bin/python scripts/scrape_assignments_to_pdfs.py \
    --input docs/problem_set_links_coverage.md \
    --out-dir data/assignment_pdf_bundles
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import textwrap
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


ASSIGNMENT_KEYWORDS = (
    "assign",
    "homework",
    "hw",
    "pset",
    "problem",
    "exercise",
    "worksheet",
    "lab",
    "project",
    "quiz",
    "midterm",
    "final",
)

SKIP_PREFIXES = ("mailto:", "javascript:", "#")
PDF_EXTENSIONS = (".pdf", ".ps")


@dataclass
class Artifact:
    url: str
    local_pdf: Path
    source_url: str
    kind: str  # downloaded_pdf | rendered_html


def slugify(name: str) -> str:
    value = name.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return re.sub(r"_+", "_", value).strip("_")


def parse_classes(markdown_path: Path) -> Dict[str, List[str]]:
    classes: Dict[str, List[str]] = {}
    current_class = None

    for raw_line in markdown_path.read_text(encoding="utf-8").splitlines():
        heading = re.match(r"^####\s+(.+?)\s*\(", raw_line)
        if heading:
            current_class = heading.group(1).strip()
            classes.setdefault(current_class, [])
            continue

        url_match = re.search(r"https?://[^ )]+", raw_line)
        if current_class and url_match:
            url = url_match.group(0).rstrip(").,")
            classes[current_class].append(url)

    # De-duplicate while preserving order.
    for class_name, urls in list(classes.items()):
        seen = set()
        deduped = []
        for u in urls:
            if u not in seen:
                seen.add(u)
                deduped.append(u)
        classes[class_name] = deduped

    return classes


def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            )
        }
    )
    return s


def fetch(session: requests.Session, url: str, timeout_s: int, retries: int) -> requests.Response:
    last_err = None
    for attempt in range(retries):
        try:
            resp = session.get(url, timeout=timeout_s, allow_redirects=True)
            return resp
        except requests.RequestException as exc:
            last_err = exc
            # Small backoff.
            time.sleep(0.4 * (attempt + 1))
    raise RuntimeError(f"Failed to fetch {url}: {last_err}")


def looks_like_pdf(url: str, content_type: str) -> bool:
    return url.lower().endswith(PDF_EXTENSIONS) or "application/pdf" in content_type.lower()


def should_keep_discovered_link(link: str, anchor_text: str, source_netloc: str) -> bool:
    lower_link = link.lower()
    lower_text = anchor_text.lower()

    if not (lower_link.startswith("http://") or lower_link.startswith("https://")):
        return False
    if any(lower_link.startswith(prefix) for prefix in SKIP_PREFIXES):
        return False

    # Always keep direct PDF-like links.
    if lower_link.endswith(PDF_EXTENSIONS):
        return True

    has_keyword = any(k in lower_link or k in lower_text for k in ASSIGNMENT_KEYWORDS)
    if not has_keyword:
        return False

    # Keep same-domain assignment-like links by default.
    return urlparse(link).netloc == source_netloc


def discover_assignment_links(
    session: requests.Session,
    source_url: str,
    timeout_s: int,
    retries: int,
    max_links_per_source: int,
) -> List[str]:
    try:
        resp = fetch(session, source_url, timeout_s=timeout_s, retries=retries)
    except Exception:
        return []

    content_type = resp.headers.get("Content-Type", "")
    final_url = resp.url

    if looks_like_pdf(final_url, content_type):
        return [final_url]

    if "text/html" not in content_type.lower():
        # Non-HTML content that's not PDF is ignored.
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    source_netloc = urlparse(final_url).netloc
    discovered: List[str] = []

    # Include the page itself as a fallback artifact.
    discovered.append(final_url)

    for a in soup.find_all("a", href=True):
        href = a.get("href", "").strip()
        if not href:
            continue
        full = urljoin(final_url, href)
        text = a.get_text(" ", strip=True)
        if should_keep_discovered_link(full, text, source_netloc):
            discovered.append(full)
        if len(discovered) >= max_links_per_source:
            break

    # De-duplicate preserving order.
    seen = set()
    out = []
    for u in discovered:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out[:max_links_per_source]


def write_text_pdf(out_pdf: Path, title: str, body_text: str) -> None:
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(out_pdf), pagesize=letter)
    width, height = letter
    left_margin = 44
    top = height - 44
    line_height = 12
    max_chars = 105

    lines = [f"Source: {title}", ""]
    for paragraph in body_text.splitlines():
        if not paragraph.strip():
            lines.append("")
            continue
        lines.extend(textwrap.wrap(paragraph, width=max_chars))

    y = top
    for line in lines:
        if y < 44:
            c.showPage()
            y = top
        c.drawString(left_margin, y, line[:max_chars])
        y -= line_height
    c.save()


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.extract()
    text = soup.get_text("\n", strip=True)
    # Avoid gigantic whitespace blocks.
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def download_or_render_to_pdf(
    session: requests.Session,
    url: str,
    source_url: str,
    out_pdf: Path,
    timeout_s: int,
    retries: int,
) -> Tuple[bool, str]:
    try:
        resp = fetch(session, url, timeout_s=timeout_s, retries=retries)
    except Exception as exc:
        return False, f"fetch_failed: {exc}"

    content_type = resp.headers.get("Content-Type", "")
    final_url = resp.url

    if looks_like_pdf(final_url, content_type):
        out_pdf.parent.mkdir(parents=True, exist_ok=True)
        out_pdf.write_bytes(resp.content)
        return True, "downloaded_pdf"

    if "text/html" in content_type.lower() or not content_type:
        text = html_to_text(resp.text)
        if not text.strip():
            return False, "empty_html_text"
        write_text_pdf(out_pdf, title=final_url, body_text=text)
        return True, "rendered_html"

    return False, f"unsupported_content_type:{content_type}"


def merge_pdfs(input_pdfs: Sequence[Path], out_pdf: Path) -> None:
    writer = PdfWriter()
    for pdf_path in input_pdfs:
        try:
            reader = PdfReader(str(pdf_path))
            for page in reader.pages:
                writer.add_page(page)
        except Exception:
            # Skip unreadable PDFs but continue.
            continue
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    with out_pdf.open("wb") as f:
        writer.write(f)


def run(
    input_md: Path,
    out_dir: Path,
    timeout_s: int,
    retries: int,
    delay_s: float,
    max_links_per_source: int,
    max_artifacts_per_class: int,
) -> None:
    classes = parse_classes(input_md)
    if not classes:
        raise RuntimeError(f"No class/source URLs found in {input_md}")

    out_dir.mkdir(parents=True, exist_ok=True)
    session = make_session()

    all_class_bundles: List[Path] = []
    global_manifest = {}
    # URL cache avoids repeatedly downloading the same artifact across classes.
    # url -> (ok, kind_or_err, cached_pdf_path)
    url_cache: Dict[str, Tuple[bool, str, Path | None]] = {}

    for class_name, source_urls in classes.items():
        print(f"[class] {class_name} ({len(source_urls)} source URLs)")
        class_slug = slugify(class_name)
        class_dir = out_dir / class_slug
        raw_dir = class_dir / "raw_pdfs"
        raw_dir.mkdir(parents=True, exist_ok=True)

        class_manifest = {
            "class_name": class_name,
            "source_urls": source_urls,
            "sources": [],
            "artifacts": [],
        }

        artifacts: List[Artifact] = []
        artifact_counter = 1

        for source_url in source_urls:
            discovered = discover_assignment_links(
                session=session,
                source_url=source_url,
                timeout_s=timeout_s,
                retries=retries,
                max_links_per_source=max_links_per_source,
            )
            print(f"  [source] discovered {len(discovered)} candidate links: {source_url}")

            source_record = {
                "source_url": source_url,
                "discovered_links": discovered,
                "results": [],
            }

            for link in discovered:
                if len(artifacts) >= max_artifacts_per_class:
                    break

                local_pdf = raw_dir / f"{artifact_counter:04d}.pdf"
                if link in url_cache:
                    ok, kind_or_err, cached_pdf = url_cache[link]
                    if ok and cached_pdf and cached_pdf.exists():
                        local_pdf.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(cached_pdf, local_pdf)
                else:
                    ok, kind_or_err = download_or_render_to_pdf(
                        session=session,
                        url=link,
                        source_url=source_url,
                        out_pdf=local_pdf,
                        timeout_s=timeout_s,
                        retries=retries,
                    )
                    cached_pdf = local_pdf if ok else None
                    url_cache[link] = (ok, kind_or_err, cached_pdf)

                if ok:
                    artifacts.append(
                        Artifact(
                            url=link,
                            local_pdf=local_pdf,
                            source_url=source_url,
                            kind=kind_or_err,
                        )
                    )
                    source_record["results"].append(
                        {"url": link, "status": "ok", "kind": kind_or_err, "local_pdf": str(local_pdf)}
                    )
                    artifact_counter += 1
                else:
                    source_record["results"].append(
                        {"url": link, "status": "failed", "error": kind_or_err}
                    )

                if delay_s > 0:
                    time.sleep(delay_s)

            class_manifest["sources"].append(source_record)
            if len(artifacts) >= max_artifacts_per_class:
                print(f"  [cap] reached max_artifacts_per_class={max_artifacts_per_class}")
                break

        for art in artifacts:
            class_manifest["artifacts"].append(
                {
                    "url": art.url,
                    "local_pdf": str(art.local_pdf),
                    "source_url": art.source_url,
                    "kind": art.kind,
                }
            )

        class_bundle = class_dir / f"{class_slug}_bundle.pdf"
        merge_pdfs([a.local_pdf for a in artifacts], class_bundle)
        class_manifest["bundle_pdf"] = str(class_bundle)
        class_manifest["artifact_count"] = len(artifacts)
        print(f"  [class_done] artifacts={len(artifacts)} bundle={class_bundle}")

        (class_dir / "manifest.json").write_text(json.dumps(class_manifest, indent=2), encoding="utf-8")
        global_manifest[class_name] = class_manifest

        if class_bundle.exists() and class_bundle.stat().st_size > 0:
            all_class_bundles.append(class_bundle)

    # Master bundle.
    master_bundle = out_dir / "all_classes_bundle.pdf"
    merge_pdfs(all_class_bundles, master_bundle)
    global_manifest_path = out_dir / "manifest.json"
    global_manifest_path.write_text(json.dumps(global_manifest, indent=2), encoding="utf-8")

    print(f"Wrote class bundles and manifests to: {out_dir}")
    print(f"Wrote master bundle: {master_bundle}")


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--input",
        type=Path,
        default=Path("docs/problem_set_links_coverage.md"),
        help="Markdown file containing class headings and source URLs.",
    )
    p.add_argument(
        "--out-dir",
        type=Path,
        default=Path("data/assignment_pdf_bundles"),
        help="Directory where raw PDFs, manifests, and bundles are written.",
    )
    p.add_argument("--timeout-s", type=int, default=25, help="HTTP timeout in seconds.")
    p.add_argument("--retries", type=int, default=3, help="HTTP retries per URL.")
    p.add_argument("--delay-s", type=float, default=0.15, help="Delay between requests.")
    p.add_argument(
        "--max-links-per-source",
        type=int,
        default=50,
        help="Max discovered assignment links to process per source URL.",
    )
    p.add_argument(
        "--max-artifacts-per-class",
        type=int,
        default=150,
        help="Safety cap for number of PDFs generated per class.",
    )
    return p


def main() -> None:
    args = build_arg_parser().parse_args()
    run(
        input_md=args.input,
        out_dir=args.out_dir,
        timeout_s=args.timeout_s,
        retries=args.retries,
        delay_s=args.delay_s,
        max_links_per_source=args.max_links_per_source,
        max_artifacts_per_class=args.max_artifacts_per_class,
    )


if __name__ == "__main__":
    main()
