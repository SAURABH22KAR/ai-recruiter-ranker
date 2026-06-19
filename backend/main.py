import io
import json
import csv
import pandas as pd
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Any

from models import RankRequest, RankResponse
from ranker import rank_candidates

app = FastAPI(title="AI Recruiter API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RankRequestBody(BaseModel):
    job_description: str
    candidates: list[dict[str, Any]]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/rank", response_model=RankResponse)
async def rank(body: RankRequestBody):
    if not body.job_description.strip():
        raise HTTPException(status_code=400, detail="job_description is required")
    if not body.candidates:
        raise HTTPException(status_code=400, detail="candidates list is empty")

    try:
        result = rank_candidates(body.job_description, body.candidates)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload-candidates")
async def upload_candidates(file: UploadFile = File(...)):
    """Accept JSON or CSV candidate file, return parsed list."""
    content = await file.read()

    if file.filename.endswith(".json"):
        data = json.loads(content)
        if isinstance(data, dict) and "candidates" in data:
            data = data["candidates"]
        return {"candidates": data, "count": len(data)}

    elif file.filename.endswith(".csv"):
        df = pd.read_csv(io.StringIO(content.decode("utf-8")))
        records = df.where(pd.notnull(df), None).to_dict(orient="records")
        # Parse skills column if it's a string
        for r in records:
            if isinstance(r.get("skills"), str):
                r["skills"] = [s.strip() for s in r["skills"].split(",") if s.strip()]
        return {"candidates": records, "count": len(records)}

    else:
        raise HTTPException(status_code=400, detail="Only .json and .csv files are supported")


@app.post("/api/export-csv")
async def export_csv(result: RankResponse):
    """Convert ranked results to downloadable CSV."""
    rows = []
    for rc in result.ranked_candidates:
        rows.append({
            "rank": rc.rank,
            "candidate_id": rc.candidate.id,
            "name": rc.candidate.name,
            "total_score": rc.scores.total,
            "skill_match": rc.scores.skill_match,
            "experience_relevance": rc.scores.experience_relevance,
            "career_trajectory": rc.scores.career_trajectory,
            "education_fit": rc.scores.education_fit,
            "behavioral_signals": rc.scores.behavioral_signals,
            "recommendation": rc.recommendation,
            "key_strengths": " | ".join(rc.key_strengths),
            "gaps": " | ".join(rc.gaps),
            "reasoning": rc.llm_reasoning,
            "total_experience_years": rc.candidate.total_experience_years,
            "skills": ", ".join(rc.candidate.skills[:10]),
        })

    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=ranked_candidates.csv"},
    )
