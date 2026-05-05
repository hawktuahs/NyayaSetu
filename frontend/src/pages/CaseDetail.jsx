import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getCase, retryExtraction, getPdf } from '../api/client'
import StatusBadge from '../components/StatusBadge'
import ConfBar from '../components/ConfBar'
import DocumentChatbot from '../components/DocumentChatbot'
import toast from 'react-hot-toast'

function Field({ label, val, conf, pages, quote, onJumpToPage }) {
  return (
    <div className="field">
      <div className="field-label" style={{ display: 'flex', alignItems: 'center' }}>
        {label}
        {conf !== undefined && <ConfBar score={conf} />}
        {pages?.length > 0 && (
          <button 
            className="btn btn-ghost" 
            style={{ padding: '0 4px', fontSize: 10, marginLeft: 'auto', height: 18, minHeight: 18, color: 'var(--saffron)' }} 
            onClick={() => onJumpToPage(pages[0])} 
            title={quote ? `Source Quote:\n"${quote}"` : "Jump to source page"}
          >
            📄 P.{pages[0]}
          </button>
        )}
      </div>
      {val
        ? <div className="field-val" title={quote ? `Source: "${quote}"` : ''}>{val}</div>
        : <div className="field-null">—</div>}
    </div>
  )
}

function OutcomeBanner({ outcome, govOutcome }) {
  if (!govOutcome) return null
  const map = {
    WON: { cls: 'won', icon: '✅', title: 'Government Prevailed', sub: outcome },
    LOST: { cls: 'lost', icon: '⚠️', title: 'Government Did Not Prevail', sub: outcome },
    PARTIAL: { cls: 'partial', icon: '⚖️', title: 'Partial Outcome', sub: outcome },
  }
  const m = map[govOutcome] || map['PARTIAL']
  return (
    <div className={`outcome-banner ${m.cls}`}>
      <span className="outcome-banner-icon">{m.icon}</span>
      <div>
        <div className="outcome-banner-title">{m.title}</div>
        <div className="outcome-banner-sub">{m.sub}</div>
      </div>
    </div>
  )
}

function CheckItem({ item, caseId, index }) {
  const checkId = `check-${caseId}-${index}`;
  const [checked, setChecked] = useState(() => localStorage.getItem(checkId) === 'true');
  const toggle = () => {
    const next = !checked;
    setChecked(next);
    localStorage.setItem(checkId, next);
  };
  return (
    <div className="checklist-item" onClick={toggle} style={{ cursor: 'pointer' }}>
      <input 
        type="checkbox" 
        checked={checked} 
        onChange={() => {}} 
        style={{ width: 16, height: 16, cursor: 'pointer', accentColor: 'var(--saffron)' }} 
      />
      <div className="check-text" style={{ opacity: checked ? 0.5 : 1, textDecoration: checked ? 'line-through' : 'none' }}>
        {item.item}
        <div className="check-dept">{item.responsible_department}</div>
      </div>
      {item.target_date && <span className="check-date">{item.target_date}</span>}
    </div>
  );
}

