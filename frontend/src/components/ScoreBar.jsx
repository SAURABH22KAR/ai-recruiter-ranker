import React from 'react'

const DIMS = [
  { key: 'skill_match', label: 'Skill Match', color: '#6366f1' },
  { key: 'experience_relevance', label: 'Experience', color: '#22c55e' },
  { key: 'career_trajectory', label: 'Career Arc', color: '#f59e0b' },
  { key: 'education_fit', label: 'Education', color: '#06b6d4' },
  { key: 'behavioral_signals', label: 'Signals', color: '#ec4899' },
]

export function ScoreBar({ value, color, height = 6 }) {
  return (
    <div style={{ background: '#1e2235', borderRadius: 99, overflow: 'hidden', height }}>
      <div
        style={{
          width: `${Math.round(value * 100)}%`,
          background: color,
          height: '100%',
          transition: 'width 0.5s ease',
          borderRadius: 99,
        }}
      />
    </div>
  )
}

export function ScoreBreakdown({ scores }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {DIMS.map(d => (
        <div key={d.key}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
            <span style={{ fontSize: 11, color: '#8892a4' }}>{d.label}</span>
            <span style={{ fontSize: 11, color: d.color, fontWeight: 600 }}>
              {Math.round(scores[d.key] * 100)}%
            </span>
          </div>
          <ScoreBar value={scores[d.key]} color={d.color} />
        </div>
      ))}
    </div>
  )
}
