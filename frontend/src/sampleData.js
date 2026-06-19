// Sample candidates in real Redrob schema format (from candidates.jsonl)
export const SAMPLE_CANDIDATES = [
  {
    candidate_id: "CAND_0081846",
    profile: {
      anonymized_name: "Sample Lead AI Engineer",
      headline: "Lead AI Engineer | Embeddings, Retrieval, LLMs",
      summary: "Lead AI Engineer with 6.7 years building production ML systems for search and recommendation at product companies. Deep expertise in dense retrieval, vector databases, and LLM fine-tuning.",
      location: "Bangalore", country: "India",
      years_of_experience: 6.7,
      current_title: "Lead AI Engineer",
      current_company: "TechProduct Co",
      current_company_size: "501-1000",
      current_industry: "Technology"
    },
    career_history: [
      {
        company: "TechProduct Co", title: "Lead AI Engineer",
        start_date: "2022-01-01", end_date: null, duration_months: 30,
        is_current: true, industry: "Technology", company_size: "501-1000",
        description: "Built production semantic search using sentence-transformers and FAISS. Deployed vector retrieval pipeline serving 2M daily queries. Fine-tuned BERT and LLaMA models for ranking. Led A/B testing framework for search quality evaluation (NDCG, MRR)."
      },
      {
        company: "SearchCo", title: "Senior ML Engineer",
        start_date: "2018-06-01", end_date: "2021-12-31", duration_months: 42,
        is_current: false, industry: "Technology", company_size: "201-500",
        description: "NLP and information retrieval for e-commerce search. Built hybrid BM25 + dense retrieval with Elasticsearch. Deployed recommendation systems with collaborative filtering."
      }
    ],
    education: [{ institution: "IIT Bombay", degree: "B.Tech", field_of_study: "Computer Science", start_year: 2013, end_year: 2017, grade: "8.5 CGPA", tier: "tier_1" }],
    skills: [
      { name: "sentence-transformers", proficiency: "expert", endorsements: 45, duration_months: 36 },
      { name: "FAISS", proficiency: "expert", endorsements: 38, duration_months: 30 },
      { name: "PyTorch", proficiency: "expert", endorsements: 52, duration_months: 48 },
      { name: "NLP", proficiency: "expert", endorsements: 60, duration_months: 60 },
      { name: "Elasticsearch", proficiency: "advanced", endorsements: 30, duration_months: 40 },
      { name: "LLM fine-tuning", proficiency: "advanced", endorsements: 25, duration_months: 24 },
      { name: "NDCG", proficiency: "advanced", endorsements: 18, duration_months: 30 },
      { name: "Python", proficiency: "expert", endorsements: 70, duration_months: 80 },
      { name: "BM25", proficiency: "advanced", endorsements: 20, duration_months: 30 },
      { name: "LoRA", proficiency: "intermediate", endorsements: 12, duration_months: 18 },
      { name: "Qdrant", proficiency: "intermediate", endorsements: 10, duration_months: 12 },
      { name: "A/B testing", proficiency: "advanced", endorsements: 22, duration_months: 36 },
      { name: "Recommendation Systems", proficiency: "advanced", endorsements: 35, duration_months: 42 },
      { name: "RAG", proficiency: "advanced", endorsements: 15, duration_months: 18 }
    ],
    certifications: [],
    languages: [{ language: "English", proficiency: "professional" }],
    redrob_signals: {
      profile_completeness_score: 92, signup_date: "2025-01-10",
      last_active_date: "2026-05-03", open_to_work_flag: true,
      profile_views_received_30d: 45, applications_submitted_30d: 3,
      recruiter_response_rate: 0.73, avg_response_time_hours: 12,
      skill_assessment_scores: { "NLP": 88, "PyTorch": 91, "sentence-transformers": 85 },
      connection_count: 450, endorsements_received: 62,
      notice_period_days: 30, expected_salary_range_inr_lpa: { min: 35, max: 55 },
      preferred_work_mode: "hybrid", willing_to_relocate: true,
      github_activity_score: 72, search_appearance_30d: 180,
      saved_by_recruiters_30d: 12, interview_completion_rate: 0.90,
      offer_acceptance_rate: 0.75, verified_email: true, verified_phone: true, linkedin_connected: true
    }
  }
]
