// ============================================
// MESSAGERIE — Tickets, conversations, réponses
// ============================================

const messagingState = {
  conversations: [],
  activeTicketId: null,
  activeTicket: null,
  selectedRecipient: null,
  searchTimeout: null,
  recipientSuggestions: []
};

async function getMessagesContent() {
  const html = await loadTemplate('messages');
  return html;
}

async function initMessagingCenter() {
  const listPanel = document.getElementById('ticketListPanel');
  if (!listPanel) return;
  listPanel.innerHTML = '<div class="text-center py-4"><span class="spinner-border text-primary"></span></div>';

  const data = await api(`messages/conversations?role=${USER.role}&user_id=${USER.id}`);
  if (data.error) {
    listPanel.innerHTML = `<div class="alert alert-danger m-3">${data.error}</div>`;
    return;
  }

  messagingState.conversations = data.tickets || [];
  const stillExists = messagingState.conversations.some(t => t.ticket_id === messagingState.activeTicketId);
  if (!stillExists) messagingState.activeTicketId = null;
  renderConversationList();

  if (messagingState.conversations.length === 0) {
    renderEmptyConversation();
  } else if (!messagingState.activeTicketId) {
    openConversation(messagingState.conversations[0].ticket_id);
  }

  renderRecipientSuggestions();
}

function renderConversationList() {
  const listPanel = document.getElementById('ticketListPanel');
  if (!listPanel) return;

  if (!messagingState.conversations.length) {
    listPanel.innerHTML = '<div class="text-center text-muted py-4">Aucun ticket pour l\'instant.</div>';
    return;
  }

  listPanel.innerHTML = messagingState.conversations.map(ticket => {
    const statusText = (ticket.status || 'open').toUpperCase();
    const active = ticket.ticket_id === messagingState.activeTicketId ? 'active' : '';
    const contact = USER.role === 'teacher'
      ? `${ticket.student_first_name || ''} ${ticket.student_last_name || ''}`.trim() || 'Étudiant'
      : `${ticket.teacher_first_name || ''} ${ticket.teacher_last_name || ''}`.trim() || 'Enseignant';
    const badgeClass = ticket.status === 'closed'
      ? 'badge bg-success-100 text-success-600'
      : ticket.status === 'pending'
        ? 'badge bg-warning-100 text-warning-600'
        : 'badge bg-primary-100 text-primary-600';
    const preview = ticket.last_message ? ticket.last_message.substring(0, 70) : 'Pas encore de message.';
    const time = ticket.last_message_at ? new Date(ticket.last_message_at).toLocaleString() : '';

    return `
      <button type="button" class="list-group-item list-group-item-action ${active}"
        onclick="openConversation(${ticket.ticket_id})">
        <div class="d-flex justify-content-between align-items-start mb-1">
          <div>
            <div class="fw-semibold text-sm">${ticket.subject}</div>
            <div class="text-xs text-neutral-500">${contact}</div>
          </div>
          <span class="${badgeClass} text-xxs text-uppercase">${statusText}</span>
        </div>
        <div class="text-xs text-neutral-500">${preview}</div>
        <div class="text-xxs text-neutral-400 mt-1">${time}</div>
      </button>
    `;
  }).join('');
}

function renderEmptyConversation() {
  const header = document.getElementById('ticketThreadHeader');
  const panel = document.getElementById('ticketMessagesPanel');
  const textarea = document.getElementById('ticketReplyInput');
  const button = document.querySelector('#ticketComposer button');
  if (header) header.textContent = 'Sélectionnez un ticket';
  if (panel) panel.innerHTML = '<div class="text-center text-muted py-5">Aucune conversation sélectionnée.</div>';
  if (textarea) textarea.disabled = true;
  if (button) button.disabled = true;
}

