#!/usr/bin/env python3
"""
Exhaustive enrichment crawl for lecture + problem resources across all classes.

Outputs:
- data/assignment_pdf_bundles/enriched_manifest.json
- data/assignment_pdf_bundles/<class_slug>/enriched_pdfs/*.pdf
"""

from __future__ import annotations

import argparse
import io
import json
import re
import textwrap
import time
import zipfile
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


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
KEYWORDS = PROBLEM_KWS + LECTURE_KWS + PROJECT_KWS + EXAM_KWS

HTML_EXCLUDE_KWS = (
    "calendar",
    "office",
    "discussion",
    "piazza",
    "edstem",
    "discord",
    "gradescope",
    "logistics",
    "policy",
    "staff",
)

FILE_EXTS = (".pdf", ".tex", ".zip", ".ps", ".txt", ".md")
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp")
SKIP_PREFIXES = ("mailto:", "javascript:", "#")


@dataclass
class HarvestedItem:
    url: str
    category: str
    kind: str
    local_pdf: str
    source_page: str
    depth: int


def slugify(name: str) -> str:
    value = name.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return re.sub(r"_+", "_", value).strip("_")


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
    last_exc = None
    for attempt in range(retries):
        try:
            return session.get(url, timeout=timeout_s, allow_redirects=True)
        except requests.RequestException as exc:
            last_exc = exc
            time.sleep(0.4 * (attempt + 1))
    raise RuntimeError(f"fetch_failed: {last_exc}")


def category_for_url(url: str) -> str:
    u = url.lower()
    if any(k in u for k in PROBLEM_KWS):
        return "Problems"
    if any(k in u for k in LECTURE_KWS):
        return "Lectures/Notes"
    if any(k in u for k in PROJECT_KWS):
        return "Projects/Labs"
    if any(k in u for k in EXAM_KWS):
        return "Exams"
    return "Reference"


def has_keywords(text: str) -> bool:
    low = text.lower()
    return any(k in low for k in KEYWORDS)


def should_skip_url(url: str) -> bool:
    low = url.lower()
    if any(low.startswith(p) for p in SKIP_PREFIXES):
        return True
    return any(k in low for k in HTML_EXCLUDE_KWS)


def should_consider_resource(url: str, anchor_text: str) -> bool:
    low = url.lower()
    if any(low.endswith(ext) for ext in FILE_EXTS):
        return True
    return has_keywords(low) or has_keywords(anchor_text)


def should_crawl_html(url: str, anchor_text: str, allowed_hosts: Set[str], depth: int, max_depth: int) -> bool:
    if depth >= max_depth:
        return False
    low = url.lower()
    if any(low.endswith(ext) for ext in FILE_EXTS + IMAGE_EXTS):
        return False
    if should_skip_url(low):
        return False
    host = urlparse(url).netloc.lower()
    if host not in allowed_hosts:
        return False
    return has_keywords(low) or has_keywords(anchor_text) or "/resources/" in low or "/assignments/" in low


def decode_text(data: bytes) -> str:
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "nav", "footer", "header"]):
        tag.extract()

    # Prefer main/article content if available.
    main = soup.find("main") or soup.find("article")
    target = main if main is not None else soup
    text = target.get_text("\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Keep lines likely relevant to lecture/problem content.
    kept = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        low = line.lower()
        if any(k in low for k in HTML_EXCLUDE_KWS):
            continue
        if len(line) < 2:
            continue
        kept.append(line)
    return "\n".join(kept[:2500])


def write_text_pdf(out_pdf: Path, title: str, body: str) -> None:
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(out_pdf), pagesize=letter)
    width, height = letter
    x = 44
    y = height - 44
    max_chars = 105
    line_h = 12
    lines = [f"Source: {title}", ""]
    for para in body.splitlines():
        if not para.strip():
            lines.append("")
            continue
        lines.extend(textwrap.wrap(para, width=max_chars))
    for line in lines:
        if y < 44:
            c.showPage()
            y = height - 44
        c.drawString(x, y, line[:max_chars])
        y -= line_h
    c.save()


