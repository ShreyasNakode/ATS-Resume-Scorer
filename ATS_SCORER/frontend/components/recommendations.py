from typing import Any, Dict
import streamlit as st


def display_recommendations(analysis: Dict[str, Any]) -> None:
    """Render high-level recommendation cards with priority and impact badges."""
    recs = analysis.get("recommendations", [])
    if not recs:
        return

    st.markdown("### 💡 Strategic Recommendations")
    for item in recs:
        title = item.get("title") if isinstance(item, dict) else getattr(item, "title", "")
        desc = item.get("description") if isinstance(item, dict) else getattr(item, "description", "")
        priority = item.get("priority") if isinstance(item, dict) else getattr(item, "priority", "medium")
        impact = item.get("impact_score") if isinstance(item, dict) else getattr(item, "impact_score", 5.0)

        badge_color = "#DC2626" if priority == "critical" else "#D97706" if priority == "high" else "#2563EB"

        st.markdown(
            f"""
            <div style="background:#FFFFFF; border:1px solid #E5E7EB; border-radius:10px; padding:16px; margin-bottom:12px; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <span style="font-weight:700; font-size:16px; color:#111827;">{title}</span>
                    <span style="background:{badge_color}; color:white; font-size:11px; padding:3px 10px; border-radius:12px; font-weight:600; text-transform:uppercase;">
                        {priority} (+{impact:.1f} pts)
                    </span>
                </div>
                <p style="margin:0; font-size:14px; color:#4B5563;">{desc}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
