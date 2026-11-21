from typing import Any, Dict
import streamlit as st

from frontend.components.action_items import display_action_items
from frontend.components.detailed_feedback import display_detailed_feedback
from frontend.components.jd_comparison import display_jd_comparison
from frontend.components.recommendations import display_recommendations
from frontend.components.score_display import display_overall_score, display_score_breakdown
from frontend.components.skill_validation import display_skill_validation
from frontend.components.strengths_issues import display_critical_issues, display_strengths


def display_results_dashboard(analysis: Dict[str, Any]) -> None:
    """Render comprehensive interactive ATS diagnostic dashboard."""
    display_overall_score(analysis)
    st.markdown("---")

    display_score_breakdown(analysis)
    st.markdown("---")

    col_a, col_b = st.columns([1, 1])
    with col_a:
        display_strengths(analysis.get("strengths") or [])
    with col_b:
        display_critical_issues(analysis)
    st.markdown("---")

    display_skill_validation(analysis)
    st.markdown("---")

    jd_comp = analysis.get("jd_comparison") or analysis.get("jd_match_analysis")
    if jd_comp:
        display_jd_comparison(jd_comp)
        st.markdown("---")

    display_detailed_feedback(analysis)
    st.markdown("---")

    display_action_items(analysis)
    st.markdown("---")

    display_recommendations(analysis)
