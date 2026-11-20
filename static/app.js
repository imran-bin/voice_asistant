/**
 * JARVIS AI — Client Script
 * Handles Speech Recognition, Speech Synthesis, Ollama API integration & HUD state.
 * Features Continuous Hands-Free Listening & Automatic Conversation Loop.
 */

// Global State
const state = {
  isListening: false,
  isSpeaking: false,
  isProcessing: false,
  handsFreeActive: false, // Hands-free session active
  restartTimer: null,
  submitTimer: null,
  recognition: null,
  synthesis: window.speechSynthesis || null,
  selectedVoice: null,
  availableVoices: [],
  conversationHistory: [], // [{role: 'user', content: '...'}, {role: 'assistant', content: '...'}]
  activeModel: 'llama3.2:latest',
};

// DOM Elements
const elements = {
  systemStatus: document.getElementById('system-status'),
  statusLabel: document.getElementById('status-label'),
  modelSelector: document.getElementById('model-selector'),
  clearBtn: document.getElementById('clear-btn'),
  clockDisplay: document.getElementById('clock-display'),
  arcReactor: document.getElementById('arc-reactor'),
  coreOrb: document.getElementById('core-orb'),
  equalizer: document.getElementById('equalizer'),
  voiceState: document.getElementById('voice-state'),
  transcriptPreview: document.getElementById('transcript-preview'),
  micToggleBtn: document.getElementById('mic-toggle-btn'),
  micBtnLabel: document.getElementById('mic-btn-label'),
  dockMicBtn: document.getElementById('dock-mic-btn'),
  stopSpeechBtn: document.getElementById('stop-speech-btn'),
  voiceSelect: document.getElementById('voice-select'),
  micLangSelect: document.getElementById('mic-lang-select'),
  handsFreeToggle: document.getElementById('hands-free-toggle'),
  autoSpeakToggle: document.getElementById('auto-speak-toggle'),
  autoSubmitMic: document.getElementById('auto-submit-mic'),
  chatViewport: document.getElementById('chat-viewport'),
  messageStream: document.getElementById('message-stream'),
  chatForm: document.getElementById('chat-form'),
  userInput: document.getElementById('user-input'),
  sendBtn: document.getElementById('send-btn'),
};

// 1. Initial Setup & Initialization
document.addEventListener('DOMContentLoaded', () => {
  initClock();
  initSpeechRecognition();
  initSpeechSynthesis();
  checkSystemStatus();
  bindEventListeners();
});

// Real-time HUD Clock
function initClock() {
  const updateClock = () => {
    const now = new Date();
    elements.clockDisplay.textContent = now.toTimeString().split(' ')[0];
  };
  updateClock();
  setInterval(updateClock, 1000);
}

// 2. Ollama Status & Model Fetching
async function checkSystemStatus() {
  try {
    const resp = await fetch('/api/status');
    const data = await resp.json();

    if (data.online) {
      elements.systemStatus.classList.remove('offline');
      elements.systemStatus.classList.add('online');
      elements.statusLabel.textContent = 'ONLINE // SECURE';

      // Populate models
      await loadAvailableModels();
    } else {
      elements.systemStatus.classList.remove('online');
      elements.systemStatus.classList.add('offline');
      elements.statusLabel.textContent = 'OLLAMA OFFLINE';
      elements.transcriptPreview.textContent = 'Warning: Local Ollama service is unreachable.';
    }
  } catch (err) {
    elements.systemStatus.classList.add('offline');
    elements.statusLabel.textContent = 'BACKEND OFFLINE';
    console.error('Status check error:', err);
  }
}

async function loadAvailableModels() {
  try {
    const resp = await fetch('/api/models');
    const data = await resp.json();

    if (data.models && data.models.length > 0) {
      elements.modelSelector.innerHTML = '';
      data.models.forEach((modelName) => {
        const opt = document.createElement('option');
        opt.value = modelName;
        opt.textContent = modelName;
        elements.modelSelector.appendChild(opt);
      });

      if (data.active_default) {
        elements.modelSelector.value = data.active_default;
        state.activeModel = data.active_default;
      }
    }
  } catch (err) {
    console.warn('Failed to load models list:', err);
  }
}

