from typing import Any, Dict
import streamlit as st
from frontend.components._helpers import get_score_color, get_score_emoji

COMPONENTS = [
    ("Formatting & Structure", "formatting", 20, "📝"),
    ("Keywords & Technical Skills", "keywords", 25, "🔑"),
    ("Content Quality & Verbs", "content", 25, "📄"),
    ("BERT Skill Validation", "skill_validation", 15, "🤖"),
    ("ATS Compatibility & Privacy", "ats_compatibility", 15, "🛡️"),
]


def display_overall_score(analysis: Dict[str, Any]) -> None:
    """Display prominent overall score card with evaluation statement."""
    score = float(analysis.get("ATS_score", analysis.get("ats_score", 0.0)))
    interpretation = analysis.get("interpretation", "")
    text_color, bg_color = get_score_color(score)
    emoji = get_score_emoji(score)

    st.markdown("## 📊 Overall ATS Compatibility Score")
    _, center_col, _ = st.columns([1, 2.5, 1])
    with center_col:
        st.markdown(
            f"""
            <div style="text-align:center; padding:2rem; background-color:{bg_color};
                        border-radius:16px; border: 2px solid {text_color}22; box-shadow:0 8px 24px rgba(0,0,0,0.06);">
                <div style="font-size:1.1rem; color:#4B5563; font-weight:600; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;">
                    Overall ATS Compatibility
                </div>
                <h1 style="color:{text_color}; font-size:4.8rem; margin:0; line-height:1; font-weight:800;">
                    {score:.0f}<span style="font-size:2.2rem; color:#9CA3AF; font-weight:400;">/100</span>
                </h1>
                <div style="font-size:1.4rem; margin-top:10px;">{emoji}</div>
                <p style="color:#374151; font-size:1.1rem; font-weight:500; margin-top:0.75rem;">{interpretation}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def display_score_breakdown(analysis: Dict[str, Any]) -> None:
    """Render 5-dimension score breakdown with progress bars."""
    component_scores = analysis.get("component_scores") or {}
    st.markdown("### 📈 Multi-Dimensional Score Breakdown")

    left, right = st.columns(2)
    for idx, (label, key, max_score, icon) in enumerate(COMPONENTS):
        value = float(component_scores.get(key, 0.0))
        percentage = min(1.0, max(0.0, value / max_score if max_score else 0.0))
        bar_color = "#10B981" if percentage >= 0.8 else "#F59E0B" if percentage >= 0.6 else "#EF4444"

        target_col = left if idx % 2 == 0 else right
        with target_col:
            st.markdown(
                f"""
                <div style="margin-bottom:14px; background:#FFFFFF; padding:12px 16px; border-radius:10px; border:1px solid #E5E7EB;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                        <span style="font-weight:600; font-size:14px; color:#1F2937;">{icon} {label}</span>
                        <span style="font-weight:700; font-size:15px; color:{bar_color};">{value:.1f} / {max_score}</span>
                    </div>
                    <div style="background-color:#E5E7EB; border-radius:6px; height:10px; width:100%; overflow:hidden;">
                        <div style="background-color:{bar_color}; width:{percentage * 100}%; height:100%; border-radius:6px;"></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
