import React, { useState } from 'react'

export default function JobAnalysis({ analysis }) {
  const [open, setOpen] = useState(false)
  if (!analysis) return null

  return (
    <div className="card" style={{ marginBottom: 20, borderColor: 'rgba(99,102,241,0.3)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h3 style={{ fontSize: 15, fontWeight: 600 }}>{analysis.title}</h3>
          <p style={{ color: '#8892a4', fontSize: 12, marginTop: 2 }}>
            {analysis.seniority_level} · {analysis.domain} · {analysis.min_experience_years}+ years
          </p>
        </div>
        <button
          onClick={() => setOpen(v => !v)}
          style={{ color: '#6366f1', background: 'none', fontSize: 12 }}
        >
          {open ? '▲ Hide analysis' : '▼ JD Analysis'}
        </button>
      </div>

      {open && (
        <div style={{ marginTop: 16, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div>
            <p style={{ fontSize: 11, color: '#8892a4', fontWeight: 600, marginBottom: 6 }}>REQUIRED SKILLS</p>
            <div>{analysis.required_skills?.map(s => <span key={s} className="tag">{s}</span>)}</div>
          </div>
          <div>
            <p style={{ fontSize: 11, color: '#8892a4', fontWeight: 600, marginBottom: 6 }}>NICE TO HAVE</p>
            <div>{analysis.preferred_skills?.map(s => <span key={s} className="tag" style={{ background: 'rgba(34,197,94,0.08)', color: '#4ade80' }}>{s}</span>)}</div>
          </div>
          <div>
            <p style={{ fontSize: 11, color: '#8892a4', fontWeight: 600, marginBottom: 6 }}>CORE COMPETENCIES</p>
            <div>{analysis.core_competencies?.map(s => <span key={s} className="tag" style={{ background: 'rgba(251,191,36,0.08)', color: '#fbbf24' }}>{s}</span>)}</div>
          </div>
          <div>
            <p style={{ fontSize: 11, color: '#8892a4', fontWeight: 600, marginBottom: 6 }}>IMPLICIT REQUIREMENTS</p>
            <div>{analysis.implicit_requirements?.map(s => <span key={s} className="tag" style={{ background: 'rgba(236,72,153,0.08)', color: '#f472b6' }}>{s}</span>)}</div>
          </div>
        </div>
      )}
    </div>
  )
}
