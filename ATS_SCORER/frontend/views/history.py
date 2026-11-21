import requests
import streamlit as st
from frontend.services import api_client


def _show_backend_error(exc: Exception) -> None:
    if isinstance(exc, requests.ConnectionError):
        st.error("Cannot connect to backend server on port 8000.")
    elif isinstance(exc, requests.HTTPError) and exc.response is not None:
        st.error(f"Backend error {exc.response.status_code}: {exc.response.text}")
    else:
        st.error(f"Error loading history: {exc}")


def render():
    st.title("📊 Analysis History")
    st.markdown("Past resume evaluations saved against your Clerk account.")

    access_token = st.session_state.get("clerk_token") or "demo_token"

    try:
        history = api_client.get_history(access_token)
    except Exception as exc:
        _show_backend_error(exc)
        return

    if not history:
        st.info("No saved analyses found for this account. Upload and evaluate a resume in the ATS Scorer view.")
        if st.button("🎯 Go to ATS Scorer"):
            st.session_state.current_view = "scorer"
            st.rerun()
        return

    st.markdown(f"**Total Saved Analyses:** `{len(history)}`")
    st.markdown("---")

    for idx, entry in enumerate(history):
        entry_id = entry.get("id")
        filename = entry.get("filename", "resume.pdf")
        score = float(entry.get("ats_score", 0.0))
        created_at = entry.get("created_at", "")[:19].replace("T", " ")
        analysis_data = entry.get("analysis_result", {})
        cs = analysis_data.get("component_scores", {})

        badge_color = "#10B981" if score >= 80 else "#F59E0B" if score >= 60 else "#EF4444"

        with st.expander(f"📄 {filename}  —  Score: {score:.0f}/100  —  {created_at}"):
            m1, m2, m3, m4, m5 = st.columns(5)
            with m1:
                st.metric("Overall Score", f"{score:.0f}/100")
            with m2:
                st.metric("Formatting", f"{cs.get('formatting', 0):.0f}/20")
            with m3:
                st.metric("Keywords", f"{cs.get('keywords', 0):.0f}/25")
            with m4:
                st.metric("Content", f"{cs.get('content', 0):.0f}/25")
            with m5:
                st.metric("BERT Validation", f"{cs.get('skill_validation', 0):.0f}/15")

            act1, act2 = st.columns([1, 1])
            with act1:
                # Download PDF button for this history entry
                if st.button(f"📥 Download PDF", key=f"pdf_btn_{idx}"):
                    try:
                        pdf_bytes = api_client.get_history_pdf(entry_id, access_token)
                        st.download_button(
                            label=f"Save {filename}.pdf",
                            data=pdf_bytes,
                            file_name=f"ATS_Report_{filename}.pdf",
                            mime="application/pdf",
                            key=f"dl_{idx}",
                        )
                    except Exception as exc:
                        st.error(f"Failed to fetch PDF: {exc}")

            with act2:
                if st.button(f"🗑️ Delete Record", key=f"del_btn_{idx}"):
                    try:
                        api_client.delete_history_entry(entry_id, access_token)
                        st.success("Record deleted successfully.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Failed to delete record: {exc}")