def write_image_pdf(out_pdf: Path, title: str, img: bytes) -> None:
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(out_pdf), pagesize=letter)
    w, h = letter
    c.setFont("Helvetica", 10)
    c.drawString(44, h - 28, f"Source: {title}"[:140])
    reader = ImageReader(io.BytesIO(img))
    c.drawImage(reader, 44, 80, width=w - 88, height=h - 140, preserveAspectRatio=True, anchor="c")
    c.save()


def write_zip_summary_pdf(out_pdf: Path, title: str, zip_bytes: bytes) -> None:
    lines: List[str] = ["ZIP archive summary", ""]
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        infos = zf.infolist()
        lines.append(f"Entries: {len(infos)}")
        lines.append("")
        for info in infos[:400]:
            lines.append(f"- {info.filename} ({info.file_size} bytes)")
        lines.append("")
        lines.append("Preview of TeX/text files:")
        shown = 0
        for info in infos:
            if shown >= 20:
                break
            n = info.filename.lower()
            if info.is_dir():
                continue
            if not n.endswith((".tex", ".txt", ".md")):
                continue
            if info.file_size > 350_000:
                continue
            try:
                text = decode_text(zf.read(info.filename))
            except Exception:
                continue
            lines.append("")
            lines.append(f"=== {info.filename} ===")
            lines.extend(text.splitlines()[:70])
            shown += 1
    write_text_pdf(out_pdf, title, "\n".join(lines))


def to_pdf(
    session: requests.Session,
    url: str,
    out_pdf: Path,
    timeout_s: int,
    retries: int,
) -> Tuple[bool, str]:
    try:
        resp = fetch(session, url, timeout_s=timeout_s, retries=retries)
    except Exception as exc:
        return False, f"fetch_failed:{exc}"

    final_url = resp.url
    ctype = (resp.headers.get("Content-Type") or "").lower()
    path_low = urlparse(final_url).path.lower()
    data = resp.content or b""

    if data.startswith(b"%PDF-"):
        out_pdf.parent.mkdir(parents=True, exist_ok=True)
        out_pdf.write_bytes(data)
        return True, "downloaded_pdf"

    if path_low.endswith(".pdf") or "application/pdf" in ctype:
        # mislabeled/non-pdf payload
        text = decode_text(data)
        if "<html" in text.lower() or "<!doctype" in text.lower():
            text = html_to_text(text)
        if text.strip():
            write_text_pdf(out_pdf, final_url, text)
            return True, "rendered_text_from_invalid_pdf"
        return False, "invalid_pdf_payload"

    if "text/html" in ctype or path_low.endswith((".html", ".htm")):
        text = html_to_text(resp.text)
        if not text.strip():
            return False, "empty_html_text"
        write_text_pdf(out_pdf, final_url, text)
        return True, "rendered_html"

    if path_low.endswith(".zip") or "application/zip" in ctype or "application/x-zip-compressed" in ctype:
        try:
            write_zip_summary_pdf(out_pdf, final_url, data)
            return True, "rendered_zip_summary"
        except Exception as exc:
            return False, f"zip_render_failed:{exc}"

    if path_low.endswith((".tex", ".txt", ".md", ".ps")) or ctype.startswith("text/") or "application/x-tex" in ctype:
        text = decode_text(data)
        if not text.strip():
            return False, "empty_text"
        write_text_pdf(out_pdf, final_url, text)
        return True, "rendered_text"

    if path_low.endswith(IMAGE_EXTS) or ctype.startswith("image/"):
        try:
            write_image_pdf(out_pdf, final_url, data)
            return True, "rendered_image"
        except Exception as exc:
            return False, f"image_render_failed:{exc}"

    return False, f"unsupported_content_type:{ctype}"


