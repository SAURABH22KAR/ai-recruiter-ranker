"""
Orchestrates the full candidate ranking pipeline:
1. Parse JD → structured analysis
2. Parse candidates → normalized models
3. Score each candidate (multi-dimensional)
4. LLM re-rank top K
5. Return final ranked list
"""
from typing import Any
from models import Candidate, JobDescription, RankedCandidate, RankResponse, ScoreBreakdown
from jd_parser import build_jd_object
from candidate_parser import parse_candidates
from scorer import compute_scores
from llm_reranker import llm_rerank
from config import TOP_K_LLM_RERANK


def rank_candidates(
    jd_text: str,
    raw_candidates: list[dict[str, Any]],
) -> RankResponse:
    """Full pipeline: JD text + raw candidate dicts → ranked response."""

    # Step 1: Parse JD
    jd, jd_analysis = build_jd_object(jd_text)

    # Step 2: Parse candidates
    candidates = parse_candidates(raw_candidates)

    # Step 3: Score every candidate
    scored: list[tuple[Candidate, ScoreBreakdown]] = []
    for candidate in candidates:
        scores = compute_scores(candidate, jd)
        scored.append((candidate, scores))

    # Step 4: Sort by total score descending
    scored.sort(key=lambda x: x[1].total, reverse=True)

    # Step 5: LLM re-rank top K
    llm_insights: dict[str, dict] = {}
    if scored:
        try:
            llm_insights = llm_rerank(scored, jd_analysis)
        except Exception as e:
            print(f"LLM re-rank failed (continuing without it): {e}")

    # Step 6: Build final response
    ranked: list[RankedCandidate] = []
    for rank_idx, (candidate, scores) in enumerate(scored):
        insights = llm_insights.get(candidate.id, {})
        ranked.append(RankedCandidate(
            rank=rank_idx + 1,
            candidate=candidate,
            scores=scores,
            llm_reasoning=insights.get("reasoning", ""),
            key_strengths=insights.get("key_strengths", []),
            gaps=insights.get("gaps", []),
            recommendation=insights.get("recommendation", ""),
        ))

    # Shortlist: "Strong Yes" + "Yes" candidates, or top 20% by score
    shortlist_ids = {cid for cid, ins in llm_insights.items() if ins.get("recommendation") in ("Strong Yes", "Yes")}
    shortlist_cutoff = max(
        sum(1 for r in ranked if r.candidate.id in shortlist_ids),
        max(1, len(ranked) // 5),
    )

    return RankResponse(
        job_analysis=jd_analysis,
        ranked_candidates=ranked,
        total_candidates=len(ranked),
        shortlist_cutoff=shortlist_cutoff,
    )
