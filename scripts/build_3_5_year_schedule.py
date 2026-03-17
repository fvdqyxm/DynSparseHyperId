#!/usr/bin/env python3
"""
Build a 3.5-year (42-month) study schedule for the OR + Applied Math Bible.

Outputs:
- data/assignment_pdf_bundles/or_applied_math_bible_3_5_year_schedule.tex
- data/assignment_pdf_bundles/or_applied_math_bible_3_5_year_schedule.pdf
- data/assignment_pdf_bundles/or_applied_math_bible_3_5_year_schedule.json
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List


PHASES = [
    {
        "name": "Phase I: Foundations (Proofs, Optimization, Linear Algebra, Computing)",
        "months": list(range(1, 13)),
        "classes": [
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
            "MATH 220",
            "STAT 150",
        ],
    },
    {
        "name": "Phase II: Core OR + Stochastic and Statistical Theory",
        "months": list(range(13, 25)),
        "classes": [
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
            "IEOR 221",
            "IEOR 222",
            "IEOR 180",
            "IEOR 269",
        ],
    },
    {
        "name": "Phase III: Advanced Pure Math + High-Dimensional Frontier",
        "months": list(range(25, 35)),
        "classes": [
            "MATH 185",
            "MATH 202A",
            "MATH 202B",
            "MATH 113",
            "MATH 142",
            "MATH 142B",
            "STAT 260",
            "CS 189",
        ],
    },
]

REVIEW_MONTHS = {
    35: "Integration Sprint I: Deterministic Optimization + Convexity",
    36: "Integration Sprint II: Integer/Combinatorial + Network Optimization",
    37: "Integration Sprint III: Stochastic Processes + Measure/Analysis",
    38: "Integration Sprint IV: Financial Engineering + Dynamic Models",
    39: "Integration Sprint V: Statistical Inference + High-Dimensional Methods",
    40: "Integration Sprint VI: Algorithms + Learning Theory + Computation",
    41: "Capstone Month I: Comprehensive Mock Quals + Oral Explanations",
    42: "Capstone Month II: Research-Style Problem Portfolio + Final Review",
}


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


def month_label(month_index: int) -> str:
    year = (month_index - 1) // 12 + 1
    month_of_year = ((month_index - 1) % 12) + 1
    return f"Y{year}-M{month_of_year:02d}"


def build_part_units(classes: List[str], class_parts: Dict[str, int]) -> List[Dict[str, object]]:
    units: List[Dict[str, object]] = []
    for c in classes:
        total = class_parts.get(c, 0)
        for k in range(1, total + 1):
            units.append({"class": c, "part": k, "total_parts": total})
    return units


def build_schedule(class_parts: Dict[str, int]) -> List[Dict[str, object]]:
    schedule: List[Dict[str, object]] = []
    for phase in PHASES:
        units = build_part_units(phase["classes"], class_parts)
        months = phase["months"]
        n_units = len(units)
        n_months = len(months)
        base = n_units // n_months
        rem = n_units % n_months
        quotas = [base + (1 if i < rem else 0) for i in range(n_months)]

        cursor = 0
        for m, quota in zip(months, quotas):
            block = units[cursor : cursor + quota]
            cursor += quota
            schedule.append(
                {
                    "month_index": m,
                    "month_label": month_label(m),
                    "phase": phase["name"],
                    "mode": "core",
                    "units": block,
                    "hours_target": "60-80h" if quota >= 3 else ("45-60h" if quota == 2 else "25-35h"),
                    "deliverables": [
                        "Derive and summarize key lecture results.",
                        "Complete core problem-set block.",
                        "Write one-page synthesis + unresolved questions.",
                    ],
                }
            )
        if cursor != n_units:
            raise RuntimeError(f"Scheduling bug in phase {phase['name']}: not all class-parts allocated.")

    for m in range(35, 43):
        schedule.append(
            {
                "month_index": m,
                "month_label": month_label(m),
                "phase": "Phase IV: Integration and Capstone",
                "mode": "review",
                "review_focus": REVIEW_MONTHS[m],
                "hours_target": "30-45h",
                "deliverables": [
                    "Comprehensive problem marathon and timed sets.",
                    "Cross-topic concept map updates.",
                    "Oral explanation drill (teach-back style).",
                ],
            }
        )

    return schedule


def write_schedule_json(out_dir: Path, schedule: List[Dict[str, object]]) -> Path:
    out = out_dir / "or_applied_math_bible_3_5_year_schedule.json"
    out.write_text(json.dumps(schedule, indent=2), encoding="utf-8")
    return out


def write_schedule_tex(
    out_dir: Path,
    schedule: List[Dict[str, object]],
    class_summary: Dict[str, Dict[str, int]],
    total_parts: int,
) -> Path:
    tex = out_dir / "or_applied_math_bible_3_5_year_schedule.tex"
    lines: List[str] = [
        r"\documentclass[11pt]{article}",
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
        r"\usepackage{enumitem}",
        r"\usepackage[most]{tcolorbox}",
        r"\hypersetup{colorlinks=true,linkcolor=MidnightBlue,urlcolor=MidnightBlue}",
        r"\setlength{\parskip}{0.35em}",
        r"\title{3.5-Year Schedule: OR and Applied Mathematics Bible}",
        r"\author{Study Plan Edition}",
        r"\date{}",
        r"\begin{document}",
        r"\maketitle",
        r"\begin{tcolorbox}[colback=blue!4,colframe=MidnightBlue,title=Mission]",
        r"This schedule is designed so that a steady long-run effort yields deep OR + applied math mastery.",
        r"It maps directly to the class-part structure from the compiled Bible.",
        r"\end{tcolorbox}",
        r"\section*{Structure}",
        r"\begin{itemize}[leftmargin=1.2em]",
        r"\item Horizon: 42 months (3.5 years).",
        rf"\item Core execution window: Months 1--34 (all {total_parts} class-parts).",
        r"\item Integration and capstone window: Months 35--42.",
        r"\item Recommended weekly rhythm (8--12 hrs/week):",
        r"Week 1 = lecture theory extraction; Week 2 = foundational problems; Week 3 = advanced problems/proofs; Week 4 = synthesis + oral review.",
        r"\end{itemize}",
        r"\section*{Coverage Snapshot}",
        r"\begin{longtable}{p{0.34\textwidth}p{0.18\textwidth}p{0.18\textwidth}p{0.18\textwidth}}",
        r"\toprule",
        r"Class & Parts & Core PDFs & Companion Links \\",
        r"\midrule",
        r"\endfirsthead",
        r"\toprule",
        r"Class & Parts & Core PDFs & Companion Links \\",
        r"\midrule",
        r"\endhead",
    ]
    for cls, info in class_summary.items():
        lines.append(
            rf"{tex_escape(cls)} & {info['parts']} & {info['pdf_resources']} & {info['web_links']} \\"
        )
    lines.extend([r"\bottomrule", r"\end{longtable}"])

    lines.extend(
        [
            r"\section*{Month-by-Month Plan}",
            r"\begin{longtable}{p{0.09\textwidth}p{0.24\textwidth}p{0.38\textwidth}p{0.13\textwidth}p{0.14\textwidth}}",
            r"\toprule",
            r"Month & Phase & Core Focus & Hours & Deliverable \\",
            r"\midrule",
            r"\endfirsthead",
            r"\toprule",
            r"Month & Phase & Core Focus & Hours & Deliverable \\",
            r"\midrule",
            r"\endhead",
        ]
    )
    for row in schedule:
        label = row["month_label"]
        phase = row["phase"]
        hours = row["hours_target"]
        if row["mode"] == "core":
            units = row["units"]
            focus = "; ".join(
                f"{u['class']} Part {u['part']}/{u['total_parts']}" for u in units
            )
            deliverable = "Solve assigned block + synthesis memo"
        else:
            focus = row["review_focus"]
            deliverable = "Timed mixed-set + oral defense drill"
        lines.append(
            rf"{tex_escape(str(label))} & {tex_escape(str(phase))} & {tex_escape(str(focus))} & "
            rf"{tex_escape(str(hours))} & {tex_escape(str(deliverable))} \\"
        )
    lines.extend([r"\bottomrule", r"\end{longtable}"])

    lines.extend(
        [
            r"\section*{Quarterly Milestones}",
            r"\begin{enumerate}[leftmargin=1.4em]",
            r"\item Every 3 months: one 4-hour mixed-topic problem exam simulation.",
            r"\item Every 6 months: one written synthesis report (10--15 pages).",
            r"\item Year 2 end: complete a full OR methods portfolio (deterministic + stochastic).",
            r"\item Year 3 end: complete a theory portfolio (analysis/probability/statistics).",
            r"\item Final 6 months: run full mock qualifying-cycle with oral explanations.",
            r"\end{enumerate}",
            r"\end{document}",
        ]
    )
    tex.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return tex


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
    return out_dir / "or_applied_math_bible_3_5_year_schedule.pdf"


def run(out_dir: Path) -> None:
    out_dir = out_dir.resolve()
    summary_path = out_dir / "or_applied_math_bible_chunked_summary.json"
    if not summary_path.exists():
        raise RuntimeError(f"Missing required summary file: {summary_path}")

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    class_summary: Dict[str, Dict[str, int]] = summary["class_summary"]
    class_parts = {cls: int(info["parts"]) for cls, info in class_summary.items()}
    schedule = build_schedule(class_parts)
    json_path = write_schedule_json(out_dir, schedule)
    total_parts = sum(class_parts.values())
    tex_path = write_schedule_tex(out_dir, schedule, class_summary, total_parts)
    pdf_path = compile_tex(out_dir, tex_path)

    if not pdf_path.exists() or pdf_path.stat().st_size == 0:
        raise RuntimeError("Schedule PDF was not generated.")
    print(f"Wrote schedule JSON: {json_path}")
    print(f"Wrote schedule TeX: {tex_path}")
    print(f"Wrote schedule PDF: {pdf_path}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir", type=Path, default=Path("data/assignment_pdf_bundles"))
    args = p.parse_args()
    run(args.out_dir)


if __name__ == "__main__":
    main()
