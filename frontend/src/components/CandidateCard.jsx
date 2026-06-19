import React, { useState } from 'react'
import { ScoreBreakdown } from './ScoreBar.jsx'

const REC_CLASS = {
  'Strong Yes': 'badge-strong-yes',
  'Yes': 'badge-yes',
  'Maybe': 'badge-maybe',
  'No': 'badge-no',
}

function TotalRing({ value }) {
  const pct = Math.round(value * 100)
  const r = 28
  const circ = 2 * Math.PI * r
  const color = pct >= 75 ? '#22c55e' : pct >= 55 ? '#6366f1' : pct >= 35 ? '#eab308' : '#ef4444'
  return (
    <div style={{ position: 'relative', width: 72, height: 72, flexShrink: 0 }}>
      <svg width="72" height="72" style={{ transform: 'rotate(-90deg)' }}>
        <circle cx="36" cy="36" r={r} fill="none" stroke="#1e2235" strokeWidth="5" />
        <circle
          cx="36" cy="36" r={r} fill="none"
          stroke={color} strokeWidth="5"
          strokeDasharray={circ}
          strokeDashoffset={circ * (1 - value)}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 0.6s ease' }}
        />
      </svg>
      <div style={{
        position: 'absolute', inset: 0,
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
      }}>
        <span style={{ fontSize: 16, fontWeight: 700, color }}>{pct}</span>
        <span style={{ fontSize: 9, color: '#8892a4', marginTop: -2 }}>score</span>
      </div>
    </div>
  )
}

export default function CandidateCard({ ranked, shortlist }) {
  const [expanded, setExpanded] = useState(false)
  const { rank, candidate, scores, recommendation, key_strengths, gaps, llm_reasoning } = ranked

  return (
    <div
      className="card"
      style={{
        marginBottom: 10,
        borderColor: shortlist ? 'rgba(99,102,241,0.4)' : '#2e3349',
        background: shortlist ? 'rgba(99,102,241,0.04)' : '#1a1d27',
      }}
    >
      {/* Header row */}
      <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
        {/* Rank badge */}
        <div style={{
          width: 32, height: 32, borderRadius: 8,
          background: rank <= 3 ? '#6366f1' : '#1e2235',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontWeight: 700, fontSize: 13, flexShrink: 0, marginTop: 4,
        }}>
          #{rank}
        </div>

        {/* Name + meta */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <h3 style={{ fontSize: 15, fontWeight: 600 }}>{candidate.name}</h3>
            {recommendation && (
              <span className={`badge ${REC_CLASS[recommendation] || 'badge-maybe'}`}>
                {recommendation}
              </span>
            )}
          </div>
          <p style={{ color: '#8892a4', fontSize: 12, marginTop: 2 }}>
            {candidate.total_experience_years}y exp
            {candidate.experience?.[0]?.title && ` · ${candidate.experience[0].title}`}
            {candidate.experience?.[0]?.company && ` @ ${candidate.experience[0].company}`}
          </p>
          {/* Skills */}
          <div style={{ marginTop: 6 }}>
            {candidate.skills.slice(0, 6).map(s => (
              <span key={s} className="tag">{s}</span>
            ))}
            {candidate.skills.length > 6 && (
              <span style={{ color: '#8892a4', fontSize: 11, marginLeft: 4 }}>
                +{candidate.skills.length - 6}
              </span>
            )}
          </div>
        </div>

        {/* Score ring */}
        <TotalRing value={scores.total} />
      </div>

      {/* Expand toggle */}
      <button
        onClick={() => setExpanded(v => !v)}
        style={{
          marginTop: 12, color: '#6366f1', background: 'none',
          fontSize: 12, fontWeight: 500, padding: 0,
        }}
      >
        {expanded ? '▲ Hide details' : '▼ Show details'}
      </button>

      {expanded && (
        <div style={{ marginTop: 14, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
          {/* Score breakdown */}
          <div>
            <p style={{ fontSize: 12, color: '#8892a4', marginBottom: 8, fontWeight: 600 }}>SCORE BREAKDOWN</p>
            <ScoreBreakdown scores={scores} />
          </div>

          {/* Recruiter insights */}
          <div>
            {llm_reasoning && (
              <div style={{ marginBottom: 12 }}>
                <p style={{ fontSize: 12, color: '#8892a4', fontWeight: 600, marginBottom: 4 }}>RECRUITER TAKE</p>
                <p style={{ fontSize: 12, color: '#c7d0e8', lineHeight: 1.6 }}>{llm_reasoning}</p>
              </div>
            )}
            {key_strengths?.length > 0 && (
              <div style={{ marginBottom: 8 }}>
                <p style={{ fontSize: 11, color: '#22c55e', fontWeight: 600, marginBottom: 4 }}>STRENGTHS</p>
                {key_strengths.map((s, i) => (
                  <p key={i} style={{ fontSize: 12, color: '#c7d0e8', paddingLeft: 10, marginBottom: 2 }}>• {s}</p>
                ))}
              </div>
            )}
            {gaps?.length > 0 && (
              <div>
                <p style={{ fontSize: 11, color: '#eab308', fontWeight: 600, marginBottom: 4 }}>GAPS</p>
                {gaps.map((g, i) => (
                  <p key={i} style={{ fontSize: 12, color: '#c7d0e8', paddingLeft: 10, marginBottom: 2 }}>• {g}</p>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
