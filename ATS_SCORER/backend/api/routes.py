import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import Response

from backend.api.auth import get_current_user
from backend.core.config import SENTENCE_TRANSFORMER_MODEL
from backend.database.db import delete_analysis, get_user_history, save_analysis
from backend.models.schemas import (
    AnalysisResponse,
    ComponentScores,
    HealthResponse,
    HistoryItem,
    JDComparison,
    SkillValidationDetails,
)
from backend.services.pdf_export import generate_combined_pdf
from backend.services.report_generator import generate_html_reports
from backend.services.resume_analyzer import analyze_full_resume
from backend.services.resume_parser import parse_resume_file

logger = logging.getLogger("ats_resume_scorer")
router = APIRouter(prefix="/api/v1", tags=["Analysis"])


@router.post("/analyze-resume", response_model=AnalysisResponse)
async def analyze_resume(
    request: Request,
    resume: UploadFile = File(..., description="Resume file (PDF or DOCX, max 10MB)"),
    job_description: str = Form("", description="Target Job Description text (optional)"),
    user_id: str = Depends(get_current_user),
):
    """
    Primary ATS scoring endpoint: parses resume, calculates BERT semantic similarity,
    evaluates formatting/keywords/content/compatibility, and returns comprehensive feedback.
    """
    nlp = getattr(request.app.state, "nlp", None)
    embedder = getattr(request.app.state, "embedder", None)

    # 1. Parse Document (PyPDF2 / python-docx)
    try:
        file_bytes = await resume.read()
        filename = resume.filename or "resume.pdf"
        resume_text, metadata = parse_resume_file(file_bytes, filename)
        logger.info(f"Successfully parsed '{filename}': {metadata.get('text_length', 0)} characters extracted.")
    except Exception as exc:
        logger.error(f"File parsing error for '{resume.filename}': {exc}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not read or parse resume file: {exc}",
        )

    # 2. Run Comprehensive Multi-Model Analysis Pipeline
    try:
        analysis_result = analyze_full_resume(
            resume_text=resume_text,
            nlp=nlp,
            embedder=embedder,
            job_description=job_description,
        )
    except Exception as exc:
        logger.error(f"Analysis pipeline error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis pipeline failed: {exc}",
        )

    # 3. Format Response Objects
    jd_res = analysis_result.get("jd_match_analysis")
    jd_comparison_obj = None
    if jd_res:
        jd_comparison_obj = JDComparison(
            match_percentage=jd_res.get("match_percentage", 0.0),
            semantic_similarity=jd_res.get("semantic_similarity", 0.0),
            matched_keywords=jd_res.get("matched_keywords", [])[:25],
            missing_keywords=jd_res.get("missing_keywords", [])[:20],
            skills_gap=jd_res.get("skills_gap", [])[:15],
        )

    svd = analysis_result.get("skill_validation_details") or {}
    skill_val_obj = SkillValidationDetails(
        validated=svd.get("validated", []),
        unvalidated=svd.get("unvalidated", []),
        total=svd.get("total", 0),
        validated_count=svd.get("validated_count", 0),
        validation_pct=svd.get("validation_pct", 0.0),
    )

    response = AnalysisResponse(
        ATS_score=analysis_result["ATS_score"],
        component_scores=ComponentScores(**analysis_result["component_scores"]),
        issues_summary=analysis_result.get("issues_summary", []),
        detailed_feedback=analysis_result.get("detailed_feedback", []),
        jd_match_analysis=jd_comparison_obj,
        skill_validation_details=skill_val_obj,
        recommendations=analysis_result.get("recommendations", []),
        ats_score=analysis_result["ats_score"],
        keyword_match=jd_comparison_obj.match_percentage if jd_comparison_obj else 0.0,
        missing_keywords=analysis_result.get("missing_keywords", []),
        matched_keywords=analysis_result.get("matched_keywords", []),
        suggestions=analysis_result.get("suggestions", []),
        strengths=analysis_result.get("strengths", []),
        critical_issues=analysis_result.get("critical_issues", []),
        skills=analysis_result.get("skills", []),
        jd_comparison=jd_comparison_obj,
        interpretation=analysis_result.get("interpretation", ""),
    )

    # 4. Save to User History asynchronously (non-blocking)
    try:
        await save_analysis(user_id=user_id, filename=filename, analysis_result=analysis_result)
    except Exception as exc:
        logger.warning(f"History persistence warning (non-fatal): {exc}")

    return response


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request):
    """Health check verifying model states and service readiness."""
    nlp = getattr(request.app.state, "nlp", None)
    embedder = getattr(request.app.state, "embedder", None)
    return HealthResponse(
        status="healthy",
        nlp_loaded=nlp is not None,
        embedder_loaded=embedder is not None,
        bert_model=SENTENCE_TRANSFORMER_MODEL,
        clerk_auth_active=True,
    )


@router.get("/history", response_model=List[HistoryItem])
async def get_history(user_id: str = Depends(get_current_user)):
    """Fetch all saved past resume analyses for the authenticated Clerk user."""
    try:
        records = await get_user_history(user_id)
        return [
            HistoryItem(
                id=r["id"],
                filename=r["filename"],
                ats_score=r["ats_score"],
                keyword_match=r.get("keyword_match", 0.0),
                missing_keywords=r.get("missing_keywords", []),
                created_at=r["created_at"],
                analysis_result=r.get("analysis_result", {}),
            )
            for r in records
        ]
    except Exception as exc:
        logger.error(f"Failed to fetch user history: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not load history: {exc}",
        )


@router.delete("/history/{analysis_id}")
async def delete_history(analysis_id: str, user_id: str = Depends(get_current_user)):
    """Delete a past analysis entry owned by the user."""
    success = await delete_analysis(analysis_id, user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis record not found.")
    return {"status": "deleted", "id": analysis_id}


@router.post("/generate-pdf")
async def generate_pdf_report(
    data: AnalysisResponse,
    user_id: str = Depends(get_current_user),
):
    """Generate and return an ATS evaluation report in PDF format."""
    try:
        raw_data = data.model_dump()
        html_docs = generate_html_reports(raw_data)
        pdf_bytes = generate_combined_pdf(html_docs, fallback_data=raw_data)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=ATS_Evaluation_Report.pdf"},
        )
    except Exception as exc:
        logger.error(f"Failed to generate PDF: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF generation failed: {exc}",
        )


@router.get("/history/{analysis_id}/pdf")
async def generate_history_pdf_report(
    analysis_id: str,
    user_id: str = Depends(get_current_user),
):
    """Generate PDF for a historic analysis record."""
    records = await get_user_history(user_id)
    match = next((r for r in records if r["id"] == analysis_id), None)
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="History record not found.")

    analysis_data = match.get("analysis_result", {})
    try:
        html_docs = generate_html_reports(analysis_data)
        pdf_bytes = generate_combined_pdf(html_docs, fallback_data=analysis_data)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=ATS_Report_{analysis_id}.pdf"},
        )
    except Exception as exc:
        logger.error(f"History PDF generation failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF generation failed: {exc}",
        )
