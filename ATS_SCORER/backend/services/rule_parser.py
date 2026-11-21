import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

from backend.services.spacy_service import extract_action_verbs, extract_keywords_and_phrases

logger = logging.getLogger("ats_resume_scorer")

# Curated Technical & Domain Skills for Heuristic Extraction
COMMON_SKILLS_TAXONOMY = {
    "python", "java", "c++", "c#", "c", "javascript", "typescript", "ruby", "php", "swift",
    "kotlin", "go", "golang", "rust", "scala", "r", "sql", "nosql", "html", "css", "sass",
    "react", "react.js", "angular", "vue", "vue.js", "next.js", "node.js", "express",
    "fastapi", "flask", "django", "spring boot", "asp.net", "graphql", "rest api", "grpc",
    "docker", "kubernetes", "aws", "azure", "gcp", "terraform", "ansible", "jenkins", "gitlab ci",
    "github actions", "linux", "git", "ci/cd", "microservices", "serverless", "kafka", "rabbitmq",
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "sqlite", "dynamodb", "cassandra",
    "machine learning", "deep learning", "nlp", "computer vision", "tensorflow", "pytorch",
    "keras", "scikit-learn", "pandas", "numpy", "opencv", "hugging face", "bert", "llm",
    "transformers", "data analysis", "data engineering", "power bi", "tableau", "spark",
    "agile", "scrum", "jira", "unit testing", "pytest", "jest", "selenium", "system design",
}

EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
PHONE_PATTERN = r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
LINKEDIN_PATTERN = r"(?:https?:\/\/)?(?:www\.)?linkedin\.com\/in\/[A-Za-z0-9_-]+"
GITHUB_PATTERN = r"(?:https?:\/\/)?(?:www\.)?github\.com\/[A-Za-z0-9_-]+"


def extract_skills_heuristic(text: str) -> List[str]:
    """Extract known technical and soft skills from resume text."""
    text_lower = text.lower()
    matched = set()
    for skill in COMMON_SKILLS_TAXONOMY:
        pattern = rf"\b{re.escape(skill)}\b"
        if re.search(pattern, text_lower):
            matched.add(skill.title() if len(skill) > 3 and not skill.isupper() else skill.upper() if len(skill) <= 3 else skill)
    return sorted(list(matched))


def parse_resume_local(text: str) -> Dict[str, Any]:
    """
    High-fidelity offline resume extractor using regex and structural parsing.
    Requires no external API keys.
    """
    # 1. Contact Information
    email_match = re.search(EMAIL_PATTERN, text)
    phone_match = re.search(PHONE_PATTERN, text)
    linkedin_match = re.search(LINKEDIN_PATTERN, text, re.IGNORECASE)
    github_match = re.search(GITHUB_PATTERN, text, re.IGNORECASE)

    email = email_match.group(0) if email_match else None
    phone = phone_match.group(0) if phone_match else None
    linkedin = linkedin_match.group(0) if linkedin_match else None
    github = github_match.group(0) if github_match else None

    # 2. Extract Candidate Name (usually top lines)
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    candidate_name = lines[0] if lines else "Candidate"
    if candidate_name and len(candidate_name.split()) > 4:
        candidate_name = "Candidate"

    # 3. Section Boundary Splitting
    sections: Dict[str, List[str]] = {
        "summary": [],
        "experience": [],
        "projects": [],
        "education": [],
        "skills": [],
        "certifications": [],
    }

    current_section = "summary"
    section_patterns = {
        "summary": r"\b(summary|professional summary|profile|about me|objective)\b",
        "experience": r"\b(experience|work experience|employment history|work history)\b",
        "projects": r"\b(projects|personal projects|technical projects|academic projects)\b",
        "education": r"\b(education|academic background|qualifications)\b",
        "skills": r"\b(skills|technical skills|core competencies|technologies)\b",
        "certifications": r"\b(certifications|certificates|licenses)\b",
    }

    for line in lines:
        lower_line = line.lower().strip()
        matched_section = None
        for sec_name, sec_regex in section_patterns.items():
            if re.match(f"^{sec_regex}", lower_line) or re.match(f"^#+\\s*{sec_regex}", lower_line):
                matched_section = sec_name
                break

        if matched_section:
            current_section = matched_section
        else:
            sections[current_section].append(line)

    summary_text = " ".join(sections["summary"][:6])
    skills_found = extract_skills_heuristic(text)
    action_verbs = extract_action_verbs(text)
    keywords = extract_keywords_and_phrases(text)

    # 4. Parse Project Entries
    projects = []
    proj_lines = sections["projects"]
    current_proj = {"title": "", "description": "", "technologies": []}
    for line in proj_lines:
        if line.startswith(("-", "•", "*")):
            current_proj["description"] += " " + line.lstrip("-•* ")
        else:
            if current_proj["title"] and current_proj["description"]:
                current_proj["technologies"] = extract_skills_heuristic(current_proj["title"] + " " + current_proj["description"])
                projects.append(current_proj)
                current_proj = {"title": line, "description": "", "technologies": []}
            else:
                current_proj["title"] = line

    if current_proj["title"]:
        current_proj["technologies"] = extract_skills_heuristic(current_proj["title"] + " " + current_proj["description"])
        projects.append(current_proj)

    # 5. Parse Experience Entries
    experience = []
    exp_lines = sections["experience"]
    current_exp = {"job_title": "", "company": "", "duration_months": 12, "description": ""}
    for line in exp_lines:
        if line.startswith(("-", "•", "*")):
            current_exp["description"] += " " + line.lstrip("-•* ")
        else:
            if current_exp["job_title"] and current_exp["description"]:
                experience.append(current_exp)
                current_exp = {"job_title": line, "company": "", "duration_months": 12, "description": ""}
            elif not current_exp["job_title"]:
                current_exp["job_title"] = line
            else:
                current_exp["company"] = line

    if current_exp["job_title"]:
        experience.append(current_exp)

    # 6. Parse Education
    education = []
    for line in sections["education"]:
        if any(deg in line.lower() for deg in ["bachelor", "master", "phd", "b.tech", "b.s.", "m.s.", "degree"]):
            education.append({"degree": line, "institution": "", "year": ""})

    return {
        "name": candidate_name,
        "email": email,
        "phone": phone,
        "linkedin": linkedin,
        "github": github,
        "professional_summary": summary_text,
        "skills": skills_found if skills_found else ["Python", "Problem Solving", "Git"],
        "experience": experience,
        "education": education,
        "certifications": sections["certifications"][:5],
        "projects": projects,
        "action_verbs": action_verbs,
        "keywords": keywords if keywords else skills_found,
    }


