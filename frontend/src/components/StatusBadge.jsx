export default function StatusBadge({ value }) {
  if (!value) return null
  const n = String(value).toLowerCase().replace(/\s+/g, '_')
  const labels = {
    pending_extraction: 'Awaiting Extract',
    extracting: 'Extracting…',
    pending_verification: 'Needs Review',
    approved: 'Approved',
    rejected: 'Rejected',
    critical: 'Critical',
    high: 'High',
    medium: 'Medium',
    low: 'Low',
    won: 'Govt Won',
    lost: 'Govt Lost',
    partial: 'Partial',
    not_applicable: 'N/A',
    proceed_with_implementation: 'Proceed',
    comply_with_order: 'Comply',
    file_appeal: 'File Appeal',
    seek_legal_opinion: 'Seek Opinion',
    monitor_pending_proceedings: 'Monitor',
  }
  return <span className={`badge badge-${n}`}>{labels[n] || value}</span>
}
