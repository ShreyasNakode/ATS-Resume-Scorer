import streamlit as st


def render():
    """Render landing page with modern hero section, feature cards, and workflow."""
    # Hero Section
    st.markdown(
        """
        <div style="text-align:center; padding:3rem 2rem; background:linear-gradient(135deg, #4F46E5 0%, #7C3AED 50%, #9333EA 100%);
                    color:white; border-radius:18px; margin-bottom:2rem; box-shadow:0 12px 36px rgba(79, 70, 229, 0.25);">
            <div style="display:inline-block; background:rgba(255,255,255,0.2); padding:4px 14px; border-radius:20px; font-size:13px; font-weight:600; margin-bottom:12px;">
                ⚡ Powered by BERT (Bidirectional Transformers) & spaCy NLP
            </div>
            <h1 style="font-size:3rem; font-weight:800; margin:0 0 10px 0; letter-spacing:-0.5px;">
                🎯 AI Resume ATS Scorer & Optimizer
            </h1>
            <p style="font-size:1.2rem; opacity:0.92; max-width:760px; margin:0 auto 20px auto; line-height:1.5;">
                Benchmark your resume against modern Applicant Tracking Systems using deep contextual BERT embeddings,
                spaCy linguistic entity recognition, and Scikit-Learn keyword extraction.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Call-to-Action
    _, mid_col, _ = st.columns([1, 2, 1])
    with mid_col:
        if st.button("🚀 Analyze Your Resume Now", use_container_width=True, type="primary"):
            st.session_state.current_view = "scorer"
            st.rerun()

    st.markdown("---")

    # Key Features
    st.markdown("## 🌟 Enterprise-Grade ATS Analysis")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div style="background:#FFFFFF; padding:20px; border-radius:12px; border:1px solid #E5E7EB; min-height:220px;">
                <h3 style="color:#4F46E5; margin-top:0;">🤖 BERT Semantic Matching</h3>
                <p style="color:#4B5563; font-size:14px;">
                    Goes beyond naive keyword counting. Uses bidirectional transformer embeddings to understand context,
                    synonyms, and role qualifications.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div style="background:#FFFFFF; padding:20px; border-radius:12px; border:1px solid #E5E7EB; min-height:220px;">
                <h3 style="color:#7C3AED; margin-top:0;">✅ Skill Validation Engine</h3>
                <p style="color:#4B5563; font-size:14px;">
                    Verifies whether claimed skills are genuinely demonstrated in your project bullets and work history.
                    Eliminates empty keyword stuffing.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
            <div style="background:#FFFFFF; padding:20px; border-radius:12px; border:1px solid #E5E7EB; min-height:220px;">
                <h3 style="color:#059669; margin-top:0;">🔒 Secure Clerk Auth & Privacy</h3>
                <p style="color:#4B5563; font-size:14px;">
                    Secured by Clerk authentication. Evaluates location privacy risk and strips sensitive PII before ATS ingestion.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Workflow Steps
    st.markdown("## 🛠️ How It Works")
    s1, s2, s3 = st.columns(3)
    with s1:
        st.markdown("#### 1️⃣ Upload Resume\nUpload your **PDF** or **DOCX** file. PyPDF2 & Python-Docx extract text, metadata, and hyperlink annotations.")
    with s2:
        st.markdown("#### 2️⃣ Neural & NLP Scoring\nBERT embeddings, spaCy POS tagging, and Scikit-Learn TF-IDF evaluate your resume against 5 ATS dimensions.")
    with s3:
        st.markdown("#### 3️⃣ Actionable Diagnosis\nReceive a granular 0-100 score, prioritized checklist, before/after fixes, and downloadable PDF report.")