def seed_urls_for_class(out_dir: Path, class_name: str) -> List[str]:
    slug = slugify(class_name)
    mf = out_dir / slug / "manifest.json"
    if not mf.exists():
        return []
    obj = json.loads(mf.read_text(encoding="utf-8"))
    seeds = []
    for u in obj.get("source_urls", []):
        if isinstance(u, str):
            seeds.append(u)
    for s in obj.get("sources", []):
        su = s.get("source_url")
        if isinstance(su, str):
            seeds.append(su)
        for r in s.get("results", []):
            if r.get("status") == "ok" and r.get("kind") in ("rendered_html", "downloaded_pdf"):
                u = r.get("url")
                if isinstance(u, str):
                    seeds.append(u)
    out = []
    seen = set()
    for u in seeds:
        if not u or u in seen:
            continue
        seen.add(u)
        out.append(u)
    return out


def crawl_and_harvest(
    session: requests.Session,
    class_name: str,
    out_dir: Path,
    max_depth: int,
    max_pages: int,
    max_items: int,
    timeout_s: int,
    retries: int,
    delay_s: float,
) -> Dict[str, object]:
    slug = slugify(class_name)
    class_dir = out_dir / slug
    enrich_dir = class_dir / "enriched_pdfs"
    enrich_dir.mkdir(parents=True, exist_ok=True)

    # Clear old enriched output for deterministic rebuild.
    for old in enrich_dir.glob("*.pdf"):
        old.unlink(missing_ok=True)

    seeds = seed_urls_for_class(out_dir, class_name)
    if not seeds:
        return {"class_name": class_name, "class_slug": slug, "seeds": [], "harvested": [], "failed": []}

    allowed_hosts: Set[str] = set()
    for u in seeds:
        host = urlparse(u).netloc.lower()
        if host:
            allowed_hosts.add(host)
            # Allow subdomain variants by suffix matching later.

    def host_allowed(url: str) -> bool:
        host = urlparse(url).netloc.lower()
        if host in allowed_hosts:
            return True
        return any(host.endswith("." + ah) for ah in allowed_hosts)

    queue = deque((u, 0, u) for u in seeds if u.startswith("http"))
    seen_pages: Set[str] = set()
    candidate_resources: Dict[str, Tuple[str, int, str]] = {}
    # url -> (category, depth, source_page)

    while queue and len(seen_pages) < max_pages and len(candidate_resources) < max_items:
        page_url, depth, source_page = queue.popleft()
        if page_url in seen_pages:
            continue
        if not host_allowed(page_url):
            continue
        seen_pages.add(page_url)

        try:
            resp = fetch(session, page_url, timeout_s=timeout_s, retries=retries)
        except Exception:
            continue

        final_url = resp.url
        ctype = (resp.headers.get("Content-Type") or "").lower()
        low_path = urlparse(final_url).path.lower()

        # Direct resource page.
        if any(low_path.endswith(ext) for ext in FILE_EXTS) or "application/pdf" in ctype:
            candidate_resources[final_url] = (category_for_url(final_url), depth, source_page)
            continue

        if "text/html" not in ctype:
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = (a.get("href") or "").strip()
            if not href:
                continue
            link = urljoin(final_url, href)
            if should_skip_url(link):
                continue
            if not link.startswith("http"):
                continue
            if not host_allowed(link):
                continue
            text = a.get_text(" ", strip=True)

            if should_consider_resource(link, text):
                if link not in candidate_resources:
                    candidate_resources[link] = (category_for_url(link + " " + text), depth + 1, final_url)

            if should_crawl_html(link, text, allowed_hosts, depth, max_depth):
                queue.append((link, depth + 1, final_url))

        if delay_s > 0:
            time.sleep(delay_s)

    harvested: List[HarvestedItem] = []
    failed: List[Dict[str, str]] = []
    seen_local = set()
    idx = 1
    for url, (category, depth, source_page) in list(candidate_resources.items())[:max_items]:
        out_pdf = enrich_dir / f"enrich_{idx:04d}.pdf"
        ok, kind_or_err = to_pdf(session, url, out_pdf, timeout_s=timeout_s, retries=retries)
        if ok:
            rel = out_pdf.relative_to(out_dir)
            if str(rel) in seen_local:
                continue
            seen_local.add(str(rel))
            harvested.append(
                HarvestedItem(
                    url=url,
                    category=category,
                    kind=kind_or_err,
                    local_pdf=str(rel),
                    source_page=source_page,
                    depth=depth,
                )
            )
            idx += 1
        else:
            failed.append({"url": url, "error": kind_or_err, "source_page": source_page})
        if delay_s > 0:
            time.sleep(delay_s)

    return {
        "class_name": class_name,
        "class_slug": slug,
        "seeds": seeds,
        "crawled_pages": len(seen_pages),
        "candidate_resources": len(candidate_resources),
        "harvested": [h.__dict__ for h in harvested],
        "failed": failed,
    }


