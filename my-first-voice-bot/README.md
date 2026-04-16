#  My First Voice Bot (LiveKit + Gemini + Deepgram)

A real-time **Voice AI Assistant** built using **LiveKit Agents**, powered by:

* **LLM**: Google Gemini (via LiveKit inference)
* **STT (Speech-to-Text)**: Deepgram Nova-3
* **TTS (Text-to-Speech)**: Deepgram Aura-2
* **VAD (Voice Activity Detection)**: Silero

This bot listens, understands, and responds to users in real-time voice conversations.

---

##  Features

* Real-time voice interaction using LiveKit RTC
* Multilingual speech recognition
* Fast and lightweight Gemini LLM responses
* Natural-sounding voice output via Deepgram
* Voice Activity Detection using Silero
* Preemptive response generation for low latency

---

##  Project Structure

```
my-first-voice-bot/
│
├── .venv/                # Virtual environment
├── .env                 # Environment variables
├── .env.example         # Example env file
├── .python-version      # Python version
├── main.py              # Main application
├── pyproject.toml       # Project config
├── README.md            # Documentation
├── requirements.txt     # Dependencies
├── uv.lock              # Lock file
└── .gitignore
```

---

##  Prerequisites

* Python 3.10+
* LiveKit Cloud or self-hosted instance
* API Keys Needed:

  * LiveKit API Key & Secret
  * Deepgram API Key
  * Google API Key (for Gemini)

---

## Environment Variables

Create a `.env` file using `.env.example`:

```
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_secret
LIVEKIT_URL=your_livekit_url
DEEPGRAM_API_KEY=your_deepgram_api_key
GOOGLE_API_KEY=your_google_api_key
```

---

##  Installation

```bash
# Clone repository
git clone https://github.com/laxmanhedaoo/ai-chatbot-apps
cd ai-chatbot-apps/my-first-voice-bot

# Install uv (if not installed)
```bash
pip install uv
```
# Create virtual environment & install dependencies
```bash
uv sync
```
# Install dependencies
```bash
uv pip install -r requirements.txt
```

---

##  Running the Application

```bash
uv run main.py
```

This will:

* Start the LiveKit Agent server
* Initialize STT, LLM, and TTS pipelines
* Wait for a user to join a room

---

##  How It Works

### 1. Prewarm Phase

* Loads Silero VAD model for speech detection

### 2. Voice Pipeline Setup

* **STT** → Deepgram Nova-3 converts speech to text
* **LLM** → Gemini generates response
* **TTS** → Deepgram Aura-2 converts text to speech

### 3. Session Flow

* User joins LiveKit room
* Agent connects
* Greets user
* Starts real-time conversation loop

---

##  Assistant Behavior

* Friendly, concise, and conversational
* No emojis or complex formatting in responses
* Designed for real-time voice UX
* Optimized for low latency interaction

---

## 🔧 Key Configuration

```python
AGENT_MODEL = "google/gemini-3-flash-preview"
```

* Fast Gemini model optimized for real-time use

---

## 🧪 Customization Ideas

* Add turn detection
* Integrate memory (Redis / DB)
* Add tool calling (APIs, DB queries)
* Multi-agent orchestration
* Language-specific voice tuning

---

##  Troubleshooting

* ❌ Missing env variable → Check `.env`
* ❌ No audio → Verify Deepgram API key
* ❌ Connection issues → Validate LiveKit URL & credentials
* ❌ Latency → Disable `preemptive_generation` or optimize model

---

##  Future Improvements

* UI dashboard for monitoring
* Conversation history storage
* Speaker diarization
* Emotion-aware responses

---

##  License

MIT License

---

##  Author

**Nikhil H Pathrabe**
AI / Voice Agent Developer

---

##  Acknowledgements

* LiveKit Agents Framework
* Deepgram Speech APIs
* Google Gemini LLM
* Silero VAD

---
