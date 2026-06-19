"""
Web UI demo script — runs the FastAPI-based ranker on the real dataset.
Produces output/ranked_candidates.csv for the web dashboard.

NOTE: For the hackathon submission CSV, use rank.py instead:
  python rank.py --candidates ./candidates.jsonl --out ./submission.csv

This script uses the Claude API for JD understanding and LLM re-ranking.
Requires ANTHROPIC_API_KEY in backend/.env
"""
import sys, json, os, csv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "backend", ".env"))

from ranker import rank_candidates

JD_TEXT = """Senior AI Engineer — Founding Team
Company: Redrob AI (Series A AI-native talent intelligence platform)
Location: Pune/Noida, India (Hybrid)
Experience: 5–9 years

What you'd actually be doing:
Own the intelligence layer of Redrob's product — ranking, retrieval, and matching systems.
Ship a v2 ranking system using embeddings, hybrid retrieval, and LLM-based re-ranking.
Set up evaluation infrastructure: NDCG, MRR, offline benchmarks, A/B testing.
Drive long-term architecture for candidate-JD matching at scale.

Things you absolutely need:
- Production experience with embeddings-based retrieval (sentence-transformers, BGE, E5, OpenAI)
- Production experience with vector databases (Pinecone, Weaviate, Qdrant, Milvus, FAISS, Elasticsearch)
- Strong Python
- Hands-on experience designing evaluation frameworks for ranking systems (NDCG, MRR, MAP)
- 5+ years in applied ML/AI at product companies (not pure consulting or research)

Nice to have:
- LLM fine-tuning (LoRA, QLoRA, PEFT)
- Learning-to-rank models (XGBoost-based or neural)
- Background in HR-tech, recruiting tech, or marketplace products
- Open-source contributions in AI/ML

Explicitly NOT wanted:
- Pure researchers without production deployment
- Only consulting firm experience (TCS, Infosys, Wipro, Accenture, etc.)
- Computer vision/speech specialists without NLP/IR exposure
- Title-chasers who switch companies every 1.5 years
"""


def load_real_candidates(limit: int = 200) -> list[dict]:
    """Load first N candidates from the real JSONL file."""
    path = os.path.join(os.path.dirname(__file__), "candidates.jsonl")
    candidates = []
    with open(path) as f:
        for i, line in enumerate(f):
            if i >= limit:
                break
            line = line.strip()
            if line:
                candidates.append(json.loads(line))
    return candidates


def main():
    print("Loading candidates...")
    candidates = load_real_candidates(limit=500)
    print(f"Loaded {len(candidates)} candidates. Running ranking pipeline...")

    result = rank_candidates(JD_TEXT, candidates)

    print(f"\nJob: {result.job_analysis.get('title')}")
    print(f"Shortlist cutoff: top {result.shortlist_cutoff}")
    print("-" * 60)

    output_path = os.path.join(os.path.dirname(__file__), "output", "ranked_candidates_ui.csv")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    rows = []
    for rc in result.ranked_candidates:
        flag = "SHORTLIST" if rc.rank <= result.shortlist_cutoff else ""
        print(f"#{rc.rank:3d} {rc.candidate.name:<22} score={rc.scores.total:.3f}  {rc.recommendation} {flag}")
        rows.append({
            "rank": rc.rank,
            "candidate_id": rc.candidate.id,
            "name": rc.candidate.name,
            "total_score": rc.scores.total,
            "recommendation": rc.recommendation,
            "key_strengths": " | ".join(rc.key_strengths),
            "gaps": " | ".join(rc.gaps),
            "reasoning": rc.llm_reasoning,
            "total_experience_years": rc.candidate.total_experience_years,
            "skills": ", ".join(rc.candidate.skills[:8]),
        })

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSaved to {output_path}")


if __name__ == "__main__":
    main()