def run(
    out_dir: Path,
    classes_filter: List[str] | None,
    max_depth: int,
    max_pages: int,
    max_items: int,
    timeout_s: int,
    retries: int,
    delay_s: float,
) -> None:
    out_dir = out_dir.resolve()
    session = make_session()
    classes = []
    seen_classes = set()
    for _, group in TOPIC_ORDER:
        for cls in group:
            if cls in seen_classes:
                continue
            seen_classes.add(cls)
            classes.append(cls)
    existing_manifest_path = out_dir / "enriched_manifest.json"
    if existing_manifest_path.exists():
        try:
            existing_manifest: Dict[str, object] = json.loads(existing_manifest_path.read_text(encoding="utf-8"))
        except Exception:
            existing_manifest = {}
    else:
        existing_manifest = {}

    if classes_filter:
        wanted = {c.strip().upper() for c in classes_filter if c.strip()}
        classes = [c for c in classes if c.upper() in wanted]
        if not classes:
            raise RuntimeError(f"No classes matched --classes filter: {classes_filter}")

    global_manifest: Dict[str, object] = dict(existing_manifest)
    for class_name in classes:
        print(f"[class] {class_name}")
        data = crawl_and_harvest(
            session=session,
            class_name=class_name,
            out_dir=out_dir,
            max_depth=max_depth,
            max_pages=max_pages,
            max_items=max_items,
            timeout_s=timeout_s,
            retries=retries,
            delay_s=delay_s,
        )
        global_manifest[class_name] = data
        print(
            f"  crawled={data.get('crawled_pages', 0)} "
            f"candidates={data.get('candidate_resources', 0)} "
            f"harvested={len(data.get('harvested', []))} "
            f"failed={len(data.get('failed', []))}"
        )

    out = out_dir / "enriched_manifest.json"
    out.write_text(json.dumps(global_manifest, indent=2), encoding="utf-8")
    print(f"Wrote: {out}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir", type=Path, default=Path("data/assignment_pdf_bundles"))
    p.add_argument("--max-depth", type=int, default=2)
    p.add_argument("--max-pages", type=int, default=120)
    p.add_argument("--max-items", type=int, default=240)
    p.add_argument("--timeout-s", type=int, default=25)
    p.add_argument("--retries", type=int, default=4)
    p.add_argument("--delay-s", type=float, default=0.05)
    p.add_argument(
        "--classes",
        nargs="*",
        default=None,
        help="Optional class filter, e.g. --classes 'MATH 54' 'CS 70'",
    )
    args = p.parse_args()
    run(
        out_dir=args.out_dir,
        classes_filter=args.classes,
        max_depth=args.max_depth,
        max_pages=args.max_pages,
        max_items=args.max_items,
        timeout_s=args.timeout_s,
        retries=args.retries,
        delay_s=args.delay_s,
    )


if __name__ == "__main__":
    main()
