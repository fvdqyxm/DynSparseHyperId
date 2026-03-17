#!/usr/bin/env python3
"""
Build a PDF guide for topic-organized problem bundles.

Outputs:
- data/assignment_pdf_bundles/topic_problem_bundles/topic_problem_guide.tex
- data/assignment_pdf_bundles/topic_problem_bundles/topic_problem_guide.pdf
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List


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


def load_json(path: Path) -> Dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def compile_tex(out_dir: Path, tex_path: Path) -> Path:
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
    proc = subprocess.run(cmd, cwd=out_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    if proc.returncode != 0:
        raise RuntimeError(
            "latexmk failed.\n"
            f"stdout_tail:\n{proc.stdout[-3000:]}\n\n"
            f"stderr_tail:\n{proc.stderr[-3000:]}"
        )
    return out_dir / "topic_problem_guide.pdf"


def run(out_dir: Path, max_per_topic: int) -> None:
    out_dir = out_dir.resolve()
    topic_dir = out_dir / "topic_problem_bundles"
    idx = load_json(topic_dir / "topic_problem_index.json")
    matrix = load_json(topic_dir / "class_topic_matrix.json")
    topics = idx.get("topics", [])
    if not isinstance(topics, list) or not topics:
        raise RuntimeError("Missing topic_problem_index.json or topics list.")

    lines: List[str] = [
        r"\documentclass[11pt]{book}",
        r"\usepackage[margin=1in]{geometry}",
        r"\usepackage[T1]{fontenc}",
        r"\usepackage[utf8]{inputenc}",
        r"\usepackage{lmodern}",
        r"\usepackage{microtype}",
        r"\usepackage[dvipsnames,table]{xcolor}",
        r"\usepackage{hyperref}",
        r"\usepackage{xurl}",
        r"\usepackage{longtable}",
        r"\usepackage{booktabs}",
        r"\hypersetup{colorlinks=true,linkcolor=MidnightBlue,urlcolor=MidnightBlue}",
        r"\title{Topic-Organized Problem Guide}",
        r"\author{OR + Applied Math Bible Companion}",
        r"\date{}",
        r"\begin{document}",
        r"\maketitle",
        r"\tableofcontents",
        r"\chapter*{Overview}",
        r"\addcontentsline{toc}{chapter}{Overview}",
        rf"Total problem-like resources indexed: {idx.get('total_problemish_resources', 0)}\\",
        rf"Total topics: {idx.get('topic_count', 0)}\\",
        r"This guide organizes problems by topic keywords found in resource URLs and first-page content.",
        r"\chapter*{Topic Map}",
        r"\addcontentsline{toc}{chapter}{Topic Map}",
        r"\begin{longtable}{p{0.70\textwidth}p{0.20\textwidth}}",
        r"\toprule",
        r"Topic & Resources \\",
        r"\midrule",
        r"\endfirsthead",
        r"\toprule",
        r"Topic & Resources \\",
        r"\midrule",
        r"\endhead",
    ]
    for row in topics:
        topic = str(row.get("topic", ""))
        count = int(row.get("resource_count", 0))
        lines.append(rf"{tex_escape(topic)} & {count} \\")
    lines.extend([r"\bottomrule", r"\end{longtable}"])

    matrix_topics = matrix.get("topics", []) if isinstance(matrix, dict) else []
    matrix_classes = matrix.get("classes", {}) if isinstance(matrix, dict) else {}
    if isinstance(matrix_topics, list) and isinstance(matrix_classes, dict) and matrix_topics and matrix_classes:
        lines.extend(
            [
                r"\chapter*{Class-Topic Coverage Matrix}",
                r"\addcontentsline{toc}{chapter}{Class-Topic Coverage Matrix}",
                r"Counts of problem-like resources assigned to each topic per class.",
                r"\begin{longtable}{p{0.22\textwidth}p{0.72\textwidth}}",
                r"\toprule",
                r"Class & Topic Counts \\",
                r"\midrule",
                r"\endfirsthead",
                r"\toprule",
                r"Class & Topic Counts \\",
                r"\midrule",
                r"\endhead",
            ]
        )
        for cls, topic_counts in matrix_classes.items():
            if not isinstance(topic_counts, dict):
                continue
            chunks = []
            for topic in matrix_topics:
                count = int(topic_counts.get(topic, 0))
                if count > 0:
                    chunks.append(f"{topic}: {count}")
            if not chunks:
                chunks = ["(no assigned problem resources)"]
            lines.append(rf"{tex_escape(str(cls))} & {tex_escape('; '.join(chunks))} \\")
        lines.extend([r"\bottomrule", r"\end{longtable}"])

    for row in topics:
        topic = str(row.get("topic", ""))
        slug = str(row.get("topic_slug", ""))
        manifest = load_json(topic_dir / slug / "manifest.json")
        resources = manifest.get("resources", [])
        if not isinstance(resources, list):
            continue
        lines.extend(
            [
                rf"\chapter*{{{tex_escape(topic)}}}",
                rf"\addcontentsline{{toc}}{{chapter}}{{{tex_escape(topic)}}}",
                rf"\noindent\textbf{{Total resources in topic:}} {len(resources)}",
                rf"\noindent\textbf{{Linked PDFs folder: }}\texttt{{\detokenize{{topic_problem_bundles/{slug}/pdf_links}}}}",
                r"\begin{longtable}{p{0.05\textwidth}p{0.13\textwidth}p{0.12\textwidth}p{0.63\textwidth}}",
                r"\toprule",
                r"\# & Class & Type & URL \\",
                r"\midrule",
                r"\endfirsthead",
                r"\toprule",
                r"\# & Class & Type & URL \\",
                r"\midrule",
                r"\endhead",
            ]
        )
        for i, r in enumerate(resources[:max_per_topic], start=1):
            cls = tex_escape(str(r.get("class", "")))
            cat = tex_escape(str(r.get("category", "")))
            url = str(r.get("url", ""))
            lines.append(rf"{i} & {cls} & {cat} & \url{{{url}}} \\")
        lines.extend([r"\bottomrule", r"\end{longtable}"])
        if len(resources) > max_per_topic:
            lines.append(
                rf"\noindent\textit{{Showing first {max_per_topic} resources. Full list is in }}"
                + rf"\texttt{{\detokenize{{topic_problem_bundles/{slug}/manifest.json}}}}."
            )

    lines.append(r"\end{document}")
    tex_path = topic_dir / "topic_problem_guide.tex"
    tex_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    pdf_path = compile_tex(topic_dir, tex_path)
    print(f"Wrote topic guide TeX: {tex_path}")
    print(f"Wrote topic guide PDF: {pdf_path}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir", type=Path, default=Path("data/assignment_pdf_bundles"))
    p.add_argument("--max-per-topic", type=int, default=120)
    args = p.parse_args()
    run(args.out_dir, max_per_topic=args.max_per_topic)


if __name__ == "__main__":
    main()
