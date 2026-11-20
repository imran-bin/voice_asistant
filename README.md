# JARVIS AI — Personal Ollama Voice Assistant & Windows Automation

A personal AI voice assistant powered by local Ollama models with a futuristic, Iron-Man-inspired HUD dashboard, real-time voice recognition, text-to-speech audio feedback, and full **Windows PC Automation** capabilities.

---

## 🚀 Features

- **100% Local LLM Processing**: Direct integration with local Ollama instance (`http://127.0.0.1:11434`).
- **Hands-Free / Continuous Voice**: Auto-restart voice recognition loop so you never have to click the microphone repeatedly.
- **Windows PC Automation**:
  - **YouTube & Media**: Open YouTube and search for any video, topic, or waz (e.g., *"youtube open then waz open"*, *"play waz on youtube"*, *"open youtube"*).
  - **Web Searches**: Search Google instantly (*"search [query]"*, *"google [query]"*).
  - **Folder Navigation**: Open Downloads, Desktop, Documents, Pictures, Videos, Music, C Drive (*"open downloads folder"*, *"open desktop"*, *"downloads open"*).
  - **Application Launcher**: Launch Notepad, Calculator, VS Code, Chrome, Edge, Command Prompt, PowerShell, Task Manager, Windows Settings (*"open notepad"*, *"open vs code"*, *"open calculator"*).
  - **Real-Time System Info**: Time and date reporting (*"what time is it"*, *"what's the date"*).
- **Holographic HUD**:
  - Animated Arc Reactor visualizer with dynamic ring states (*Standby*, *Listening*, *Processing*, *Speaking*).
  - Multi-frequency audio equalizer waveform.
  - Live system status monitor and local time display.
- **Natural Voice Synthesis (Text-to-Speech)**:
  - Spoken responses tailored for speech (clean markdown stripping for natural cadence).
  - Selectable browser synthesis voices (UK / US / Natural).
  - Instant speech cancellation / mute control (`ESC` key or `MUTE SPEECH`).
- **Multi-Language Speech Input**: Supports **English (US)**, **English (UK)**, and **বাংলা (Bangladesh)**.

---

## 📁 Project Structure

```text
jarvis/
├── main.py              # FastAPI server & Ollama chat bridge
├── automation.py        # Windows Automation Engine (YouTube, Apps, Folders, Web)
├── requirements.txt      # Python dependencies
├── run.bat              # Windows 1-click launcher
├── run.ps1              # PowerShell launcher
├── README.md            # Documentation & setup guide
├── static/
│   ├── index.html       # JARVIS futuristic HUD interface
│   ├── style.css        # Sci-Fi theme, animations & responsive layout
│   └── app.js           # Hands-free Speech API, visualizer & chat state
└── venv/                # Python virtual environment (pre-installed)
```

---

## ⚡ Quick Start

### 1-Click Launch (Recommended)
Simply double-click [run.bat](file:///c:/Users/MW/OneDrive/Desktop/jarvis/run.bat) (or run `.\run.bat` in Command Prompt / Terminal).

It will:
1. Detect Python 3.10+.
2. Activate the pre-configured `venv`.
3. Launch the server at `http://127.0.0.1:8000`.
4. Automatically open your default web browser (Chrome or Edge recommended).

👉 **URL**: **`http://127.0.0.1:8000`**

---

## 🗣️ Supported Voice Commands & Directives

| Category | Voice Command Example | Action Performed |
| :--- | :--- | :--- |
| **YouTube Search** | `"youtube open then waz open"` | Opens YouTube and searches for "waz" |
| **YouTube Play** | `"play waz on youtube"` | Searches and plays "waz" on YouTube |
| **YouTube Home** | `"open youtube"` or `"youtube open"` | Opens YouTube homepage in browser |
| **Web Search** | `"search quantum computing"` / `"google waz"` | Searches Google for the topic |
| **Websites** | `"open google"`, `"open github"`, `"open chatgpt"` | Opens the respective website |
| **Folders** | `"open downloads folder"` or `"downloads open"` | Opens Windows `Downloads` in File Explorer |
| **Folders** | `"open desktop"` or `"open documents"` | Opens `Desktop` or `Documents` |
| **Applications** | `"open notepad"` or `"notepad open"` | Launches Windows Notepad |
| **Applications** | `"open calculator"` or `"calculator open"` | Launches Windows Calculator |
| **Applications** | `"open vs code"` or `"open code"` | Launches Visual Studio Code |
| **Applications** | `"open cmd"` or `"open terminal"` | Launches Command Prompt |
| **Applications** | `"open settings"` / `"open task manager"` | Opens Windows Settings / Task Manager |
| **System Info** | `"what time is it"` / `"what's the date"` | JARVIS states the current time or date |
| **Conversations** | Any question or request | Answered by local Ollama model (`llama3.2`) |
