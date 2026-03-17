#!/usr/bin/env python3
"""
Build a single giant LaTeX-compiled PDF from all class bundle PDFs.

Output files (by default):
- data/assignment_pdf_bundles/mega_problem_book.tex
- data/assignment_pdf_bundles/mega_problem_book.pdf
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import List


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


def build_tex_content(out_dir: Path, class_names: List[str]) -> str:
    lines = [
        r"\documentclass[11pt]{article}",
        r"\usepackage[margin=1in]{geometry}",
        r"\usepackage[T1]{fontenc}",
        r"\usepackage[utf8]{inputenc}",
        r"\usepackage{lmodern}",
        r"\usepackage{hyperref}",
        r"\usepackage{pdfpages}",
        r"\hypersetup{colorlinks=true,linkcolor=blue,urlcolor=blue}",
        r"\title{Mega Problem Set Book}",
        r"\date{}",
        r"\begin{document}",
        r"\maketitle",
        r"\tableofcontents",
        r"\clearpage",
    ]

    for class_name in class_names:
        class_slug = class_name.lower()
        class_slug = "".join(ch if ch.isalnum() else "_" for ch in class_slug)
        while "__" in class_slug:
            class_slug = class_slug.replace("__", "_")
        class_slug = class_slug.strip("_")
        rel_pdf = Path(class_slug) / f"{class_slug}_bundle.pdf"
        lines.append(rf"\section*{{{tex_escape(class_name)}}}")
        lines.append(rf"\addcontentsline{{toc}}{{section}}{{{tex_escape(class_name)}}}")
        lines.append(rf"\includepdf[pages=-,pagecommand={{}}]{{\detokenize{{{str(rel_pdf)}}}}}")
        lines.append("")

    lines.append(r"\end{document}")
    return "\n".join(lines) + "\n"


def run_latexmk(tex_path: Path, workdir: Path) -> None:
    cmd = [
        "/Library/TeX/texbin/latexmk",
        "-pdf",
        "-interaction=nonstopmode",
        "-halt-on-error",
        tex_path.name,
    ]
    env = os.environ.copy()
    env["LC_ALL"] = "en_US.UTF-8"
    env["LANG"] = "en_US.UTF-8"
    env["LC_CTYPE"] = "en_US.UTF-8"
    proc = subprocess.run(
        cmd,
        cwd=workdir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            "latexmk failed.\n"
            f"stdout:\n{proc.stdout[-4000:]}\n\n"
            f"stderr:\n{proc.stderr[-4000:]}"
        )


def run(out_dir: Path) -> None:
    manifest_path = out_dir / "manifest.json"
    if not manifest_path.exists():
        raise RuntimeError(f"Missing manifest: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    class_names = sorted(manifest.keys())
    if not class_names:
        raise RuntimeError("No classes found in manifest.")

    for class_name in class_names:
        class_slug = class_name.lower()
        class_slug = "".join(ch if ch.isalnum() else "_" for ch in class_slug)
        while "__" in class_slug:
            class_slug = class_slug.replace("__", "_")
        class_slug = class_slug.strip("_")
        class_pdf = out_dir / class_slug / f"{class_slug}_bundle.pdf"
        if not class_pdf.exists() or class_pdf.stat().st_size == 0:
            raise RuntimeError(f"Missing/empty class bundle: {class_pdf}")

    tex_path = out_dir / "mega_problem_book.tex"
    tex_path.write_text(build_tex_content(out_dir, class_names), encoding="utf-8")
    run_latexmk(tex_path=tex_path, workdir=out_dir)

    pdf_path = out_dir / "mega_problem_book.pdf"
    if not pdf_path.exists() or pdf_path.stat().st_size == 0:
        raise RuntimeError(f"Expected output PDF not produced: {pdf_path}")
    print(f"Wrote LaTeX mega PDF: {pdf_path}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--out-dir",
        type=Path,
        default=Path("data/assignment_pdf_bundles"),
        help="Directory containing class bundle PDFs and manifest.json",
    )
    args = p.parse_args()
    run(args.out_dir)


if __name__ == "__main__":
    main()
