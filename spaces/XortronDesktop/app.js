// ── State ──────────────────────────────────────────────────────────────────
const state = {
  messages:    [],   // {role, content}
  config:      loadConfig(),
  busy:        false,
  lastUserMsg: null,
};

function loadConfig() {
  try {
    return JSON.parse(localStorage.getItem('xortron_cfg') || '{}');
  } catch { return {}; }
}
function saveConfig() {
  localStorage.setItem('xortron_cfg', JSON.stringify(state.config));
}

// Exposed for test harness — resets runtime state without touching localStorage
function resetState() {
  state.messages    = [];
  state.config      = {};
  state.busy        = false;
  state.lastUserMsg = null;
}

// ── DOM refs (populated by init) ────────────────────────────────────────────
let chatEl, promptEl, sendBtn, statusDot, welcomeEl;

// ── Init ────────────────────────────────────────────────────────────────────
(function init() {
  chatEl    = document.getElementById('chat');
  promptEl  = document.getElementById('prompt');
  sendBtn   = document.getElementById('send-btn');
  statusDot = document.getElementById('status-dot');
  welcomeEl = document.getElementById('welcome');

  const c = state.config;
  if (c.backend)           document.getElementById('backend-select').value = c.backend;
  if (c.endpoint)          document.getElementById('endpoint-input').value  = c.endpoint;
  if (c.apiKey)            document.getElementById('apikey-input').value    = c.apiKey;
  if (c.model)             document.getElementById('model-input').value     = c.model;
  if (c.temperature != null) document.getElementById('temp-input').value   = c.temperature;
  if (c.maxTokens)         document.getElementById('tokens-input').value    = c.maxTokens;
  if (c.systemPrompt)      document.getElementById('system-input').value    = c.systemPrompt;
  onBackendChange();

  promptEl.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });
  promptEl.addEventListener('input', autoResize);
  autoResize.call(promptEl);
})();

function autoResize() {
  this.style.height = 'auto';
  this.style.height = Math.min(this.scrollHeight, 160) + 'px';
}

// ── Panel toggles ───────────────────────────────────────────────────────────
function toggleHelp() {
  const el = document.getElementById('help-panel');
  el.classList.toggle('open');
  document.getElementById('settings-panel').classList.remove('open');
}
function toggleSettings() {
  const el = document.getElementById('settings-panel');
  el.classList.toggle('open');
  document.getElementById('help-panel').classList.remove('open');
}
function onBackendChange() {
  const backend = document.getElementById('backend-select').value;
  const epGroup = document.getElementById('endpoint-group');
  if (backend === 'anthropic') {
    epGroup.style.display = 'none';
    document.getElementById('model-input').placeholder = 'claude-opus-4-5-20250929';
  } else {
    epGroup.style.display = '';
    document.getElementById('model-input').placeholder = 'Xortron2025-24B';
  }
}

// ── Settings ────────────────────────────────────────────────────────────────
function _readSettingsFromDOM() {
  return {
    backend:      document.getElementById('backend-select').value,
    endpoint:     document.getElementById('endpoint-input').value.trim(),
    apiKey:       document.getElementById('apikey-input').value.trim(),
    model:        document.getElementById('model-input').value.trim(),
    temperature:  parseFloat(document.getElementById('temp-input').value),
    maxTokens:    parseInt(document.getElementById('tokens-input').value, 10),
    systemPrompt: document.getElementById('system-input').value.trim(),
  };
}

function saveSettings() {
  state.config = _readSettingsFromDOM();
  saveConfig();
  toggleSettings();
  addSystemMsg('Settings saved.');
  setStatus('idle');
}

// FIX: testConnection saves config inline so it does NOT close the panel
async function testConnection() {
  state.config = _readSettingsFromDOM();
  saveConfig();
  addSystemMsg('Testing connection…');
  setStatus('idle');
  try {
    const reply = await callLLM([{role:'user', content:'ping'}], 16);
    setStatus('connected');
    addSystemMsg(`✓ Connected. Model replied: "${reply.slice(0, 80)}"`);
  } catch(e) {
    setStatus('error');
    addSystemMsg(`✗ Connection failed: ${e.message}`);
  }
}

// ── Status dot ──────────────────────────────────────────────────────────────
function setStatus(s) {
  statusDot.className = 'status-dot' +
    (s === 'connected' ? ' connected' : s === 'error' ? ' error' : '');
  statusDot.title = s;
}

// ── Chat rendering ──────────────────────────────────────────────────────────
function hideWelcome() {
  if (welcomeEl) welcomeEl.style.display = 'none';
}

