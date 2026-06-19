"""
LLM-powered re-ranking of top candidates.
Takes the top K candidates by score and asks Claude to do a holistic review,
providing reasoning, strengths, gaps, and a recommendation.
"""
import json
import anthropic
from models import Candidate, JobDescription, RankedCandidate, ScoreBreakdown
from config import ANTHROPIC_API_KEY, MODEL_ID, TOP_K_LLM_RERANK

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

RERANK_PROMPT = """You are a senior technical recruiter with 15 years of experience.

You have already received a preliminary ranking of candidates using semantic analysis.
Now do a holistic review and provide reasoning for each candidate.

Job Description Analysis:
{jd_analysis}

For each candidate below, provide:
1. key_strengths: 2-3 specific, concrete strengths relevant to THIS role
2. gaps: 1-2 honest gaps or risks (be specific, not generic)
3. recommendation: One of "Strong Yes", "Yes", "Maybe", "No"
4. reasoning: 1-2 sentence summary of your assessment

Candidates (in preliminary score order):
{candidates_json}

Return a JSON array in this exact format:
[
  {{
    "candidate_id": "...",
    "key_strengths": ["...", "..."],
    "gaps": ["..."],
    "recommendation": "Strong Yes|Yes|Maybe|No",
    "reasoning": "..."
  }},
  ...
]

Be specific and honest. Reference actual details from the candidate profiles.
Return ONLY the JSON array, no markdown."""


def _build_candidate_summary(candidate: Candidate, scores: ScoreBreakdown) -> dict:
    return {
        "id": candidate.id,
        "name": candidate.name,
        "summary": candidate.summary[:300] if candidate.summary else "",
        "skills": candidate.skills[:15],
        "total_experience_years": candidate.total_experience_years,
        "recent_roles": [
            {"title": e.title, "company": e.company, "months": e.duration_months}
            for e in candidate.experience[:3]
        ],
        "education": [
            {"degree": e.degree, "field": e.field}
            for e in candidate.education[:2]
        ],
        "scores": {
            "skill_match": scores.skill_match,
            "experience": scores.experience_relevance,
            "trajectory": scores.career_trajectory,
            "total": scores.total,
        }
    }


def llm_rerank(
    candidates_with_scores: list[tuple[Candidate, ScoreBreakdown]],
    jd_analysis: dict,
) -> dict[str, dict]:
    """
    Takes top K candidates and their scores, returns a dict of
    candidate_id → {key_strengths, gaps, recommendation, reasoning}
    """
    top_k = candidates_with_scores[:TOP_K_LLM_RERANK]

    summaries = [
        _build_candidate_summary(c, s) for c, s in top_k
    ]

    prompt = RERANK_PROMPT.format(
        jd_analysis=json.dumps(jd_analysis, indent=2),
        candidates_json=json.dumps(summaries, indent=2),
    )

    response = client.messages.create(
        model=MODEL_ID,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    results = json.loads(raw)
    return {r["candidate_id"]: r for r in results}
