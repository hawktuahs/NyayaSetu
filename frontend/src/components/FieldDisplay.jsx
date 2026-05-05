import ConfidenceBadge from './ConfidenceBadge'

/**
 * Displays a single extracted field with its label, value, and confidence score.
 * If editable, renders an input/textarea.
 */
export function FieldDisplay({
  label,
  value,
  confidence,
  editable = false,
  fieldKey,
  onChange,
  multiline = false,
  isArray = false,
}) {
  const displayValue = isArray
    ? (Array.isArray(value) ? value.join('; ') : value)
    : value

  const handleChange = (v) => {
    if (!onChange) return
    if (isArray) {
      // Split by ; or newline
      const arr = v.split(/[;\n]/).map(s => s.trim()).filter(Boolean)
      onChange(fieldKey, arr)
    } else {
      onChange(fieldKey, v)
    }
  }

  return (
    <div className="field-item">
      <div className="field-label">
        {label}
        {confidence !== undefined && (
          <ConfidenceBadge score={confidence} />
        )}
      </div>
      {editable ? (
        multiline ? (
          <textarea
            className="form-textarea"
            value={isArray ? (Array.isArray(value) ? value.join('\n') : value || '') : (value || '')}
            onChange={(e) => handleChange(e.target.value)}
            rows={isArray ? Math.max(3, (value?.length || 1) + 1) : 3}
            style={{ marginTop: 4, fontSize: 13 }}
          />
        ) : (
          <input
            className="form-input"
            value={value || ''}
            onChange={(e) => handleChange(e.target.value)}
            style={{ marginTop: 4, fontSize: 13 }}
          />
        )
      ) : (
        <div className={`field-value ${!displayValue ? 'field-null' : ''}`}>
          {displayValue || '—'}
        </div>
      )}
      {confidence !== undefined && (
        <div style={{ marginTop: 8 }}>
          <ConfidenceBadge score={confidence} showBar />
        </div>
      )}
    </div>
  )
}

export default FieldDisplay