// 3. Speech Recognition Setup (Web Speech API)
function initSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognition) {
    elements.transcriptPreview.textContent =
      'Notice: Speech Recognition not supported in this browser. Please use Chrome or Edge.';
    elements.micToggleBtn.disabled = true;
    elements.dockMicBtn.disabled = true;
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.continuous = true; // Stay active across pauses
  recognition.interimResults = true;
  recognition.lang = elements.micLangSelect ? elements.micLangSelect.value : 'en-US';

  recognition.onstart = () => {
    state.isListening = true;
    updateVisualizerState('listening');
    elements.micToggleBtn.classList.add('listening');
    elements.dockMicBtn.classList.add('active');
    elements.micBtnLabel.textContent = state.handsFreeActive
      ? 'ALWAYS LISTENING'
      : 'LISTENING...';
    elements.voiceState.textContent = state.handsFreeActive
      ? 'HANDS-FREE PROTOCOL ACTIVE'
      : 'MICROPHONE ENGAGED';
    elements.transcriptPreview.textContent = 'Listening to voice directive...';
  };

  recognition.onresult = (event) => {
    let interimTranscript = '';
    let finalTranscript = '';

    for (let i = event.resultIndex; i < event.results.length; ++i) {
      if (event.results[i].isFinal) {
        finalTranscript += event.results[i][0].transcript;
      } else {
        interimTranscript += event.results[i][0].transcript;
      }
    }

    const currentText = (finalTranscript || interimTranscript).trim();
    if (currentText) {
      elements.transcriptPreview.textContent = `"${currentText}"`;
      elements.userInput.value = currentText;
    }

    if (finalTranscript && elements.autoSubmitMic.checked) {
      if (state.submitTimer) clearTimeout(state.submitTimer);
      state.submitTimer = setTimeout(() => {
        try {
          recognition.stop();
        } catch (e) {}
        handleUserSubmit(finalTranscript.trim());
      }, 350);
    }
  };

  recognition.onerror = (event) => {
    console.warn('Speech recognition notice:', event.error);
    if (event.error === 'no-speech' || event.error === 'aborted') {
      // Natural silence or browser restart - do NOT stop hands-free
      return;
    }
    if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
      state.handsFreeActive = false;
      stopListening(true);
      elements.transcriptPreview.textContent =
        'Microphone permission blocked. Please grant microphone access.';
      return;
    }
    elements.transcriptPreview.textContent = `Mic notice: ${event.error}`;
  };

  recognition.onend = () => {
    state.isListening = false;
    elements.dockMicBtn.classList.remove('active');

    // Auto-restart if hands-free is enabled and not speaking/processing
    if (state.handsFreeActive && !state.isSpeaking && !state.isProcessing) {
      scheduleAutoRestart(300);
    } else if (!state.handsFreeActive) {
      stopListening(false);
    }
  };

  state.recognition = recognition;
}

function startListening(fromUserAction = false) {
  if (!state.recognition) return;
  if (state.isListening) return;

  if (fromUserAction) {
    // If user clicked mic button, activate hands-free according to checkbox
    state.handsFreeActive = elements.handsFreeToggle.checked;
  }

  // Interrupt active speech
  stopSpeaking();

  if (elements.micLangSelect) {
    state.recognition.lang = elements.micLangSelect.value;
  }

  try {
    state.recognition.start();
  } catch (e) {
    // If browser is still resetting, schedule restart
    scheduleAutoRestart(350);
  }
}

function stopListening(forceShutdown = false) {
  if (forceShutdown) {
    state.handsFreeActive = false;
  }

  if (state.restartTimer) {
    clearTimeout(state.restartTimer);
    state.restartTimer = null;
  }

  state.isListening = false;
  elements.micToggleBtn.classList.remove('listening');
  elements.dockMicBtn.classList.remove('active');
  elements.micBtnLabel.textContent = 'START VOICE';

  try {
    if (state.recognition) state.recognition.stop();
  } catch (e) {}

  if (!state.isProcessing && !state.isSpeaking) {
    updateVisualizerState('standby');
    elements.voiceState.textContent = 'SYSTEM READY';
  }
}

