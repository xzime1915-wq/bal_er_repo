# 3 bolod
**SENZ** is a JARVIS-style PC automation agent for Windows — voice + chat control over your computer, powered by Google Gemini.

![SENZ Dashboard](docs/dashboard.png)

## Features

- **Chat & voice** — type instructions or say **"hey senz"** (wake word)
- **PC control** — open/close apps, files, volume, screenshots, PowerShell
- **Web** — search, headlines feed
- **Sub-agents** — background workers for long tasks
- **Memory & notes** — remembers preferences
- **Visual Hub** — Mermaid diagrams from the agent

## Quick start

### 1. Requirements

- Windows 10/11
- [Node.js](https://nodejs.org/) 20+
- [Python](https://www.python.org/) 3.11+
- Gemini API key: https://aistudio.google.com/apikey

### 2. Setup

```bash
cd f:\senz
copy .env.example .env
# Edit .env — add GEMINI_API_KEY=...
```

Install dependencies:

```bash
npm install
npm run install:all
```

> **PyAudio on Windows:** If `pip install pyaudio` fails:
> ```bash
> pip install pipwin
> pipwin install pyaudio
> ```

### 3. Run (Desktop app — NOT browser)

**Double-click `start.bat`** — a **SENZ window** opens on your PC (Electron desktop app).

Optional: run `Create Desktop Shortcut.bat` once → Desktop এ **SENZ** shortcut.

```bash
npm run app
```

Same as `start.bat` — opens the desktop UI.

> **মনে রাখবেন:** `http://127.0.0.1:8765` browser এ খুলবেন না — সেটা শুধু backend API। UI শুধু **SENZ app window** এ।

`npm run backend` শুধু developer testing এর জন্য; normal use এ লাগে না — Electron নিজেই backend চালু করে।

### 4. Voice

Click the **microphone** button in the center panel. Say **"hey senz"** then your command.

Customize wake phrase in `.env`:

```
SENZ_WAKE_PHRASE=hey senz
```

## Example commands

| Banglish / English | Action |
|--------------------|--------|
| `chrome kholo` | Opens Chrome |
| `screenshot nao` | Saves screenshot to Pictures/SENZ |
| `volume 50 koro` | Sets volume |
| `ajker headlines dao` | Fetches news |
| `desktop e pdf khujo` | File search |
| `daraz e trending product khujo background e` | Spawns sub-agent |

## Project structure

```
senz/
├── backend/          # Python FastAPI agent + tools
│   ├── agent/        # Gemini, memory, sub-agents
│   └── main.py       # WebSocket API
├── frontend/         # Electron + React UI
└── data/             # SQLite memory (auto-created)
```

## Configuration (.env)

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Required — Google AI Studio key |
| `GEMINI_MODEL` | Default `gemini-2.0-flash` |
| `SENZ_WAKE_PHRASE` | Wake word (default `hey senz`) |
| `SENZ_PORT` | Backend port (default `8765`) |

## Security note

SENZ can run PowerShell and control your PC. Only use on your own machine. Review tool actions in the **LOGS** tab.

## Roadmap

- [ ] Live camera / screen share (Media Link)
- [ ] Sat-Link video feeds
- [ ] Custom wake word (Porcupine)
- [ ] More apps & Bengali STT

---

Built for you. **SENZ** is always listening — when you want it to be.
