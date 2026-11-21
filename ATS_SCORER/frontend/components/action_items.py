from typing import Any, Dict
import streamlit as st


def display_action_items(analysis: Dict[str, Any]) -> None:
    """Render prioritized checklist of action items."""
    feedback_items = analysis.get("detailed_feedback", [])
    all_actions = []

    for item in feedback_items:
        actions = item.get("action_items") if isinstance(item, dict) else getattr(item, "action_items", [])
        for act in actions:
            if act not in all_actions:
                all_actions.append(act)

    if not all_actions:
        return

    st.markdown("### 📋 Quick Action Checklist")
    st.caption("Step-by-step checklist to increase your ATS match probability:")

    for idx, act in enumerate(all_actions[:8]):
        st.checkbox(act, key=f"action_chk_{idx}")
