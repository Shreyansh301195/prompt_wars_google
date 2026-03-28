import { useState, useEffect, useCallback } from 'react'
import Header from './components/Header'
import InputPanel from './components/InputPanel'
import ProcessingVisualizer from './components/ProcessingVisualizer'
import ResultsDashboard from './components/ResultsDashboard'
import HistoryPanel from './components/HistoryPanel'
import ServicesBar from './components/ServicesBar'
import './index.css'

const API_BASE = 'http://localhost:8000/api'

function App() {
  const [isProcessing, setIsProcessing] = useState(false)
  const [processingStages, setProcessingStages] = useState([])
  const [result, setResult] = useState(null)
  const [history, setHistory] = useState([])
  const [services, setServices] = useState({})
  const [error, setError] = useState(null)

  // Fetch services status on mount
  useEffect(() => {
    fetchServicesStatus()
    fetchHistory()
  }, [])

  const fetchServicesStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/services-status`)
      if (res.ok) {
        const data = await res.json()
        setServices(data)
      }
    } catch (e) {
      console.log('Backend not connected yet')
    }
  }

  const fetchHistory = async () => {
    try {
      const res = await fetch(`${API_BASE}/history`)
      if (res.ok) {
        const data = await res.json()
        setHistory(data.history || [])
      }
    } catch (e) {
      console.log('Could not fetch history')
    }
  }

  const handleProcess = useCallback(async ({ text, image, audio, document: doc }) => {
    setIsProcessing(true)
    setError(null)
    setResult(null)
    setProcessingStages([
      { stage: 'classification', status: 'processing', label: 'Classifying Input' },
      { stage: 'extraction', status: 'pending', label: 'Extracting Data' },
      { stage: 'action_generation', status: 'pending', label: 'Generating Actions' },
      { stage: 'verification', status: 'pending', label: 'Verifying Safety' },
      { stage: 'assembly', status: 'pending', label: 'Assembling Response' },
    ])

    try {
      const formData = new FormData()
      if (text) formData.append('text', text)
      if (image) formData.append('image', image)
      if (audio) formData.append('audio', audio)
      if (doc) formData.append('document', doc)

      // Simulate stage progression for UX
      const stageTimers = [
        setTimeout(() => {
          setProcessingStages(prev => prev.map((s, i) => 
            i === 0 ? { ...s, status: 'complete' } : 
            i === 1 ? { ...s, status: 'processing' } : s
          ))
        }, 1500),
        setTimeout(() => {
          setProcessingStages(prev => prev.map((s, i) => 
            i <= 1 ? { ...s, status: 'complete' } : 
            i === 2 ? { ...s, status: 'processing' } : s
          ))
        }, 3000),
        setTimeout(() => {
          setProcessingStages(prev => prev.map((s, i) => 
            i <= 2 ? { ...s, status: 'complete' } : 
            i === 3 ? { ...s, status: 'processing' } : s
          ))
        }, 4500),
      ]

      const res = await fetch(`${API_BASE}/process`, {
        method: 'POST',
        body: formData,
      })

      stageTimers.forEach(clearTimeout)

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.detail || `Processing failed (${res.status})`)
      }

      const data = await res.json()
      
      // Mark all stages complete
      setProcessingStages(prev => prev.map(s => ({ ...s, status: 'complete' })))
      
      setTimeout(() => {
        setResult(data)
        setIsProcessing(false)
        fetchHistory()
      }, 800)

    } catch (e) {
      setError(e.message)
      setIsProcessing(false)
      setProcessingStages([])
    }
  }, [])

  const handleTTS = useCallback(async (text) => {
    try {
      const res = await fetch(`${API_BASE}/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, language: 'en-US', voice_type: 'standard' }),
      })

      if (res.ok) {
        const data = await res.json()
        if (data.audio_base64) {
          const audio = new Audio(`data:audio/mp3;base64,${data.audio_base64}`)
          audio.play()
          return
        }
      }

      // Fallback: Use browser speech synthesis
      if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(text)
        utterance.rate = 0.9
        utterance.pitch = 1
        window.speechSynthesis.speak(utterance)
      }
    } catch (e) {
      // Fallback to browser speech synthesis
      if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(text)
        window.speechSynthesis.speak(utterance)
      }
    }
  }, [])

  const handleNewSession = () => {
    setResult(null)
    setProcessingStages([])
    setError(null)
  }

  return (
    <div className="app" role="application" aria-label="JeevanSetu.AI Application">
      {/* Skip to main content — Accessibility */}
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>

      <Header services={services} />

      <main className="app-main" id="main-content" role="main">
        {/* Hero */}
        {!result && !isProcessing && (
          <section className="hero animate-fade-in" aria-label="Welcome section">
            <h2>Transform Chaos into Clarity</h2>
            <p>
              Paste text, record your voice, upload photos or documents — 
              JeevanSetu.AI instantly converts them into structured, verified, life-saving actions.
            </p>
          </section>
        )}

        {/* Services Status Bar */}
        <ServicesBar services={services} />

        {/* Input Panel */}
        {!isProcessing && !result && (
          <InputPanel 
            onProcess={handleProcess} 
            isProcessing={isProcessing}
          />
        )}

        {/* Error display */}
        {error && (
          <div className="glass-card animate-scale-in" role="alert" style={{
            borderColor: 'rgba(231, 76, 60, 0.3)',
            borderLeft: '4px solid var(--accent-danger)'
          }}>
            <strong style={{ color: 'var(--accent-danger)' }}>⚠️ Processing Error</strong>
            <p style={{ marginTop: '8px', color: 'var(--text-secondary)' }}>{error}</p>
            <button 
              onClick={handleNewSession}
              className="submit-btn" 
              style={{ marginTop: '12px', padding: '8px 20px', fontSize: '0.875rem' }}
            >
              Try Again
            </button>
          </div>
        )}

        {/* Processing Visualizer */}
        {isProcessing && (
          <ProcessingVisualizer stages={processingStages} />
        )}

        {/* Results Dashboard */}
        {result && (
          <>
            <ResultsDashboard 
              result={result} 
              onTTS={handleTTS}
              onNewSession={handleNewSession}
            />
          </>
        )}

        {/* History Panel */}
        {history.length > 0 && !isProcessing && (
          <HistoryPanel history={history} />
        )}
      </main>

      {/* Footer */}
      <footer style={{
        textAlign: 'center',
        padding: '24px',
        color: 'var(--text-muted)',
        fontSize: 'var(--font-size-xs)',
        borderTop: '1px solid var(--border-color)'
      }}>
        <p>
          JeevanSetu.AI — Powered by Google Gemini | 
          Built for societal benefit 🌍
        </p>
      </footer>
    </div>
  )
}

export default App
