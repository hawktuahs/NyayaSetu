import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { uploadCase } from '../api/client'

export default function Upload() {
  const [drag, setDrag] = useState(false)
  const [file, setFile] = useState(null)
  const [progress, setProgress] = useState(0)
  const [uploading, setUploading] = useState(false)
  const inputRef = useRef()
  const navigate = useNavigate()

  const handleFile = (f) => {
    if (!f) return
    if (!f.name.toLowerCase().endsWith('.pdf')) {
      toast.error('Only PDF files accepted')
      return
    }
    if (f.size > 50 * 1024 * 1024) {
      toast.error('File exceeds 50 MB limit')
      return
    }
    setFile(f)
  }

  const submit = async () => {
    if (!file || uploading) return
    setUploading(true)
    setProgress(10)
    const form = new FormData()
    form.append('file', file)
    try {
      setProgress(40)
      const { data } = await uploadCase(form)
      setProgress(100)
      toast.success('Uploaded — AI extraction started')
      navigate(`/cases/${data.id}`)
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Upload failed')
      setProgress(0)
      setUploading(false)
    }
  }

  return (
    <div className="page fade-in">
      <div className="ph">
        <h1 className="ph-title">Upload Court Judgment</h1>
        <p className="ph-sub">Upload a PDF judgment — AI will extract all key information and generate an action plan</p>
      </div>

      <div style={{ maxWidth: 640 }}>
        {/* Drop zone */}
        <div
          className={`upload-zone ${drag ? 'drag' : ''}`}
          onClick={() => !file && inputRef.current.click()}
          onDragOver={e => { e.preventDefault(); setDrag(true) }}
          onDragLeave={() => setDrag(false)}
          onDrop={e => { e.preventDefault(); setDrag(false); handleFile(e.dataTransfer.files[0]) }}
        >
          <input ref={inputRef} type="file" accept=".pdf" hidden onChange={e => handleFile(e.target.files[0])} />
          <span className="upload-icon">📄</span>
          {file ? (
            <div>
              <div className="upload-title" style={{ color: 'var(--saffron-light)' }}>✓ {file.name}</div>
              <div className="upload-sub">{(file.size / 1024 / 1024).toFixed(2)} MB · Click to change</div>
            </div>
          ) : (
            <div>
              <div className="upload-title">Drag & Drop or Click to Browse</div>
              <div className="upload-sub">Court judgment PDFs · Multi-page · Max 50 MB</div>
            </div>
          )}
        </div>

        {progress > 0 && (
          <div style={{ marginTop: 10 }}>
            <div className="progress">
              <div className="progress-fill" style={{ width: `${progress}%` }} />
            </div>
          </div>
        )}

        {file && (
          <div style={{ marginTop: 14, display: 'flex', gap: 10 }}>
            <button className="btn btn-primary btn-lg" onClick={submit} disabled={uploading} style={{ flex: 1 }}>
              {uploading ? <><span className="spinner" /> Uploading…</> : '↑ Upload & Extract'}
            </button>
            {!uploading && (
              <button className="btn btn-ghost" onClick={() => { setFile(null); setProgress(0) }}>Clear</button>
            )}
          </div>
        )}

        <div style={{ marginTop: 32 }}>
          <p className="sh">How it works</p>
          {[
            ['📄', 'Upload PDF', 'Drag in any court judgment — High Court, Supreme Court, Tribunal'],
            ['🤖', 'AI Extraction', 'LLaMA 3.1 reads the judgment and extracts parties, directions, deadlines, outcome'],
            ['📋', 'Action Plan', 'AI generates a structured action plan: comply, appeal, or monitor'],
            ['✅', 'Human Review', 'A reviewer verifies each field, edits if needed, then approves or rejects'],
            ['📊', 'Dashboard', 'Only approved, verified records appear on the government dashboard'],
          ].map(([icon, title, desc]) => (
            <div key={title} style={{ display: 'flex', gap: 14, marginBottom: 14, alignItems: 'flex-start' }}>
              <div style={{ fontSize: 20, flexShrink: 0, marginTop: 1 }}>{icon}</div>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-1)', marginBottom: 2 }}>{title}</div>
                <div style={{ fontSize: 12, color: 'var(--text-3)', lineHeight: 1.55 }}>{desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