export default function CaseDetail() {
  const { id } = useParams()
  const [data, setData] = useState(null)
  const [tab, setTab] = useState('extraction')
  const [retrying, setRetrying] = useState(false)
  const [pdfPage, setPdfPage] = useState(1)
  const [pdfSearch, setPdfSearch] = useState('')

  const jumpToPage = (pageNum, quote) => {
    setPdfPage(pageNum)
    setPdfSearch(quote || '')
    setTab('pdf')
  }

  useEffect(() => {
    let interval
    const load = async () => {
      try { const r = await getCase(id); setData(r.data) } catch {}
    }
    load()
    interval = setInterval(() => {
      if (data?.status === 'extracting' || data?.status === 'pending_extraction') load()
    }, 4000)
    return () => clearInterval(interval)
  }, [id, data?.status])

  const retry = async () => {
    setRetrying(true)
    try {
      await retryExtraction(id)
      toast.success('Re-extraction triggered')
      setTimeout(async () => { const r = await getCase(id); setData(r.data); setRetrying(false) }, 1000)
    } catch { toast.error('Retry failed'); setRetrying(false) }
  }

  if (!data) return <div className="loading"><span className="spinner lg" /></div>

  const e = data.extraction
  const p = data.action_plan
  const conf = e?.confidence_scores || {}
  const pdfUrl = `/api/cases/${id}/pdf`
  const isExtracting = data.status === 'extracting' || data.status === 'pending_extraction'

  return (
    <div className="page fade-in">
      <div className="ph">
        <div className="ph-row">
          <div>
            <div className="ph-back">
              <Link to="/cases" style={{ textDecoration: 'none', color: 'var(--text-3)' }}>← All Cases</Link>
            </div>
            <h1 className="ph-title" style={{ fontSize: 18 }}>{data.original_filename}</h1>
            <div style={{ display: 'flex', gap: 8, marginTop: 6, flexWrap: 'wrap', alignItems: 'center' }}>
              <StatusBadge value={data.status} />
              {data.is_scanned && <span className="badge badge-warn">📸 Scanned</span>}
              {e?.case_number && <span className="tag mono">{e.case_number}</span>}
              {e?.date_of_order && <span className="tag">📅 {e.date_of_order}</span>}
              <span className="text-muted" style={{ fontSize: 12 }}>{data.page_count} pages</span>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {data.status === 'approved' && (
              <button className="btn btn-primary" onClick={() => window.print()}>⎙ Print Action Plan</button>
            )}
            {data.status === 'pending_verification' && (
              <Link to={`/verify/${id}`} className="btn btn-primary">✓ Review Now</Link>
            )}
            <button className="btn btn-ghost" onClick={retry} disabled={retrying || isExtracting}>
              {retrying ? <span className="spinner" /> : '↺'} Re-extract
            </button>
          </div>
        </div>
      </div>

      {isExtracting && (
        <div className="alert alert-info" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span className="spinner" />
          AI is reading this judgment… This may take 1–3 minutes. Page will auto-update.
        </div>
      )}

      {data.extraction_error && (
        <div className="alert alert-warn">{data.extraction_error}</div>
      )}

      {e && (
        <>
          <OutcomeBanner outcome={e.outcome} govOutcome={e.outcome_for_government} />

          <div className="tabs">
            {[['extraction', '📋 Extracted Data'], ['actionplan', '⚡ Action Plan'], ['pdf', '📄 View PDF']].map(([k, l]) => (
              <button key={k} className={`tab ${tab === k ? 'active' : ''}`} onClick={() => setTab(k)}>{l}</button>
            ))}
          </div>

          {tab === 'extraction' && (
            <div className="fade-in">
              <div className="sh">Case Identity</div>
              <div className="fields" style={{ marginBottom: 20 }}>
                <Field label="Case Number" val={e.case_number} conf={conf.case_number} pages={e.source_pages?.case_number} quote={e.source_quotes?.case_number} onJumpToPage={jumpToPage} />
                <Field label="Court" val={e.court} conf={conf.court} pages={e.source_pages?.court} quote={e.source_quotes?.court} onJumpToPage={jumpToPage} />
                <Field label="Bench" val={e.bench_type} />
                <Field label="Date of Order" val={e.date_of_order} conf={conf.date_of_order} pages={e.source_pages?.date_of_order} quote={e.source_quotes?.date_of_order} onJumpToPage={jumpToPage} />
                <Field label="Case Type" val={e.case_type} />
                <Field label="Subject Matter" val={e.subject_matter} />
              </div>

              <div className="sh">Parties</div>
              <div className="fields" style={{ marginBottom: 20 }}>
                <div className="field">
                  <div className="field-label">Appellants</div>
                  {e.appellants?.length ? e.appellants.map((a,i) => <div key={i} className="field-val">{a}</div>) : <div className="field-null">—</div>}
                </div>
                <div className="field">
                  <div className="field-label">Respondents</div>
                  {e.respondents?.length ? e.respondents.map((r,i) => <div key={i} className="field-val">{r}</div>) : <div className="field-null">—</div>}
                </div>
                <Field label="Appellant Advocate" val={e.appellant_advocate} />
                <Field label="Respondent Advocate" val={e.respondent_advocate} />
                <div className="field">
                  <div className="field-label">Bench / Judges</div>
                  {e.judges?.length ? e.judges.map((j,i) => <div key={i} className="field-val">{j}</div>) : <div className="field-null">—</div>}
                </div>
              </div>

              <div className="sh">Government & Outcome</div>
              <div className="fields" style={{ marginBottom: 20 }}>
                <Field label="Government as" val={e.government_party} conf={conf.outcome_for_government} />
                <div className="field">
                  <div className="field-label">Government Departments</div>
                  {e.government_departments?.length ? e.government_departments.map((d,i) => <div key={i} className="field-val">{d}</div>) : <div className="field-null">—</div>}
                </div>
                <Field label="Outcome" val={e.outcome} conf={conf.outcome} pages={e.source_pages?.outcome} quote={e.source_quotes?.outcome} onJumpToPage={jumpToPage} />
                <Field label="Outcome for Govt" val={e.outcome_for_government} conf={conf.outcome_for_government} />
                <Field label="Stay Status" val={e.stay_status} pages={e.source_pages?.stay_status} quote={e.source_quotes?.stay_status} onJumpToPage={jumpToPage} />
              </div>

              <div className="sh" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                Operative Order
                {e.source_pages?.operative_order?.length > 0 && (
                  <button className="btn btn-ghost" style={{ padding: '0 4px', fontSize: 10, height: 18, minHeight: 18, color: 'var(--saffron)' }} onClick={() => jumpToPage(e.source_pages.operative_order[0])}>
                    📄 P.{e.source_pages.operative_order[0]}
                  </button>
                )}
              </div>
              {e.operative_order
                ? <div className="operative-box" style={{ marginBottom: 20 }}>{e.operative_order}</div>
                : <div className="field-null" style={{ marginBottom: 20 }}>Not extracted</div>}

              <div className="sh">Key Directions</div>
              <div style={{ marginBottom: 20 }}>
                {e.key_directions?.length
                  ? e.key_directions.map((d, i) => (
                    <div key={i} style={{ display: 'flex', gap: 12, marginBottom: 8, alignItems: 'flex-start' }}>
                      <span style={{ color: 'var(--saffron-light)', fontWeight: 700, flexShrink: 0, marginTop: 1 }}>{i + 1}.</span>
                      <span style={{ fontSize: 13, color: 'var(--text-1)', lineHeight: 1.6 }}>{d}</span>
                    </div>
                  ))
                  : <div className="field-null">None extracted</div>}
              </div>

              <div className="sh">Timelines</div>
              <div className="fields" style={{ marginBottom: 20 }}>
                <Field label="Compliance Deadline" val={e.compliance_deadline} conf={conf.compliance_deadline} pages={e.source_pages?.compliance_deadline} quote={e.source_quotes?.compliance_deadline} onJumpToPage={jumpToPage} />
                <Field label="Appeal Limitation Period" val={e.appeal_limitation_period} conf={conf.appeal_limitation_period} pages={e.source_pages?.appeal_limitation_period} quote={e.source_quotes?.appeal_limitation_period} onJumpToPage={jumpToPage} />
                <Field label="Last Date for Appeal" val={e.last_date_for_appeal} />
                <Field label="Next Proceedings" val={e.next_proceedings} pages={e.source_pages?.next_proceedings} quote={e.source_quotes?.next_proceedings} onJumpToPage={jumpToPage} />
              </div>

              <div className="sh">Relevant Laws</div>
              <div style={{ marginBottom: 20 }}>
                {e.relevant_laws?.length ? e.relevant_laws.map((l,i) => <span key={i} className="tag">{l}</span>) : <div className="field-null">None identified</div>}
              </div>

              <div className="sh">AI Summary</div>
              <div className="card" style={{ marginBottom: 8 }}>
                <p style={{ fontSize: 13, color: 'var(--text-2)', lineHeight: 1.7 }}>{e.summary || '—'}</p>
              </div>
            </div>
          )}

          {tab === 'actionplan' && p && (
            <div className="fade-in">
              {/* Header */}
              <div className="card" style={{ marginBottom: 16, borderLeft: '3px solid var(--saffron)' }}>
                <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'flex-start' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', gap: 8, marginBottom: 8, flexWrap: 'wrap' }}>
                      <StatusBadge value={p.action_type} />
                      <StatusBadge value={p.priority} />
                    </div>
                    <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-1)', marginBottom: 4 }}>
                      {p.urgency_reason}
                    </div>
                    {p.responsible_authority && (
                      <div style={{ fontSize: 12, color: 'var(--text-3)' }}>
                        Responsible: <strong style={{ color: 'var(--text-2)' }}>{p.responsible_authority}</strong>
                      </div>
                    )}
                  </div>
                  {p.risk_if_delayed && (
                    <div style={{ maxWidth: 280, fontSize: 12, color: '#FBBF24', background: 'rgba(217,119,6,.08)', border: '1px solid rgba(217,119,6,.2)', padding: '10px 12px', borderRadius: 'var(--radius)' }}>
                      ⚠️ Risk if delayed: {p.risk_if_delayed}
                    </div>
                  )}
                </div>
              </div>

              {/* Critical flags */}
              {p.critical_flags?.length > 0 && (
                <>
                  <div className="sh">🔴 Critical Flags</div>
                  {p.critical_flags.map((f, i) => (
                    <div key={i} className="flag-card">
                      <span className="flag-icon">🚨</span>
                      <div>
                  <div className="flag-title">{f.flag || f}</div>
                  <div className="flag-detail">{f.detail || ''}</div>
                  {f.action_required && <div className="flag-detail" style={{ color: 'var(--text-1)', marginTop: 4 }}>→ {f.action_required}</div>}
                  {f.deadline && <div className="flag-deadline">⏰ Deadline: {f.deadline}</div>}
                      </div>
                    </div>
                  ))}
                </>
              )}

              {/* Timeline (NEW) */}
              {p.compliance_timeline?.length > 0 && (
                <>
                  <div className="sh" style={{ marginTop: 20 }}>Timeline of Events</div>
                  <div className="card" style={{ padding: '16px 20px' }}>
                    <div style={{ position: 'relative', borderLeft: '2px solid var(--border)', marginLeft: 8, paddingLeft: 20, display: 'flex', flexDirection: 'column', gap: 16 }}>
                      {p.compliance_timeline.map((evt, i) => (
                        <div key={i} style={{ position: 'relative' }}>
                          <div style={{ position: 'absolute', left: -26, top: 4, width: 10, height: 10, borderRadius: '50%', background: 'var(--saffron)', border: '2px solid var(--bg-1)' }} />
                          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-1)' }}>{evt.event}</div>
                          {evt.date_or_duration && <div style={{ fontSize: 12, color: 'var(--p-critical)', marginTop: 4 }}>⏰ {evt.date_or_duration}</div>}
                          {evt.responsible_party && <div style={{ fontSize: 12, color: 'var(--text-3)', marginTop: 2 }}>👤 {evt.responsible_party}</div>}
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}

              {/* Immediate actions */}
              {p.immediate_actions?.length > 0 && (
                <>
                  <div className="sh" style={{ marginTop: 20 }}>Immediate Actions (48 hours)</div>
                  {p.immediate_actions.map((a, i) => (
                    <div key={i} className="step-row">
                      <div className={`step-num ${a.is_critical ? 'critical' : 'normal'}`}>{a.step}</div>
                      <div>
                        <div className="step-action">{a.action}</div>
                        <div className="step-meta">{a.responsible_officer}</div>
                      </div>
                      {a.deadline && <span className="tag" style={{ fontSize: 11, whiteSpace: 'nowrap' }}>⏰ {a.deadline}</span>}
                    </div>
                  ))}
                </>
              )}

              {/* Short-term actions */}
              {p.short_term_actions?.length > 0 && (
                <>
                  <div className="sh" style={{ marginTop: 20 }}>Short-term Actions</div>
                  {p.short_term_actions.map((a, i) => (
                    <div key={i} className="step-row">
                      <div className="step-num normal">{a.step}</div>
                      <div>
                        <div className="step-action">{a.action}</div>
                        <div className="step-meta">{a.responsible_officer}</div>
                      </div>
                      {a.deadline && <span className="tag" style={{ fontSize: 11 }}>⏰ {a.deadline}</span>}
                    </div>
                  ))}
                </>
              )}

              {/* Appeal assessment */}
              {p.appeal_assessment && (
                <>
                  <div className="sh" style={{ marginTop: 20 }}>Appeal Assessment</div>
                  <div className="card">
                    <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                      {p.appeal_assessment.last_date && (
                        <div className="deadline-box" style={{ flex: '0 0 200px' }}>
                          <div className="deadline-title">⏰ Appeal Deadline</div>
                          <div className="deadline-val">{p.appeal_assessment.last_date}</div>
                          <div className="deadline-sub">{p.appeal_assessment.limitation_period}</div>
                        </div>
                      )}
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-1)', marginBottom: 6 }}>
                          {p.appeal_assessment.recommendation}
                        </div>
                        {p.appeal_assessment.grounds_for_appeal && (
                          <div style={{ fontSize: 12, color: 'var(--text-2)', lineHeight: 1.6 }}>
                            {p.appeal_assessment.grounds_for_appeal}
                          </div>
                        )}
                        {p.appeal_assessment.appeal_forum && (
                          <div style={{ fontSize: 12, color: 'var(--text-3)', marginTop: 6 }}>
                            Forum: {p.appeal_assessment.appeal_forum}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </>
              )}

              {/* Compliance checklist */}
              {p.compliance_checklist?.length > 0 && (
                <>
                  <div className="sh" style={{ marginTop: 20 }}>Compliance Checklist</div>
                  <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                    {p.compliance_checklist.map((item, i) => (
                      <CheckItem key={i} item={item} caseId={data.id} index={i} />
                    ))}
                  </div>
                </>
              )}

              {/* AI reasoning */}
              {p.ai_reasoning && (
                <div className="alert alert-info" style={{ marginTop: 16 }}>
                  <strong>AI Reasoning:</strong> {p.ai_reasoning}
                </div>
              )}
              
              {/* Technical Reference */}
              {p.technical_reference && (
                <div className="alert alert-info" style={{ marginTop: 16, borderLeftColor: 'var(--saffron)' }}>
                  <strong>Technical Reference:</strong> {p.technical_reference}
                </div>
              )}
            </div>
          )}

          {tab === 'actionplan' && !p && (
            <div className="empty"><div className="empty-icon">⏳</div><div className="empty-title">Action plan generating…</div></div>
          )}

          {tab === 'pdf' && (
            <div className="fade-in" style={{ height: '75vh' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <div style={{ fontSize: 12, color: 'var(--text-2)' }}>Viewing Original PDF</div>
                <div style={{ fontSize: 12, color: 'var(--text-3)' }}>Page {pdfPage}</div>
              </div>
              <iframe 
                key={`${pdfPage}-${pdfSearch}`} 
                src={`${pdfUrl}#page=${pdfPage}${pdfSearch ? '&search=' + encodeURIComponent(pdfSearch) : ''}`} 
                width="100%" height="100%" 
                style={{ border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)' }} 
              />
            </div>
          )}
        </>
      )}

      {!e && !isExtracting && (
        <div className="empty">
          <div className="empty-icon">🤖</div>
          <div className="empty-title">No extraction yet</div>
          <button className="btn btn-primary" onClick={retry} disabled={retrying}>
            {retrying ? <span className="spinner" /> : '↺ Start Extraction'}
          </button>
        </div>
      )}

      <DocumentChatbot caseId={id} onJumpToPage={jumpToPage} />
    </div>
  )
}
