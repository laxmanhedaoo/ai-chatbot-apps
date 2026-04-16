# Demo Agent Outbound Calling


## Important Notes

- `outbound.json` is not currently referenced by the runtime code.




# Follow this command 

- To sync the uv packages
```bash
uv sync
```
- The Streamlit app should be started with 
```bash
streamlit run outbound_agent_app.py`
```


- not `streamlit run outbound_agent.py`.
- The worker should be started with `python3 outbound_agent.py start`.
- The UI does not rely only on cached Streamlit state for active calls; it checks the LiveKit room and `phone_user` participant while a call is in progress.
- Do not commit real API keys, tokens, SIP credentials, or LiveKit secrets into the README.




This project contains:

- a LiveKit outbound calling worker in `outbound_agent.py`
- a Streamlit control panel in `outbound_agent_app.py`
- local voice and language definitions in `utils/agent_utils/voice_catalog.py`
- Upstash-backed config loading and prospect persistence

The current outbound flow is for the Hedoo Developers booking agent, with optional custom prompts from the Streamlit UI.

## Requirements

- Python 3.10+
- A LiveKit project
- A configured SIP outbound trunk ID
- Azure Speech credentials for TTS
- OpenAI or Azure OpenAI credentials for the LLM path
- Upstash Redis credentials if you want remote config and prospect storage

## Install

Recommended with `uv`:

```bash
uv sync
```

If you use `uv` without activating `.venv`, run commands with `uv run`.

If you prefer `venv` + `pip`:

macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e .
```

Windows PowerShell:

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
py -3 -m pip install --upgrade pip
py -3 -m pip install -e .
```

## Environment Setup

Create a `.env` file from `example.env` and fill in the local bootstrap values:

```env
ENV=dev
PROFILE=dev
MAX_JOBS=1

SIP_OUTBOUND_TRUNK_ID=ST_xxxxxxxxxxxxx