function scheduleAutoRestart(delayMs = 300) {
  if (state.restartTimer) clearTimeout(state.restartTimer);
  state.restartTimer = setTimeout(() => {
    if (
      state.handsFreeActive &&
      !state.isSpeaking &&
      !state.isProcessing &&
      !state.isListening
    ) {
      try {
        if (elements.micLangSelect) {
          state.recognition.lang = elements.micLangSelect.value;
        }
        state.recognition.start();
      } catch (err) {
        console.warn('Auto-restart retry:', err);
      }
    }
  }, delayMs);
}

// 4. Speech Synthesis Setup (Text-to-Speech)
function initSpeechSynthesis() {
  if (!state.synthesis) {
    console.warn('Speech synthesis not supported in this browser.');
    return;
  }

  const populateVoiceList = () => {
    state.availableVoices = state.synthesis.getVoices();
    elements.voiceSelect.innerHTML = '';

    if (state.availableVoices.length === 0) return;

    let selectedIndex = 0;
    // Prefer English voices with natural qualities (UK / US / Daniel / Oliver / George / Google)
    state.availableVoices.forEach((voice, index) => {
      const opt = document.createElement('option');
      opt.value = index;
      opt.textContent = `${voice.name} (${voice.lang})${voice.default ? ' [Default]' : ''}`;
      elements.voiceSelect.appendChild(opt);

      const nameLower = voice.name.toLowerCase();
      if (
        nameLower.includes('george') ||
        nameLower.includes('daniel') ||
        nameLower.includes('uk english male') ||
        nameLower.includes('natural') ||
        nameLower.includes('jarvis')
      ) {
        selectedIndex = index;
      }
    });

    elements.voiceSelect.selectedIndex = selectedIndex;
    state.selectedVoice = state.availableVoices[selectedIndex];
  };

  populateVoiceList();
  if (state.synthesis.onvoiceschanged !== undefined) {
    state.synthesis.onvoiceschanged = populateVoiceList;
  }
}

function speakText(text) {
  if (!state.synthesis || !text) {
    if (state.handsFreeActive) scheduleAutoRestart(400);
    return;
  }

  // Cancel any active speech
  stopSpeaking();

  // Stop mic while speaking so JARVIS doesn't transcribe its own voice
  if (state.recognition) {
    try {
      state.recognition.stop();
    } catch (e) {}
  }

  // Clean formatted text for natural audio speech
  const cleanedText = cleanTextForSpeech(text);
  if (!cleanedText) {
    if (state.handsFreeActive) scheduleAutoRestart(400);
    return;
  }

  const utterance = new SpeechSynthesisUtterance(cleanedText);

  // Set selected voice
  const voiceIndex = elements.voiceSelect.value;
  if (state.availableVoices[voiceIndex]) {
    utterance.voice = state.availableVoices[voiceIndex];
  }

  utterance.rate = 1.05; // Brisk, confident JARVIS pace
  utterance.pitch = 0.95; // Refined pitch

  utterance.onstart = () => {
    state.isSpeaking = true;
    updateVisualizerState('speaking');
    elements.voiceState.textContent = 'JARVIS TRANSMITTING SPEECH';
  };

  utterance.onend = () => {
    state.isSpeaking = false;
    // When done speaking, resume hands-free listening automatically!
    if (state.handsFreeActive) {
      elements.voiceState.textContent = 'STANDBY // RESUMING MIC...';
      scheduleAutoRestart(400);
    } else {
      if (!state.isListening && !state.isProcessing) {
        updateVisualizerState('standby');
        elements.voiceState.textContent = 'SYSTEM READY';
      }
    }
  };

  utterance.onerror = (e) => {
    console.warn('Speech synthesis error:', e);
    state.isSpeaking = false;
    if (state.handsFreeActive) {
      scheduleAutoRestart(400);
    } else {
      updateVisualizerState('standby');
    }
  };

  state.synthesis.speak(utterance);
}

function stopSpeaking() {
  if (state.synthesis) {
    state.synthesis.cancel();
    state.isSpeaking = false;
    if (!state.isListening && !state.isProcessing) {
      updateVisualizerState('standby');
      elements.voiceState.textContent = 'SYSTEM READY';
    }
  }
}

