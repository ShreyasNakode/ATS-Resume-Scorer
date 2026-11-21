import sys
from pathlib import Path
import streamlit as st

# Add project root and frontend directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
FRONTEND_DIR = Path(__file__).resolve().parent
if str(FRONTEND_DIR) not in sys.path:
    sys.path.insert(0, str(FRONTEND_DIR))

from frontend.components.clerk_auth import render_clerk_auth_sidebar
from frontend.views import history, landing, resources, scorer

# Page configuration
st.set_page_config(
    page_title="BERT ATS Resume Scorer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize Session State
default_states = {
    "current_view": "landing",
    "clerk_token": "demo_token_authenticated",
    "user_email": "demo.candidate@ats-scorer.com",
    "is_demo": True,
    "latest_analysis": None,
    "analyzed_filename": None,
}
for key, default_val in default_states.items():
    if key not in st.session_state:
        st.session_state[key] = default_val


# Load CSS
def load_styles():
    css_path = FRONTEND_DIR / "assets" / "styles.css"
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_styles()

# Sidebar Navigation
with st.sidebar:
    st.markdown("## 🎯 ATS Scorer")
    st.caption("Bidirectional Transformer & NLP Engine")
    st.markdown("---")

    if st.button("🏠 Home", use_container_width=True, key="nav_home"):
        st.session_state.current_view = "landing"
        st.rerun()

    if st.button("🎯 ATS Scorer", use_container_width=True, key="nav_scorer"):
        st.session_state.current_view = "scorer"
        st.rerun()

    if st.button("📊 History", use_container_width=True, key="nav_history"):
        st.session_state.current_view = "history"
        st.rerun()

    if st.button("📚 Resources & Guides", use_container_width=True, key="nav_resources"):
        st.session_state.current_view = "resources"
        st.rerun()

    st.markdown("---")
    render_clerk_auth_sidebar()

# Main View Router
current_view = st.session_state.get("current_view", "landing")

if current_view == "landing":
    landing.render()
elif current_view == "scorer":
    scorer.render()
elif current_view == "history":
    history.render()
elif current_view == "resources":
    resources.render()
else:
    landing.render()
