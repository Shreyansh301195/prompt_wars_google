import { useState, useRef, useCallback } from 'react'
import { FiType, FiMic, FiImage, FiFile, FiSend, FiX, FiUpload, FiMicOff } from 'react-icons/fi'

const TABS = [
  { id: 'text', label: 'Text', icon: FiType },
  { id: 'voice', label: 'Voice', icon: FiMic },
  { id: 'image', label: 'Image', icon: FiImage },
  { id: 'document', label: 'Document', icon: FiFile },
]

export default function InputPanel({ onProcess, isProcessing }) {
  const [activeTab, setActiveTab] = useState('text')
  const [text, setText] = useState('')
  const [imageFile, setImageFile] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)
  const [docFile, setDocFile] = useState(null)
  const [isRecording, setIsRecording] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const [transcript, setTranscript] = useState('')
  const [audioBlob, setAudioBlob] = useState(null)
  
  const mediaRecorderRef = useRef(null)
  const timerRef = useRef(null)
  const fileInputRef = useRef(null)
  const docInputRef = useRef(null)

  // Voice recording
  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' })
      const chunks = []

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.push(e.data)
      }

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'audio/webm' })
        setAudioBlob(blob)
        stream.getTracks().forEach(track => track.stop())

        // Try browser speech recognition for transcript
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
          // Already handled by SpeechRecognition API below
        }
      }

      mediaRecorderRef.current = mediaRecorder
      mediaRecorder.start()
      setIsRecording(true)
      setRecordingTime(0)

      // Timer
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1)
      }, 1000)

      // Also start speech recognition for live transcript
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
      if (SpeechRecognition) {
        const recognition = new SpeechRecognition()
        recognition.continuous = true
        recognition.interimResults = true
        recognition.lang = 'en-US'
        
        recognition.onresult = (event) => {
          let finalTranscript = ''
          for (let i = 0; i < event.results.length; i++) {
            finalTranscript += event.results[i][0].transcript
          }
          setTranscript(finalTranscript)
        }

        recognition.onerror = () => {} // silently handle
        recognition.start()
        mediaRecorderRef.current._recognition = recognition
      }

    } catch (err) {
      console.error('Microphone access denied:', err)
      alert('Please allow microphone access to use voice input.')
    }
  }, [])

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop()
      if (mediaRecorderRef.current._recognition) {
        mediaRecorderRef.current._recognition.stop()
      }
    }
    clearInterval(timerRef.current)
    setIsRecording(false)
  }, [])

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60).toString().padStart(2, '0')
    const secs = (seconds % 60).toString().padStart(2, '0')
    return `${mins}:${secs}`
  }

  // Image handling
  const handleImageSelect = (e) => {
    const file = e.target.files?.[0]
    if (file) {
      setImageFile(file)
      const reader = new FileReader()
      reader.onload = (ev) => setImagePreview(ev.target.result)
      reader.readAsDataURL(file)
    }
  }

  // Document handling
  const handleDocSelect = (e) => {
    const file = e.target.files?.[0]
    if (file) setDocFile(file)
  }

  // Drop handling
  const [isDragging, setIsDragging] = useState(false)

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files?.[0]
    if (file) {
      if (file.type.startsWith('image/')) {
        setImageFile(file)
        const reader = new FileReader()
        reader.onload = (ev) => setImagePreview(ev.target.result)
        reader.readAsDataURL(file)
        setActiveTab('image')
      } else {
        setDocFile(file)
        setActiveTab('document')
      }
    }
  }, [])

  // Submit
  const handleSubmit = () => {
    const payload = {}
    
    if (text.trim()) payload.text = text
    if (transcript.trim()) payload.text = (payload.text || '') + '\n' + transcript
    if (imageFile) payload.image = imageFile
    if (audioBlob) payload.audio = new File([audioBlob], 'recording.webm', { type: 'audio/webm' })
    if (docFile) payload.document = docFile

    if (Object.keys(payload).length === 0) {
      alert('Please provide some input first.')
      return
    }

    onProcess(payload)
  }

  const hasInput = text.trim() || transcript.trim() || imageFile || audioBlob || docFile

  return (
    <section 
      className="input-panel animate-scale-in" 
      aria-label="Input panel"
      onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
    >
      {/* Tabs */}
      <div className="input-tabs" role="tablist" aria-label="Input type selection">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            role="tab"
            id={`tab-${id}`}
            aria-selected={activeTab === id}
            aria-controls={`panel-${id}`}
            className={`input-tab ${activeTab === id ? 'active' : ''}`}
            onClick={() => setActiveTab(id)}
          >
            <Icon aria-hidden="true" />
            <span>{label}</span>
          </button>
        ))}
      </div>

      {/* Text Panel */}
      {activeTab === 'text' && (
        <div id="panel-text" role="tabpanel" aria-labelledby="tab-text" className="text-input-area">
          <textarea
            id="text-input"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Describe anything — symptoms, emergency situation, traffic incident, weather concern, or paste medical records, news articles...

Example: &quot;My grandmother is 72, diabetic, took metformin this morning, now complaining of severe chest pain and difficulty breathing. We are in Koramangala, Bangalore.&quot;"
            aria-label="Text input for processing"
            maxLength={10000}
          />
          <span className="char-count" aria-live="polite">{text.length}/10000</span>
        </div>
      )}

      {/* Voice Panel */}
      {activeTab === 'voice' && (
        <div id="panel-voice" role="tabpanel" aria-labelledby="tab-voice" className="voice-input-area">
          <button
            className={`voice-btn ${isRecording ? 'recording' : ''}`}
            onClick={isRecording ? stopRecording : startRecording}
            aria-label={isRecording ? 'Stop recording' : 'Start recording'}
          >
            {isRecording ? <FiMicOff /> : <FiMic />}
          </button>

          {isRecording && (
            <div className="voice-timer" aria-live="polite" aria-label="Recording duration">
              {formatTime(recordingTime)}
            </div>
          )}

          <p className="voice-status">
            {isRecording 
              ? 'Recording... Click to stop'
              : audioBlob 
                ? '✅ Recording captured. Click to re-record.' 
                : 'Click the microphone to start recording'}
          </p>

          {transcript && (
            <div className="voice-transcript" aria-label="Transcription">
              <strong style={{ color: 'var(--accent-primary)', fontSize: '0.75rem' }}>
                Live Transcript:
              </strong>
              <br />
              {transcript}
            </div>
          )}
        </div>
      )}

      {/* Image Panel */}
      {activeTab === 'image' && (
        <div id="panel-image" role="tabpanel" aria-labelledby="tab-image" className="upload-area">
          <div
            className={`dropzone ${isDragging ? 'drag-active' : ''}`}
            onClick={() => fileInputRef.current?.click()}
            role="button"
            tabIndex={0}
            aria-label="Upload image area. Click or drag and drop."
            onKeyDown={(e) => e.key === 'Enter' && fileInputRef.current?.click()}
          >
            <FiUpload className="dropzone-icon" aria-hidden="true" />
            <div className="dropzone-text">
              <p>Drag & drop an image here, or <span className="browse-link">browse</span></p>
              <p style={{ fontSize: '0.7rem', marginTop: '4px', opacity: 0.6 }}>
                Supports: JPG, PNG, GIF, WebP, BMP, TIFF (max 10MB)
              </p>
            </div>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleImageSelect}
            style={{ display: 'none' }}
            aria-hidden="true"
          />

          {imageFile && (
            <div className="file-preview">
              <div className="file-preview-item">
                {imagePreview && <img src={imagePreview} alt="Preview" />}
                <span>{imageFile.name}</span>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>
                  ({(imageFile.size / 1024).toFixed(1)} KB)
                </span>
                <button
                  className="file-remove-btn"
                  onClick={() => { setImageFile(null); setImagePreview(null) }}
                  aria-label="Remove image"
                >
                  <FiX />
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Document Panel */}
      {activeTab === 'document' && (
        <div id="panel-document" role="tabpanel" aria-labelledby="tab-document" className="upload-area">
          <div
            className={`dropzone ${isDragging ? 'drag-active' : ''}`}
            onClick={() => docInputRef.current?.click()}
            role="button"
            tabIndex={0}
            aria-label="Upload document area. Click or drag and drop."
            onKeyDown={(e) => e.key === 'Enter' && docInputRef.current?.click()}
          >
            <FiFile className="dropzone-icon" aria-hidden="true" />
            <div className="dropzone-text">
              <p>Drag & drop a document here, or <span className="browse-link">browse</span></p>
              <p style={{ fontSize: '0.7rem', marginTop: '4px', opacity: 0.6 }}>
                Supports: PDF, TXT, DOC, DOCX, CSV (max 10MB)
              </p>
            </div>
          </div>
          <input
            ref={docInputRef}
            type="file"
            accept=".pdf,.txt,.doc,.docx,.csv"
            onChange={handleDocSelect}
            style={{ display: 'none' }}
            aria-hidden="true"
          />

          {docFile && (
            <div className="file-preview">
              <div className="file-preview-item">
                <FiFile style={{ fontSize: '1.5rem', color: 'var(--accent-primary)' }} />
                <span>{docFile.name}</span>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>
                  ({(docFile.size / 1024).toFixed(1)} KB)
                </span>
                <button
                  className="file-remove-btn"
                  onClick={() => setDocFile(null)}
                  aria-label="Remove document"
                >
                  <FiX />
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Also allow text alongside other inputs */}
      {activeTab !== 'text' && (
        <div className="text-input-area" style={{ marginTop: '16px' }}>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Add additional context or description (optional)..."
            aria-label="Additional text context"
            style={{ minHeight: '80px' }}
            maxLength={10000}
          />
        </div>
      )}

      {/* Submit */}
      <div className="submit-section">
        <p className="input-hint">
          💡 Tip: You can combine multiple inputs — e.g., upload an image and add text description for better results.
        </p>
        <button
          id="process-btn"
          className="submit-btn"
          onClick={handleSubmit}
          disabled={!hasInput || isProcessing}
          aria-label="Process input through JeevanSetu.AI pipeline"
        >
          <FiSend aria-hidden="true" />
          <span>{isProcessing ? 'Processing...' : 'Process with JeevanSetu'}</span>
        </button>
      </div>
    </section>
  )
}
