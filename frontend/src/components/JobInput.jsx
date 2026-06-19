import React, { useState } from 'react'

const SAMPLE_JD = `Senior Machine Learning Engineer

We are looking for a Senior ML Engineer to join our Search Relevance team. You will build and deploy large-scale ML systems that power our search and recommendation engines serving 100M+ users.

Responsibilities:
- Design, train, and deploy ML models for ranking, classification, and semantic search
- Collaborate with data engineers to build robust data pipelines
- Lead model evaluation and A/B testing frameworks
- Mentor junior ML engineers

Requirements:
- 5+ years of experience in machine learning or applied AI
- Strong proficiency in Python and ML frameworks (PyTorch, TensorFlow, scikit-learn)
- Experience with NLP and text embeddings (BERT, transformers)
- Experience deploying models to production at scale (Kubernetes, Docker)
- Strong understanding of data structures, algorithms, and system design
- Experience with distributed systems and big data tools (Spark, Kafka)

Nice to have:
- PhD in ML, Statistics, or related field
- Experience with recommender systems or search ranking
- Publications in top ML conferences (NeurIPS, ICML, ICLR)
- Experience with LLMs and prompt engineering`

export default function JobInput({ onSubmit, loading }) {
  const [jd, setJd] = useState('')

  const loadSample = () => setJd(SAMPLE_JD)

  return (
    <div className="card" style={{ marginBottom: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
        <h2 style={{ fontSize: 16, fontWeight: 600, color: '#c7d0e8' }}>Job Description</h2>
        <button className="btn-outline" style={{ fontSize: 12, padding: '5px 12px' }} onClick={loadSample}>
          Load Sample JD
        </button>
      </div>
      <textarea
        value={jd}
        onChange={e => setJd(e.target.value)}
        placeholder="Paste the full job description here..."
        style={{
          width: '100%',
          minHeight: 200,
          background: '#0f1117',
          border: '1px solid #2e3349',
          borderRadius: 8,
          color: '#e2e8f0',
          padding: '12px 14px',
          fontSize: 13,
          resize: 'vertical',
          outline: 'none',
        }}
      />
      <div style={{ marginTop: 12, display: 'flex', gap: 10, alignItems: 'center' }}>
        <button
          className="btn-primary"
          disabled={!jd.trim() || loading}
          onClick={() => onSubmit(jd)}
        >
          {loading ? <><span className="spinner" style={{ width: 14, height: 14, marginRight: 8 }} />Analyzing...</> : 'Analyze & Rank Candidates'}
        </button>
        {jd.trim() && (
          <span style={{ color: '#8892a4', fontSize: 12 }}>{jd.length} chars</span>
        )}
      </div>
    </div>
  )
}
