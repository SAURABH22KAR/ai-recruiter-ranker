import json
import anthropic
from config import ANTHROPIC_API_KEY, MODEL_ID
from models import JobDescription

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

JD_PARSE_PROMPT = """You are an expert technical recruiter. Analyze the following job description and extract structured information.

Return a JSON object with these exact fields:
{{
  "title": "job title",
  "domain": "primary domain/industry (e.g. 'Machine Learning', 'Backend Engineering', 'Data Science')",
  "required_skills": ["list of must-have skills"],
  "preferred_skills": ["list of nice-to-have skills"],
  "min_experience_years": <number>,
  "education_requirement": "e.g. 'Bachelor's in CS or related', 'Master's preferred'",
  "responsibilities": ["key responsibilities as short phrases"],
  "implicit_requirements": ["inferred needs not explicitly stated, e.g. 'startup mindset', 'cross-functional collaboration'"],
  "seniority_level": "Junior/Mid/Senior/Lead/Principal/Manager",
  "core_competencies": ["5-8 core competencies a great candidate must have"]
}}

Job Description:
{jd_text}

Return ONLY valid JSON, no markdown, no explanation."""


def parse_job_description(jd_text: str) -> dict:
    """Use Claude to deeply understand a job description."""
    response = client.messages.create(
        model=MODEL_ID,
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": JD_PARSE_PROMPT.format(jd_text=jd_text)
        }]
    )

    raw = response.content[0].text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    parsed = json.loads(raw)

    # Normalize min_experience_years
    exp = parsed.get("min_experience_years", 0)
    if isinstance(exp, str):
        try:
            exp = float(exp.split("-")[0].strip())
        except Exception:
            exp = 0.0
    parsed["min_experience_years"] = float(exp)

    return parsed


def build_jd_object(jd_text: str, jd_id: str = "jd_001") -> tuple[JobDescription, dict]:
    """Parse raw JD text and return both a JobDescription model and the full analysis dict."""
    analysis = parse_job_description(jd_text)

    jd = JobDescription(
        id=jd_id,
        title=analysis.get("title", ""),
        description=jd_text,
        required_skills=analysis.get("required_skills", []),
        preferred_skills=analysis.get("preferred_skills", []),
        min_experience_years=analysis.get("min_experience_years", 0.0),
        education_requirement=analysis.get("education_requirement", ""),
        domain=analysis.get("domain", ""),
        responsibilities=analysis.get("responsibilities", []),
    )

    return jd, analysis
