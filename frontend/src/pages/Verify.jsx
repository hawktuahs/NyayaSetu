import { useEffect, useState } from 'react'
import { Link, useParams, useNavigate } from 'react-router-dom'
import { getCase, submitVerification, getPdf } from '../api/client'
import StatusBadge from '../components/StatusBadge'
import ConfBar from '../components/ConfBar'
import DocumentChatbot from '../components/DocumentChatbot'
import toast from 'react-hot-toast'

function CheckItem({ item, caseId, index }) {
  const checkId = `check-${caseId}-${index}`;
  const [checked, setChecked] = useState(() => localStorage.getItem(checkId) === 'true');
  const toggle = () => {
    const next = !checked;
    setChecked(next);
    localStorage.setItem(checkId, next);
  };
  return (
    <div key={index} style={{ display: 'flex', gap: 10, fontSize: 12, marginBottom: 6, cursor: 'pointer', alignItems: 'flex-start' }} onClick={toggle}>
      <input type="checkbox" checked={checked} onChange={() => {}} style={{ marginTop: 2, cursor: 'pointer' }} />
      <div style={{ flex: 1, opacity: checked ? 0.6 : 1, textDecoration: checked ? 'line-through' : 'none', color: 'var(--text-1)' }}>
        {item.item}
        <div style={{ fontSize: 10, color: 'var(--text-3)' }}>{item.responsible_department}</div>
      </div>
    </div>
  );
}

