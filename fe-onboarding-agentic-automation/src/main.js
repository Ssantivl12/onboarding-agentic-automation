import { marked } from 'marked';

marked.use({ breaks: true });

const API_BASE = import.meta.env.VITE_API_URL ?? '';

let sessionId = crypto.randomUUID();

const messagesEl  = document.getElementById('messages');
const inputEl     = document.getElementById('input');
const sendBtn     = document.getElementById('btn-send');
const newSessBtn  = document.getElementById('btn-new-session');

// ── Session ──────────────────────────────────────────────────────────────────

function resetSession() {
  sessionId = crypto.randomUUID();
  messagesEl.innerHTML = `
    <div class="welcome">
      <p>Hola. Soy el agente de onboarding de 30X.</p>
      <p>Preguntame lo que necesités sobre el equipo, los programas o las herramientas.</p>
    </div>`;
  inputEl.focus();
}

// ── Render ───────────────────────────────────────────────────────────────────

function removeWelcome() {
  messagesEl.querySelector('.welcome')?.remove();
}

function scrollToBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function appendMessage(role, content, meta = {}) {
  removeWelcome();

  const wrapper = document.createElement('div');
  wrapper.className = `message message-${role}`;

  const bubble = document.createElement('div');
  bubble.className = 'bubble';

  if (role === 'user') {
    bubble.textContent = content;
  } else {
    const body = document.createElement('div');
    body.className = 'bubble-content';
    body.innerHTML = marked.parse(content);
    bubble.appendChild(body);

    if (meta.source) {
      const el = document.createElement('div');
      el.className = 'meta meta-source';
      el.textContent = meta.source;
      bubble.appendChild(el);
    }

    if (meta.escalated_to) {
      const el = document.createElement('div');
      el.className = 'meta meta-escalation';
      el.innerHTML = `<span class="escalation-label">Escalar a</span>${meta.escalated_to}`;
      bubble.appendChild(el);
    }
  }

  wrapper.appendChild(bubble);
  messagesEl.appendChild(wrapper);
  scrollToBottom();
}

function appendLoading() {
  const wrapper = document.createElement('div');
  wrapper.className = 'message message-assistant';
  wrapper.innerHTML = '<div class="bubble loading"><span></span><span></span><span></span></div>';
  messagesEl.appendChild(wrapper);
  scrollToBottom();
  return wrapper;
}

// ── Send ─────────────────────────────────────────────────────────────────────

async function sendMessage() {
  const text = inputEl.value.trim();
  if (!text || sendBtn.disabled) return;

  inputEl.value = '';
  autoResize();
  sendBtn.disabled = true;

  appendMessage('user', text);
  const loadingEl = appendLoading();

  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, session_id: sessionId }),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    loadingEl.remove();
    appendMessage('assistant', data.reply, {
      source: data.source,
      escalated_to: data.escalated_to,
    });
  } catch {
    loadingEl.remove();
    appendMessage(
      'assistant',
      'No se pudo conectar con el servidor. Verificá que el backend esté corriendo en `localhost:8000`.',
    );
  } finally {
    sendBtn.disabled = false;
    inputEl.focus();
  }
}

// ── Input ────────────────────────────────────────────────────────────────────

function autoResize() {
  inputEl.style.height = 'auto';
  inputEl.style.height = Math.min(inputEl.scrollHeight, 200) + 'px';
}

inputEl.addEventListener('input', autoResize);

inputEl.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

sendBtn.addEventListener('click', sendMessage);
newSessBtn.addEventListener('click', resetSession);

// Focus on load
inputEl.focus();
