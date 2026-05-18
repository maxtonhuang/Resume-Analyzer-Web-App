"""
main.py — CLI entry point for the Day 4 Resume Analyzer.

Task 5 of the Day 4 lab (Track A).
Study material reference: §4 The Multi-Stage Pipeline

Your job is to write the main() function. The argument parser is already
provided — do not modify parse_args().
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from parse import read_resume_pdf, read_jd_text
from analyzer import (
    extract_resume_profile,
    extract_jd_profile,
    analyse_keyword_match,
    analyse_bullets,
    analyse_jargon,
    analyse_structure,
    analyse_degree_alignment,
    summarise_overall,
    compute_overall_score,
)
from report import render_markdown


VALID_DEGREES = {"RTIS", "IMGD", "UXGD", "BFA"}
ATS_PASS_THRESHOLD = 60


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments. Pre-provided — do not modify.

    Usage:
        python main.py --resume path/to/resume.pdf \\
                       --jd     path/to/job_description.txt \\
                       --degree RTIS
    """
    parser = argparse.ArgumentParser(
        description="Day 4 Resume × JD Analyzer — diagnostic feedback only."
    )
    parser.add_argument(
        "--resume", required=True,
        help="Path to the PDF résumé."
    )
    parser.add_argument(
        "--jd", required=True,
        help="Path to the plain-text job description."
    )
    parser.add_argument(
        "--degree", required=True, choices=sorted(VALID_DEGREES),
        help="Your DigiPen degree code (RTIS | IMGD | UXGD | BFA)."
    )
    return parser.parse_args()


def run_analysis(
    resume_path: str,
    jd_path: str,
    degree: str,
    progress: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """
    Run the full analysis pipeline and return the report dict.

    Args:
        resume_path: Path to the PDF resume.
        jd_path:     Path to the plain-text job description.
        degree:      One of VALID_DEGREES.
        progress:    Optional callback invoked with a status string
                     before each step. Pass `print` for CLI usage, or a
                     UI-bound writer for Streamlit.

    Returns:
        The full report dict including overall_score, passes_ats_threshold,
        and summary.

    Raises:
        ValueError: If documents cannot be read.
        Exception:  Any LLM step may raise.
    """
    notify = progress if progress is not None else (lambda _msg: None)

    notify("[1/8] Loading documents...")
    resume_text = read_resume_pdf(resume_path)
    jd_text = read_jd_text(jd_path)

    notify("[2/8] Extracting profiles...")
    resume_profile = extract_resume_profile(resume_text)
    jd_profile = extract_jd_profile(jd_text)

    notify("[3/8] Analysing keyword match...")
    keyword_match = analyse_keyword_match(resume_profile, jd_profile)

    notify("[4/8] Analysing bullets...")
    bullets = analyse_bullets(resume_profile)

    notify("[5/8] Analysing jargon...")
    jargon = analyse_jargon(resume_profile, degree, jd_profile)

    notify("[6/8] Analysing structure...")
    structure = analyse_structure(resume_text)

    notify("[7/8] Analysing degree alignment...")
    degree_alignment = analyse_degree_alignment(jd_profile, degree)

    notify("[8/8] Generating executive summary...")
    report: dict[str, Any] = {
        "resume_profile": resume_profile,
        "jd_profile": jd_profile,
        "keyword_match": keyword_match,
        "bullets": bullets,
        "jargon": jargon,
        "structure": structure,
        "degree_alignment": degree_alignment,
    }
    overall_score = compute_overall_score(report)
    report["overall_score"] = overall_score
    report["passes_ats_threshold"] = overall_score >= ATS_PASS_THRESHOLD
    report["summary"] = summarise_overall(report)

    return report


def main() -> int:
    """
    Orchestrate the full analysis pipeline. Return 0 on success, 1 on error.

    Steps to implement:
      [1/8] Parse CLI arguments (call parse_args()).
      [2/8] Load documents — call read_resume_pdf() and read_jd_text();
            catch ValueError and print to stderr, then return 1.
      [3/8] Extract structured profiles — call extract_resume_profile() and
            extract_jd_profile(); print progress as "[3/8] Extracting profiles…".
      [4/8] Run the 5 evaluations in order:
              analyse_keyword_match(resume_profile, jd_profile)
              analyse_bullets(resume_profile)
              analyse_jargon(resume_profile, args.degree, jd_profile)
              analyse_structure(resume_text)
              analyse_degree_alignment(jd_profile, args.degree)
            Print a [4/8]…[8/8] progress line for each.
      [9/9] Assemble the report dict:
              {
                "resume_profile":  resume_profile,
                "jd_profile":      jd_profile,
                "keyword_match":   keyword_match,
                "bullets":         bullets,
                "jargon":          jargon,
                "structure":       structure,
                "degree_alignment": degree_alignment,
              }
            Compute overall_score with compute_overall_score(report).
            Add to report:
              report["overall_score"]       = overall_score
              report["passes_ats_threshold"] = overall_score >= ATS_PASS_THRESHOLD
              report["summary"]             = summarise_overall(report)

            Build a timestamped filename:
              ts = datetime.now().strftime("%Y%m%d_%H%M%S")
              json_path = Path("outputs") / f"match_report_{ts}.json"
              md_path   = Path("outputs") / f"match_report_{ts}.md"

            Save JSON: json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
            Save Markdown: render_markdown(report, out_path=md_path)

            Print the final verdict and the 3-bullet summary.
            Return 0.
    """
    args = parse_args()

    try:
        report = run_analysis(args.resume, args.jd, args.degree, progress=print)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    outputs_dir = Path("outputs")
    outputs_dir.mkdir(parents=True, exist_ok=True)
    json_path = outputs_dir / f"match_report_{ts}.json"
    md_path = outputs_dir / f"match_report_{ts}.md"

    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    render_markdown(report, out_path=str(md_path))

    verdict = "PASS" if report["passes_ats_threshold"] else "FAIL"
    print()
    print(f"Overall Score: {report['overall_score']} / 100  {verdict}")
    print()
    print("Executive Summary:")
    print(report["summary"])
    print()
    print("Reports saved to:")
    print(f"  {json_path}")
    print(f"  {md_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
