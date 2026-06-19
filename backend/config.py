import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL_ID = "claude-sonnet-4-6"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Scoring weights (must sum to 1.0)
SCORING_WEIGHTS = {
    "skill_match": 0.30,
    "experience_relevance": 0.25,
    "career_trajectory": 0.20,
    "education_fit": 0.10,
    "behavioral_signals": 0.15,
}

TOP_K_LLM_RERANK = 20  # How many candidates to send to LLM for final re-ranking