UPSTASH_CONFIG_REDIS_URL=https://your-config-store.upstash.io
UPSTASH_CONFIG_REDIS_TOKEN=your-config-token
```

Important notes:

- `PROFILE` selects which Upstash config profile is loaded.
- `SIP_OUTBOUND_TRUNK_ID` is read directly from the environment.
- `UPSTASH_CONFIG_REDIS_URL` and `UPSTASH_CONFIG_REDIS_TOKEN` are used to connect to the Upstash config store.
- Other runtime keys can come from Upstash profile JSON.

## Upstash Config JSON

The app expects config JSON in Upstash under:

```text
config:env:<PROFILE>
```

Example for `PROFILE=dev`:

```json
{
  "config": {
    "LIVEKIT_API_KEY": "your-livekit-api-key",
    "LIVEKIT_API_SECRET": "your-livekit-api-secret",
    "LIVEKIT_URL": "wss://your-livekit-instance.livekit.cloud",
    "UPSTASH_REDIS_URL": "https://your-runtime-redis.upstash.io",
    "UPSTASH_REDIS_TOKEN": "your-runtime-redis-token",
    "AZURE_OPENAI_API_KEY": "your-azure-openai-key",
    "AZURE_SPEECH_API_KEY": "your-azure-speech-key",
    "AZURE_SPEECH_REGION": "centralindia",
    "OPEN_AI_API_KEY": "your-openai-key",
    "DEEPGRAM_API_KEY": "your-deepgram-key",
    "AWS_ACCESS_KEY_ID": "",
    "AWS_SECRET_ACCESS_KEY": "",
    "AWS_REGION": "",
    "AWS_VOICE_ID": "",
    "GOOGLE_AGENT_API_KEY": "",
    "GOOGLE_SA_JSON": "{\"type\":\"service_account\",\"project_id\":\"your-project-id\"}",
    "CARTESIA_API_KEY": "",
    "CARTESIA_VOICE_ID": ""
  }
}
```

How it is used:

1. `utils/config_utils/config_loader.py` reads `config:env:<PROFILE>` from Upstash.
2. The JSON is flattened into key-value config entries.
3. `get_config()` uses those values across the worker, TTS, and repository code.
4. `utils/config_utils/db_config.py` uses `UPSTASH_REDIS_URL` and `UPSTASH_REDIS_TOKEN` to connect to the runtime Redis store for prospect data.

## Optional: Generate `.env` From Upstash

You can materialize a `.env` file from Upstash with:

```bash
python3 scripts/generate-env-from-upstash --profile dev
```

That script:

- fetches `config:env:dev`
- flattens the JSON
- writes a local `.env`

## Run The Worker

Start the LiveKit worker:

```bash
python3 outbound_agent.py
```

Or with `uv`:

```bash
uv run python outbound_agent.py
```

This starts the outbound agent worker registered as:

```text
outbound-caller
```

## Run The Streamlit App

Start the UI in another terminal:

```bash
streamlit run outbound_agent_app.py
```

Or with `uv`:

```bash
uv run streamlit run outbound_agent_app.py
```

From the Streamlit app you can:

- choose gender
- choose language
- choose a filtered `voice_id`
- preview the selected voice
- add a custom prompt
- place a call
- end an active call from the UI
- start or stop the worker from the sidebar

While a call is active, the Streamlit app checks LiveKit every 2 seconds to keep the UI in sync with the real call state. If the callee hangs up from their phone, the app automatically clears the live call state, stops the timer, and returns the UI to `Idle`.

## Streamlit Session State

The app stores the active UI state in `st.session_state` with these keys:

- `agent_prompt`
- `phone_number`
- `call_started_at`
- `call_room_name`
- `call_status`
- `call_error`
- `preview_voice_key`
- `preview_audio_bytes`
- `outbound_worker_pid`

What they do:

- `agent_prompt` holds the custom prompt typed by the user.
- `phone_number` holds the destination number.
- `call_started_at`, `call_room_name`, and `call_status` power the live timer and status UI.
- `call_room_name` is also used to check the real room state from LiveKit while a call is active.
- `call_error` stores the latest UI error.
- `preview_voice_key` and `preview_audio_bytes` cache the latest preview audio for the selected voice.
- `outbound_worker_pid` tracks the worker process started from the sidebar.

Current call status behavior:

- `Make Call` creates the LiveKit room and updates the UI status to `Connected to <phone_number>`.
- `Reset Session / End Call` deletes the active LiveKit room and disconnects the call.
- If the phone participant disappears because the user hung up from their handset, the UI automatically resets to `Idle`.
- If ending the call fails, the app keeps the room name and shows `Call still active` so you can retry.

## Voice Selection Flow

The selected `voice_id` does not come from Upstash in the current codebase.

It flows like this:

1. Languages and voices are defined in `utils/agent_utils/voice_catalog.py`.
2. Streamlit loads voice options based on selected language and gender.
3. The selected voice is assigned as `voice_id` in `outbound_agent_app.py`.
4. `CallSettings` receives that `voice_id`.
5. `outbound_calling.py` serializes it into the dispatch metadata JSON.
6. `outbound_agent.py` reads the metadata back into `CallSettings`.
7. `get_tts()` receives `voice_id=call_settings.resolved_voice_id`.
8. Azure TTS uses that exact voice when creating the TTS client.

Flow summary:

```text
voice_catalog.py -> Streamlit dropdown -> CallSettings -> dispatch metadata -> worker -> get_tts() -> Azure voice
```

## Call Metadata JSON

When a call is created, the worker receives metadata based on `CallSettings.to_metadata()`.

If the prompt is blank:

```json
{
  "language": "Hindi",
  "gender": "Female",
  "voice_id": "hi-IN-SwaraNeural",
  "phone_number": "+919999999999",
  "prospect_id": "generated-or-passed-id"
}
```

If a custom prompt is provided:

```json
{
  "prompt": "Call the user and explain the offer briefly.",
  "language": "Hindi",
  "gender": "Female",
  "voice_id": "hi-IN-SwaraNeural",
  "phone_number": "+919999999999",
  "prospect_id": "generated-or-passed-id"
}
```

Behavior:

- blank or missing `prompt` enables the default Hedoo booking flow
- non-empty `prompt` enables the custom prompt flow

## Supported Voice Catalog

Voices are currently defined locally in `utils/agent_utils/voice_catalog.py`.

Examples:

- English: `en-IN-NeerjaNeural`, `en-IN-PrabhatNeural`
- Hindi: `hi-IN-SwaraNeural`, `hi-IN-MadhurNeural`
- Marathi: `mr-IN-AarohiNeural`, `mr-IN-ManoharNeural`
- Gujarati: `gu-IN-DhwaniNeural`, `gu-IN-NiranjanNeural`
- Bengali: `bn-IN-TanishaaNeural`, `bn-IN-BashkarNeural`
- Tamil: `ta-IN-PallaviNeural`, `ta-IN-ValluvarNeural`
- Telugu: `te-IN-ShrutiNeural`, `te-IN-MohanNeural`
- Kannada: `kn-IN-SapnaNeural`, `kn-IN-GaganNeural`
- Malayalam: `ml-IN-SobhanaNeural`, `ml-IN-MidhunNeural`
- Arabic (United Arab Emirates): `ar-AE-FatimaNeural`, `ar-AE-HamdanNeural`

## Make A Test Call From Code

The helper entrypoint in `outbound_agent.py` can place a test call using the hardcoded number list:

```bash
python3 outbound_agent.py --make-call
```

Or with `uv`:

```bash
uv run python outbound_agent.py --make-call
```

Update the phone number list inside `outbound_agent.py` before using this mode.

## Manual LiveKit Dispatch

You can also create a dispatch manually with the LiveKit CLI.

macOS or Linux:

```bash
lk dispatch create \
  --new-room \
  --agent-name outbound-caller \
  --url "$LIVEKIT_URL" \
  --api-key "$LIVEKIT_API_KEY" \
  --api-secret "$LIVEKIT_API_SECRET" \
  --metadata '{"language":"Hindi","gender":"Female","voice_id":"hi-IN-SwaraNeural","phone_number":"+919999999999","prospect_id":"demo-prospect-001"}'
```

Windows PowerShell:

```powershell
lk dispatch create `
  --new-room `
  --agent-name outbound-caller `
  --url $env:LIVEKIT_URL `
  --api-key $env:LIVEKIT_API_KEY `
  --api-secret $env:LIVEKIT_API_SECRET `
  --metadata "{\"language\":\"Hindi\",\"gender\":\"Female\",\"voice_id\":\"hi-IN-SwaraNeural\",\"phone_number\":\"+919999999999\",\"prospect_id\":\"demo-prospect-001\"}"
```

## Prospect Storage In Upstash

Prospect data is stored in the runtime Redis database as hashes like:

```text
prospect:<prospect_id>
```

This includes values such as:

- phone
- timezone
- appointment_date
- appointment_time
- email
- objections
- responses

