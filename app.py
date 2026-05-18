"""
app.py - Streamlit UI for the Day 4 Resume Analyzer.
"""
import json
import tempfile
from datetime import datetime
from pathlib import Path

import streamlit as st

from main import ATS_PASS_THRESHOLD, VALID_DEGREES, run_analysis
from report import render_markdown


st.set_page_config(page_title="Resume Analyzer", layout="wide")
st.title("Resume Analyzer")


def reset_results() -> None:
    st.session_state.report = None
    st.session_state.md_text = None
    st.session_state.report_ts = None


if "report" not in st.session_state:
    reset_results()


with st.sidebar:
    st.header("Inputs")
    resume_file = st.file_uploader("Resume (PDF)", type=["pdf"])
    jd_file = st.file_uploader("Job description (TXT)", type=["txt"])
    degree = st.selectbox("Degree", sorted(VALID_DEGREES))

    can_analyze = resume_file is not None and jd_file is not None
    analyze_clicked = st.button("Analyze", type="primary", disabled=not can_analyze)
    st.button("Reset", on_click=reset_results)


if analyze_clicked and resume_file is not None and jd_file is not None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        resume_path = tmp / resume_file.name
        jd_path = tmp / jd_file.name
        resume_path.write_bytes(resume_file.getvalue())
        jd_path.write_bytes(jd_file.getvalue())

        with st.status("Running analysis...", expanded=True) as status:
            try:
                report = run_analysis(
                    str(resume_path),
                    str(jd_path),
                    degree,
                    progress=lambda msg: status.write(msg),
                )
            except ValueError as exc:
                status.update(label="Failed to load documents", state="error")
                st.error(str(exc))
                st.stop()
            except Exception as exc:
                status.update(label="Pipeline failed", state="error")
                st.error(f"Unexpected error: {exc}")
                st.stop()

            md_path = tmp / "report.md"
            render_markdown(report, out_path=str(md_path))
            md_text = md_path.read_text(encoding="utf-8")

            status.update(label="Analysis complete", state="complete")

        st.session_state.report = report
        st.session_state.md_text = md_text
        st.session_state.report_ts = datetime.now().strftime("%Y%m%d_%H%M%S")


if st.session_state.report is not None:
    report = st.session_state.report
    md_text = st.session_state.md_text
    ts = st.session_state.report_ts

    verdict = "PASS" if report["passes_ats_threshold"] else "FAIL"

    col_score, col_summary = st.columns([1, 2])
    with col_score:
        st.metric("Overall Score", f"{report['overall_score']} / 100")
        if verdict == "PASS":
            st.success(f"Verdict: {verdict}")
        else:
            st.error(f"Verdict: {verdict}")
    with col_summary:
        st.subheader("Executive Summary")
        st.write(report["summary"])

    st.divider()
    st.subheader("Full Report")
    st.markdown(md_text)

    st.divider()
    dl_json, dl_md = st.columns(2)
    with dl_json:
        st.download_button(
            "Download JSON",
            data=json.dumps(report, indent=2),
            file_name=f"match_report_{ts}.json",
            mime="application/json",
        )
    with dl_md:
        st.download_button(
            "Download Markdown",
            data=md_text,
            file_name=f"match_report_{ts}.md",
            mime="text/markdown",
        )