def parse_job_description_local(text: str) -> Dict[str, Any]:
    """Parse job description text into required skills, preferred skills, and keywords."""
    skills = extract_skills_heuristic(text)
    keywords = extract_keywords_and_phrases(text)

    # Identify lines with required vs preferred
    lines = text.split("\n")
    required = []
    preferred = []
    is_preferred = False

    for line in lines:
        lower = line.lower()
        if "preferred" in lower or "nice to have" in lower or "bonus" in lower:
            is_preferred = True
        elif "required" in lower or "qualifications" in lower or "requirements" in lower:
            is_preferred = False

        line_skills = extract_skills_heuristic(line)
        if is_preferred:
            preferred.extend(line_skills)
        else:
            required.extend(line_skills)

    if not required and skills:
        required = skills[:max(3, len(skills) // 2)]
        preferred = skills[len(required):]

    return {
        "job_title": lines[0][:60] if lines else "Target Position",
        "required_skills": sorted(list(set(required))),
        "preferred_skills": sorted(list(set(preferred))),
        "experience_required": "2+ years",
        "education_required": "Bachelor's degree or equivalent experience",
        "key_responsibilities": [l.strip("-• ") for l in lines if l.startswith(("-", "•"))][:6],
        "keywords": sorted(list(set(keywords + skills))),
    }


def parse_resume_hybrid(text: str) -> Dict[str, Any]:
    """
    Parse resume with Groq LLM if configured; automatically fall back to local rule-based parser.
    """
    groq_api_key = os.getenv("GROQ_API_KEY", "")
    if groq_api_key:
        try:
            from groq import Groq
            client = Groq(api_key=groq_api_key)
            prompt = f"Extract resume details as strict JSON:\n{text[:4000]}"
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a resume parser. Output ONLY valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
            )
            content = resp.choices[0].message.content.strip()
            if content.startswith("```"):
                content = re.sub(r"^```(?:json)?\n?", "", content)
                content = re.sub(r"\n?```$", "", content)
            parsed = json.loads(content)
            # Ensure required keys exist
            defaults = {
                "name": "Candidate", "email": None, "phone": None,
                "linkedin": None, "github": None, "professional_summary": "",
                "skills": [], "experience": [], "education": [],
                "certifications": [], "projects": [], "action_verbs": [], "keywords": [],
            }
            for k, v in defaults.items():
                parsed.setdefault(k, v)
            return parsed
        except Exception as exc:
            logger.warning(f"Groq parsing failed: {exc}. Falling back to local parser.")

    return parse_resume_local(text)


def parse_job_description_hybrid(text: str) -> Dict[str, Any]:
    """Parse JD using Groq LLM with fallback to local rule-based extractor."""
    groq_api_key = os.getenv("GROQ_API_KEY", "")
    if groq_api_key:
        try:
            from groq import Groq
            client = Groq(api_key=groq_api_key)
            prompt = f"Extract job description details as strict JSON with required_skills, preferred_skills, keywords:\n{text[:4000]}"
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a job description parser. Output ONLY valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
            )
            content = resp.choices[0].message.content.strip()
            if content.startswith("```"):
                content = re.sub(r"^```(?:json)?\n?", "", content)
                content = re.sub(r"\n?```$", "", content)
            parsed = json.loads(content)
            defaults = {
                "job_title": "Target Role",
                "required_skills": [],
                "preferred_skills": [],
                "key_responsibilities": [],
                "keywords": [],
            }
            for k, v in defaults.items():
                parsed.setdefault(k, v)
            return parsed
        except Exception as exc:
            logger.warning(f"Groq JD parsing failed: {exc}. Falling back to local parser.")

    return parse_job_description_local(text)
