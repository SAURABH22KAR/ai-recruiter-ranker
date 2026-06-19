# AI Recruiter — Redrob Hackathon Submission

Offline candidate ranker for the Redrob Senior AI Engineer JD. Scores and ranks 100,000 candidates using multi-dimensional, JD-aware heuristics with honeypot detection. Fully offline — no API calls during ranking.

## Reproduce the submission

```bash
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```

Runtime: ~3 minutes on a standard laptop CPU. No GPU, no network required.

**Validate the output:**
```bash
python validate_submission.py submission.csv
# Submission is valid.
```

## How it works

`rank.py` scores each of the 100,000 candidates across six dimensions, then selects the top 100.

### Scoring dimensions

| Dimension | Weight | What it measures |
|---|---|---|
| Career relevance | 35% | Career descriptions contain ML/search/retrieval signals at product companies |
| Skill quality | 28% | Critical JD skills (FAISS, NDCG, etc.) weighted 3×; core AI skills 2×; padded skills penalized |
| Behavioral availability | 18% | Activity recency, response rate, open-to-work flag, notice period, interview completion |
| Experience fit | 12% | Target 5–9 years, peak 6–8 years |
| Education | 4% | Institution tier + field relevance |
| Location | 3% | India preferred; relocation willingness |

### Three-tier skill weighting

Skills from the JD's "things you absolutely need" section get the highest weight:

- **Critical (3×)**: sentence-transformers, FAISS, Pinecone, Weaviate, Qdrant, Milvus, OpenSearch, Elasticsearch, NDCG, MRR, learning-to-rank, BM25, hybrid search, vector databases
- **Core AI (2×)**: PyTorch, NLP, LLMs, RAG, fine-tuning, MLOps tools
- **Nice-to-have (0.7×)**: Docker, SQL, cloud platforms

### Honeypot detection

Six traps, applied as a multiplier on the career + skill score:

1. **Non-technical title + many AI skills** — "HR Manager" with 10 AI skills → 0.40× penalty
2. **Skills not backed by career** — 6+ AI skills but zero AI mentions in career descriptions → 0.50×
3. **Advanced/expert claims + failing assessments** — proficiency mismatch with Redrob scores → 0.75×
4. **Framework enthusiast** — many skills, no GitHub, no assessments, no career evidence → 0.60×
5. **Impossible timeline** — claimed YOE far exceeds sum of career entry durations → 0.35×
6. **Expert with zero usage** — "expert" proficiency on skills with 0 months duration → 0.45×

### Behavioral scoring

The JD explicitly calls out that "a perfect-on-paper candidate who hasn't logged in for 6 months and has a 5% response rate is, for hiring purposes, not actually available." Behavioral signals make up 18% of the score:

- Activity recency (30% of behavioral): last login within 14 days = 1.0; 6+ months = 0.15
- Recruiter response rate (20%): sigmoid centred at 0.4
- Open to work flag (15%)
- Interview completion rate (12%)
- Notice period (10%): ≤30 days = 0.90; >90 days = 0.40

### Reasoning quality

Each candidate's reasoning string cites specific facts from their profile:
- Current title + company (e.g., "Lead AI Engineer @ Razorpay")
- Actual years of experience
- Top 2–3 critical skill names actually in their profile (e.g., "FAISS, Information Retrieval, Learning to Rank")
- Response rate + last active date
- Gap acknowledgment when relevant (e.g., "concern: long notice (120d)", "low response rate (7%)")

## Dependencies (submission script)

`rank.py` uses **Python standard library only** — no pip installs required.

```
python >= 3.8
```

## Optional: Full-stack demo UI

The project also includes a FastAPI backend + React/Vite frontend that uses Claude and sentence-transformers for a live demo. This is **not** used for the submission CSV.

### Backend setup

```bash
cd backend
# Windows:
C:\Users\<user>\anaconda3\python.exe -m pip install -r requirements.txt
copy .env.example .env
# Add ANTHROPIC_API_KEY to .env
start.bat
```

### Frontend setup

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

### Start both together

```bat
start_all.bat
```

## Project structure

```
rank.py                    # THE submission script — offline, stdlib only
validate_submission.py     # Official format validator (provided by hackathon)
submission_metadata.yaml   # Submission metadata
output/submission.csv      # Pre-generated ranked output (top 100)
backend/                   # FastAPI demo backend (uses Claude API)
  main.py                  # API endpoints: /api/rank, /api/upload-candidates
  ranker.py                # Full pipeline: JD parse → score → LLM re-rank
  scorer.py                # 5-dimension semantic scorer (sentence-transformers)
  jd_parser.py             # Claude-powered JD analysis
  llm_reranker.py          # Claude holistic re-ranking of top 20
  candidate_parser.py      # Redrob schema → internal models
frontend/                  # React 18 + Vite demo UI
  src/components/          # CandidateCard, JobInput, ScoreBar, JobAnalysis
```

## Top 10 results

| Rank | Candidate | Company | Key Skills |
|---|---|---|---|
| 1 | Lead AI Engineer | Razorpay | Information Retrieval, Learning to Rank, Elasticsearch |
| 2 | Senior ML Engineer | Zomato | Weaviate, Pinecone, Information Retrieval |
| 3 | Applied ML Engineer | LinkedIn | Pinecone, Sentence Transformers, Qdrant |
| 4 | Senior AI Engineer | Apple | FAISS, OpenSearch, Weaviate |
| 5 | NLP Engineer | Aganitha | Semantic Search, FAISS, Embeddings |
| 6 | Senior NLP Engineer | Niramai | OpenSearch, FAISS, Embeddings |
| 7 | Senior AI Engineer | Netflix | Learning to Rank, Weaviate, BM25 |
| 8 | Senior NLP Engineer | Salesforce | Pinecone, BM25, OpenSearch |
| 9 | Senior NLP Engineer | Ola | Learning to Rank, Qdrant, Sentence Transformers |
| 10 | AI Engineer | Vedantu | Elasticsearch, Learning to Rank, BM25 |
