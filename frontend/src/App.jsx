import React, { useState } from 'react'
import axios from 'axios'
import JobInput from './components/JobInput.jsx'
import CandidateUpload from './components/CandidateUpload.jsx'
import CandidateCard from './components/CandidateCard.jsx'
import JobAnalysis from './components/JobAnalysis.jsx'
import { SAMPLE_CANDIDATES } from './sampleData.js'

export default function App() {
  const [candidates, setCandidates] = useState([])
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [filter, setFilter] = useState('all') // all | shortlist

  const handleRank = async (jd) => {
    const cands = candidates.length > 0 ? candidates : SAMPLE_CANDIDATES
    if (!cands.length) {
      setError('Please upload candidate data or use the sample dataset.')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const res = await axios.post('/api/rank', {
        job_description: jd,
        candidates: cands,
      })
      setResult(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleExport = async () => {
    if (!result) return
    try {
      const res = await axios.post('/api/export-csv', result, { responseType: 'blob' })
      const url = URL.createObjectURL(res.data)
      const a = document.createElement('a')
      a.href = url
      a.download = 'ranked_candidates.csv'
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      alert('Export failed: ' + e.message)
    }
  }

  const displayed = result?.ranked_candidates?.filter(rc =>
    filter === 'shortlist' ? rc.rank <= result.shortlist_cutoff : true
  ) || []

  return (
    <div style={{ maxWidth: 960, margin: '0 auto', padding: '32px 20px' }}>
      {/* Header */}
      <div style={{ marginBottom: 32, textAlign: 'center' }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, background: 'linear-gradient(90deg, #818cf8, #6366f1)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          AI Recruiter
        </h1>
        <p style={{ color: '#8892a4', marginTop: 6 }}>
          Semantic candidate ranking powered by Claude — no keyword matching
        </p>
      </div>

      {/* Input panels */}
      <JobInput onSubmit={handleRank} loading={loading} />
      <CandidateUpload candidates={candidates} setCandidates={setCandidates} />

      {candidates.length === 0 && (
        <p style={{ color: '#8892a4', fontSize: 12, marginTop: -12, marginBottom: 20 }}>
          No candidates uploaded — will use {SAMPLE_CANDIDATES.length} built-in sample candidates.
        </p>
      )}

      {/* Error */}
      {error && (
        <div style={{
          background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
          borderRadius: 8, padding: '12px 16px', marginBottom: 20, color: '#ef4444', fontSize: 13,
        }}>
          {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <>
          <JobAnalysis analysis={result.job_analysis} />

          {/* Toolbar */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <div style={{ display: 'flex', gap: 8 }}>
              {['all', 'shortlist'].map(f => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  style={{
                    padding: '6px 16px', borderRadius: 6, fontSize: 13, fontWeight: 500,
                    background: filter === f ? '#6366f1' : 'transparent',
                    color: filter === f ? '#fff' : '#8892a4',
                    border: '1px solid',
                    borderColor: filter === f ? '#6366f1' : '#2e3349',
                  }}
                >
                  {f === 'all' ? `All (${result.total_candidates})` : `Shortlist (${result.shortlist_cutoff})`}
                </button>
              ))}
            </div>
            <button className="btn-outline" onClick={handleExport} style={{ fontSize: 12 }}>
              ↓ Export CSV
            </button>
          </div>

          {/* Candidate cards */}
          {displayed.map(rc => (
            <CandidateCard
              key={rc.candidate.id}
              ranked={rc}
              shortlist={rc.rank <= result.shortlist_cutoff}
            />
          ))}
        </>
      )}
    </div>
  )
}
