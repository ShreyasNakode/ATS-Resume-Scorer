from typing import Any, Dict
import streamlit as st


def display_jd_comparison(jd_comparison: Dict[str, Any]) -> None:
    """Render comparison between resume and job description."""
    if not jd_comparison:
        return

    st.markdown("### 🎯 Job Description Alignment & Gap Analysis")
    match_pct = float(jd_comparison.get("match_percentage", 0.0))
    semantic_sim = float(jd_comparison.get("semantic_similarity", 0.0))
    matched_kws = jd_comparison.get("matched_keywords", [])
    missing_kws = jd_comparison.get("missing_keywords", [])
    skills_gap = jd_comparison.get("skills_gap", [])

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Composite JD Match", f"{match_pct:.1f}%")
    with c2:
        st.metric("BERT Semantic Similarity", f"{semantic_sim * 100:.1f}%")
    with c3:
        st.metric("Keyword Overlap", f"{len(matched_kws)} matched", f"{len(missing_kws)} missing")

    left, right = st.columns(2)
    with left:
        st.markdown(f"#### ✅ Matched Target Keywords ({len(matched_kws)})")
        if matched_kws:
            pills = "".join(
                f'<span style="display:inline-block; background:#ECFDF5; color:#065F46; border:1px solid #A7F3D0; padding:4px 10px; border-radius:12px; margin:3px; font-size:13px;">{kw}</span>'
                for kw in matched_kws[:18]
            )
            st.markdown(pills, unsafe_allow_html=True)
        else:
            st.info("No matching keywords detected.")

    with right:
        st.markdown(f"#### ❌ Missing Critical Keywords ({len(missing_kws)})")
        if missing_kws:
            pills = "".join(
                f'<span style="display:inline-block; background:#FEF2F2; color:#991B1B; border:1px solid #FECACA; padding:4px 10px; border-radius:12px; margin:3px; font-size:13px;">{kw}</span>'
                for kw in missing_kws[:18]
            )
            st.markdown(pills, unsafe_allow_html=True)
        else:
            st.success("Your resume covers all target job description keywords!")

    if skills_gap:
        st.markdown("#### 🔍 Priority Skills Gap")
        gap_pills = "".join(
            f'<span style="display:inline-block; background:#FFFBEB; color:#92400E; border:1px solid #FDE68A; padding:4px 10px; border-radius:12px; margin:3px; font-size:13px; font-weight:600;">⚠️ {skill}</span>'
            for skill in skills_gap[:10]
        )
        st.markdown(gap_pills, unsafe_allow_html=True)
