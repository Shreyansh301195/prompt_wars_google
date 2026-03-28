import { 
  FiTarget, FiList, FiCheckCircle, FiMap, FiVolume2, 
  FiRefreshCw, FiPhone, FiMapPin, FiShield, FiTag,
  FiAlertTriangle, FiFileText
} from 'react-icons/fi'

export default function ResultsDashboard({ result, onTTS, onNewSession }) {
  if (!result) return null

  const {
    request_id, domain, urgency, confidence, input_type,
    structured_data, action_plan, locations, ai_engine_used,
    input_summary, audio_available
  } = result

  // Build text summary for TTS
  const buildTTSSummary = () => {
    let text = `JeevanSetu AI Analysis Complete. Domain: ${domain}. Urgency: ${urgency}. `
    text += structured_data?.summary || input_summary || ''
    text += '. Action Plan: '
    action_plan?.forEach((action, i) => {
      text += `Action ${i + 1}: ${action.title}. ${action.description}. `
    })
    return text
  }

  return (
    <div className="animate-fade-in">
      {/* New Session Button */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <h2 style={{ fontSize: 'var(--font-size-xl)', fontWeight: 800 }}>
            Analysis Results
          </h2>
          <span className={`engine-badge ${ai_engine_used}`}>
            {ai_engine_used === 'gemini' ? '✨' : '🦙'} {ai_engine_used}
          </span>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button 
            className="tts-btn"
            onClick={() => onTTS(buildTTSSummary())}
            aria-label="Read results aloud"
            title="Read aloud (Accessibility)"
          >
            <FiVolume2 aria-hidden="true" />
            <span>Read Aloud</span>
          </button>
          <button 
            className="submit-btn" 
            onClick={onNewSession}
            style={{ padding: '8px 20px', fontSize: '0.875rem' }}
          >
            <FiRefreshCw aria-hidden="true" />
            <span>New Analysis</span>
          </button>
        </div>
      </div>

      <div className="results-dashboard" role="region" aria-label="Analysis results">
        
        {/* Classification Card */}
        <div className="result-card" role="region" aria-label="Classification">
          <div className="result-card-header">
            <div className="result-card-title">
              <FiTarget aria-hidden="true" />
              <span>Classification</span>
            </div>
            <span className={`urgency-badge ${urgency}`}>
              {urgency === 'critical' && <FiAlertTriangle aria-hidden="true" />}
              {urgency}
            </span>
          </div>
          <div className="classification-grid">
            <div className="classification-item">
              <div className="label">Domain</div>
              <div className="value">{domain}</div>
            </div>
            <div className="classification-item">
              <div className="label">Input Type</div>
              <div className="value">{input_type}</div>
            </div>
            <div className="classification-item">
              <div className="label">Urgency</div>
              <div className="value" style={{ 
                color: urgency === 'critical' ? 'var(--accent-danger)' : 
                       urgency === 'high' ? 'var(--accent-tertiary)' : 'inherit'
              }}>
                {urgency}
              </div>
            </div>
            <div className="classification-item">
              <div className="label">Confidence</div>
              <div className="value">{(confidence * 100).toFixed(0)}%</div>
              <div className="confidence-bar">
                <div className="confidence-fill" style={{ width: `${confidence * 100}%` }} />
              </div>
            </div>
          </div>
        </div>

        {/* Structured Data Card */}
        <div className="result-card" role="region" aria-label="Extracted data">
          <div className="result-card-header">
            <div className="result-card-title">
              <FiFileText aria-hidden="true" />
              <span>Extracted Data</span>
            </div>
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
              {structured_data?.entities?.length || 0} entities
            </span>
          </div>

          {/* Summary */}
          {structured_data?.summary && (
            <div className="summary-text" style={{ marginBottom: '16px' }}>
              {structured_data.summary}
            </div>
          )}

          {/* Entities */}
          {structured_data?.entities?.length > 0 && (
            <div style={{ marginBottom: '16px' }}>
              <h4 style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Entities
              </h4>
              <div className="entities-list">
                {structured_data.entities.map((entity, i) => (
                  <span key={i} className="entity-tag">
                    <span className="entity-type">{entity.type}</span>
                    <span>{entity.name || entity.value}</span>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Key Facts */}
          {structured_data?.key_facts?.length > 0 && (
            <div>
              <h4 style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Key Facts
              </h4>
              <ul className="facts-list">
                {structured_data.key_facts.map((fact, i) => (
                  <li key={i}>
                    <span className="fact-bullet">▸</span>
                    <span>{fact}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Action Plan Card — Full Width */}
        <div className="result-card full-width" role="region" aria-label="Action plan">
          <div className="result-card-header">
            <div className="result-card-title">
              <FiCheckCircle aria-hidden="true" />
              <span>Action Plan</span>
            </div>
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
              {action_plan?.length || 0} actions
            </span>
          </div>
          
          <div className="action-list">
            {action_plan?.map((action, i) => (
              <div key={i} className={`action-item ${action.priority}`}>
                <div className="action-header">
                  <div className="action-title">
                    <span className="action-num">{action.id || i + 1}</span>
                    <span>{action.title}</span>
                  </div>
                  <span className={`priority-tag ${action.priority}`}>
                    {action.priority}
                  </span>
                </div>
                <p className="action-description">{action.description}</p>
                <div className="action-meta">
                  <span className="action-meta-item">
                    <FiTag aria-hidden="true" />
                    {action.category}
                  </span>
                  {action.is_verified && (
                    <span className="verified-badge">
                      <FiShield aria-hidden="true" />
                      Verified
                    </span>
                  )}
                  {action.contact_info && (
                    <span className="action-meta-item">
                      <FiPhone aria-hidden="true" />
                      <a href={`tel:${action.contact_info}`}>{action.contact_info}</a>
                    </span>
                  )}
                </div>
                {action.verification_notes && (
                  <p style={{ 
                    paddingLeft: '36px', 
                    marginTop: '6px', 
                    fontSize: 'var(--font-size-xs)', 
                    color: 'var(--text-muted)',
                    fontStyle: 'italic'
                  }}>
                    ℹ️ {action.verification_notes}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Locations Card */}
        {locations?.length > 0 && (
          <div className="result-card full-width" role="region" aria-label="Locations">
            <div className="result-card-header">
              <div className="result-card-title">
                <FiMap aria-hidden="true" />
                <span>Relevant Locations</span>
              </div>
            </div>
            <div className="locations-list">
              {locations.map((loc, i) => (
                <div key={i} className="location-item">
                  <div className="loc-icon">
                    <FiMapPin style={{ color: 'var(--accent-primary)' }} aria-hidden="true" />
                  </div>
                  <div className="loc-details">
                    <div className="loc-name">{loc.name}</div>
                    {loc.address && <div className="loc-address">{loc.address}</div>}
                  </div>
                  <span className="loc-type">{loc.type}</span>
                  <a
                    href={`https://www.google.com/maps/search/?api=1&query=${loc.lat},${loc.lng}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ 
                      fontSize: 'var(--font-size-xs)', 
                      color: 'var(--accent-info)',
                      textDecoration: 'none',
                      whiteSpace: 'nowrap'
                    }}
                    aria-label={`Open ${loc.name} in Google Maps`}
                  >
                    Open in Maps →
                  </a>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Input Summary for reference */}
        {input_summary && (
          <div className="result-card full-width" role="region" aria-label="Original input summary" style={{ opacity: 0.7 }}>
            <div className="result-card-header">
              <div className="result-card-title">
                <FiList aria-hidden="true" />
                <span>Original Input</span>
              </div>
              <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
                ID: {request_id}
              </span>
            </div>
            <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)', fontStyle: 'italic' }}>
              "{input_summary}"
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
