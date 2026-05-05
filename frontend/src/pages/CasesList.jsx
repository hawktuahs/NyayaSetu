import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { listCases } from '../api/client'
import StatusBadge from '../components/StatusBadge'

const STATUS_TABS = ['all', 'pending_extraction', 'extracting', 'pending_verification', 'approved', 'rejected']

export default function CasesList() {
  const [cases, setCases] = useState([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState('all')
  const navigate = useNavigate()

  useEffect(() => {
    const load = async () => {
      try { const { data } = await listCases(); setCases(data) }
      catch {}
      setLoading(false)
    }
    load()
    const t = setInterval(load, 6000)
    return () => clearInterval(t)
  }, [])

  const filtered = tab === 'all' ? cases : cases.filter(c => c.status === tab)

  return (
    <div className="page fade-in">
      <div className="ph">
        <div className="ph-row">
          <div>
            <h1 className="ph-title">All Cases</h1>
            <p className="ph-sub">{cases.length} total · auto-refreshes every 6s</p>
          </div>
          <Link to="/" className="btn btn-primary">↑ Upload</Link>
        </div>
      </div>

      <div className="tabs">
        {STATUS_TABS.map(s => (
          <button key={s} className={`tab ${tab === s ? 'active' : ''}`} onClick={() => setTab(s)}>
            {s === 'all' ? `All (${cases.length})` : `${s.replace(/_/g, ' ')} (${cases.filter(c => c.status === s).length})`}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="loading"><span className="spinner lg" />Loading…</div>
      ) : filtered.length === 0 ? (
        <div className="empty">
          <div className="empty-icon">📁</div>
          <div className="empty-title">No cases</div>
          <div>
            {tab === 'all'
              ? <Link to="/" className="text-accent">Upload your first judgment →</Link>
              : 'No cases with this status.'}
          </div>
        </div>
      ) : (
        <div className="tbl-wrap">
          <table className="tbl">
            <thead>
              <tr>
                <th>#</th>
                <th>File</th>
                <th>Status</th>
                <th>Uploaded</th>
                <th>Pages</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((c, i) => (
                <tr key={c.id} onClick={() => navigate(`/cases/${c.id}`)}>
                  <td className="text-muted mono" style={{ width: 40 }}>{i + 1}</td>
                  <td style={{ fontWeight: 600, color: 'var(--text-1)', maxWidth: 320 }}>
                    <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {c.original_filename}
                    </div>
                  </td>
                  <td><StatusBadge value={c.status} /></td>
                  <td className="text-muted">{new Date(c.upload_time).toLocaleDateString('en-IN')}</td>
                  <td className="text-muted">{c.page_count}</td>
                  <td>
                    {c.status === 'pending_verification'
                      ? <Link to={`/verify/${c.id}`} className="btn btn-primary btn-sm" onClick={e => e.stopPropagation()}>Review</Link>
                      : <Link to={`/cases/${c.id}`} className="btn btn-ghost btn-sm" onClick={e => e.stopPropagation()}>View</Link>
                    }
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
