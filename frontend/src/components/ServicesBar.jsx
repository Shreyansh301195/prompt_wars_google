export default function ServicesBar({ services }) {
  if (!services || Object.keys(services).length === 0) {
    return null
  }

  const serviceList = [
    { key: 'gemini', icon: '✨', label: 'Gemini AI' },
    { key: 'ollama', icon: '🦙', label: 'Ollama' },
    { key: 'speech_to_text', icon: '🎤', label: 'Speech-to-Text' },
    { key: 'text_to_speech', icon: '🔊', label: 'Text-to-Speech' },
    { key: 'natural_language', icon: '📝', label: 'NLP' },
    { key: 'vision', icon: '👁️', label: 'Vision' },
    { key: 'maps', icon: '🗺️', label: 'Maps' },
  ]

  return (
    <div className="services-bar" role="status" aria-label="Google services status">
      {serviceList.map(({ key, icon, label }) => {
        const service = services[key]
        const isActive = service?.available
        return (
          <div
            key={key}
            className={`service-chip ${isActive ? 'active' : 'inactive'}`}
            title={`${label}: ${isActive ? 'Connected' : 'Not available'}`}
          >
            <span className="chip-dot" aria-hidden="true" />
            <span aria-hidden="true">{icon}</span>
            <span>{label}</span>
          </div>
        )
      })}
    </div>
  )
}
