#!/usr/bin/env python3
"""
Redrob Hackathon — Offline Candidate Ranker
Senior AI Engineer @ Redrob AI (Series A, Pune/Noida)

Usage:
  python rank.py --candidates ./candidates.jsonl --out ./submission.csv

Runs fully offline (no network). All scoring is local.
Produces exactly 100 rows in submission format.
"""
# Requires Python >= 3.9 (uses list[str] generic type hint)

import argparse
import csv
import json
import math
import re
import sys
from datetime import datetime, date
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# JD-derived constants  (hardcoded from the actual job description)
# ─────────────────────────────────────────────────────────────────────────────

# "Things you absolutely need" from JD — top-weighted
CRITICAL_JD_SKILLS = {
    "sentence-transformers", "sentence transformers", "embeddings", "dense retrieval",
    "faiss", "pinecone", "weaviate", "qdrant", "milvus", "opensearch", "elasticsearch",
    "vector database", "vector db", "vector search", "hybrid search", "hybrid retrieval",
    "semantic search", "ndcg", "mrr", "map", "evaluation framework", "offline evaluation",
    "learning to rank", "ltr", "information retrieval", "bm25", "ranking", "search ranking",
    "reranking", "re-ranking",
}

# Tier-1 AI/ML skills directly relevant to this role
CORE_AI_SKILLS = {
    # Embeddings & retrieval
    "sentence-transformers", "sentence transformers", "embeddings", "dense retrieval",
    "semantic search", "bge", "e5", "openai embeddings", "text embeddings",
    # Vector DBs / hybrid search
    "pinecone", "weaviate", "qdrant", "milvus", "faiss", "opensearch",
    "elasticsearch", "vector database", "vector db", "vector search",
    "hybrid search", "hybrid retrieval", "ann", "hnsw",
    # Ranking & Retrieval
    "ranking", "search ranking", "learning to rank", "ltr", "bm25",
    "information retrieval", "recommendation", "recommender", "reranking",
    "re-ranking", "colbert", "cross-encoder", "bi-encoder",
    # Evaluation
    "ndcg", "mrr", "map", "precision@k", "recall@k", "a/b testing",
    "ab testing", "a/b test", "evaluation framework", "offline evaluation",
    # LLMs / fine-tuning
    "llm", "large language model", "fine-tuning", "fine tuning", "lora",
    "qlora", "peft", "rag", "retrieval augmented", "instruction tuning",
    "transformers", "bert", "gpt", "llama", "mistral",
    # ML fundamentals
    "pytorch", "tensorflow", "scikit-learn", "sklearn", "xgboost", "lightgbm",
    "nlp", "natural language processing", "machine learning", "deep learning",
    "neural network", "gradient boosting",
    # MLOps
    "mlflow", "kubeflow", "feature store", "model serving", "triton",
    "torchserve", "onnx", "quantization", "distillation",
    # Data infra that's adjacent
    "spark", "kafka", "airflow", "dbt",
}

# Skills that are nice-to-have (lower weight)
NICE_TO_HAVE_SKILLS = {
    "python", "sql", "docker", "kubernetes", "git", "aws", "gcp", "azure",
    "flask", "fastapi", "redis", "postgresql", "mongodb", "hadoop",
    "pyspark", "pandas", "numpy", "jupyter", "databricks",
    "weights & biases", "wandb", "bentoml",
}

# Signals in career descriptions that indicate production ML/AI work
PRODUCTION_SIGNALS = {
    "production", "deployed", "deployment", "serving", "inference",
    "real-time", "real time", "at scale", "million", "billion", "qps",
    "latency", "throughput", "a/b test", "a/b testing", "online evaluation",
    "experiment", "model monitoring", "feature store", "pipeline",
}

# Career keywords strongly relevant to this specific role
CAREER_MATCH_TERMS = {
    "recommendation", "recommender", "search", "ranking", "retrieval",
    "nlp", "natural language", "embedding", "semantic", "information retrieval",
    "text", "language model", "llm", "transformer", "bert", "gpt",
    "machine learning engineer", "ml engineer", "ai engineer", "applied ml",
    "applied ai", "research engineer", "data scientist",
}

