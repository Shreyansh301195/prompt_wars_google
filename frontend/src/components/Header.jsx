import { FiActivity, FiWifi, FiWifiOff } from 'react-icons/fi'

export default function Header({ services }) {
  const geminiActive = services?.gemini?.available
  const ollamaActive = services?.ollama?.available
  const engineName = geminiActive ? 'Gemini' : ollamaActive ? 'Ollama' : 'Offline'

  return (
    <header className="header" role="banner">
      <div className="header-brand">
        <div className="header-logo" aria-hidden="true">
          🌉
        </div>
        <div className="header-title">
          <h1>JeevanSetu.AI</h1>
          <span className="tagline">Universal Intent-to-Action Bridge</span>
        </div>
      </div>

      <div className="header-status" aria-label="System status">
        <div className={`status-badge ${geminiActive || ollamaActive ? 'active' : 'inactive'}`}>
          <span className="status-dot" aria-hidden="true" />
          <span>{engineName}</span>
        </div>
        <div className={`status-badge ${Object.keys(services).length > 0 ? 'active' : 'inactive'}`}>
          {Object.keys(services).length > 0 ? (
            <FiWifi aria-hidden="true" />
          ) : (
            <FiWifiOff aria-hidden="true" />
          )}
          <span>{Object.keys(services).length > 0 ? 'Connected' : 'Offline'}</span>
        </div>
      </div>
    </header>
  )
}