function cleanTextForSpeech(raw) {
  let text = raw;
  // Remove markdown code fences ```python ... ```
  text = text.replace(/```[\s\S]*?```/g, 'Code block omitted for speech.');
  // Remove inline backticks `code`
  text = text.replace(/`([^`]+)`/g, '$1');
  // Remove markdown bold / italic **text** or *text*
  text = text.replace(/\*\*([^*]+)\*\*/g, '$1');
  text = text.replace(/\*([^*]+)\*/g, '$1');
  // Remove markdown headings ###
  text = text.replace(/#{1,6}\s+/g, '');
  // Remove markdown link syntax [text](url)
  text = text.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');
  // Remove bullets and numbers
  text = text.replace(/^\s*[-*+]\s+/gm, '');
  text = text.replace(/^\s*\d+\.\s+/gm, '');
  return text.trim();
}

// 5. Visualizer State Manager
function updateVisualizerState(status) {
  elements.arcReactor.classList.remove(
    'state-listening',
    'state-processing',
    'state-speaking'
  );

  if (status === 'listening') {
    elements.arcReactor.classList.add('state-listening');
    elements.equalizer.classList.add('active');
  } else if (status === 'processing') {
    elements.arcReactor.classList.add('state-processing');
    elements.equalizer.classList.add('active');
  } else if (status === 'speaking') {
    elements.arcReactor.classList.add('state-speaking');
    elements.equalizer.classList.add('active');
  } else {
    elements.equalizer.classList.remove('active');
  }
}

// 6. Chat Messaging & Ollama API
async function handleUserSubmit(queryText) {
  const query = (queryText || elements.userInput.value).trim();
  if (!query) return;

  // Add user bubble
  appendMessage('user', query);
  elements.userInput.value = '';

  // Update State to Processing
  state.isProcessing = true;
  updateVisualizerState('processing');
  elements.voiceState.textContent = 'ANALYZING DIRECTIVE...';
  elements.transcriptPreview.textContent = `Consulting Ollama (${state.activeModel})...`;
  elements.sendBtn.disabled = true;

  try {
    const payload = {
      message: query,
      history: state.conversationHistory,
      model: elements.modelSelector.value || state.activeModel,
    };

    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!resp.ok) {
      const errData = await resp.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(errData.detail || `Server status ${resp.status}`);
    }

    const data = await resp.json();
    const assistantReply = data.response;

    // Append to UI
    appendMessage('assistant', assistantReply);

    // Save to context history
    state.conversationHistory.push({ role: 'user', content: query });
    state.conversationHistory.push({ role: 'assistant', content: assistantReply });

    // Auto-Speak if enabled
    if (elements.autoSpeakToggle.checked) {
      speakText(assistantReply);
    } else {
      updateVisualizerState('standby');
      elements.voiceState.textContent = 'DIRECTIVE COMPLETE';
      if (state.handsFreeActive) {
        scheduleAutoRestart(350);
      }
    }
  } catch (err) {
    console.error('Chat API Error:', err);
    appendMessage(
      'assistant',
      `Sir, an error occurred while processing your request: ${err.message}`
    );
    updateVisualizerState('standby');
    elements.voiceState.textContent = 'PROTOCOL EXCEPTION';
    if (state.handsFreeActive) {
      scheduleAutoRestart(1000);
    }
  } finally {
    state.isProcessing = false;
    elements.sendBtn.disabled = false;
  }
}

function appendMessage(role, text) {
  const isUser = role === 'user';
  const bubble = document.createElement('div');
  bubble.className = `message-bubble ${isUser ? 'user-bubble' : 'assistant-bubble'}`;

  const now = new Date();
  const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  // Bubble Header
  const header = document.createElement('div');
  header.className = 'bubble-header';
  header.innerHTML = `
    <span class="agent-tag">${isUser ? 'USER // AUTHORIZED' : 'JARVIS'}</span>
    <span class="message-time">${timeStr}</span>
  `;

  // Bubble Content
  const content = document.createElement('div');
  content.className = 'bubble-content';

  if (text.includes('```')) {
    content.innerHTML = formatCodeBlocks(text);
  } else {
    content.textContent = text;
  }

  bubble.appendChild(header);
  bubble.appendChild(content);

  // Actions for Assistant bubble (Speak / Copy)
  if (!isUser) {
    const actions = document.createElement('div');
    actions.className = 'bubble-actions';

    const speakBtn = document.createElement('button');
    speakBtn.className = 'bubble-action-btn';
    speakBtn.title = 'Speak this message';
    speakBtn.innerHTML = `
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
        <path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path>
      </svg>
      Speak
    `;
    speakBtn.onclick = () => speakText(text);

    actions.appendChild(speakBtn);
    bubble.appendChild(actions);
  }

  elements.messageStream.appendChild(bubble);
  elements.chatViewport.scrollTo({
    top: elements.chatViewport.scrollHeight,
    behavior: 'smooth',
  });
}

