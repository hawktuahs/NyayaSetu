import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { listCases } from '../api/client'
import StatusBadge from '../components/StatusBadge'

export default function VerifyQueue() {
  const [cases, setCases] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    const load = async () => {
      try {
        const { data } = await listCases()
        setCases(data.filter(c => c.status === 'pending_verification'))
      } catch {}
      setLoading(false)
    }
    load()
    const t = setInterval(load, 6000)
    return () => clearInterval(t)
  }, [])

  return (
    <div className="page fade-in">
      <div className="ph">
        <div className="ph-row">
          <div>
            <h1 className="ph-title">Review Queue</h1>
            <p className="ph-sub">Human verification is mandatory before any record reaches the dashboard</p>
          </div>
          <Link to="/cases" className="btn btn-ghost">View All Cases</Link>
        </div>
      </div>

      {loading ? (
        <div className="loading"><span className="spinner lg" /></div>
      ) : cases.length === 0 ? (
        <div className="empty">
          <div className="empty-icon">✅</div>
          <div className="empty-title">Queue is clear</div>
          <p style={{ marginBottom: 14 }}>No cases awaiting review.</p>
          <Link to="/" className="btn btn-primary">↑ Upload a Judgment</Link>
        </div>
      ) : (
        <>
          <div className="alert alert-warn" style={{ marginBottom: 20, fontSize: 13 }}>
            🔒 <strong>{cases.length} case{cases.length !== 1 ? 's' : ''}</strong> awaiting human review.
            Review each carefully — only approved records appear on the dashboard.
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {cases.map((c, i) => (
              <div key={c.id} className="card" style={{ cursor: 'pointer', borderLeft: '3px solid var(--saffron)' }} onClick={() => navigate(`/verify/${c.id}`)}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 16, justifyContent: 'space-between', flexWrap: 'wrap' }}>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 14, color: 'var(--text-1)', marginBottom: 4 }}>
                      #{i + 1} — {c.original_filename}
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--text-3)' }}>
                      📅 {new Date(c.upload_time).toLocaleString('en-IN')} · {c.page_count} pages
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                    <StatusBadge value="pending_verification" />
                    <Link to={`/verify/${c.id}`} className="btn btn-primary btn-sm" onClick={e => e.stopPropagation()}>
                      Review →
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
