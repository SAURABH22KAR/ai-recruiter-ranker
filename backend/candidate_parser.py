"""
Normalize raw Redrob candidate data (from the challenge JSONL)
into the internal Candidate model.

The real schema uses:
  candidate_id, profile{}, career_history[], education[], skills[],
  certifications[], languages[], redrob_signals{}
"""
from typing import Any
from models import Candidate, WorkExperience, Education, BehavioralSignals


def _safe_float(val: Any, default: float = 0.0) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _parse_experience(career_history: list[dict]) -> tuple[list[WorkExperience], float]:
    exps = []
    total_months = 0
    for item in career_history:
        if not isinstance(item, dict):
            continue
        title = item.get("title") or ""
        company = item.get("company") or ""
        description = item.get("description") or ""
        duration_months = int(_safe_float(item.get("duration_months", 12)))
        skills_used = []  # real schema doesn't have skills_used per role

        exps.append(WorkExperience(
            title=str(title),
            company=str(company),
            duration_months=duration_months,
            description=str(description)[:1200],
            skills_used=skills_used,
        ))
        total_months += duration_months

    return exps, total_months / 12.0


def _parse_education(edu_list: list[dict]) -> list[Education]:
    result = []
    for item in edu_list:
        if not isinstance(item, dict):
            continue
        result.append(Education(
            degree=str(item.get("degree") or ""),
            field=str(item.get("field_of_study") or ""),
            institution=str(item.get("institution") or ""),
            year=item.get("end_year"),
        ))
    return result


def _parse_behavioral(signals: dict | None) -> BehavioralSignals | None:
    if not signals:
        return None

    # Normalize github score: -1 means no GitHub → treat as 0
    github = signals.get("github_activity_score", -1)
    github_norm = max(0.0, github) / 100.0

    # Activity recency score: days since last_active
    from datetime import datetime, date
    last_active = signals.get("last_active_date", "")
    try:
        d = datetime.strptime(last_active, "%Y-%m-%d").date()
        days_inactive = (date.today() - d).days
        activity = max(0.0, 1.0 - days_inactive / 180)
    except Exception:
        activity = 0.5

    # profile completeness: 0-100 → 0-1
    completeness = min(1.0, _safe_float(signals.get("profile_completeness_score", 50)) / 100)

    # Application quality proxy: interview_completion_rate × offer_acceptance_rate
    icr = _safe_float(signals.get("interview_completion_rate", 0.7))
    oar = _safe_float(signals.get("offer_acceptance_rate", 0))
    quality = icr * max(0, oar) if oar >= 0 else icr * 0.65

    rr = min(1.0, _safe_float(signals.get("recruiter_response_rate", 0.5)))

    return BehavioralSignals(
        platform_activity_score=round(min(1.0, 0.4 * activity + 0.3 * github_norm + 0.3 * completeness), 3),
        endorsements_count=int(_safe_float(signals.get("endorsements_received", 0))),
        profile_completeness=completeness,
        application_quality=round(min(1.0, quality), 3),
        response_rate=rr,
    )


def parse_candidate(raw: dict[str, Any]) -> Candidate:
    """Normalize a Redrob-schema candidate dict into the internal Candidate model."""
    cid = str(raw.get("candidate_id") or "unknown")
    profile = raw.get("profile", {}) or {}
    name = str(profile.get("anonymized_name") or "Unknown")
    summary = str(profile.get("summary") or profile.get("headline") or "")

    # Skills: extract name strings (for embedding) and proficiency
    skills_raw = raw.get("skills", []) or []
    skills = [sk["name"] for sk in skills_raw if isinstance(sk, dict) and sk.get("name")]

    # Career history
    career_raw = raw.get("career_history", []) or []
    experience, total_years = _parse_experience(career_raw)

    # Use profile years_of_experience if available
    profile_years = _safe_float(profile.get("years_of_experience", 0))
    if profile_years > 0:
        total_years = profile_years

    # Education
    edu_raw = raw.get("education", []) or []
    education = _parse_education(edu_raw)

    # Behavioral signals
    signals_raw = raw.get("redrob_signals")
    behavioral = _parse_behavioral(signals_raw)

    return Candidate(
        id=cid,
        name=name,
        summary=summary,
        skills=skills,
        experience=experience,
        education=education,
        total_experience_years=round(total_years, 1),
        behavioral_signals=behavioral,
        raw_data=raw,
    )


def parse_candidates(raw_list: list[dict[str, Any]]) -> list[Candidate]:
    return [parse_candidate(r) for r in raw_list]
