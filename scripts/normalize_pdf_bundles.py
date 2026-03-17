#!/usr/bin/env python3
"""
Normalize generated assignment PDF bundles to improve rendering consistency.

This script rewrites each class bundle with Ghostscript, rebuilds the master
bundle from normalized class bundles, and then normalizes the master as well.
"""

from __future__ import annotations

import argparse
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from pypdf import PdfReader, PdfWriter


@dataclass
class NormalizeResult:
    path: Path
    before_size: int
    after_size: int
    ok: bool
    error: str = ""


def find_gs() -> str:
    for candidate in ("/opt/homebrew/bin/gs", "gs"):
        try:
            proc = subprocess.run(
                [candidate, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                text=True,
            )
            if proc.returncode == 0:
                return candidate
        except FileNotFoundError:
            continue
    raise RuntimeError("Ghostscript executable not found (expected /opt/homebrew/bin/gs or gs)")


def has_pdf_signature(path: Path) -> bool:
    if not path.exists() or path.stat().st_size == 0:
        return False
    try:
        with path.open("rb") as f:
            return f.read(5) == b"%PDF-"
    except Exception:
        return False


def run_pdfinfo(path: Path) -> bool:
    for candidate in ("/opt/homebrew/bin/pdfinfo", "pdfinfo"):
        try:
            proc = subprocess.run(
                [candidate, str(path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                text=True,
            )
            if proc.returncode == 0:
                return True
        except FileNotFoundError:
            continue
    # If pdfinfo is unavailable, fallback to signature check.
    return has_pdf_signature(path)


def normalize_with_gs(gs_bin: str, in_pdf: Path, out_pdf: Path) -> None:
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.setdefault("XDG_CACHE_HOME", "/tmp/.cache")
    env.setdefault("HOME", str(Path.cwd()))
    cmd = [
        gs_bin,
        "-q",
        "-dNOPAUSE",
        "-dBATCH",
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.6",
        "-dDetectDuplicateImages=true",
        "-dCompressFonts=true",
        "-dSubsetFonts=true",
        "-dEmbedAllFonts=true",
        "-dAutoRotatePages=/None",
        f"-sOutputFile={out_pdf}",
        str(in_pdf),
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "ghostscript failed")


def merge_pdfs(input_pdfs: Iterable[Path], out_pdf: Path) -> None:
    writer = PdfWriter()
    for pdf_path in input_pdfs:
        try:
            reader = PdfReader(str(pdf_path), strict=False)
            for page in reader.pages:
                writer.add_page(page)
        except Exception:
            continue
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    with out_pdf.open("wb") as f:
        writer.write(f)


def normalize_file(gs_bin: str, pdf_path: Path) -> NormalizeResult:
    before = pdf_path.stat().st_size if pdf_path.exists() else 0
    tmp = pdf_path.with_suffix(pdf_path.suffix + ".gs_tmp")
    try:
        normalize_with_gs(gs_bin, pdf_path, tmp)
        if not has_pdf_signature(tmp) or not run_pdfinfo(tmp):
            raise RuntimeError("normalized output failed validation")
        tmp.replace(pdf_path)
        after = pdf_path.stat().st_size
        return NormalizeResult(path=pdf_path, before_size=before, after_size=after, ok=True)
    except Exception as exc:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        return NormalizeResult(path=pdf_path, before_size=before, after_size=before, ok=False, error=str(exc))


def build_report(results: List[NormalizeResult], master_result: NormalizeResult, out_path: Path) -> None:
    ok_count = sum(1 for r in results if r.ok) + (1 if master_result.ok else 0)
    total_count = len(results) + 1
    lines = [
        "# Rendering Normalization Report",
        "",
        f"- Bundles processed: {len(results)} class bundles + 1 master bundle",
        f"- Successes: {ok_count}/{total_count}",
        "",
        "## Class Bundles",
        "",
        "| Bundle | Status | Before (bytes) | After (bytes) | Error |",
        "|---|---|---:|---:|---|",
    ]
    for r in results:
        status = "ok" if r.ok else "failed"
        err = "" if r.ok else r.error.replace("|", "/")
        lines.append(f"| {r.path} | {status} | {r.before_size} | {r.after_size} | {err} |")
    lines.extend(
        [
            "",
            "## Master Bundle",
            "",
            "| Bundle | Status | Before (bytes) | After (bytes) | Error |",
            "|---|---|---:|---:|---|",
            f"| {master_result.path} | {'ok' if master_result.ok else 'failed'} | "
            f"{master_result.before_size} | {master_result.after_size} | "
            f"{'' if master_result.ok else master_result.error.replace('|', '/')} |",
            "",
        ]
    )
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(out_dir: Path) -> None:
    gs_bin = find_gs()
    class_bundles = sorted(out_dir.glob("*/*_bundle.pdf"))
    if not class_bundles:
        raise RuntimeError(f"No class bundles found under {out_dir}")

    class_results: List[NormalizeResult] = []
    for idx, bundle in enumerate(class_bundles, start=1):
        print(f"[{idx}/{len(class_bundles)}] normalize class bundle: {bundle}")
        class_results.append(normalize_file(gs_bin, bundle))

    master = out_dir / "all_classes_bundle.pdf"
    print(f"[merge] rebuilding master from {len(class_bundles)} normalized class bundles")
    merge_pdfs(class_bundles, master)

    print("[master] normalizing master bundle")
    master_result = normalize_file(gs_bin, master)

    report = out_dir / "rendering_fix_report.md"
    build_report(class_results, master_result, report)
    print(f"Wrote normalization report: {report}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--out-dir",
        type=Path,
        default=Path("data/assignment_pdf_bundles"),
        help="Bundle output directory.",
    )
    args = p.parse_args()
    run(args.out_dir)


if __name__ == "__main__":
    main()