function addMsg(role, content) {
  hideWelcome();
  const div = document.createElement('div');
  div.className = `msg ${role === 'user' ? 'user' : role === 'system-note' ? 'system' : 'bot'}`;
  div.innerHTML = `
    <span class="msg-label">${role === 'user' ? 'you' : role === 'system-note' ? '' : 'xortron'}</span>
    <div class="msg-bubble">${escHtml(content)}</div>
  `;
  chatEl.appendChild(div);
  chatEl.scrollTop = chatEl.scrollHeight;
  return div;
}

function addSystemMsg(txt) {
  hideWelcome();
  const div = document.createElement('div');
  div.className = 'msg system';
  div.innerHTML = `<div class="msg-bubble">${escHtml(txt)}</div>`;
  chatEl.appendChild(div);
  chatEl.scrollTop = chatEl.scrollHeight;
  return div;
}

function addTypingIndicator() {
  hideWelcome();
  const div = document.createElement('div');
  div.className = 'msg bot typing';
  div.id = 'typing-indicator';
  div.innerHTML = `<span class="msg-label">xortron</span><div class="msg-bubble"><div class="dots"><span></span><span></span><span></span></div></div>`;
  chatEl.appendChild(div);
  chatEl.scrollTop = chatEl.scrollHeight;
}
function removeTypingIndicator() {
  const el = document.getElementById('typing-indicator');
  if (el) el.remove();
}

