import streamlit as st


def render_clerk_auth_sidebar():
    """Render Clerk authentication status and controls in the Streamlit sidebar."""
    st.markdown("### 👤 Clerk Authentication")

    user_token = st.session_state.get("clerk_token")
    user_email = st.session_state.get("user_email")
    is_demo = st.session_state.get("is_demo", False)

    if user_token:
        # User is authenticated
        badge_text = "Guest Mode" if is_demo else "Verified via Clerk"
        badge_color = "#6B7280" if is_demo else "#10B981"
        st.markdown(
            f"""
            <div style="background:#F3F4F6; padding:10px 14px; border-radius:8px; margin-bottom:10px;">
                <p style="margin:0; font-size:13px; color:#374151;">Signed in as:</p>
                <p style="margin:2px 0 6px 0; font-weight:600; color:#111827;">{user_email or 'candidate@ats.local'}</p>
                <span style="background:{badge_color}; color:white; font-size:11px; padding:2px 8px; border-radius:12px;">{badge_text}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("🚪 Sign Out", key="clerk_signout", use_container_width=True):
            st.session_state.clerk_token = None
            st.session_state.user_email = None
            st.session_state.is_demo = False
            st.success("Signed out successfully.")
            st.rerun()
    else:
        # User is not authenticated
        tab1, tab2 = st.tabs(["Demo / Quick Access", "Clerk Token"])

        with tab1:
            st.caption("Test the ATS system instantly without configuring third-party Clerk keys.")
            if st.button("⚡ Continue as Demo User", key="btn_demo_login", use_container_width=True, type="primary"):
                st.session_state.clerk_token = "demo_token_authenticated"
                st.session_state.user_email = "demo.candidate@ats-scorer.com"
                st.session_state.is_demo = True
                st.success("Signed in in demo mode!")
                st.rerun()

        with tab2:
            st.caption("Paste a Clerk session token from your Clerk frontend app:")
            token_input = st.text_input("Clerk Session JWT", type="password", key="clerk_jwt_input")
            email_input = st.text_input("User Email (Optional)", key="clerk_email_input", placeholder="user@example.com")
            if st.button("Sign In with Token", key="btn_clerk_token_login", use_container_width=True):
                if token_input.strip():
                    st.session_state.clerk_token = token_input.strip()
                    st.session_state.user_email = email_input.strip() or "clerk_user@app.local"
                    st.session_state.is_demo = False
                    st.success("Authenticated with Clerk token.")
                    st.rerun()
                else:
                    st.error("Please enter a valid Clerk JWT.")