# Consulting/services firm titles that the JD explicitly flags as bad fit
CONSULTING_FIRMS = {
    "tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini",
    "hcl", "tech mahindra", "mphasis", "hexaware", "mindtree",
    "l&t infotech", "l&t technology", "cyient", "mastech",
}

# Non-technical current titles that suggest the candidate is a keyword stuffer
NON_TECHNICAL_TITLES = {
    "hr manager", "human resources", "marketing manager", "content writer",
    "sales executive", "accountant", "operations manager", "business analyst",
    "project manager", "graphic designer", "customer support",
    "civil engineer", "mechanical engineer", "electrical engineer",
}

# Preferred locations (India, willing to relocate)
INDIA_LOCATIONS = {
    "india", "noida", "pune", "delhi", "delhi ncr", "mumbai", "bangalore",
    "bengaluru", "hyderabad", "chennai", "gurgaon", "gurugram", "ncr",
}


# ─────────────────────────────────────────────────────────────────────────────
# Helper utilities
# ─────────────────────────────────────────────────────────────────────────────

def _norm(s: str) -> str:
    return s.lower().strip() if s else ""


def _days_since(date_str: str) -> int:
    """Days between today and a date string (YYYY-MM-DD). Returns 9999 on error."""
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        return (date.today() - d).days
    except Exception:
        return 9999


def _count_matching_skills(skill_names: list[str], target_set: set[str]) -> int:
    """How many skills in skill_names fuzzy-match any term in target_set."""
    count = 0
    for s in skill_names:
        sn = _norm(s)
        for t in target_set:
            if t in sn or sn in t or _token_overlap(sn, t) >= 0.6:
                count += 1
                break
    return count


