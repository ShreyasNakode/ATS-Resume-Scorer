from typing import Any, Dict, List
import streamlit as st


def display_strengths(strengths: List[str]) -> None:
    """Render resume strengths list."""
    st.markdown("### 🌟 Key Resume Strengths")
    if not strengths:
        st.info("No standout strengths identified yet. Address the action items below to build a stronger profile.")
        return

    for item in strengths:
        st.markdown(
            f"""
            <div style="background:#F0FDF4; border-left:4px solid #10B981; padding:10px 14px; border-radius:6px; margin-bottom:8px;">
                <span style="color:#065F46; font-size:14px; font-weight:500;">✅ {item}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def display_critical_issues(analysis: Dict[str, Any]) -> None:
    """Render critical issues and warnings."""
    critical = analysis.get("critical_issues", [])
    if not critical:
        return

    st.markdown("### ⚠️ Critical ATS Roadblocks")
    for issue in critical:
        st.markdown(
            f"""
            <div style="background:#FEF2F2; border-left:4px solid #EF4444; padding:10px 14px; border-radius:6px; margin-bottom:8px;">
                <span style="color:#991B1B; font-size:14px; font-weight:600;">🔴 {issue}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