export default function Verify() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [reviewerName, setReviewerName] = useState('')
  const [reviewerDesig, setReviewerDesig] = useState('')
  const [comment, setComment] = useState('')
  const [editing, setEditing] = useState(false)
  const [edits, setEdits] = useState({})
  const [editsAP, setEditsAP] = useState({})
  const [submitting, setSubmitting] = useState(false)
  const [pdfPage, setPdfPage] = useState(1)
  const [pdfSearch, setPdfSearch] = useState('')

  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    getCase(id).then(r => {
      setData(r.data)
      if (r.data.extraction) setEdits({ ...r.data.extraction })
      if (r.data.action_plan) setEditsAP({ ...r.data.action_plan })
      setLoading(false)
    }).catch(err => {
      console.error(err)
      setError(err.response?.data?.detail || 'Could not load case')
      setLoading(false)
      toast.error('Could not load case')
    })
  }, [id])

  const submit = async (decision) => {
    if (!reviewerName.trim()) { toast.error('Reviewer name required'); return }
    setSubmitting(true)
    try {
      await submitVerification(id, {
        reviewer_name: reviewerName,
        reviewer_designation: reviewerDesig,
        decision,
        comment,
        edited_extraction: editing ? edits : null,
        edited_action_plan: editing ? editsAP : null,
      })
      toast.success(decision === 'approved' ? '✅ Approved — case moved to dashboard' : '❌ Rejected')
      navigate('/verify')
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Submission failed')
      setSubmitting(false)
    }
  }

  if (loading) return <div className="loading"><span className="spinner lg" /></div>
  if (error) return (
    <div className="page fade-in">
      <div className="empty">
        <div className="empty-icon">❌</div>
        <div className="empty-title">Error Loading Case</div>
        <p style={{ marginBottom: 20 }}>{error}</p>
        <Link to="/verify" className="btn btn-ghost">Return to Queue</Link>
      </div>
    </div>
  )
  if (!data) return <div className="empty">No case data found</div>
  const e = data.extraction
  const p = data.action_plan
  const conf = e?.confidence_scores || {}

  const EditField = ({ k, label }) => {
    const pages = e?.source_pages?.[k]
    const quote = e?.source_quotes?.[k]
    return (
      <div className="field">
        <div className="field-label" style={{ display: 'flex', alignItems: 'center' }}>
          {label}
          {conf[k] !== undefined && <ConfBar score={conf[k]} />}
          {pages?.length > 0 && (
            <button 
              className="btn btn-ghost" 
              style={{ padding: '0 4px', fontSize: 10, marginLeft: 'auto', height: 18, minHeight: 18, color: 'var(--saffron)' }} 
              onClick={() => { setPdfPage(pages[0]); setPdfSearch(quote || ''); }} 
              title={quote ? `Source Quote:\n"${quote}"` : "Jump to source page"}
            >
              📄 P.{pages[0]}
            </button>
          )}
        </div>
        {editing
          ? <input className="form-input" value={edits[k] || ''} onChange={ev => setEdits(p => ({ ...p, [k]: ev.target.value }))} style={{ marginTop: 4 }} />
          : edits[k] ? <div className="field-val" title={quote ? `Source: "${quote}"` : ''}>{edits[k]}</div> : <div className="field-null">—</div>}
      </div>
    )
  }

  return (
    <div className="page fade-in">
      <div className="ph-back">
        <Link to="/verify" className="text-muted" style={{ fontSize: 12, textDecoration: 'none' }}>← Review Queue</Link>
      </div>

      <div className="ph">
        <div className="ph-row">
          <div>
            <h1 className="ph-title" style={{ fontSize: 18 }}>Review: {data.original_filename}</h1>
            <div style={{ display: 'flex', gap: 8, marginTop: 6, flexWrap: 'wrap' }}>
              <StatusBadge value={data.status} />
              {data.is_scanned && <span className="badge badge-warn">📸 Scanned</span>}
              {e?.case_number && <span className="tag mono">{e.case_number}</span>}
              {e?.date_of_order && <span className="tag">📅 {e.date_of_order}</span>}
              <span className="text-muted" style={{ fontSize: 12 }}>{data.page_count} pages</span>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-ghost" onClick={() => window.print()}>⎙ Print Report</button>
            <button className={`btn ${editing ? 'btn-primary' : 'btn-ghost'}`} onClick={() => setEditing(v => !v)}>
              {editing ? '✓ Editing Mode' : '✏ Edit Fields'}
            </button>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, alignItems: 'start' }}>
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <p className="sh">Original Judgment PDF</p>
            <div style={{ fontSize: 11, color: 'var(--text-3)' }}>Page {pdfPage}</div>
          </div>
          <iframe
            key={`${pdfPage}-${pdfSearch}`}
            src={getPdf(id) + `#page=${pdfPage}${pdfSearch ? '&search=' + encodeURIComponent(pdfSearch) : ''}`}
            width="100%" height="750px"
            style={{ border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)' }}
          />
        </div>

        {/* Right: Extracted data */}
        <div>
          <p className="sh">AI Extracted Data {editing && <span style={{ color: 'var(--saffron-light)', fontStyle: 'normal', textTransform: 'none', fontSize: 11, letterSpacing: 0 }}>— Edit mode active</span>}</p>

          {data.extraction_error && (
            <div className="alert alert-warn" style={{ marginBottom: 12, fontSize: 12 }}>{data.extraction_error}</div>
          )}

          {e ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <div className="fields" style={{ gridTemplateColumns: '1fr 1fr' }}>
                <EditField k="case_number" label="Case Number" />
                <EditField k="court" label="Court" />
                <EditField k="date_of_order" label="Date of Order" />
                <EditField k="bench_type" label="Bench Type" />
              </div>

              <div className="field">
                <div className="field-label">Outcome for Government <ConfBar score={conf.outcome_for_government} /></div>
                {editing
                  ? <select className="form-select" style={{ marginTop: 4 }} value={edits.outcome_for_government || ''} onChange={ev => setEdits(p => ({ ...p, outcome_for_government: ev.target.value }))}>
                      <option value="">—</option>
                      <option value="WON">WON</option>
                      <option value="LOST">LOST</option>
                      <option value="PARTIAL">PARTIAL</option>
                    </select>
                  : <div className={`field-val ${edits.outcome_for_government === 'WON' ? 'text-won' : edits.outcome_for_government === 'LOST' ? 'text-lost' : ''}`} style={{ fontWeight: 700 }}>
                      {edits.outcome_for_government || '—'}
                    </div>}
              </div>

              <div className="field">
                <div className="field-label">Operative Order</div>
                {editing
                  ? <textarea className="form-textarea" rows={4} value={edits.operative_order || ''} onChange={ev => setEdits(p => ({ ...p, operative_order: ev.target.value }))} />
                  : <div className="operative-box" style={{ fontSize: 12, maxHeight: 120, overflowY: 'auto' }}>{edits.operative_order || '—'}</div>}
              </div>

              <div className="field">
                <div className="field-label">Key Directions</div>
                <div style={{ fontSize: 12, color: 'var(--text-2)', lineHeight: 1.6 }}>
                  {e.key_directions?.map((d,i) => <div key={i}>• {d}</div>)}
                </div>
              </div>

              <div className="fields" style={{ gridTemplateColumns: '1fr 1fr' }}>
                <EditField k="compliance_deadline" label="Compliance Deadline" />
                <EditField k="last_date_for_appeal" label="Last Date for Appeal" />
              </div>

              <EditField k="subject_matter" label="Subject Matter" />
              <EditField k="summary" label="AI Summary" />
            </div>
          ) : (
            <div className="alert alert-warn">No extraction data available. Re-extract from the case detail page.</div>
          )}

          {/* Action Plan Summary */}
          {p && (
            <div style={{ marginTop: 16 }}>
              <p className="sh">Action Plan (AI Assisted)</p>
              <div className="card" style={{ borderLeft: editsAP.priority === 'critical' ? '3px solid var(--p-critical)' : '3px solid var(--saffron)' }}>
                {editing ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    <div className="fields" style={{ gridTemplateColumns: '1fr 1fr' }}>
                      <div className="form-group">
                        <label className="form-label">Action Type</label>
                        <select className="form-select" value={editsAP.action_type || ''} onChange={ev => setEditsAP(p => ({ ...p, action_type: ev.target.value }))}>
                          <option value="proceed_with_implementation">Proceed with Implementation</option>
                          <option value="comply_with_order">Comply with Order</option>
                          <option value="file_appeal">File Appeal</option>
                          <option value="seek_legal_opinion">Seek Legal Opinion</option>
                          <option value="monitor_pending_proceedings">Monitor Pending Proceedings</option>
                        </select>
                      </div>
                      <div className="form-group">
                        <label className="form-label">Priority</label>
                        <select className="form-select" value={editsAP.priority || ''} onChange={ev => setEditsAP(p => ({ ...p, priority: ev.target.value }))}>
                          <option value="critical">Critical</option>
                          <option value="high">High</option>
                          <option value="medium">Medium</option>
                          <option value="low">Low</option>
                        </select>
                      </div>
                    </div>
                    <div className="form-group">
                      <label className="form-label">Urgency Reason</label>
                      <input className="form-input" value={editsAP.urgency_reason || ''} onChange={ev => setEditsAP(p => ({ ...p, urgency_reason: ev.target.value }))} />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Responsible Authority</label>
                      <input className="form-input" value={editsAP.responsible_authority || ''} onChange={ev => setEditsAP(p => ({ ...p, responsible_authority: ev.target.value }))} />
                    </div>
                  </div>
                ) : (
                  <>
                    <div style={{ display: 'flex', gap: 8, marginBottom: 8, flexWrap: 'wrap' }}>
                      <StatusBadge value={editsAP.action_type} />
                      <StatusBadge value={editsAP.priority} />
                    </div>
                    {editsAP.urgency_reason && <div style={{ fontSize: 13, color: 'var(--text-1)', fontWeight: 600, marginBottom: 4 }}>{editsAP.urgency_reason}</div>}
                    {editsAP.responsible_authority && <div style={{ fontSize: 12, color: 'var(--text-3)', marginBottom: 8 }}>Responsible: {editsAP.responsible_authority}</div>}
                  </>
                )}

                {p.ai_reasoning && (
                  <div className="alert alert-info" style={{ fontSize: 11, marginBottom: 12, opacity: 0.8 }}>
                    <strong>AI Insight:</strong> {p.ai_reasoning}
                  </div>
                )}

                {p.technical_reference && (
                  <div className="alert alert-info" style={{ fontSize: 11, marginBottom: 12, opacity: 0.8, borderLeftColor: 'var(--saffron)' }}>
                    <strong>Technical Reference:</strong> {p.technical_reference}
                  </div>
                )}

                {p.critical_flags?.length > 0 && (
                  <div className="alert alert-error" style={{ fontSize: 12 }}>
                    🚨 {p.critical_flags.length} critical flag{p.critical_flags.length > 1 ? 's' : ''}: {p.critical_flags[0]?.flag || p.critical_flags[0]}
                  </div>
                )}
                
                {/* Timeline and Checklist remain interactive via their sub-components */}
                {p.compliance_timeline?.length > 0 && (
                  <div style={{ marginTop: 12, padding: '10px 12px', background: 'var(--bg-2)', borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}>
                    <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-3)', marginBottom: 6, textTransform: 'uppercase' }}>Compliance Timeline</div>
                    {p.compliance_timeline.map((evt, i) => (
                      <div key={i} style={{ display: 'flex', gap: 8, fontSize: 12, marginBottom: 4 }}>
                        <span style={{ color: 'var(--saffron)' }}>•</span>
                        <div style={{ flex: 1, color: 'var(--text-1)' }}>{evt.event}</div>
                        {evt.date_or_duration && <span style={{ color: 'var(--text-2)', whiteSpace: 'nowrap' }}>⏰ {evt.date_or_duration}</span>}
                      </div>
                    ))}
                  </div>
                )}
                {p.compliance_checklist?.length > 0 && (
                  <div style={{ marginTop: 12, padding: '10px 12px', background: 'var(--bg-2)', borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}>
                    <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-3)', marginBottom: 8, textTransform: 'uppercase' }}>Compliance Checklist</div>
                    {p.compliance_checklist.map((item, i) => (
                      <CheckItem key={i} item={item} caseId={id} index={i} />
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Verification decision */}
          <div style={{ marginTop: 20 }}>
            <p className="sh">Verification Decision</p>
            <div className="card">
              <div className="form-group">
                <label className="form-label">Reviewer Name *</label>
                <input className="form-input" value={reviewerName} onChange={e => setReviewerName(e.target.value)} placeholder="Your full name" />
              </div>
              <div className="form-group">
                <label className="form-label">Designation</label>
                <input className="form-input" value={reviewerDesig} onChange={e => setReviewerDesig(e.target.value)} placeholder="e.g. Deputy Secretary, Finance" />
              </div>
              <div className="form-group">
                <label className="form-label">Comments / Notes</label>
                <textarea className="form-textarea" value={comment} onChange={e => setComment(e.target.value)} placeholder="Reason for approval/rejection, or corrections made…" />
              </div>

              <div className="alert alert-info" style={{ fontSize: 12, marginBottom: 14 }}>
                Only approved records will appear on the government dashboard. This action is logged for audit.
              </div>

              <div style={{ display: 'flex', gap: 10 }}>
                <button className="btn btn-success" style={{ flex: 1 }} onClick={() => submit('approved')} disabled={submitting || !e}>
                  {submitting ? <span className="spinner" /> : '✓'} Approve
                </button>
                <button className="btn btn-danger" onClick={() => submit('rejected')} disabled={submitting}>
                  ✕ Reject
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      <DocumentChatbot caseId={id} onJumpToPage={(page, quote) => { setPdfPage(page); setPdfSearch(quote || ''); }} />
    </div>
  )
}