function formatCodeBlocks(raw) {
  const escaped = raw
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  return escaped.replace(/```([\w]*)\n([\s\S]*?)```/g, (match, lang, code) => {
    return `<pre><code>${code.trim()}</code></pre>`;
  });
}

// 7. Event Listeners & UI Binding
function bindEventListeners() {
  // Chat form submit
  elements.chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    handleUserSubmit();
  });

  // Main Mic Toggle Button (Clicking toggles continuous voice listening)
  elements.micToggleBtn.addEventListener('click', () => {
    if (state.isListening || state.handsFreeActive) {
      stopListening(true); // Force complete shutdown
      elements.transcriptPreview.textContent = 'Voice recognition stopped.';
    } else {
      state.handsFreeActive = elements.handsFreeToggle.checked;
      startListening(true);
    }
  });

  // Dock shortcut Mic Button
  elements.dockMicBtn.addEventListener('click', () => {
    if (state.isListening || state.handsFreeActive) {
      stopListening(true);
    } else {
      state.handsFreeActive = elements.handsFreeToggle.checked;
      startListening(true);
    }
  });

  // Hands-Free Mode Toggle
  elements.handsFreeToggle.addEventListener('change', (e) => {
    if (!e.target.checked) {
      state.handsFreeActive = false;
      elements.transcriptPreview.textContent = 'Hands-free continuous mode disabled.';
    } else {
      state.handsFreeActive = true;
      elements.transcriptPreview.textContent = 'Hands-free continuous mode enabled.';
      if (!state.isListening && !state.isSpeaking && !state.isProcessing) {
        startListening(true);
      }
    }
  });

  // Language Selector Change
  if (elements.micLangSelect) {
    elements.micLangSelect.addEventListener('change', (e) => {
      if (state.recognition) {
        state.recognition.lang = e.target.value;
        if (state.isListening) {
          try {
            state.recognition.stop();
          } catch (err) {}
          scheduleAutoRestart(250);
        }
      }
    });
  }

  // Stop Speech Mute Button
  elements.stopSpeechBtn.addEventListener('click', () => {
    stopSpeaking();
  });

  // Model Selection Change
  elements.modelSelector.addEventListener('change', (e) => {
    state.activeModel = e.target.value;
    elements.transcriptPreview.textContent = `Active model switched to ${state.activeModel}`;
  });

  // Clear Conversation Button
  elements.clearBtn.addEventListener('click', () => {
    stopSpeaking();
    state.conversationHistory = [];
    elements.messageStream.innerHTML = `
      <div class="message-bubble assistant-bubble">
        <div class="bubble-header">
          <span class="agent-tag">JARVIS</span>
          <span class="message-time">RESET</span>
        </div>
        <div class="bubble-content">
          Conversation memory purged, sir. I am standing by for fresh instructions.
        </div>
      </div>
    `;
    elements.transcriptPreview.textContent = 'Conversation context cleared.';
  });

  // Quick Prompt Chips
  document.querySelectorAll('.quick-chip').forEach((chip) => {
    chip.addEventListener('click', () => {
      const prompt = chip.getAttribute('data-prompt');
      if (prompt) {
        elements.userInput.value = prompt;
        handleUserSubmit(prompt);
      }
    });
  });

  // Keyboard shortcut: Escape cancels speech immediately
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      stopSpeaking();
      stopListening(true);
    }
  });
}