async function openConversation(ticketId) {
  messagingState.activeTicketId = ticketId;
  renderConversationList();

  const header = document.getElementById('ticketThreadHeader');
  const panel = document.getElementById('ticketMessagesPanel');
  const textarea = document.getElementById('ticketReplyInput');
  const button = document.querySelector('#ticketComposer button');
  if (!header || !panel || !textarea || !button) return;

  header.textContent = 'Chargement du ticket...';
  panel.innerHTML = '<div class="text-center py-4"><span class="spinner-border text-primary"></span></div>';
  textarea.disabled = true;
  button.disabled = true;

  const details = await api(`messages/conversations/${ticketId}?role=${USER.role}&user_id=${USER.id}`);
  if (details.error) {
    panel.innerHTML = `<div class="alert alert-danger m-3">${details.error}</div>`;
    header.textContent = 'Ticket indisponible';
    return;
  }

  messagingState.activeTicket = details.ticket;
  renderConversationDetail(details.ticket, details.messages || []);
}

function renderConversationDetail(ticket, messages) {
  const header = document.getElementById('ticketThreadHeader');
  const panel = document.getElementById('ticketMessagesPanel');
  const textarea = document.getElementById('ticketReplyInput');
  const button = document.querySelector('#ticketComposer button');
  if (!header || !panel || !textarea || !button) return;

  const contact = USER.role === 'teacher'
    ? `${ticket.student_first_name || ''} ${ticket.student_last_name || ''}`.trim() || 'Étudiant'
    : `${ticket.teacher_first_name || ''} ${ticket.teacher_last_name || ''}`.trim() || 'Enseignant';
  const badgeClass = ticket.status === 'closed'
    ? 'badge bg-success-100 text-success-600'
    : ticket.status === 'pending'
      ? 'badge bg-warning-100 text-warning-600'
      : 'badge bg-primary-100 text-primary-600';
  const statusText = (ticket.status || 'open').toUpperCase();

  header.innerHTML = `
    <div>
      <div class="fw-semibold">${ticket.subject}</div>
      <div class="text-sm text-neutral-500">${contact}</div>
    </div>
    <span class="${badgeClass} text-uppercase text-xxs">${statusText}</span>
  `;

  const timeline = messages.map(msg => {
    const mine = msg.sender_role === USER.role;
    const align = mine ? 'flex-row-reverse text-end' : '';
    const bubble = mine ? 'bg-primary-600 text-white' : 'bg-neutral-100 text-neutral-900';
    const name = mine ? 'Moi' : msg.sender_role === 'teacher' ? 'Professeur' : 'Étudiant';
    const date = msg.created_at ? new Date(msg.created_at).toLocaleString() : '';
    return `
      <div class="d-flex ${align} mb-3">
        <div class="p-3 radius-12 ${bubble}" style="max-width: 80%;">
          <div class="fw-semibold text-xs mb-1">${name}</div>
          <div class="text-sm mb-1">${msg.body}</div>
          <div class="text-xxs">${date}</div>
        </div>
      </div>
    `;
  }).join('');

  panel.innerHTML = timeline || '<div class="text-center text-muted py-5">Aucun message pour le moment.</div>';

  const isClosed = (ticket.status || '').toLowerCase() === 'closed';
  textarea.disabled = isClosed;
  button.disabled = isClosed;
  textarea.value = '';
}

async function sendConversationReply() {
  if (!messagingState.activeTicketId) return;
  const textarea = document.getElementById('ticketReplyInput');
  const button = document.querySelector('#ticketComposer button');
  const body = (textarea?.value || '').trim();
  if (!body) return;

  textarea.disabled = true;
  button.disabled = true;

  const resp = await api(`messages/conversations/${messagingState.activeTicketId}/messages`, {
    method: 'POST',
    body: JSON.stringify({ sender_role: USER.role, sender_id: USER.id, body })
  });

  if (resp && !resp.error) {
    await initMessagingCenter();
    await openConversation(messagingState.activeTicketId);
  } else {
    alert(resp?.error || "Erreur lors de l'envoi");
    textarea.disabled = false;
    button.disabled = false;
  }
}

function notifyTicketForm(type, message) {
  const box = document.getElementById('ticketFormAlert');
  if (!box) return;
  if (!message) { box.style.display = 'none'; return; }
  const classes = type === 'error'
    ? 'alert alert-danger d-flex align-items-center gap-2 mb-3'
    : 'alert alert-warning d-flex align-items-center gap-2 mb-3';
  box.className = classes;
  box.innerHTML = `<i class="ri-information-line"></i><span>${message}</span>`;
  box.style.display = 'flex';
}

