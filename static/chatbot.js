/**
 * UDYAMSetu — Floating AI Loan Assistant Chatbot Widget
 * Self-contained vanilla JS. Works on every page that loads this script.
 * Requires: /api/chat endpoint (Flask), CSS in style.css.
 */

(function () {
  'use strict';

  /* -----------------------------------------------------------------------
     1. Inject widget HTML into <body>
  ----------------------------------------------------------------------- */
  const WIDGET_HTML = `
  <div id="chat-widget" aria-label="AI Loan Assistant" role="complementary">

    <!-- Floating Action Button -->
    <button id="chat-fab" type="button" aria-expanded="false" aria-controls="chat-modal">
      <span class="fab-icon" aria-hidden="true">💬</span>
      <span class="fab-label">Ask UDYAMSetu</span>
    </button>

    <!-- Chat Modal -->
    <div id="chat-modal" role="dialog" aria-modal="true" aria-label="UDYAMSetu AI Loan Assistant">

      <!-- Header -->
      <div class="chat-header">
        <div class="chat-header-info">
          <div class="chat-avatar" aria-hidden="true">🤖</div>
          <div class="chat-header-text">
            <h4>UDYAMSetu AI</h4>
            <p>Stand-Up India &amp; NSFDC Advisor</p>
          </div>
        </div>
        <button id="chat-close-btn" type="button" aria-label="Close chat assistant">✕</button>
      </div>

      <!-- Message thread -->
      <div id="chat-messages" role="log" aria-live="polite" aria-label="Chat messages"></div>

      <!-- Suggestion chips — shown until user sends first message -->
      <div class="chat-chips" id="chat-chips">
        <button class="chat-chip" type="button">Am I eligible with an existing home loan?</button>
        <button class="chat-chip" type="button">What documents are required for Stand-Up India?</button>
        <button class="chat-chip" type="button">What is the family income limit for NSFDC?</button>
      </div>

      <!-- Input row -->
      <div class="chat-input-row">
        <input
          id="chat-input"
          type="text"
          placeholder="Ask about eligibility, documents, schemes…"
          maxlength="400"
          autocomplete="off"
          aria-label="Type your question"
        />
        <button id="chat-send-btn" type="button" aria-label="Send message" disabled>➤</button>
      </div>

    </div><!-- /#chat-modal -->
  </div><!-- /#chat-widget -->
  `;

  document.body.insertAdjacentHTML('beforeend', WIDGET_HTML);

  /* -----------------------------------------------------------------------
     2. State
  ----------------------------------------------------------------------- */
  let isOpen = false;
  let isLoading = false;
  /** @type {{ role: 'user'|'model', parts: [string] }[]} */
  const conversationHistory = [];
  let chipsVisible = true;

  /* -----------------------------------------------------------------------
     3. DOM refs
  ----------------------------------------------------------------------- */
  const fab        = document.getElementById('chat-fab');
  const modal      = document.getElementById('chat-modal');
  const closeBtn   = document.getElementById('chat-close-btn');
  const messages   = document.getElementById('chat-messages');
  const input      = document.getElementById('chat-input');
  const sendBtn    = document.getElementById('chat-send-btn');
  const chipsEl    = document.getElementById('chat-chips');
  const chips      = chipsEl.querySelectorAll('.chat-chip');

  /* -----------------------------------------------------------------------
     4. Open / Close
  ----------------------------------------------------------------------- */
  function openChat() {
    isOpen = true;
    modal.classList.add('open');
    fab.setAttribute('aria-expanded', 'true');
    input.focus();

    // Show greeting on first open
    if (conversationHistory.length === 0) {
      appendAssistantBubble(
        '👋 Hello! I\'m the UDYAMSetu AI advisor.\n\nI can help you understand eligibility for **Stand-Up India** and **NSFDC** schemes, required documents, income limits, and more.\n\nPlease use the quick-start chips below or type your question — having an active home loan is perfectly fine! 😊'
      );
    }
  }

  function closeChat() {
    isOpen = false;
    modal.classList.remove('open');
    fab.setAttribute('aria-expanded', 'false');
    fab.focus();
  }

  fab.addEventListener('click', () => isOpen ? closeChat() : openChat());
  closeBtn.addEventListener('click', closeChat);

  // Close on Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && isOpen) closeChat();
  });

  /* -----------------------------------------------------------------------
     5. Input enablement
  ----------------------------------------------------------------------- */
  input.addEventListener('input', () => {
    sendBtn.disabled = input.value.trim().length === 0 || isLoading;
  });

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !sendBtn.disabled) {
      e.preventDefault();
      sendMessage(input.value.trim());
    }
  });

  sendBtn.addEventListener('click', () => {
    if (!sendBtn.disabled) sendMessage(input.value.trim());
  });

  /* -----------------------------------------------------------------------
     6. Suggestion chips
  ----------------------------------------------------------------------- */
  chips.forEach((chip) => {
    chip.addEventListener('click', () => {
      if (isLoading) return;
      sendMessage(chip.textContent.trim());
    });
  });

  function hideChips() {
    if (chipsVisible) {
      chipsEl.style.display = 'none';
      chipsVisible = false;
    }
  }

  /* -----------------------------------------------------------------------
     7. Bubble helpers
  ----------------------------------------------------------------------- */
  function appendBubble(role, text) {
    const div = document.createElement('div');
    div.className = `chat-bubble ${role}`;
    // Simple markdown: **bold** and newlines
    div.innerHTML = escapeHtml(text)
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br>');
    messages.appendChild(div);
    scrollToBottom();
    return div;
  }

  function appendUserBubble(text) {
    return appendBubble('user', text);
  }

  function appendAssistantBubble(text) {
    return appendBubble('assistant', text);
  }

  function showLoadingDots() {
    const loader = document.createElement('div');
    loader.className = 'chat-loading';
    loader.id = 'chat-loader';
    loader.setAttribute('aria-label', 'AI is typing');
    loader.innerHTML = '<span></span><span></span><span></span>';
    messages.appendChild(loader);
    scrollToBottom();
  }

  function removeLoadingDots() {
    const loader = document.getElementById('chat-loader');
    if (loader) loader.remove();
  }

  function scrollToBottom() {
    messages.scrollTop = messages.scrollHeight;
  }

  function escapeHtml(str) {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  /* -----------------------------------------------------------------------
     8. Send message → /api/chat
  ----------------------------------------------------------------------- */
  async function sendMessage(text) {
    if (!text || isLoading) return;

    hideChips();

    // Render user bubble
    appendUserBubble(text);
    input.value = '';
    sendBtn.disabled = true;

    // Add to history
    conversationHistory.push({ role: 'user', parts: [text] });

    // Show loading
    isLoading = true;
    showLoadingDots();

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          // Send all history except the last user message (server builds it)
          history: conversationHistory.slice(0, -1)
        })
      });

      const data = await response.json();
      removeLoadingDots();

      if (data.error) {
        appendAssistantBubble(
          '⚠️ Sorry, I\'m temporarily unavailable. ' + data.error +
          '\n\nFor direct assistance, call the **Stand-Up India helpline: 1800-180-1111** or visit standupmitra.in.'
        );
      } else {
        const replyText = data.reply || 'I could not generate a response. Please try again.';
        appendAssistantBubble(replyText);
        // Record model reply in history
        conversationHistory.push({ role: 'model', parts: [replyText] });
      }
    } catch (err) {
      removeLoadingDots();
      appendAssistantBubble(
        '⚠️ Network error — please check your connection and try again.\n\nFor immediate help, visit **standupmitra.in** or call **1800-180-1111**.'
      );
      console.error('[UDYAMSetu Chat]', err);
    } finally {
      isLoading = false;
      sendBtn.disabled = input.value.trim().length === 0;
    }
  }

})();