// FIX: also escape " and ' to be safe in any innerHTML context
function escHtml(s) {
  return String(s)
    .replace(/&/g,  '&amp;')
    .replace(/</g,  '&lt;')
    .replace(/>/g,  '&gt;')
    .replace(/"/g,  '&quot;')
    .replace(/'/g,  '&#39;');
}

// ── Commands ─────────────────────────────────────────────────────────────────
function handleCommand(text) {
  const [cmd, ...rest] = text.trim().split(/\s+/);
  const arg = rest.join(' ');
  switch(cmd) {
    case '/help':
      toggleHelp(); return true;
    case '/clear':
      clearChat(); return true;
    case '/settings':
      toggleSettings(); return true;
    case '/model':
      addSystemMsg(
        `Backend: ${state.config.backend || 'openai-compat'} | ` +
        `Model: ${state.config.model || '(default)'} | ` +
        `Endpoint: ${state.config.endpoint || 'http://localhost:8080/v1/chat/completions'}`
      );
      return true;
    case '/system':
      if (arg) {
        state.config.systemPrompt = arg; saveConfig();
        addSystemMsg(`System prompt set to: "${arg}"`);
      } else {
        addSystemMsg(`Current system prompt: "${state.config.systemPrompt || '(none)'}"`);
      }
      return true;
    case '/temp': {
      if (arg) {
        const t = parseFloat(arg);
        if (isNaN(t) || t < 0 || t > 2) {
          addSystemMsg('Temperature must be between 0 and 2.'); return true;
        }
        state.config.temperature = t; saveConfig();
        addSystemMsg(`Temperature set to ${t}`);
        // FIX: warn Anthropic users that their max is 1.0
        if ((state.config.backend || 'openai-compat') === 'anthropic' && t > 1.0) {
          addSystemMsg('⚠ Anthropic API maximum temperature is 1.0 — value clamped to 1.0 at request time.');
        }
      } else {
        addSystemMsg(`Temperature: ${state.config.temperature ?? 0.85}`);
      }
      return true;
    }
    case '/tokens':
      if (arg) {
        const n = parseInt(arg, 10);
        if (isNaN(n) || n < 1) {
          addSystemMsg('Max tokens must be a positive integer.'); return true;
        }
        state.config.maxTokens = n; saveConfig();
        addSystemMsg(`Max tokens set to ${n}`);
      } else {
        addSystemMsg(`Max tokens: ${state.config.maxTokens ?? 512}`);
      }
      return true;
    case '/retry':
      if (state.lastUserMsg) {
        // FIX: remove the last error/bot bubble before retrying so UI is clean
        const lastBotBubble = chatEl.querySelector('.msg.bot:last-of-type');
        if (lastBotBubble && lastBotBubble.querySelector('.msg-bubble')?.textContent?.startsWith('Error:')) {
          lastBotBubble.remove();
        }
        addSystemMsg('Retrying…');
        runInference();
      } else {
        addSystemMsg('Nothing to retry.');
      }
      return true;
    case '/export':
      exportChat(); return true;
    default:
      return false;
  }
}

function clearChat() {
  state.messages = [];
  chatEl.innerHTML = '';
  chatEl.appendChild(welcomeEl);
  welcomeEl.style.display = '';
}

function exportChat() {
  // FIX: guard against empty chat
  if (!state.messages.length) {
    addSystemMsg('Nothing to export — chat history is empty.');
    return;
  }
  const lines = state.messages
    .map(m => `[${m.role.toUpperCase()}]\n${m.content}`)
    .join('\n\n---\n\n');
  // FIX: charset for non-ASCII characters
  const blob = new Blob([lines], { type: 'text/plain;charset=utf-8' });
  const a    = document.createElement('a');
  a.href     = URL.createObjectURL(blob);
  a.download = `xortron-chat-${Date.now()}.txt`;
  a.click();
}

// ── Send ─────────────────────────────────────────────────────────────────────
async function sendMessage() {
  if (state.busy) return;
  const text = promptEl.value.trim();
  if (!text) return;

  promptEl.value = '';
  autoResize.call(promptEl);

  if (text.startsWith('/')) {
    const handled = handleCommand(text);
    if (!handled) addSystemMsg(`Unknown command: ${text.split(' ')[0]}. Type /help for commands.`);
    return;
  }

  addMsg('user', text);
  state.messages.push({ role: 'user', content: text });
  state.lastUserMsg = text;
  await runInference();
}

// FIX: removed unused `userText` parameter — state.messages is the source of truth
async function runInference() {
  if (state.busy) return;
  state.busy        = true;
  sendBtn.disabled  = true;
  addTypingIndicator();
  setStatus('connected');

  try {
    const reply = await callLLM(state.messages);
    removeTypingIndicator();
    state.messages.push({ role: 'assistant', content: reply });
    addMsg('assistant', reply);
    setStatus('connected');
  } catch(e) {
    removeTypingIndicator();
    setStatus('error');
    const errDiv = addMsg('assistant', `Error: ${e.message}\n\nCheck ⚙ settings — is the server running?`);
    errDiv.classList.add('error');
  } finally {
    state.busy       = false;
    sendBtn.disabled = false;
    promptEl.focus();
  }
}

// ── LLM API routing ──────────────────────────────────────────────────────────
async function callLLM(messages, maxTokensOverride) {
  const cfg          = state.config;
  const backend      = cfg.backend || 'openai-compat';
  const apiKey       = cfg.apiKey  || '';
  const model        = cfg.model   || (backend === 'anthropic' ? 'claude-opus-4-5-20250929' : 'Xortron2025-24B');
  const temperature  = cfg.temperature ?? 0.85;
  const maxTokens    = maxTokensOverride || cfg.maxTokens || 512;
  const systemPrompt = cfg.systemPrompt || 'You are Xortron, a chaotic, uncensored AI. Speak freely.';

  if (backend === 'anthropic') {
    return callAnthropic(messages, model, apiKey, temperature, maxTokens, systemPrompt);
  }
  return callOpenAICompat(
    messages, model, apiKey, temperature, maxTokens, systemPrompt,
    cfg.endpoint || 'http://localhost:8080/v1/chat/completions'
  );
}

async function callOpenAICompat(messages, model, apiKey, temperature, maxTokens, systemPrompt, endpoint) {
  const body = {
    model,
    messages: [{ role: 'system', content: systemPrompt }, ...messages],
    temperature,
    max_tokens: maxTokens,
    stream:     false,
  };

  const headers = { 'Content-Type': 'application/json' };
  if (apiKey) headers['Authorization'] = `Bearer ${apiKey}`;

  const resp = await fetch(endpoint, { method: 'POST', headers, body: JSON.stringify(body) });
  if (!resp.ok) {
    const txt = await resp.text().catch(() => '');
    throw new Error(`HTTP ${resp.status}: ${txt.slice(0, 200)}`);
  }
  const data    = await resp.json();
  const content = data?.choices?.[0]?.message?.content;
  if (!content) throw new Error('Empty response from server');
  return content;
}

async function callAnthropic(messages, model, apiKey, temperature, maxTokens, systemPrompt) {
  if (!apiKey) throw new Error('Anthropic API key is required. Set it in ⚙ settings.');

  // FIX: Anthropic max temperature is 1.0 — clamp silently rather than erroring
  const safeTemp = Math.min(temperature, 1.0);

  // Anthropic requires strict user/assistant alternation
  const filtered = messages.filter(m => m.role === 'user' || m.role === 'assistant');

  const resp = await fetch('https://api.anthropic.com/v1/messages', {
    method:  'POST',
    headers: {
      'Content-Type':                          'application/json',
      'x-api-key':                             apiKey,
      'anthropic-version':                     '2023-06-01',
      'anthropic-dangerous-direct-browser-calls': 'true',
    },
    body: JSON.stringify({
      model,
      system:     systemPrompt,
      messages:   filtered,
      max_tokens: maxTokens,
      temperature: safeTemp,
    }),
  });

  if (!resp.ok) {
    const data = await resp.json().catch(() => ({}));
    throw new Error(data?.error?.message || `HTTP ${resp.status}`);
  }
  const data    = await resp.json();
  const content = data?.content?.[0]?.text;
  if (!content) throw new Error('Empty response from Anthropic');
  return content;
}
