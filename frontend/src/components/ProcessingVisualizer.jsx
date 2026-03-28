import { FiSearch, FiDatabase, FiZap, FiShield, FiPackage, FiCheck } from 'react-icons/fi'

const STAGE_ICONS = {
  classification: FiSearch,
  extraction: FiDatabase,
  action_generation: FiZap,
  verification: FiShield,
  assembly: FiPackage,
}

const STAGE_LABELS = {
  classification: 'Classifying',
  extraction: 'Extracting',
  action_generation: 'Generating',
  verification: 'Verifying',
  assembly: 'Assembling',
}

export default function ProcessingVisualizer({ stages }) {
  return (
    <section 
      className="processing-visualizer" 
      aria-label="Processing pipeline status"
      role="status"
      aria-live="polite"
    >
      <div className="processing-header">
        <div className="processing-title">
          <div className="processing-spinner" aria-hidden="true" />
          <span>Processing your input</span>
          <div className="loading-dots" aria-hidden="true">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>

      <div className="pipeline-stages">
        {stages.map((stage, index) => {
          const Icon = STAGE_ICONS[stage.stage] || FiSearch
          const label = stage.label || STAGE_LABELS[stage.stage] || stage.stage
          
          return (
            <div
              key={stage.stage}
              className={`pipeline-stage ${stage.status}`}
              aria-label={`Stage ${index + 1}: ${label} - ${stage.status}`}
            >
              <div className="stage-icon">
                {stage.status === 'complete' ? (
                  <FiCheck aria-hidden="true" />
                ) : (
                  <Icon aria-hidden="true" />
                )}
              </div>
              <span className="stage-label">{label}</span>
            </div>
          )
        })}
      </div>

      <p style={{
        textAlign: 'center',
        marginTop: '24px',
        color: 'var(--text-muted)',
        fontSize: 'var(--font-size-xs)',
      }}>
        Powered by Google Gemini AI — Analyzing, structuring, and verifying your input for safety
      </p>
    </section>
  )
}
