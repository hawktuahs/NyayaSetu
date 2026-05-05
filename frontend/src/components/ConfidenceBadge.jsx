/**
 * Confidence level badge + bar for AI-extracted fields.
 * score: 0.0 – 1.0
 */
export default function ConfidenceBadge({ score, showBar = false }) {
  if (score === undefined || score === null) return null

  const pct = Math.round(score * 100)
  const level = score >= 0.75 ? 'high' : score >= 0.5 ? 'medium' : 'low'
  const label = { high: 'High', medium: 'Medium', low: 'Low' }[level]

  if (showBar) {
    return (
      <div className="confidence-bar">
        <div className="confidence-bar-track">
          <div
            className={`confidence-bar-fill ${level}`}
            style={{ width: `${pct}%` }}
          />
        </div>
        <span className={`confidence-pct ${level}`}>{pct}%</span>
      </div>
    )
  }

  return (
    <span
      className={`badge badge-${level === 'high' ? 'approved' : level === 'medium' ? 'pending' : 'rejected'}`}
      title={`Confidence: ${pct}%`}
      style={{ fontSize: '10px' }}
    >
      {label} ({pct}%)
    </span>
  )
}
