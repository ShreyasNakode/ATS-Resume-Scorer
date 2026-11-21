from typing import Any, Dict
import streamlit as st


def display_skill_validation(analysis: Dict[str, Any]) -> None:
    """Display BERT-validated skills vs unvalidated skills."""
    svd = analysis.get("skill_validation_details") or {}
    validated = svd.get("validated", [])
    unvalidated = svd.get("unvalidated", [])
    val_pct = svd.get("validation_pct", 0.0)

    st.markdown("### 🤖 BERT Skill Validation Engine")
    st.caption("Matches listed skills against project bullet points and experience descriptions using BERT embeddings.")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Validated Skills Ratio", f"{val_pct:.1f}%", f"{len(validated)} of {len(validated) + len(unvalidated)} skills")
    with col2:
        val_status = "Optimal" if val_pct >= 75 else "Moderate" if val_pct >= 50 else "High Discrepancy"
        st.metric("Evidence Level", val_status)

    left, right = st.columns(2)
    with left:
        st.markdown(f"#### ✅ Validated in Projects ({len(validated)})")
        if validated:
            for item in validated[:12]:
                skill_name = item.get("skill", "")
                projs = item.get("projects", [])
                proj_tag = f" ({', '.join(projs[:2])})" if projs else ""
                st.markdown(
                    f"""
                    <span style="display:inline-block; background:#ECFDF5; color:#065F46; border:1px solid #A7F3D0;
                                 padding:4px 10px; border-radius:12px; margin:3px 4px; font-size:13px; font-weight:500;">
                        {skill_name}{proj_tag}
                    </span>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No skills could be substantiated from project descriptions.")

    with right:
        st.markdown(f"#### ⚠️ Missing Project Evidence ({len(unvalidated)})")
        if unvalidated:
            for skill in unvalidated[:12]:
                st.markdown(
                    f"""
                    <span style="display:inline-block; background:#FEF2F2; color:#991B1B; border:1px solid #FECACA;
                                 padding:4px 10px; border-radius:12px; margin:3px 4px; font-size:13px; font-weight:500;">
                        {skill}
                    </span>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.success("All listed skills are corroborated by project descriptions!")
