# 🌉 JeevanSetu.AI — Universal Intent-to-Action Bridge

> **Gemini-powered application that transforms messy, unstructured real-world inputs into structured, verified, life-saving actions.**

JeevanSetu.AI acts as a universal bridge between human intent and complex systems. Users can input anything — voice recordings, photos of medical documents, text descriptions of emergencies, weather alerts, or news articles — and the system instantly converts them into structured, prioritized action plans with verification.

---

## ✨ Features

- **🎤 Voice Input** — Record audio, transcribed via Google Cloud Speech-to-Text
- **📸 Image Upload** — Upload photos/documents, processed with Google Cloud Vision API + Gemini
- **📝 Text Input** — Describe any situation in natural language
- **📄 Document Upload** — Upload PDFs, text files, medical records
- **🤖 AI-Powered Pipeline** — 5-stage processing (Classify → Extract → Generate → Verify → Assemble)
- **🦙 Ollama Fallback** — When Gemini credits are exhausted, seamlessly switches to local open-source models
- **🔊 Text-to-Speech** — Accessibility feature using Google Cloud TTS
- **🗺️ Location Services** — Google Maps integration for nearby hospitals, stations, shelters
- **📊 Structured Output** — Entities, key facts, relationships, and verified action plans
- **♿ Accessible** — WCAG 2.1 AA compliant, keyboard navigable, screen reader friendly

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────┐
│         React Frontend (Vite) — JeevanSetu.AI │
│  ┌──────────┐ ┌──────────┐ ┌───────────────┐ │
│  │  Input    │ │Processing│ │  Results &    │ │
│  │  Panel    │ │ Visualiz │ │  Actions      │ │
│  │(text/voice│ │  ation   │ │  Dashboard    │ │
│  │ /image)   │ │          │ │               │ │
│  └──────────┘ └──────────┘ └───────────────┘ │
└──────────────────┬───────────────────────────┘
                   │ FastAPI (REST)
┌──────────────────▼───────────────────────────┐
│           Python Backend (FastAPI)            │
│  ┌──────────────────────────────────────────┐ │
│  │         Processing Pipeline               │ │
│  │  1. Input Classification (Gemini)         │ │
│  │  2. Content Extraction (Gemini Multimodal)│ │
│  │  3. Structure Generation (Gemini)         │ │
│  │  4. Verification & Enrichment             │ │
│  │  5. Action Plan Generation (Gemini)       │ │
│  └──────────────────────────────────────────┘ │
└──────────────────────────────────────────────┘
```

---

## 🔧 Google Services Used (7 Services)

| # | Service | Purpose |
|---|---------|---------|
| 1 | **Gemini 2.5 Flash** | Core AI — multimodal understanding, structuring, action generation |
| 2 | **Cloud Speech-to-Text** | Voice input transcription |
| 3 | **Cloud Text-to-Speech** | Accessibility — read actions aloud |
| 4 | **Google Maps JavaScript API** | Display locations, hospitals, routes |
| 5 | **Google Maps Geocoding API** | Convert addresses to coordinates |
| 6 | **Cloud Natural Language API** | Entity/sentiment extraction for verification |
| 7 | **Cloud Vision API** | OCR for document images |

---

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ and **npm**
- **Python** 3.11+
- **Google Cloud** account with billing enabled
- **Gemini API Key** from [Google AI Studio](https://aistudio.google.com/)
- (Optional) **Ollama** for open-source model fallback

### 1. Clone & Setup

```bash
# Clone the repository
git clone <repo-url>
cd prompt_wars_google

# Copy environment template
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` with your API keys:

```bash
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_CLOUD_PROJECT_ID=your_project_id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json
GOOGLE_MAPS_API_KEY=your_maps_api_key_here
```

### 3. Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Run the backend
uvicorn backend.main:app --reload --port 8000
```

### 4. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 5. Open the App

Visit **http://localhost:5173** in your browser.

---

## 🦙 Ollama Fallback Setup

If your Gemini credits are exhausted, JeevanSetu.AI automatically falls back to a local Ollama model:

```bash
# Install Ollama (macOS)
brew install ollama

# Pull a model
ollama pull llama3

# Start Ollama server
ollama serve
```

Set in `.env`:
```
USE_OLLAMA_FALLBACK=true
OLLAMA_MODEL=llama3
```

---

## 🧪 Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v --cov=. --cov-report=term-missing
```

---

## 📁 Project Structure

```
prompt_wars_google/
├── frontend/                  # React + Vite frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   │   ├── Header.jsx
│   │   │   ├── InputPanel.jsx
│   │   │   ├── ProcessingVisualizer.jsx
│   │   │   ├── ResultsDashboard.jsx
│   │   │   ├── HistoryPanel.jsx
│   │   │   └── ServicesBar.jsx
│   │   ├── App.jsx            # Main app
│   │   ├── index.css          # Design system
│   │   └── main.jsx           # Entry point
│   └── index.html
├── backend/                   # Python FastAPI backend
│   ├── api/
│   │   └── routes.py          # API endpoints
│   ├── core/
│   │   ├── config.py          # Configuration
│   │   └── security.py        # Security utilities
│   ├── models/
│   │   └── schemas.py         # Pydantic models
│   ├── services/
│   │   ├── gemini_service.py  # Gemini AI + Ollama fallback
│   │   ├── speech_service.py  # Speech-to-Text
│   │   ├── tts_service.py     # Text-to-Speech
│   │   ├── nlp_service.py     # Natural Language API
│   │   ├── vision_service.py  # Vision API
│   │   └── maps_service.py    # Maps Geocoding
│   ├── tests/
│   │   └── test_api.py        # Unit tests
│   ├── main.py                # FastAPI app
│   └── requirements.txt
├── .env.example               # Environment template
└── README.md
```

---

## 🎯 Use Cases

1. **Medical Emergency** — "My grandmother is diabetic, took metformin, now has chest pain"  
   → Structured patient profile + emergency action plan + nearest hospitals

2. **Disaster Response** — Upload photo of flooding  
   → Incident classification + rescue priorities + evacuation routes

3. **Traffic Safety** — Voice: "There's a major accident on NH-48"  
   → Structured report + alternative routes + emergency contacts

4. **Document Analysis** — Upload messy medical records  
   → Organized health profile + medication interactions + follow-up actions

---

## 📜 License

MIT License

---

**Built with ❤️ for societal benefit | Powered by Google Gemini**
