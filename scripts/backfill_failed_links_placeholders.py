#!/usr/bin/env python3
"""
Recover failed scraped links into PDF artifacts so every discovered link is
represented in class bundles and the master bundle.

Recovery strategy:
- Download direct PDFs as-is.
- Render HTML/text/script/csv/tex resources to text PDFs.
- Render image resources to image PDFs.
- Render ZIP resources to a summary PDF (with archive listing + previews).
- Fall back to a placeholder PDF if conversion is not possible.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import textwrap
import time
import zipfile
from pathlib import Path
from typing import List
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

PDF_EXTENSIONS = (".pdf",)
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp")
TEXT_EXTENSIONS = (
    ".txt",
    ".tex",
    ".sty",
    ".cls",
    ".bib",
    ".m",
    ".py",
    ".r",
    ".jl",
    ".csv",
    ".tsv",
    ".md",
    ".rst",
    ".json",
    ".yaml",
    ".yml",
    ".xml",
    ".html",
    ".htm",
)


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
            return session.get(url, timeout=timeout_s, allow_redirects=True)
        except requests.RequestException as exc:
            last_err = exc
            time.sleep(0.4 * (attempt + 1))
    raise RuntimeError(f"Failed to fetch {url}: {last_err}")


def looks_like_pdf(url: str, content_type: str) -> bool:
    lower = url.lower()
    return lower.endswith(PDF_EXTENSIONS) or "application/pdf" in content_type.lower()


def looks_like_image(url: str, content_type: str) -> bool:
    lower = url.lower()
    return lower.endswith(IMAGE_EXTENSIONS) or content_type.lower().startswith("image/")


def looks_like_zip(url: str, content_type: str) -> bool:
    lower = url.lower()
    c = content_type.lower()
    return lower.endswith(".zip") or "application/zip" in c or "application/x-zip-compressed" in c


def decode_text_bytes(data: bytes) -> str:
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def is_valid_pdf_file(path: Path) -> bool:
    if not path.exists() or path.stat().st_size == 0:
        return False
    try:
        with path.open("rb") as f:
            head = f.read(5)
        return head == b"%PDF-"
    except Exception:
        return False


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.extract()
    text = soup.get_text("\n", strip=True)
    return re.sub(r"\n{3,}", "\n\n", text)


def write_lines_pdf(out_pdf: Path, lines: List[str], title: str = "") -> None:
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(out_pdf), pagesize=letter)
    width, height = letter
    x = 44
    y = height - 44
    line_h = 12
    max_chars = 105

    if title:
        lines = [f"Source: {title}", ""] + lines

    for raw in lines:
        wrapped = textwrap.wrap(raw, width=max_chars) if raw else [""]
        for line in wrapped:
            if y < 44:
                c.showPage()
                y = height - 44
            c.drawString(x, y, line[:max_chars])
            y -= line_h

    c.save()


def write_text_pdf(out_pdf: Path, title: str, body_text: str) -> None:
    lines = body_text.splitlines()
    write_lines_pdf(out_pdf, lines=lines, title=title)


def write_image_pdf(out_pdf: Path, title: str, image_bytes: bytes) -> None:
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(out_pdf), pagesize=letter)
    width, height = letter
    left, bottom = 44, 80
    draw_w, draw_h = width - 88, height - 140
    c.setFont("Helvetica", 10)
    c.drawString(44, height - 28, f"Source: {title}"[:140])
    img = ImageReader(io.BytesIO(image_bytes))
    c.drawImage(img, left, bottom, width=draw_w, height=draw_h, preserveAspectRatio=True, anchor="c")
    c.save()


def write_zip_summary_pdf(out_pdf: Path, title: str, zip_bytes: bytes) -> None:
    lines: List[str] = ["ZIP archive summary", ""]
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        infos = zf.infolist()
        lines.append(f"Archive entries: {len(infos)}")
        lines.append("")
        for info in infos[:400]:
            lines.append(f"- {info.filename} ({info.file_size} bytes)")

        lines.append("")
        lines.append("Preview of text-like files:")
        previewed = 0
        for info in infos:
            if previewed >= 12:
                break
            name = info.filename.lower()
            if info.is_dir():
                continue
            if not name.endswith(TEXT_EXTENSIONS):
                continue
            if info.file_size > 250_000:
                continue
            try:
                data = zf.read(info.filename)
                text = decode_text_bytes(data)
                lines.append("")
                lines.append(f"=== {info.filename} ===")
                for ln in text.splitlines()[:40]:
                    lines.append(ln)
                previewed += 1
            except Exception:
                continue

    write_lines_pdf(out_pdf, lines=lines, title=title)


def convert_to_pdf(
    session: requests.Session,
    url: str,
    out_pdf: Path,
    timeout_s: int,
    retries: int,
) -> tuple[bool, str]:
    try:
        resp = fetch(session, url, timeout_s=timeout_s, retries=retries)
    except Exception as exc:
        return False, f"fetch_failed: {exc}"

    content_type = resp.headers.get("Content-Type", "")
    final_url = resp.url
    lower_path = urlparse(final_url).path.lower()

    if looks_like_pdf(final_url, content_type):
        data = resp.content or b""
        if data.startswith(b"%PDF-"):
            out_pdf.parent.mkdir(parents=True, exist_ok=True)
            out_pdf.write_bytes(data)
            return True, "downloaded_pdf"
        # Some servers incorrectly label HTML as PDF; recover into text PDF.
        text = decode_text_bytes(data)
        if "<html" in text.lower() or "<!doctype" in text.lower() or text.strip():
            if "<html" in text.lower() or "<!doctype" in text.lower():
                text = html_to_text(text)
            write_text_pdf(out_pdf, title=final_url, body_text=text)
            return True, "rendered_text_from_invalid_pdf"
        return False, "invalid_pdf_payload"

    if looks_like_image(final_url, content_type):
        try:
            write_image_pdf(out_pdf, title=final_url, image_bytes=resp.content)
            return True, "rendered_image"
        except Exception as exc:
            return False, f"image_render_failed:{exc}"

    if looks_like_zip(final_url, content_type):
        try:
            write_zip_summary_pdf(out_pdf, title=final_url, zip_bytes=resp.content)
            return True, "rendered_zip_summary"
        except Exception as exc:
            return False, f"zip_render_failed:{exc}"

    lower_ct = content_type.lower()
    is_html = "text/html" in lower_ct or lower_path.endswith((".html", ".htm"))
    is_text = (
        lower_path.endswith(TEXT_EXTENSIONS)
        or lower_ct.startswith("text/")
        or "application/x-tex" in lower_ct
        or "application/matlab" in lower_ct
        or "application/postscript" in lower_ct
        or "application/json" in lower_ct
        or "application/xml" in lower_ct
        or "application/octet-stream" in lower_ct
        or lower_path.endswith(".ps")
    )
    if is_html:
        text = html_to_text(resp.text)
        if not text.strip():
            return False, "empty_html_text"
        write_text_pdf(out_pdf, title=final_url, body_text=text)
        return True, "rendered_html"

    if is_text:
        text = decode_text_bytes(resp.content)
        if not text.strip():
            return False, "empty_text"
        write_text_pdf(out_pdf, title=final_url, body_text=text)
        return True, "rendered_text"

    return False, f"unsupported_content_type:{content_type}"


def write_placeholder_pdf(out_pdf: Path, class_name: str, source_url: str, url: str, error: str) -> None:
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(out_pdf), pagesize=letter)
    width, height = letter
    y = height - 48
    lines = [
        "Assignment Artifact Placeholder",
        "",
        f"Class: {class_name}",
        f"Source URL: {source_url}",
        f"Artifact URL: {url}",
        f"Reason: {error}",
        "",
        "This link was discovered during scraping but could not be converted",
        "to a valid PDF artifact automatically.",
    ]
    for line in lines:
        c.drawString(44, y, line[:140])
        y -= 16
    c.save()


def merge_pdfs(pdf_paths: List[Path], out_pdf: Path) -> None:
    writer = PdfWriter()
    for p in pdf_paths:
        try:
            reader = PdfReader(str(p))
            for page in reader.pages:
                writer.add_page(page)
        except Exception:
            continue
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    with out_pdf.open("wb") as f:
        writer.write(f)


def run(out_dir: Path, timeout_s: int, retries: int, delay_s: float) -> None:
    class_dirs = [p for p in out_dir.iterdir() if p.is_dir()]
    class_bundles: List[Path] = []
    session = make_session()
    global_manifest = {}

    for class_dir in sorted(class_dirs):
        manifest_path = class_dir / "manifest.json"
        if not manifest_path.exists():
            continue
        manifest = json.loads(manifest_path.read_text())
        class_name = manifest.get("class_name", class_dir.name)
        raw_dir = class_dir / "raw_pdfs"
        raw_dir.mkdir(parents=True, exist_ok=True)

        # Clear stale backfill artifacts so reruns are deterministic.
        for stale in raw_dir.glob("zz_failed_*.pdf"):
            stale.unlink(missing_ok=True)

        placeholder_count = 0
        recovered_count = 0
        conversion_failed_count = 0
        for source in manifest.get("sources", []):
            source_url = source.get("source_url", "")
            for result in source.get("results", []):
                existing_ok = result.get("status") == "ok"
                existing_local_pdf = result.get("local_pdf")
                invalid_ok_artifact = False
                if existing_ok and existing_local_pdf:
                    p = Path(existing_local_pdf)
                    if not p.is_absolute():
                        p = Path.cwd() / p
                    invalid_ok_artifact = not is_valid_pdf_file(p)

                # Recover both explicit failures and invalid/empty "ok" artifacts.
                if existing_ok and not invalid_ok_artifact:
                    continue
                failed_url = result.get("url", "")
                prior_error = result.get("error", "invalid_ok_artifact" if invalid_ok_artifact else "unknown_error")
                failed_idx = recovered_count + placeholder_count + conversion_failed_count + 1
                failed_pdf = raw_dir / f"zz_failed_{failed_idx:04d}.pdf"

                ok, kind_or_err = convert_to_pdf(
                    session=session,
                    url=failed_url,
                    out_pdf=failed_pdf,
                    timeout_s=timeout_s,
                    retries=retries,
                )
                if ok:
                    recovered_count += 1
                    result["status"] = "ok"
                    result["kind"] = kind_or_err
                    result["local_pdf"] = str(failed_pdf)
                    result["recovered_from_error"] = prior_error
                    result.pop("error", None)
                else:
                    conversion_failed_count += 1
                    placeholder_count += 1
                    write_placeholder_pdf(
                        out_pdf=failed_pdf,
                        class_name=class_name,
                        source_url=source_url,
                        url=failed_url,
                        error=kind_or_err,
                    )
                    result["status"] = "ok"
                    result["kind"] = "placeholder"
                    result["local_pdf"] = str(failed_pdf)
                    result["recovered_from_error"] = prior_error
                    result["error"] = kind_or_err

                if delay_s > 0:
                    time.sleep(delay_s)

        artifacts = []
        for source in manifest.get("sources", []):
            source_url = source.get("source_url", "")
            for result in source.get("results", []):
                if result.get("status") != "ok":
                    continue
                local_pdf_str = result.get("local_pdf")
                if not local_pdf_str:
                    continue
                local_pdf = Path(local_pdf_str)
                if not local_pdf.is_absolute():
                    local_pdf = Path.cwd() / local_pdf
                if not is_valid_pdf_file(local_pdf):
                    continue
                artifacts.append(
                    {
                        "url": result.get("url", ""),
                        "local_pdf": str(local_pdf),
                        "source_url": source_url,
                        "kind": result.get("kind", "unknown"),
                    }
                )

        artifact_paths = [Path(a["local_pdf"]) for a in artifacts]
        class_bundle = class_dir / f"{class_dir.name}_bundle.pdf"
        merge_pdfs(artifact_paths, class_bundle)
        class_bundles.append(class_bundle)

        manifest["artifacts"] = artifacts
        manifest["artifact_count"] = len(artifacts)
        manifest["placeholder_count"] = placeholder_count
        manifest["recovered_count"] = recovered_count
        manifest["conversion_failed_count"] = conversion_failed_count
        manifest["bundle_pdf"] = str(class_bundle)
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        global_manifest[class_name] = manifest
        print(
            f"[class] {class_name}: recovered={recovered_count}, "
            f"placeholders={placeholder_count}, artifacts={len(artifacts)}"
        )

    master_bundle = out_dir / "all_classes_bundle.pdf"
    merge_pdfs(sorted(class_bundles), master_bundle)
    (out_dir / "manifest.json").write_text(json.dumps(global_manifest, indent=2), encoding="utf-8")
    print(f"Wrote master bundle: {master_bundle}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--out-dir",
        type=Path,
        default=Path("data/assignment_pdf_bundles"),
        help="Bundle output directory produced by scrape_assignments_to_pdfs.py",
    )
    p.add_argument("--timeout-s", type=int, default=30, help="HTTP timeout in seconds.")
    p.add_argument("--retries", type=int, default=4, help="HTTP retries per URL.")
    p.add_argument("--delay-s", type=float, default=0.05, help="Delay between requests.")
    args = p.parse_args()
    run(args.out_dir, timeout_s=args.timeout_s, retries=args.retries, delay_s=args.delay_s)


if __name__ == "__main__":
    main()
