from typing import Any, Dict
import streamlit as st
from frontend.components._helpers import get_severity_style


def display_detailed_feedback(analysis: Dict[str, Any]) -> None:
    """Render expandable detailed issues with severity styling and solutions."""
    feedback_items = analysis.get("detailed_feedback", [])
    if not feedback_items:
        return

    st.markdown("### 🔍 Detailed Issue Diagnostics")
    st.caption("Expand each diagnostic card to see specific fixes and before/after improvements.")

    for idx, item in enumerate(feedback_items):
        title = item.get("issue_title") if isinstance(item, dict) else getattr(item, "issue_title", "Issue")
        severity = item.get("severity_level") if isinstance(item, dict) else getattr(item, "severity_level", "Medium")
        explanation = item.get("explanation") if isinstance(item, dict) else getattr(item, "explanation", "")
        where = item.get("where_it_appears") if isinstance(item, dict) else getattr(item, "where_it_appears", "")
        how_to_fix = item.get("how_to_fix") if isinstance(item, dict) else getattr(item, "how_to_fix", "")
        action_items = item.get("action_items") if isinstance(item, dict) else getattr(item, "action_items", [])
        example = item.get("example_improvement") if isinstance(item, dict) else getattr(item, "example_improvement", "")

        icon, text_color, bg_color = get_severity_style(severity)

        with st.expander(f"{icon} {title} — Severity: {severity}"):
            st.markdown(f"**Explanation:** {explanation}")
            if where:
                st.markdown(f"📍 **Where it appears:** `{where}`")
            st.markdown(f"💡 **How to fix:** {how_to_fix}")

            if action_items:
                st.markdown("**Action Checklist:**")
                for act in action_items:
                    st.markdown(f"- [ ] {act}")

            if example:
                st.markdown("**Example Improvement:**")
                st.code(example, language="markdown")
