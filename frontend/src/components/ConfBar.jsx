/* confidence 0-1 displayed as a bar */
export default function ConfBar({ score }) {
  if (score === undefined || score === null) return null
  const pct = Math.round(score * 100)
  const cls = pct >= 70 ? 'hi' : pct >= 40 ? 'md' : 'lo'
  return (
    <div className="conf">
      <div className="conf-track">
        <div className={`conf-fill ${cls}`} style={{ width: `${pct}%` }} />
      </div>
      <span className={`conf-pct ${cls}`}>{pct}%</span>
    </div>
  )
}
