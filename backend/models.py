from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class WorkExperience(BaseModel):
    title: str = ""
    company: str = ""
    duration_months: int = 0
    description: str = ""
    skills_used: List[str] = Field(default_factory=list)


class Education(BaseModel):
    degree: str = ""
    field: str = ""
    institution: str = ""
    year: Optional[int] = None


class BehavioralSignals(BaseModel):
    platform_activity_score: float = 0.0   # 0-1 normalized
    endorsements_count: int = 0
    profile_completeness: float = 0.0      # 0-1
    application_quality: float = 0.0       # 0-1
    response_rate: float = 0.0             # 0-1


class Candidate(BaseModel):
    id: str
    name: str
    summary: str = ""
    skills: List[str] = Field(default_factory=list)
    experience: List[WorkExperience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    total_experience_years: float = 0.0
    behavioral_signals: Optional[BehavioralSignals] = None
    raw_data: Dict[str, Any] = Field(default_factory=dict)


class JobDescription(BaseModel):
    id: str = "jd_001"
    title: str
    description: str
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    min_experience_years: float = 0.0
    education_requirement: str = ""
    domain: str = ""
    responsibilities: List[str] = Field(default_factory=list)


class ScoreBreakdown(BaseModel):
    skill_match: float = 0.0
    experience_relevance: float = 0.0
    career_trajectory: float = 0.0
    education_fit: float = 0.0
    behavioral_signals: float = 0.0
    total: float = 0.0


class RankedCandidate(BaseModel):
    rank: int
    candidate: Candidate
    scores: ScoreBreakdown
    llm_reasoning: str = ""
    key_strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    recommendation: str = ""


class RankRequest(BaseModel):
    job_description: str
    candidates: List[Dict[str, Any]]


class RankResponse(BaseModel):
    job_analysis: Dict[str, Any]
    ranked_candidates: List[RankedCandidate]
    total_candidates: int
    shortlist_cutoff: int