def _token_overlap(a: str, b: str) -> float:
    """Jaccard-like token overlap between two strings."""
    ta = set(a.split())
    tb = set(b.split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _text_has_any(text: str, terms: set[str]) -> int:
    """Count how many terms from the set appear in the lowercased text."""
    tl = text.lower()
    return sum(1 for t in terms if t in tl)


def _sigmoid(x: float, center: float = 0.0, scale: float = 1.0) -> float:
    return 1.0 / (1.0 + math.exp(-(x - center) / scale))


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


# ─────────────────────────────────────────────────────────────────────────────
# Scoring dimensions
# ─────────────────────────────────────────────────────────────────────────────

def score_skills(c: dict) -> tuple[float, int]:
    """
    Skill quality score [0,1].
    Returns (score, count_of_core_ai_skills).
    Weights: proficiency level, endorsements, and Redrob assessment scores.
    Penalizes padded profiles (advanced skill + low assessment score).
    """
    skills = c.get("skills", [])
    if not skills:
        return 0.0, 0

    signals = c.get("redrob_signals", {})
    assessments = signals.get("skill_assessment_scores", {})
    github = signals.get("github_activity_score", -1)

    PROF_WEIGHT = {"beginner": 0.3, "intermediate": 0.6, "advanced": 0.9, "expert": 1.0}

    core_count = 0
    total_score = 0.0
    max_possible = 0.0

    for sk in skills:
        name = sk.get("name", "")
        prof = sk.get("proficiency", "beginner")
        endorsements = sk.get("endorsements", 0)
        duration = sk.get("duration_months", 0)
        name_l = _norm(name)

        # Is this a critical / core / nice-to-have skill?
        is_critical = any(t in name_l or name_l in t or _token_overlap(name_l, t) >= 0.55
                          for t in CRITICAL_JD_SKILLS)
        is_core = is_critical or any(t in name_l or name_l in t or _token_overlap(name_l, t) >= 0.55
                                     for t in CORE_AI_SKILLS)
        is_nice = any(t in name_l or name_l in t for t in NICE_TO_HAVE_SKILLS)

        if not is_core and not is_nice:
            continue  # Irrelevant skill, skip

        # Critical JD skills ("things you absolutely need") get highest weight
        weight = 3.0 if is_critical else (2.0 if is_core else 0.7)

        # Base from proficiency
        pbase = PROF_WEIGHT.get(prof, 0.3)

        # Endorsement bonus (log scale, cap at 50 endorsements)
        end_bonus = math.log1p(min(endorsements, 50)) / math.log1p(50) * 0.15

        # Duration modifier (more time using = slightly more credible)
        dur_mod = min(1.0, duration / 36) * 0.1

        # Assessment score modifier (actual proof of skill)
        asc_val = None
        for akey, aval in assessments.items():
            if _norm(akey) in _norm(name) or _norm(name) in _norm(akey):
                asc_val = aval
                break

        asc_mod = 0.0
        if asc_val is not None:
            # Assessment score 0-100 → 0-0.2 bonus
            asc_mod = (asc_val / 100) * 0.2
            # Penalty: if claiming advanced/expert but assessed low
            if prof in ("advanced", "expert") and asc_val < 40:
                pbase *= 0.6  # penalize padding

        skill_score = _clamp(pbase + end_bonus + dur_mod + asc_mod)
        total_score += skill_score * weight
        max_possible += weight

        if is_core:
            core_count += 1

    # GitHub bonus (real proof of coding)
    if github > 0:
        github_bonus = (github / 100) * 0.1
        total_score += github_bonus
        max_possible += 0.1

    if max_possible == 0:
        return 0.0, 0

    normalized = _clamp(total_score / max_possible)
    return normalized, core_count


def score_career(c: dict) -> float:
    """
    Career relevance score [0,1].
    Looks at career descriptions for ML/AI production signals.
    Penalizes: consulting-only backgrounds, non-technical current roles,
    CV-only AI exposure (no career evidence).
    """
    career = c.get("career_history", [])
    profile = c.get("profile", {})

    current_title = _norm(profile.get("current_title", ""))
    current_company = _norm(profile.get("current_company", ""))

    # Hard penalty: current title is clearly non-technical (keyword stuffer trap)
    is_non_technical = any(t in current_title for t in NON_TECHNICAL_TITLES)
    title_penalty = 0.65 if is_non_technical else 1.0

    # Check consulting-only background
    all_companies = [_norm(e.get("company", "")) for e in career]
    consulting_only = all(
        any(cf in co for cf in CONSULTING_FIRMS) for co in all_companies if co
    )
    consulting_penalty = 0.70 if consulting_only and len(all_companies) >= 2 else 1.0

    # Also: if currently at consulting firm AND no prior product experience
    if any(cf in current_company for cf in CONSULTING_FIRMS):
        # Check if any prior non-consulting role
        non_consulting = [
            co for co in all_companies
            if not any(cf in co for cf in CONSULTING_FIRMS)
        ]
        if not non_consulting:
            consulting_penalty *= 0.8  # Extra penalty for no product experience

    # Score career descriptions
    total_career_score = 0.0
    total_weight = 0.0

    for i, entry in enumerate(career[:6]):  # Look at up to 6 roles
        desc = entry.get("description", "") + " " + entry.get("title", "")
        company = _norm(entry.get("company", ""))
        is_current = entry.get("is_current", False)
        duration = entry.get("duration_months", 0)

        # Recency weight (current role = highest weight)
        recency_w = 2.5 if is_current else max(0.4, 1.5 - i * 0.25)

        # How many career match terms appear?
        career_hits = _text_has_any(desc, CAREER_MATCH_TERMS)
        production_hits = _text_has_any(desc, PRODUCTION_SIGNALS)

        # Score this role
        career_score = _sigmoid(career_hits, center=2, scale=1.5)
        prod_score = _sigmoid(production_hits, center=1.5, scale=1.0)

        # Bonus for product vs consulting company in this role
        is_consulting = any(cf in company for cf in CONSULTING_FIRMS)
        company_bonus = 0.0 if is_consulting else 0.1

        role_score = _clamp(0.55 * career_score + 0.35 * prod_score + company_bonus)

        # Current roles with no duration_months set default to 6 months so
        # the highest-weight entry isn't silently zeroed out.
        dur_for_weight = duration if duration > 0 else (6 if is_current else 0)
        total_career_score += role_score * recency_w * min(1.0, dur_for_weight / 12)
        total_weight += recency_w

    if total_weight == 0:
        return 0.0

    raw = total_career_score / total_weight
    return _clamp(raw * title_penalty * consulting_penalty)


def score_experience_fit(c: dict) -> float:
    """
    Score [0,1] for experience years in the 5-9 year target band.
    Ideal: 6-8 years. OK: 4-10. Bad: <2 or >13.
    """
    yoe = c.get("profile", {}).get("years_of_experience", 0) or 0

    if 6 <= yoe <= 8:
        return 1.0
    elif 5 <= yoe < 6:
        return 0.90
    elif 8 < yoe <= 9:
        return 0.88
    elif 4 <= yoe < 5:
        return 0.75
    elif 9 < yoe <= 11:
        return 0.75
    elif 11 < yoe <= 13:
        return 0.60
    elif 3 <= yoe < 4:
        return 0.55
    elif yoe > 13:
        return 0.50
    elif 2 <= yoe < 3:
        return 0.35
    else:
        return 0.15


def score_behavioral(c: dict) -> float:
    """
    Behavioral availability / engagement score [0,1].
    Key signals: recency of activity, response rate, open to work,
    notice period, interview completion, verified contact.
    """
    sig = c.get("redrob_signals", {})

    # Recency of activity (most important — dead profiles are useless)
    last_active = sig.get("last_active_date", "")
    days_inactive = _days_since(last_active)
    if days_inactive < 14:
        activity_score = 1.0
    elif days_inactive < 30:
        activity_score = 0.90
    elif days_inactive < 60:
        activity_score = 0.75
    elif days_inactive < 90:
        activity_score = 0.60
    elif days_inactive < 180:
        activity_score = 0.40
    else:
        activity_score = 0.15

    # Open to work flag
    open_flag = 1.0 if sig.get("open_to_work_flag", False) else 0.6

    # Recruiter response rate (critical — unavailable candidate is useless)
    # Explicit None check: `or 0.5` would wrongly treat a true 0.0 as missing.
    rr_raw = sig.get("recruiter_response_rate")
    rr = 0.5 if rr_raw is None else rr_raw
    response_score = _sigmoid(rr, center=0.4, scale=0.15)

    # Interview completion rate (did they show up?)
    icr_raw = sig.get("interview_completion_rate")
    icr = 0.7 if icr_raw is None else icr_raw
    icr_score = _sigmoid(icr, center=0.6, scale=0.15)

    # Notice period (shorter is better; JD wants <30 days)
    notice = sig.get("notice_period_days") or 60
    if notice <= 15:
        notice_score = 1.0
    elif notice <= 30:
        notice_score = 0.90
    elif notice <= 60:
        notice_score = 0.75
    elif notice <= 90:
        notice_score = 0.60
    else:
        notice_score = 0.40

    # Offer acceptance rate (indicates seriousness; -1 = no history)
    oar = sig.get("offer_acceptance_rate", -1)
    if oar < 0:
        oar_score = 0.65  # unknown, neutral
    else:
        oar_score = _sigmoid(oar, center=0.5, scale=0.2)

    # Verified contact (can actually reach them)
    verified = (sig.get("verified_email", False) or sig.get("verified_phone", False))
    verified_bonus = 0.05 if verified else -0.05

    # Profile completeness (indicates effort)
    completeness = sig.get("profile_completeness_score", 50) / 100
    completeness_score = _clamp(completeness)

    # Saved by recruiters (social proof from the platform)
    saved = sig.get("saved_by_recruiters_30d", 0)
    saved_score = min(1.0, math.log1p(saved) / math.log1p(20))

    score = (
        0.30 * activity_score
        + 0.20 * response_score
        + 0.15 * open_flag
        + 0.12 * icr_score
        + 0.10 * notice_score
        + 0.06 * oar_score
        + 0.04 * completeness_score
        + 0.03 * saved_score
    ) + verified_bonus

    return _clamp(score)


def score_education(c: dict) -> float:
    """
    Education score [0,1].
    Weights: tier, field relevance.
    """
    edu_list = c.get("education", [])
    if not edu_list:
        return 0.4

    TIER_SCORE = {
        "tier_1": 1.0, "tier_2": 0.80, "tier_3": 0.60,
        "tier_4": 0.40, "unknown": 0.50,
    }

    RELEVANT_FIELDS = {
        "computer science", "machine learning", "artificial intelligence",
        "data science", "information technology", "software engineering",
        "electrical engineering", "electronics", "statistics", "mathematics",
        "computational", "cognitive", "robotics", "signal processing",
    }

    best = 0.0
    for edu in edu_list:
        tier = edu.get("tier", "unknown")
        field = _norm(edu.get("field_of_study", ""))
        degree = _norm(edu.get("degree", ""))

        tier_s = TIER_SCORE.get(tier, 0.5)

        # Field relevance
        field_hits = sum(1 for rf in RELEVANT_FIELDS if rf in field)
        field_s = min(1.0, 0.5 + field_hits * 0.25)

        # Degree bonus
        deg_bonus = 0.0
        if "ph" in degree or "doctor" in degree:
            deg_bonus = 0.15  # PhD is good but research-only PhDs are penalized in career score
        elif "m." in degree or "master" in degree:
            deg_bonus = 0.08

        score = _clamp(0.6 * tier_s + 0.4 * field_s + deg_bonus)
        best = max(best, score)

    return best


def score_location(c: dict) -> float:
    """
    Location fit [0,1]. Prefers India (Pune/Noida/NCR/Bangalore/Hyderabad).
    Penalties for non-India or unwilling to relocate.
    """
    profile = c.get("profile", {})
    signals = c.get("redrob_signals", {})

    location = _norm(profile.get("location", ""))
    country = _norm(profile.get("country", ""))
    willing = signals.get("willing_to_relocate", False)

    is_india = country == "india" or any(loc in location for loc in INDIA_LOCATIONS)
    is_preferred = any(
        loc in location
        for loc in {"noida", "pune", "delhi", "ncr", "gurgaon", "gurugram",
                    "bangalore", "bengaluru", "hyderabad", "mumbai"}
    )

    if is_preferred:
        return 1.0
    elif is_india:
        return 0.85
    elif willing:
        return 0.70
    else:
        return 0.50


# ─────────────────────────────────────────────────────────────────────────────
# Honeypot / red-flag detection
# ─────────────────────────────────────────────────────────────────────────────

def detect_honeypot(c: dict, skill_score: float, career_score: float, core_ai_count: int) -> float:
    """
    Returns a penalty multiplier [0.3, 1.0].
    Low value = profile looks padded/suspicious.
    """
    profile = c.get("profile", {})
    signals = c.get("redrob_signals", {})
    skills = c.get("skills", [])

    current_title = _norm(profile.get("current_title", ""))
    penalty = 1.0

    # Trap 1: Non-technical title + many AI skills (keyword stuffer)
    is_non_technical = any(t in current_title for t in NON_TECHNICAL_TITLES)
    if is_non_technical and core_ai_count >= 5:
        penalty *= 0.40  # Major red flag

    # Trap 2: Career shows no AI work but skills are full of AI terms
    career_text = " ".join(
        e.get("description", "") + " " + e.get("title", "")
        for e in c.get("career_history", [])
    ).lower()
    career_ai_hits = _text_has_any(career_text, CAREER_MATCH_TERMS)
    if core_ai_count >= 6 and career_ai_hits == 0:
        penalty *= 0.50  # Skills don't match career

    # Trap 3: Advanced AI skills with very low (or no) assessment scores
    adv_with_low_assessment = 0
    for sk in skills:
        if sk.get("proficiency") in ("advanced", "expert"):
            sk_name = _norm(sk.get("name", ""))
            is_core = any(t in sk_name for t in CORE_AI_SKILLS)
            if is_core:
                assessments = signals.get("skill_assessment_scores", {})
                for akey, aval in assessments.items():
                    if _norm(akey) in sk_name or sk_name in _norm(akey):
                        if aval < 35:
                            adv_with_low_assessment += 1
    if adv_with_low_assessment >= 2:
        penalty *= 0.75

    # Trap 4: Framework enthusiast / no substance
    # High-skill count but no GitHub, no assessments, no career hits
    has_github = signals.get("github_activity_score", -1) >= 10
    has_assessments = bool(signals.get("skill_assessment_scores", {}))
    if core_ai_count >= 8 and not has_github and not has_assessments and career_ai_hits <= 1:
        penalty *= 0.60

    # Trap 5: Impossible timeline — claimed YOE far exceeds sum of career durations
    # (e.g. "8 years experience at a company founded 3 years ago")
    profile_yoe = (profile.get("years_of_experience", 0) or 0)
    total_career_months = sum((e.get("duration_months", 0) or 0) for e in c.get("career_history", []))
    if profile_yoe >= 2 and total_career_months > 0:
        career_years = total_career_months / 12
        # Allow 30% gap time between jobs; flag if claimed is 2.5× actual career total
        if profile_yoe > career_years * 2.5 and (profile_yoe - career_years) > 3:
            penalty *= 0.35

    # Trap 6: Expert proficiency on skills with zero months of actual use
    # (e.g., "expert" in 10 skills, all with duration_months=0)
    expert_zero_duration = sum(
        1 for sk in skills
        if sk.get("proficiency") in ("advanced", "expert")
        and (sk.get("duration_months") or 0) == 0
    )
    if expert_zero_duration >= 5:
        penalty *= 0.45

    return _clamp(penalty, 0.3, 1.0)


# ─────────────────────────────────────────────────────────────────────────────
# Full candidate score
# ─────────────────────────────────────────────────────────────────────────────

WEIGHTS = {
    "career":     0.35,
    "skills":     0.28,
    "experience": 0.12,
    "behavioral": 0.18,
    "education":  0.04,
    "location":   0.03,
}


def score_candidate(c: dict) -> tuple[float, dict]:
    """Returns (total_score, component_dict)."""
    skill_s, core_count = score_skills(c)
    career_s   = score_career(c)
    exp_s      = score_experience_fit(c)
    behav_s    = score_behavioral(c)
    edu_s      = score_education(c)
    loc_s      = score_location(c)

    # Honeypot / red-flag penalty applied as multiplier on career + skill scores
    hp_mult = detect_honeypot(c, skill_s, career_s, core_count)

    effective_skill  = skill_s  * hp_mult
    effective_career = career_s * hp_mult

    total = (
        WEIGHTS["career"]     * effective_career
        + WEIGHTS["skills"]   * effective_skill
        + WEIGHTS["experience"] * exp_s
        + WEIGHTS["behavioral"] * behav_s
        + WEIGHTS["education"]  * edu_s
        + WEIGHTS["location"]   * loc_s
    )

    components = {
        "skill_score":     round(skill_s, 3),
        "career_score":    round(career_s, 3),
        "experience_score": round(exp_s, 3),
        "behavioral_score": round(behav_s, 3),
        "education_score":  round(edu_s, 3),
        "location_score":   round(loc_s, 3),
        "honeypot_mult":    round(hp_mult, 3),
        "core_ai_skills":   core_count,
    }

    return _clamp(round(total, 4)), components


def build_reasoning(c: dict, comp: dict) -> str:
    """
    Reasoning string: specific facts from the profile + JD connection + gaps acknowledged.
    Checked at Stage 4 — must reference real profile data, no hallucination.
    """
    profile  = c.get("profile", {})
    signals  = c.get("redrob_signals", {})
    skills   = c.get("skills", [])

    title  = profile.get("current_title", "Unknown")[:30]
    yoe    = profile.get("years_of_experience") or 0
    rr     = signals.get("recruiter_response_rate") or 0
    last   = signals.get("last_active_date", "")
    days   = _days_since(last)
    notice = signals.get("notice_period_days") or 60
    company = profile.get("current_company", "")

    # Pick top 3 critical/core AI skill names actually in their profile
    top_skill_names = []
    for sk in skills:
        name_l = _norm(sk.get("name", ""))
        if any(t in name_l or name_l in t for t in CRITICAL_JD_SKILLS):
            top_skill_names.append(sk.get("name", ""))
        if len(top_skill_names) >= 3:
            break
    if not top_skill_names:
        for sk in skills:
            name_l = _norm(sk.get("name", ""))
            if any(t in name_l or name_l in t for t in CORE_AI_SKILLS):
                top_skill_names.append(sk.get("name", ""))
            if len(top_skill_names) >= 2:
                break

    skills_str = ", ".join(top_skill_names) if top_skill_names else "general ML skills"
    active_str = f"active {days}d ago" if days < 9999 else "activity unknown"

    # Acknowledge gaps honestly
    gaps = []
    if notice > 60:
        gaps.append(f"long notice ({notice}d)")
    if rr < 0.3:
        gaps.append(f"low response rate ({rr:.0%})")
    if days > 120:
        gaps.append("inactive >4mo")
    gap_str = f"; concern: {', '.join(gaps)}" if gaps else ""

    company_str = f" @ {company[:20]}" if company else ""
    return (
        f"{title}{company_str} | {yoe:.1f}yr exp | "
        f"{skills_str} | "
        f"response {rr:.0%} | {active_str}"
        f"{gap_str}"
    )[:220]


# ─────────────────────────────────────────────────────────────────────────────
# Main pipeline
# ─────────────────────────────────────────────────────────────────────────────

def load_candidates(path: str):
    """Stream candidates from a JSONL file."""
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def run(candidates_path: str, out_path: str, top_n: int = 100, verbose: bool = True):
    t0 = datetime.now()

    if verbose:
        print(f"Loading candidates from {candidates_path} ...")

    results = []
    total = 0

    for c in load_candidates(candidates_path):
        total += 1
        if verbose and total % 10000 == 0:
            print(f"  Scored {total:,} candidates ...", flush=True)

        score, comp = score_candidate(c)
        results.append((score, c, comp))

    if verbose:
        print(f"Scored {total:,} candidates in {(datetime.now()-t0).seconds}s")

    # Sort descending by score; tie-break by candidate_id ascending (per validation rules)
    results.sort(key=lambda x: (-x[0], x[1]["candidate_id"]))
    top = results[:top_n]

    # Write output
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])

        for rank_idx, (score, c, comp) in enumerate(top):
            cid  = c["candidate_id"]
            rank = rank_idx + 1
            # Submission scores must be non-increasing; we emit with small epsilon spacing
            # Score already non-increasing since sorted. Round to 4dp.
            out_score = round(score, 4)
            reasoning = build_reasoning(c, comp)
            writer.writerow([cid, rank, out_score, reasoning])

            if verbose:
                flag = "*" if rank <= 10 else " "
                print(f"  {flag} #{rank:3d} {cid}  score={out_score:.4f}  {reasoning}")

    elapsed = (datetime.now() - t0).seconds
    if verbose:
        print(f"\nWrote {top_n} rows to {out_path} ({elapsed}s total)")


def main():
    parser = argparse.ArgumentParser(description="Rank candidates for Redrob Senior AI Engineer role")
    parser.add_argument("--candidates", default="./candidates.jsonl", help="Path to candidates JSONL file")
    parser.add_argument("--out", default="./submission.csv", help="Output CSV path")
    parser.add_argument("--top-n", type=int, default=100, help="Number of candidates to output")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress output")
    args = parser.parse_args()

    run(args.candidates, args.out, args.top_n, verbose=not args.quiet)


if __name__ == "__main__":
    main()
