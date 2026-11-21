import re
from typing import Any, Dict, List, Optional
from backend.models.schemas import IssueDetail


def analyze_issues(
    resume_text: str,
    parsed_resume: Dict[str, Any],
    skills: List[str],
    projects: List[Dict[str, Any]],
    action_verbs: List[str],
    skill_validation: Dict[str, Any],
    scores: Dict[str, Any],
    contact_info: Optional[Dict[str, Any]] = None,
) -> List[IssueDetail]:
    """Diagnose specific defects in the resume and formulate structured recommendations."""
    detected: List[IssueDetail] = []
    text_lower = resume_text.lower()

    exp_entries = [e for e in parsed_resume.get("experience", []) if isinstance(e, dict)]
    proj_entries = [p for p in parsed_resume.get("projects", []) if isinstance(p, dict)]
    summary = (parsed_resume.get("professional_summary") or "").strip()

    # 1. Missing Projects Section
    has_proj_signals = any(kw in text_lower for kw in ["project", "github.com", "built", "implemented", "deployed", "repository"])
    if not proj_entries and not has_proj_signals:
        detected.append(
            IssueDetail(
                issue_title="Missing Dedicated Projects Section",
                severity_level="High",
                ats_impact="High",
                explanation=(
                    "No structured Projects section was detected. ATS algorithms and technical recruiters "
                    "look for concrete project implementations to validate claimed skills."
                ),
                where_it_appears="Resume structure — no 'Projects' heading found",
                how_to_fix="Add a 'Projects' section featuring 2-3 substantial technical projects.",
                action_items=[
                    "Add a bold 'PROJECTS' heading after your Experience or Education section.",
                    "Include 2-3 key projects with title, tech stack, problem statement, and solution.",
                    "Embed links to live demos or GitHub source code repositories.",
                ],
                example_improvement=(
                    "PROJECTS\n"
                    "• AI Resume Scorer — Built full-stack ATS with FastAPI, Streamlit, and BERT.\n"
                    "  Engineered semantic embeddings reaching 94% matching accuracy against JD criteria."
                ),
            )
        )

    # 2. Missing Experience Section
    has_exp_signals = any(kw in text_lower for kw in ["experience", "employment", "internship", "worked at", "company", "role"])
    if not exp_entries and not has_exp_signals:
        detected.append(
            IssueDetail(
                issue_title="Missing Work Experience Section",
                severity_level="Critical",
                ats_impact="Critical",
                explanation=(
                    "No work history or internship section was detected. Experience provides vital timeline "
                    "and seniority context to the hiring manager."
                ),
                where_it_appears="Resume structure — absence of 'Experience' heading",
                how_to_fix="Add an 'Experience' or 'Internships' section detailing your past roles or contributions.",
                action_items=[
                    "Create an 'EXPERIENCE' heading with reverse-chronological order.",
                    "Include job title, company name, location, and dates (Month Year – Month Year).",
                    "Add 3-5 accomplishment-driven bullet points for each role.",
                ],
                example_improvement=(
                    "EXPERIENCE\n"
                    "Software Engineer Intern | Acme Corp | Jun 2025 – Present\n"
                    "• Developed RESTful microservices handling 100K+ daily API requests with 99.9% uptime.\n"
                    "• Reduced database query latency by 35% through Redis caching and query indexing."
                ),
            )
        )

    # 3. Missing Professional Summary / Objective
    if len(summary) < 25:
        detected.append(
            IssueDetail(
                issue_title="Missing or Weak Professional Summary",
                severity_level="Medium",
                ats_impact="Medium",
                explanation=(
                    "A crisp 2-3 line summary at the top anchors your candidacy and primes the ATS "
                    "with high-priority keywords."
                ),
                where_it_appears="Top header section below contact details",
                how_to_fix="Add a 2-3 sentence summary articulating your specialization, key technologies, and value proposition.",
                action_items=[
                    "State your primary professional title (e.g., 'Full-Stack Software Engineer').",
                    "Highlight 3-4 core technologies and your career impact.",
                    "Tailor target keywords to the job description.",
                ],
                example_improvement=(
                    "PROFESSIONAL SUMMARY\n"
                    "Full-Stack Software Engineer with 2+ years of experience designing scalable web applications "
                    "using Python, FastAPI, React, and AWS. Proven track record optimizing backend throughput and leading agile sprints."
                ),
            )
        )

    # 4. Lack of Quantifiable Metrics
    metric_matches = re.findall(r"\b\d+%\b|\$\d+|\b\d+\s*(?:users|clients|customers|requests)\b", resume_text, re.IGNORECASE)
    if len(metric_matches) < 3:
        detected.append(
            IssueDetail(
                issue_title="Insufficient Quantifiable Achievements",
                severity_level="High",
                ats_impact="High",
                explanation=(
                    "Bullet points are predominantly task-oriented rather than metric-driven. "
                    "ATS algorithms and recruiters heavily favor numbers, percentages, and dollar values."
                ),
                where_it_appears="Experience and Projects bullet points",
                how_to_fix="Use the Google 'X-Y-Z' formula: Accomplished [X], as measured by [Y], by doing [Z].",
                action_items=[
                    "Audit every bullet point and ask 'By how much?' or 'What was the result?'.",
                    "Add percentage improvements (e.g., 'accelerated build times by 40%').",
                    "Add scale metrics (e.g., 'servicing 50,000 active monthly users').",
                ],
                example_improvement=(
                    "Before: 'Responsible for backend database maintenance.'\n"
                    "After:  'Refactored PostgreSQL queries and added Redis caching, reducing API latency by 45% for 15,000 daily users.'"
                ),
            )
        )

    # 5. Weak Action Verbs
    if len(action_verbs) < 6:
        detected.append(
            IssueDetail(
                issue_title="Sparse Use of Strong Action Verbs",
                severity_level="Medium",
                ats_impact="Medium",
                explanation=(
                    "Bullet points start with weak phrases like 'Helped with', 'Worked on', or 'Assisted'. "
                    "Impactful resumes begin every bullet with an assertive verb in past or present tense."
                ),
                where_it_appears="Start of bullet points",
                how_to_fix="Replace passive openers with decisive verbs like 'Architected', 'Spearheaded', 'Optimized', or 'Engineered'.",
                action_items=[
                    "Eliminate 'Responsible for' and 'Assisted with' from the start of every sentence.",
                    "Use varied action verbs across leadership, engineering, and innovation categories.",
                ],
                example_improvement=(
                    "Replace 'Helped test the software' with 'Spearheaded automated regression testing pipeline using Pytest, boosting coverage to 92%'."
                ),
            )
        )

    # 6. Unvalidated Skills
    unvalidated = skill_validation.get("unvalidated_skills", [])
    if len(unvalidated) >= 3:
        sample_skills = ", ".join(unvalidated[:4])
        detected.append(
            IssueDetail(
                issue_title=f"Unvalidated Skills Listed ({len(unvalidated)} skills)",
                severity_level="Medium",
                ats_impact="High",
                explanation=(
                    f"Skills such as {sample_skills} are listed in your Skills section but do not appear "
                    "in any project description or work history bullet. ATS systems often down-rank uncorroborated skills."
                ),
                where_it_appears="Skills section vs Experience/Projects text",
                how_to_fix="Mention how and where you applied each skill in your project or work history bullet points.",
                action_items=[
                    f"Integrate references to {sample_skills} inside relevant project bullets.",
                    "Alternatively, prune skills you have not actively used in projects to maintain credibility.",
                ],
                example_improvement=(
                    f"Add a project bullet demonstrating practical usage: 'Developed reactive frontend interfaces using {unvalidated[0]} integrated with REST APIs.'"
                ),
            )
        )

    # 7. Contact Information Completeness
    contact = contact_info or {}
    missing_contacts = []
    if not contact.get("email"):
        missing_contacts.append("Email address")
    if not contact.get("phone"):
        missing_contacts.append("Phone number")
    if not contact.get("linkedin"):
        missing_contacts.append("LinkedIn profile")
    if not contact.get("github"):
        missing_contacts.append("GitHub / Portfolio link")

    if missing_contacts:
        detected.append(
            IssueDetail(
                issue_title=f"Missing Contact Links ({', '.join(missing_contacts)})",
                severity_level="Low",
                ats_impact="Medium",
                explanation="Incomplete contact or online profile links make recruiter outreach and portfolio verification difficult.",
                where_it_appears="Top contact header",
                how_to_fix="Include your professional email, phone number, LinkedIn URL, and GitHub portfolio.",
                action_items=[f"Add {c} to the top header line." for c in missing_contacts],
                example_improvement="San Francisco, CA | user@email.com | (555) 012-3456 | linkedin.com/in/alexdev | github.com/alexdev",
            )
        )

    return detected


def generate_issues_summary(detailed_feedback: List[IssueDetail]) -> List[str]:
    """Provide a high-level executive summary of diagnosed issues."""
    summary = []
    for issue in detailed_feedback:
        prefix = "🔴" if issue.severity_level.lower() in ("critical", "high") else "🟡" if issue.severity_level.lower() == "medium" else "🟢"
        summary.append(f"{prefix} {issue.issue_title}: {issue.how_to_fix}")
    return summary
