import { FiClock, FiChevronRight } from 'react-icons/fi'

export default function HistoryPanel({ history }) {
  if (!history || history.length === 0) return null

  const formatTimestamp = (ts) => {
    try {
      const date = new Date(ts)
      return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    } catch {
      return ts
    }
  }

  const urgencyColors = {
    critical: 'var(--accent-danger)',
    high: 'var(--accent-tertiary)',
    medium: 'var(--accent-warning)',
    low: 'var(--accent-success)',
    info: 'var(--accent-info)',
  }

  return (
    <section className="history-panel animate-fade-in" role="region" aria-label="Processing history">
      <div className="result-card-header">
        <div className="result-card-title">
          <FiClock aria-hidden="true" />
          <span>Recent Processing History</span>
        </div>
        <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
          {history.length} {history.length === 1 ? 'entry' : 'entries'}
        </span>
      </div>

      <div className="history-list" role="list">
        {history.map((item, index) => (
          <div
            key={item.request_id || index}
            className="history-item"
            role="listitem"
            tabIndex={0}
            aria-label={`${item.domain} analysis — ${item.urgency} urgency`}
          >
            <div className="history-item-info">
              <div className="title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span className={`urgency-badge ${item.urgency}`} style={{ fontSize: '0.6rem', padding: '2px 8px' }}>
                  {item.urgency}
                </span>
                <span style={{ textTransform: 'capitalize' }}>{item.domain}</span>
              </div>
              <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', marginTop: '4px' }}>
                {item.input_summary}
              </div>
              <div className="timestamp">
                {formatTimestamp(item.timestamp)}
              </div>
            </div>
            <FiChevronRight style={{ color: 'var(--text-muted)', flexShrink: 0 }} aria-hidden="true" />
          </div>
        ))}
      </div>
    </section>
  )
}
