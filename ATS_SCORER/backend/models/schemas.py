from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ComponentScores(BaseModel):
    formatting: float = Field(..., description="Formatting score (0-20)")
    keywords: float = Field(..., description="Keywords & skills score (0-25)")
    content: float = Field(..., description="Content quality score (0-25)")
    skill_validation: float = Field(..., description="Skill validation score (0-15)")
    ats_compatibility: float = Field(..., description="ATS compatibility score (0-15)")


class JDComparison(BaseModel):
    match_percentage: float = Field(..., description="Weighted match score (0-100%)")
    semantic_similarity: float = Field(..., description="BERT cosine semantic similarity (0-1)")
    matched_keywords: List[str] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)
    skills_gap: List[str] = Field(default_factory=list)


class SkillValidationItem(BaseModel):
    skill: str
    projects: List[str] = Field(default_factory=list)
    similarity: float = 0.0


class SkillValidationDetails(BaseModel):
    validated: List[Dict[str, Any]] = Field(default_factory=list)
    unvalidated: List[str] = Field(default_factory=list)
    total: int = 0
    validated_count: int = 0
    validation_pct: float = 0.0


class IssueDetail(BaseModel):
    issue_title: str
    severity_level: str  # "Critical", "High", "Medium", "Low"
    ats_impact: str      # "High", "Medium", "Low"
    explanation: str
    where_it_appears: str
    how_to_fix: str
    action_items: List[str] = Field(default_factory=list)
    example_improvement: str = ""


class RecommendationItem(BaseModel):
    title: str
    description: str
    priority: str        # "critical", "high", "medium", "low"
    impact_score: float
    category: str
    action_items: List[str] = Field(default_factory=list)


class AnalysisResponse(BaseModel):
    # Primary API fields
    ATS_score: float
    component_scores: ComponentScores
    issues_summary: List[str] = Field(default_factory=list)
    detailed_feedback: List[IssueDetail] = Field(default_factory=list)
    jd_match_analysis: Optional[JDComparison] = None
    skill_validation_details: Optional[SkillValidationDetails] = None
    recommendations: List[RecommendationItem] = Field(default_factory=list)

    # Backward and display compatibility
    ats_score: float
    keyword_match: float = 0.0
    missing_keywords: List[str] = Field(default_factory=list)
    matched_keywords: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    critical_issues: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    jd_comparison: Optional[JDComparison] = None
    warnings: List[str] = Field(default_factory=list)
    interpretation: str = ""


class HistoryItem(BaseModel):
    id: str
    filename: str
    ats_score: float
    keyword_match: float = 0.0
    missing_keywords: List[str] = Field(default_factory=list)
    created_at: str
    analysis_result: Dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str
    nlp_loaded: bool
    embedder_loaded: bool
    bert_model: str
    clerk_auth_active: bool
