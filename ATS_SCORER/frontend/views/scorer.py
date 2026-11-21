import json
from typing import Optional
import requests
import streamlit as st

from frontend.components.dashboard import display_results_dashboard
from frontend.services import api_client


def _show_backend_error(exc: Exception) -> None:
    """Translate requests exception into friendly user message."""
    if isinstance(exc, requests.ConnectionError):
        st.error("🚨 Cannot reach FastAPI backend on port 8000. Start the backend with: `uvicorn backend.main:app --port 8000`.")
    elif isinstance(exc, requests.Timeout):
        st.error("⏱️ The backend took too long to complete analysis. Check server logs.")
    elif isinstance(exc, requests.HTTPError) and exc.response is not None:
        try:
            detail = exc.response.json().get("detail", exc.response.text)
        except Exception:
            detail = exc.response.text
        st.error(f"Backend error ({exc.response.status_code}): {detail}")
    else:
        st.error(f"Error during analysis: {exc}")


def render():
    st.title("🎯 ATS Resume Scorer")
    st.markdown("Upload your resume and benchmark your ATS compatibility using BERT and spaCy.")

    access_token = st.session_state.get("clerk_token") or "demo_token"

    # Analysis Mode Selector
    mode = st.radio(
        "Analysis Mode:",
        ["Standard Resume Diagnostic", "Target Job Description Comparison"],
        horizontal=True,
        key="analysis_mode_select",
    )

    left_col, right_col = st.columns(2)

    with left_col:
        st.markdown("### 📄 1. Upload Resume")
        resume_file = st.file_uploader(
            "Select Resume File",
            type=["pdf", "docx"],
            help="Supported: PDF (PyPDF2), DOCX (Python-Docx). Maximum 10 MB.",
            key="resume_uploader",
        )
        if resume_file:
            st.success(f"📎 **{resume_file.name}** ({resume_file.size / 1024:.1f} KB)")

    jd_text = ""
    with right_col:
        if mode == "Target Job Description Comparison":
            st.markdown("### 📋 2. Target Job Description")
            jd_input_method = st.radio("Input method:", ["Paste Text", "Upload .txt File"], horizontal=True, key="jd_method")
            if jd_input_method == "Paste Text":
                jd_text = st.text_area(
                    "Paste Job Description text here:",
                    height=200,
                    placeholder="Paste the full job requirements, skills, and qualifications...",
                    key="jd_textarea",
                )
            else:
                jd_file = st.file_uploader("Upload JD (.txt file)", type=["txt"], key="jd_uploader")
                if jd_file:
                    jd_text = jd_file.getvalue().decode("utf-8", errors="ignore")
                    st.success(f"📎 Loaded JD: {jd_file.name}")
        else:
            st.markdown("### ℹ️ Standard Diagnostic Mode")
            st.info(
                "Standard mode assesses formatting hierarchy, action verbs, "
                "measurable outcomes, BERT skill-to-project validation, and ATS parser readability."
            )

    st.markdown("")
    col_btn, _ = st.columns([1, 2])
    with col_btn:
        start_analysis = st.button("🚀 Analyze Resume", type="primary", use_container_width=True)

    if start_analysis:
        if not resume_file:
            st.error("Please select a resume file (PDF or DOCX) to analyze.")
            return

        with st.status("Analyzing resume with BERT and NLP models...", expanded=True) as status_box:
            try:
                st.write("📖 Extracting text & structure using PyPDF2 / Python-Docx...")
                st.write("🧠 Computing BERT dense semantic embeddings & spaCy linguistic tags...")
                st.write("🔍 Running Scikit-Learn TF-IDF similarity & skill validation...")

                result = api_client.analyze_resume(
                    resume_file=resume_file,
                    access_token=access_token,
                    job_description=jd_text,
                )

                st.session_state.latest_analysis = result
                st.session_state.analyzed_filename = resume_file.name
                status_box.update(label="Analysis complete!", state="complete", expanded=False)
            except Exception as exc:
                status_box.update(label="Analysis failed", state="error")
                _show_backend_error(exc)
                return

    # Render Dashboard if analysis result exists in session
    if "latest_analysis" in st.session_state and st.session_state.latest_analysis:
        analysis_data = st.session_state.latest_analysis
        st.markdown("---")

        # Top Action Bar: Download PDF & Summary
        top_left, top_right = st.columns([3, 1])
        with top_left:
            st.markdown(f"### 📑 Results for: `{st.session_state.get('analyzed_filename', 'Resume')}`")
        with top_right:
            # Download PDF Report button
            try:
                pdf_bytes = api_client.generate_pdf(analysis_data, access_token)
                st.download_button(
                    label="📥 Download PDF Report",
                    data=pdf_bytes,
                    file_name="ATS_Score_Report.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception:
                pass

        display_results_dashboard(analysis_data)
