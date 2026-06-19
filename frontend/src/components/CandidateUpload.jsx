import React, { useState, useRef } from 'react'
import axios from 'axios'

export default function CandidateUpload({ candidates, setCandidates }) {
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)
  const fileRef = useRef(null)

  const handleFile = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setUploading(true)
    setError(null)
    try {
      const form = new FormData()
      form.append('file', file)
      const res = await axios.post('/api/upload-candidates', form)
      setCandidates(res.data.candidates)
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const handlePaste = (e) => {
    try {
      const data = JSON.parse(e.target.value)
      const list = Array.isArray(data) ? data : data.candidates || []
      setCandidates(list)
      setError(null)
    } catch {
      // Not valid JSON yet — that's fine while typing
    }
  }

  return (
    <div className="card" style={{ marginBottom: 24 }}>
      <h2 style={{ fontSize: 16, fontWeight: 600, color: '#c7d0e8', marginBottom: 14 }}>
        Candidate Data
      </h2>

      <div style={{ display: 'flex', gap: 12, marginBottom: 14 }}>
        <button
          className="btn-outline"
          onClick={() => fileRef.current.click()}
          disabled={uploading}
        >
          {uploading ? 'Uploading...' : 'Upload JSON / CSV'}
        </button>
        <input
          ref={fileRef}
          type="file"
          accept=".json,.csv"
          style={{ display: 'none' }}
          onChange={handleFile}
        />
        {candidates.length > 0 && (
          <span style={{ color: '#22c55e', fontSize: 13, alignSelf: 'center' }}>
            ✓ {candidates.length} candidates loaded
          </span>
        )}
      </div>

      <div style={{ position: 'relative' }}>
        <textarea
          placeholder='Or paste JSON array of candidates here... [{"id": "1", "name": "...", "skills": [...], ...}]'
          onChange={handlePaste}
          style={{
            width: '100%',
            minHeight: 100,
            background: '#0f1117',
            border: '1px solid #2e3349',
            borderRadius: 8,
            color: '#e2e8f0',
            padding: '10px 14px',
            fontSize: 12,
            fontFamily: 'monospace',
            resize: 'vertical',
            outline: 'none',
          }}
        />
      </div>
      {error && <p style={{ color: '#ef4444', fontSize: 12, marginTop: 8 }}>{error}</p>}
    </div>
  )
}
