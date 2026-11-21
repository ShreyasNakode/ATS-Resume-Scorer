import io
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("ats_resume_scorer")


def generate_pdf_with_reportlab(analysis_data: Dict[str, Any]) -> bytes:
    """Fallback PDF generator using ReportLab when WeasyPrint system libraries are absent."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#4F46E5"),
        alignment=1,  # Center
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#6B7280"),
        alignment=1,
    )
    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#1F2937"),
        spaceBefore=10,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#374151"),
    )

    # Header
    story.append(Paragraph("🎯 ATS Resume Scorer Analysis Report", title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Evaluated via BERT Semantic Models, spaCy NLP & Scikit-Learn", subtitle_style))
    story.append(Spacer(1, 16))

    # Overall Score Card
    score = float(analysis_data.get("ATS_score", analysis_data.get("ats_score", 0.0)))
    interpretation = analysis_data.get("interpretation", "")
    score_color = "#10B981" if score >= 80 else "#F59E0B" if score >= 60 else "#EF4444"

    score_card_data = [
        [Paragraph(f"<font size=28 color='{score_color}'><b>{score:.0f} / 100</b></font>", title_style)],
        [Paragraph(f"<b>Overall ATS Compatibility</b><br/>{interpretation}", subtitle_style)],
    ]
    score_table = Table(score_card_data, colWidths=[540])
    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F9FAFB")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#E5E7EB")),
        ("PADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 16))

    # Component Scores Table
    story.append(Paragraph("📈 Score Breakdown by Dimension", section_heading))
    cs = analysis_data.get("component_scores", {})
    if hasattr(cs, "__dict__"):
        cs = cs.__dict__

    breakdown_data = [
        ["Dimension", "Score", "Max Possible", "Status"],
        ["Formatting & Structure", f"{cs.get('formatting', 0):.0f}", "20", "Optimal" if cs.get('formatting', 0) >= 15 else "Needs Work"],
        ["Keywords & Technical Skills", f"{cs.get('keywords', 0):.0f}", "25", "Optimal" if cs.get('keywords', 0) >= 18 else "Needs Work"],
        ["Content Quality & Action Verbs", f"{cs.get('content', 0):.0f}", "25", "Optimal" if cs.get('content', 0) >= 18 else "Needs Work"],
        ["BERT Skill Validation", f"{cs.get('skill_validation', 0):.0f}", "15", "Optimal" if cs.get('skill_validation', 0) >= 11 else "Needs Work"],
        ["ATS Parsing Compatibility", f"{cs.get('ats_compatibility', 0):.0f}", "15", "Optimal" if cs.get('ats_compatibility', 0) >= 12 else "Needs Work"],
    ]
    breakdown_table = Table(breakdown_data, colWidths=[200, 90, 110, 140])
    breakdown_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4F46E5")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (2, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(breakdown_table)
    story.append(Spacer(1, 16))

    # Strengths
    strengths = analysis_data.get("strengths", [])
    if strengths:
        story.append(Paragraph("✅ Key Strengths", section_heading))
        for s in strengths:
            story.append(Paragraph(f"• {s}", body_style))
        story.append(Spacer(1, 10))

    # Action Items / Detailed Feedback
    feedback = analysis_data.get("detailed_feedback", [])
    if feedback:
        story.append(Paragraph("🔧 High-Priority Action Items", section_heading))
        for item in feedback[:4]:
            title = item.get("issue_title") if isinstance(item, dict) else getattr(item, "issue_title", "")
            fix = item.get("how_to_fix") if isinstance(item, dict) else getattr(item, "how_to_fix", "")
            story.append(Paragraph(f"<b>• {title}</b>: {fix}", body_style))
            story.append(Spacer(1, 4))

    doc.build(story)
    return buffer.getvalue()


def generate_combined_pdf(html_docs: Dict[str, str], fallback_data: Optional[Dict[str, Any]] = None) -> bytes:
    """
    Generate PDF report. Uses WeasyPrint if available;
    seamlessly falls back to ReportLab to ensure zero errors on Windows or headless environments.
    """
    try:
        from weasyprint import HTML
        documents = []
        for name, html_str in html_docs.items():
            doc = HTML(string=html_str).render()
            documents.append(doc)

        first_doc = documents[0]
        for other_doc in documents[1:]:
            for page in other_doc.pages:
                first_doc.pages.append(page)

        return first_doc.write_pdf()
    except Exception as exc:
        logger.warning(f"WeasyPrint rendering unavailable ({exc}). Using ReportLab PDF engine.")
        data = fallback_data or {}
        return generate_pdf_with_reportlab(data)
