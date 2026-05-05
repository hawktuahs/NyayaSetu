import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { getDashboardCases, getDashboardStats } from '../api/client'
import StatusBadge from '../components/StatusBadge'

const PRIO_ORD = { critical: 0, high: 1, medium: 2, low: 3 }

export default function Dashboard() {
  const [cases, setCases] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filterPriority, setFilterPriority] = useState('all')
  const [filterOutcome, setFilterOutcome] = useState('all')
  const [filterDept, setFilterDept] = useState('all')
  const [expanded, setExpanded] = useState(null)
  const navigate = useNavigate()

  // Extract unique departments
  const allDepts = Array.from(new Set(cases.flatMap(c => c.departments_involved || []))).sort()

  useEffect(() => {
    const load = async () => {
      try {
        const [c, s] = await Promise.all([getDashboardCases(), getDashboardStats()])
        setCases(c.data)
        setStats(s.data)
      } catch {}
      setLoading(false)
    }
    load()
    const t = setInterval(load, 20000)
    return () => clearInterval(t)
  }, [])

  const filtered = cases.filter(c => {
    const term = search.toLowerCase()
    const matchSearch = !term || [c.case_number, c.court, c.subject_matter, c.original_filename, c.responsible_authority]
      .some(v => v && v.toLowerCase().includes(term))
    const matchPrio = filterPriority === 'all' || c.priority === filterPriority
    const matchOut = filterOutcome === 'all' || c.outcome_for_government === filterOutcome
    const matchDept = filterDept === 'all' || (c.departments_involved && c.departments_involved.some(d => d === filterDept))
    return matchSearch && matchPrio && matchOut && matchDept
  })

  return (
    <div className="page fade-in">
      <div className="ph">
        <div className="ph-row">
          <div>
            <h1 className="ph-title">Government Dashboard</h1>
            <p className="ph-sub">Verified, human-approved records only · Trusted view for decision-makers</p>
          </div>
          <Link to="/" className="btn btn-primary">↑ Upload Judgment</Link>
        </div>
      </div>

      {stats && (
        <div className="stats">
          <div className="stat orange">
            <div className="stat-icon">📋</div>
            <div className="stat-label">Total Cases</div>
            <div className="stat-value">{stats.total_cases}</div>
          </div>
          <div className="stat amber">
            <div className="stat-icon">⏳</div>
            <div className="stat-label">Pending Review</div>
            <div className="stat-value">{stats.pending_verification}</div>
          </div>
          <div className="stat green">
            <div className="stat-icon">✅</div>
            <div className="stat-label">Approved</div>
            <div className="stat-value">{stats.approved}</div>
          </div>
          <div className="stat red">
            <div className="stat-icon">🚨</div>
            <div className="stat-label">Critical Actions</div>
            <div className="stat-value">{stats.critical_actions}</div>
          </div>
          <div className="stat green">
            <div className="stat-icon">⚖</div>
            <div className="stat-label">Govt Won</div>
            <div className="stat-value">{stats.government_won}</div>
          </div>
          <div className="stat red">
            <div className="stat-icon">📛</div>
            <div className="stat-label">Govt Lost</div>
            <div className="stat-value">{stats.government_lost}</div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 18, flexWrap: 'wrap', alignItems: 'center' }}>
        <input className="form-input" style={{ maxWidth: 220 }} placeholder="🔍 Search case, court, subject…" value={search} onChange={e => setSearch(e.target.value)} />
        
        <select className="form-select" style={{ maxWidth: 180 }} value={filterDept} onChange={e => setFilterDept(e.target.value)}>
          <option value="all">All Departments</option>
          {allDepts.map(d => <option key={d} value={d}>{d}</option>)}
        </select>

        <select className="form-select" style={{ maxWidth: 140 }} value={filterPriority} onChange={e => setFilterPriority(e.target.value)}>
          <option value="all">All Priorities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>

        <select className="form-select" style={{ maxWidth: 140 }} value={filterOutcome} onChange={e => setFilterOutcome(e.target.value)}>
          <option value="all">All Outcomes</option>
          <option value="WON">Govt Won</option>
          <option value="LOST">Govt Lost</option>
          <option value="PARTIAL">Partial</option>
        </select>
        
        <span className="text-muted" style={{ fontSize: 12 }}>Showing {filtered.length} of {cases.length}</span>
      </div>

      {loading ? (
        <div className="loading"><span className="spinner lg" /></div>
      ) : cases.length === 0 ? (
        <div className="empty">
          <div className="empty-icon">📊</div>
          <div className="empty-title">No verified cases yet</div>
          <p style={{ marginBottom: 14 }}>Upload a judgment, extract, and verify it to see it here.</p>
          <Link to="/" className="btn btn-primary">Get started →</Link>
        </div>
      ) : filtered.length === 0 ? (
        <div className="empty"><div className="empty-icon">🔍</div><div className="empty-title">No results</div></div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {filtered.map(c => {
            const prioBorder = {
              critical: 'var(--p-critical)', high: 'var(--p-high)',
              medium: 'var(--p-medium)', low: 'var(--p-low)'
            }[c.priority] || 'var(--border)'

            return (
              <div key={c.id} className="card" style={{ cursor: 'pointer', borderLeft: `3px solid ${prioBorder}` }}
                onClick={() => setExpanded(expanded === c.id ? null : c.id)}>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 16, alignItems: 'start' }}>
                  <div>
                    {/* Tags row */}
                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 7 }}>
                      <StatusBadge value={c.priority} />
                      <StatusBadge value={c.outcome_for_government?.toLowerCase()} />
                      <StatusBadge value={c.action_type} />
                      {c.critical_flags_count > 0 && (
                        <span className="badge badge-critical">🚨 {c.critical_flags_count} flag{c.critical_flags_count > 1 ? 's' : ''}</span>
                      )}
                    </div>

                    {/* Case identity */}
                    <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--text-1)', marginBottom: 5 }}>
                      {c.case_number
                        ? <><span className="mono text-accent">{c.case_number}</span> — {c.subject_matter || c.original_filename}</>
                        : c.original_filename}
                    </div>

                    {/* Meta row */}
                    <div style={{ display: 'flex', gap: 16, fontSize: 12, color: 'var(--text-3)', flexWrap: 'wrap' }}>
                      {c.court && <span>🏛 {c.court}</span>}
                      {c.date_of_order && <span>📅 {c.date_of_order}</span>}
                      {c.responsible_authority && <span>👤 {c.responsible_authority}</span>}
                    </div>

                    {/* Deadlines */}
                    {(c.compliance_deadline || c.last_date_for_appeal) && (
                      <div style={{ display: 'flex', gap: 12, marginTop: 8, flexWrap: 'wrap' }}>
                        {c.compliance_deadline && (
                          <span style={{ fontSize: 11, color: '#FBBF24', fontWeight: 600 }}>
                            ⏰ Comply by: {c.compliance_deadline}
                          </span>
                        )}
                        {c.last_date_for_appeal && (
                          <span style={{ fontSize: 11, color: '#F87171', fontWeight: 600 }}>
                            ⚖ Appeal by: {c.last_date_for_appeal}
                          </span>
                        )}
                      </div>
                    )}
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 8, flexShrink: 0 }}>
                    <div style={{ fontSize: 11, color: 'var(--text-3)', textAlign: 'right' }}>
                      {c.reviewer_name && <><span style={{ color: 'var(--text-2)', fontWeight: 500 }}>{c.reviewer_name}</span><br /></>}
                      {c.verified_at && new Date(c.verified_at).toLocaleDateString('en-IN')}
                    </div>
                    <Link to={`/cases/${c.id}`} className="btn btn-ghost btn-sm" onClick={ev => ev.stopPropagation()}>
                      Full View
                    </Link>
                  </div>
                </div>

                {/* Expanded summary */}
                {expanded === c.id && c.summary && (
                  <div style={{ marginTop: 14, paddingTop: 14, borderTop: '1px solid var(--border)', fontSize: 13, color: 'var(--text-2)', lineHeight: 1.7 }}>
                    {c.urgency_reason && (
                      <div className="alert alert-warn" style={{ fontSize: 12, marginBottom: 10 }}>⚠️ {c.urgency_reason}</div>
                    )}
                    <strong style={{ color: 'var(--text-3)', fontSize: 11, textTransform: 'uppercase', letterSpacing: '.5px' }}>Summary: </strong>
                    {c.summary}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
