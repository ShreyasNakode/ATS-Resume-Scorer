import streamlit as st


def render():
    st.title("📚 ATS Optimization Knowledge Base")
    st.markdown("Proven industry guidelines, action verbs, and structural formulas to optimize your resume.")

    tab1, tab2, tab3, tab4 = st.tabs([
        "Format & Layout Rules",
        "Power Action Verbs",
        "Google's X-Y-Z Formula",
        "Common Rejection Reasons",
    ])

    with tab1:
        st.markdown("""
        ### 📐 Standard ATS Formatting Rules
        1. **Use Single-Column Layouts**: Multi-column tables often cause text streams to interleave unpredictably in older ATS parsers.
        2. **Standard Section Headers**: Stick to universally recognized headers:
           - `Summary` or `Professional Summary`
           - `Experience` or `Work History`
           - `Projects`
           - `Education`
           - `Technical Skills`
        3. **Standard Font Selection**: Use standard web-safe fonts (Calibri, Arial, Helvetica, Georgia) sized between 10pt and 12pt.
        4. **Clean Bullet Points**: Use standard solid round bullets (`•`) or hyphens (`-`). Avoid decorative unicode icons or checkboxes.
        5. **File Formats**: Use clean **PDF** or modern **DOCX**. Avoid image scans or PNG conversions.
        """)

    with tab2:
        st.markdown("""
        ### ⚡ High-Impact Action Verbs Catalog
        Categorized verbs to lead your achievement bullet points:

        - **Technical & Engineering**: *Architected, Engineered, Spearheaded, Refactored, Automated, Deployed, Benchmarked, Streamlined*
        - **Leadership & Ownership**: *Orchestrated, Directed, Governed, Championed, Founded, Mentored, Supervised*
        - **Optimization & Scale**: *Accelerated, Maximized, Reduced, Minimized, Scaled, Overhauled, Revitalized*
        - **Research & Innovation**: *Formulated, Devised, Pioneer, Designed, Synthesized, Analyzed, Validated*
        """)

    with tab3:
        st.markdown("""
        ### 🎯 Google's X-Y-Z Achievement Formula
        The gold standard for bullet point writing recommended by top tech recruiters:

        > **"Accomplished [X], as measured by [Y], by doing [Z]"**

        #### Examples:
        - **Weak**: "Responsible for making the website faster."
        - **Strong**: *"Reduced web page load time by 42% (Y) across 80,000 monthly active users (X) by implementing Redis server-side caching and optimizing SQL indices (Z)."*
        - **Weak**: "Wrote unit tests."
        - **Strong**: *"Elevated backend unit test coverage from 55% to 94% (Y) across 35 microservices (X) by architecting an automated Pytest CI/CD regression suite (Z)."*
        """)

    with tab4:
        st.markdown("""
        ### 🚫 Top 5 ATS Rejection Pitfalls
        1. **Empty Skill Listing**: Listing a technology in your Skills section without mentioning it anywhere in your projects or work history.
        2. **Over-Designed Visual Graphics**: Placing crucial contact details or skill bars inside canvas graphics, SVG charts, or PDF headers/footers.
        3. **Missing Contextual Keywords**: Omitting key industry terms and frameworks explicitly required in the target Job Description.
        4. **No Measurable Metrics**: Writing resumes that read like job descriptions rather than achievement records.
        5. **Location Overexposure**: Listing full street addresses and postal codes, which triggers ATS privacy and bias filters.
        """)