function handleRecipientInput(event) {
  const value = event.target.value || '';
  messagingState.selectedRecipient = null;
  const hidden = document.getElementById('ticketRecipientId');
  const preview = document.getElementById('recipientSelectedPreview');
  if (hidden) hidden.value = '';
  if (preview) { preview.style.display = 'none'; preview.textContent = ''; }
  if (messagingState.searchTimeout) clearTimeout(messagingState.searchTimeout);
  if (value.trim().length < 2) {
    messagingState.recipientSuggestions = [];
    renderRecipientSuggestions();
    return;
  }
  messagingState.searchTimeout = setTimeout(() => fetchRecipientSuggestions(value.trim()), 250);
}

async function fetchRecipientSuggestions(query) {
  const data = await api(`messages/recipients?type=all&q=${encodeURIComponent(query)}`);
  messagingState.recipientSuggestions = data.error ? [] : (data.results || []);
  renderRecipientSuggestions();
}

function renderRecipientSuggestions() {
  const container = document.getElementById('recipientSuggestions');
  if (!container) return;
  if (!messagingState.recipientSuggestions.length) {
    container.innerHTML = '<div class="text-xs text-neutral-400">Commencez à taper pour rechercher.</div>';
    return;
  }

  container.innerHTML = messagingState.recipientSuggestions.map(item => `
    <button type="button" class="list-group-item list-group-item-action"
      onclick="selectRecipient('${item.role}', ${item.id})">
      <div class="fw-semibold text-sm">${item.first_name} ${item.last_name}</div>
      <div class="text-xs text-neutral-500">${item.email || ''}${item.meta ? ' · ' + item.meta : ''}</div>
    </button>
  `).join('');
}

function selectRecipient(role, id) {
  const chosen = messagingState.recipientSuggestions.find(item => item.id === id && item.role === role);
  const input = document.getElementById('ticketRecipientSearch');
  const hidden = document.getElementById('ticketRecipientId');
  const preview = document.getElementById('recipientSelectedPreview');
  if (!chosen || !input || !hidden || !preview) return;
  messagingState.selectedRecipient = chosen;
  input.value = `${chosen.first_name} ${chosen.last_name}`;
  hidden.value = chosen.id;
  preview.textContent = `Destinataire sélectionné : ${chosen.first_name} ${chosen.last_name} (${chosen.role})`;
  preview.style.display = 'block';
  const container = document.getElementById('recipientSuggestions');
  if (container) container.innerHTML = '';
}

async function submitNewTicket() {
  const subject = (document.getElementById('ticketSubject')?.value || '').trim();
  const message = (document.getElementById('ticketMessageInput')?.value || '').trim();
  const recipientId = parseInt(document.getElementById('ticketRecipientId')?.value || '0', 10);

  if (!subject || !message || !recipientId) {
    notifyTicketForm('error', 'Veuillez renseigner un sujet, un destinataire et un message.');
    return;
  }

  const payload = {
    subject, message,
    starter_role: USER.role,
    starter_id: USER.id,
    recipient_id: recipientId,
    recipient_role: messagingState.selectedRecipient.role
  };

  const resp = await api('messages/conversations', {
    method: 'POST',
    body: JSON.stringify(payload)
  });

  if (resp && !resp.error) {
    notifyTicketForm('warning', 'Ticket créé avec succès.');
    document.getElementById('ticketSubject').value = '';
    document.getElementById('ticketRecipientSearch').value = '';
    document.getElementById('ticketRecipientId').value = '';
    document.getElementById('ticketMessageInput').value = '';
    const preview = document.getElementById('recipientSelectedPreview');
    if (preview) { preview.style.display = 'none'; preview.textContent = ''; }
    messagingState.selectedRecipient = null;
    messagingState.activeTicketId = null;
    initMessagingCenter();
  } else {
    notifyTicketForm('error', resp?.error || 'Impossible de créer le ticket.');
  }
}
