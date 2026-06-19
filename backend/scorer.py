"""
Multi-dimensional candidate scoring.

Each dimension returns a score in [0, 1].
"""
import numpy as np
from models import Candidate, JobDescription, ScoreBreakdown, BehavioralSignals
from embeddings import embed, max_pool_sim, text_similarity
from config import SCORING_WEIGHTS


# ── 1. Skill Match ──────────────────────────────────────────────────────────

def score_skill_match(candidate: Candidate, jd: JobDescription) -> float:
    """
    Semantic skill matching: compare candidate skills against required + preferred.
    Required skills count 2×, preferred skills count 1×.
    """
    if not candidate.skills:
        return 0.0

    required = jd.required_skills
    preferred = jd.preferred_skills

    if not required and not preferred:
        return 0.5  # No skills specified → neutral

    cand_embs = embed(candidate.skills)

    scores = []
    if required:
        req_embs = embed(required)
        scores.append((max_pool_sim(req_embs, cand_embs), 2.0))  # weight 2×

    if preferred:
        pref_embs = embed(preferred)
        scores.append((max_pool_sim(pref_embs, cand_embs), 1.0))

    total_weight = sum(w for _, w in scores)
    weighted = sum(s * w for s, w in scores) / total_weight

    # Normalize: typical good match ~0.6–0.7 cosine → map to [0,1]
    normalized = min(1.0, weighted / 0.65)
    return round(float(normalized), 4)


# ── 2. Experience Relevance ──────────────────────────────────────────────────

def score_experience_relevance(candidate: Candidate, jd: JobDescription) -> float:
    """
    Combines:
    - Years of experience vs requirement
    - Semantic relevance of past roles to the JD
    """
    # Years component (50%)
    required_years = jd.min_experience_years or 0.0
    cand_years = candidate.total_experience_years or 0.0

    if required_years == 0:
        years_score = min(1.0, cand_years / 5.0)  # more exp = better, cap at 5yr
    elif cand_years >= required_years:
        # Slightly reward exceeding, but diminishing returns
        years_score = min(1.0, 0.85 + 0.05 * min(3, cand_years - required_years))
    else:
        years_score = cand_years / required_years * 0.85  # penalty for being short

    # Semantic relevance of experience descriptions (50%)
    if not candidate.experience:
        relevance_score = 0.2
    else:
        jd_context = f"{jd.title}. {jd.domain}. {' '.join(jd.responsibilities[:5])}"
        exp_texts = [
            f"{e.title} at {e.company}: {e.description}"
            for e in candidate.experience
            if e.description or e.title
        ]
        if not exp_texts:
            relevance_score = 0.3
        else:
            sims = [text_similarity(jd_context, t) for t in exp_texts[:4]]
            # Weight recent experience higher
            weights = np.array([1.0 / (i + 1) for i in range(len(sims))])
            weights /= weights.sum()
            relevance_score = float(np.dot(sims, weights))
            relevance_score = min(1.0, relevance_score / 0.5)  # normalize

    return round(float(0.5 * years_score + 0.5 * relevance_score), 4)


# ── 3. Career Trajectory ────────────────────────────────────────────────────

def score_career_trajectory(candidate: Candidate, jd: JobDescription) -> float:
    """
    Signals: progression in seniority, tenure stability, domain consistency,
    and candidate summary alignment with the target role.
    """
    if not candidate.experience:
        return 0.3

    # Check for progression keywords in titles
    seniority_keywords = {
        "intern": 0, "junior": 1, "associate": 1, "mid": 2, "senior": 3,
        "lead": 4, "staff": 4, "principal": 5, "director": 5, "vp": 6, "head": 5
    }
    levels = []
    for exp in candidate.experience:
        title_lower = exp.title.lower()
        for kw, lvl in seniority_keywords.items():
            if kw in title_lower:
                levels.append(lvl)
                break

    progression_score = 0.5  # default neutral
    if len(levels) >= 2:
        # Is the career generally going upward?
        diffs = [levels[i] - levels[i - 1] for i in range(1, len(levels))]
        progression_score = 0.5 + 0.1 * min(2, sum(1 for d in diffs if d > 0))

    # Tenure stability: penalize lots of very short stints (<6 months)
    tenures = [e.duration_months for e in candidate.experience if e.duration_months > 0]
    if tenures:
        short_stints = sum(1 for t in tenures if t < 6)
        stability_score = max(0.3, 1.0 - 0.15 * short_stints)
    else:
        stability_score = 0.5

    # Summary alignment with role
    summary_score = 0.4
    if candidate.summary:
        jd_text = f"{jd.title} {jd.domain} {' '.join(jd.core_competencies if hasattr(jd, 'core_competencies') else [])}"
        summary_score = min(1.0, text_similarity(candidate.summary, jd_text) / 0.45)

    final = 0.35 * progression_score + 0.25 * stability_score + 0.40 * summary_score
    return round(float(min(1.0, final)), 4)


# ── 4. Education Fit ─────────────────────────────────────────────────────────

def score_education_fit(candidate: Candidate, jd: JobDescription) -> float:
    """Semantic match between education and what the JD asks for."""
    if not jd.education_requirement:
        return 0.7  # No requirement → not a differentiator

    if not candidate.education:
        return 0.2

    edu_text = " ".join(
        f"{e.degree} {e.field} {e.institution}" for e in candidate.education
    )
    score = text_similarity(edu_text, jd.education_requirement)
    return round(min(1.0, score / 0.55), 4)


# ── 5. Behavioral Signals ────────────────────────────────────────────────────

def score_behavioral_signals(candidate: Candidate) -> float:
    """
    Platform/behavioral signals: activity, endorsements, profile completeness.
    Falls back gracefully if no behavioral data.
    """
    bs: BehavioralSignals | None = candidate.behavioral_signals

    if bs is None:
        # No behavioral data — use profile completeness proxy
        has_summary = 1.0 if candidate.summary else 0.0
        has_exp = 1.0 if candidate.experience else 0.0
        has_edu = 1.0 if candidate.education else 0.0
        has_skills = min(1.0, len(candidate.skills) / 8)
        return round(float(0.25 * has_summary + 0.35 * has_exp + 0.15 * has_edu + 0.25 * has_skills), 4)

    # Endorsements: log-scale, normalize at 50 endorsements
    endorsement_score = min(1.0, np.log1p(bs.endorsements_count) / np.log1p(50))

    composite = (
        0.25 * bs.platform_activity_score
        + 0.25 * endorsement_score
        + 0.20 * bs.profile_completeness
        + 0.20 * bs.application_quality
        + 0.10 * bs.response_rate
    )
    return round(float(min(1.0, composite)), 4)


# ── Final Scorer ─────────────────────────────────────────────────────────────

def compute_scores(candidate: Candidate, jd: JobDescription) -> ScoreBreakdown:
    skill = score_skill_match(candidate, jd)
    exp = score_experience_relevance(candidate, jd)
    traj = score_career_trajectory(candidate, jd)
    edu = score_education_fit(candidate, jd)
    beh = score_behavioral_signals(candidate)

    w = SCORING_WEIGHTS
    total = (
        w["skill_match"] * skill
        + w["experience_relevance"] * exp
        + w["career_trajectory"] * traj
        + w["education_fit"] * edu
        + w["behavioral_signals"] * beh
    )

    return ScoreBreakdown(
        skill_match=round(skill, 3),
        experience_relevance=round(exp, 3),
        career_trajectory=round(traj, 3),
        education_fit=round(edu, 3),
        behavioral_signals=round(beh, 3),
        total=round(total, 3),
    )
