import { NavLink, Link } from 'react-router-dom'
import { useEffect } from 'react'
import { useAppStore } from '../store'

export default function Navbar() {
  const { llmStatus, pendingCount, fetchHealth } = useAppStore()

  useEffect(() => {
    fetchHealth()
    const t = setInterval(fetchHealth, 30000)
    return () => clearInterval(t)
  }, [])

  return (
    <nav className="nav">
      <Link to="/" className="nav-brand">
        <div className="nav-logo">⚖</div>
        <div>
          <div className="nav-name">NyayaSetu</div>
          <div className="nav-sub">न्यायसेतु · Court Case Monitor</div>
        </div>
      </Link>

      <div className="nav-links">
        {[
          { to: '/', label: 'Upload', icon: '↑', exact: true },
          { to: '/cases', label: 'All Cases', icon: '◻' },
          { to: '/verify', label: 'Review Queue', icon: '✓', badge: pendingCount },
          { to: '/dashboard', label: 'Dashboard', icon: '▦' },
        ].map(({ to, label, icon, exact, badge }) => (
          <NavLink key={to} to={to} end={exact} className={({ isActive }) => isActive ? 'active' : ''}>
            <span>{icon}</span>{label}
            {badge > 0 && <span className="nav-badge">{badge}</span>}
          </NavLink>
        ))}
      </div>

      <div className="nav-end">
        {llmStatus && (
          <div className="llm-pill">
            <span className={`dot ${llmStatus.llm_available ? 'on' : 'off'}`} />
            <span>{llmStatus.llm_available ? llmStatus.llm_model : 'LLM offline'}</span>
          </div>
        )}
      </div>
    </nav>
  )
}
