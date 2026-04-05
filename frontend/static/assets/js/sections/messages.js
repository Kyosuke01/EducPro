// ============================================
// MESSAGERIE — Tickets, conversations, réponses
// ============================================

const messagingState = {
  conversations: [],
  activeTicketId: null,
  activeTicket: null,
  selectedRecipient: null,
  searchTimeout: null,
  recipientSuggestions: [],
  lastMessageCount: 0,
  pollingInterval: null,
  lastCheck: 0,
  notificationCount: 0,
  notifiedTickets: new Set(),
  lastSubmitTime: 0,
  submitDebounceMs: 1000 // Prévenir les doubles soumissions
};

// Fonction utilitaire pour afficher une notification
function showNotification(type, message) {
  const notif = document.createElement('div');
  const bgColor = type === 'error' ? '#dc3545' : '#12664f';
  const textColor = '#f0ebd8';
  
  notif.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 9999;
    max-width: 400px;
    padding: 1rem 1.5rem;
    background-color: ${bgColor};
    color: ${textColor};
    border-radius: 0px;
    border: 2px solid #a4b0f5;
    box-shadow: 3px 3px 0px #a4b0f5;
    font-size: 0.875rem;
    animation: slideIn 0.3s ease-in-out;
    word-wrap: break-word;
    font-family: Inter, sans-serif;
  `;
  notif.textContent = message;
  document.body.appendChild(notif);
  
  setTimeout(() => {
    notif.style.animation = 'slideOut 0.3s ease-in-out';
    setTimeout(() => notif.remove(), 300);
  }, 4000);
}

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
  
  // Démarrer le polling si ce n'est pas déjà fait
  if (!messagingState.pollingInterval) {
    startMessagePolling();
  }
}

// Helper: Extract contact name from ticket
function getContactNameFromTicket(ticket) {
  if (USER.role === 'teacher' || USER.role === 'admin') {
    return `${ticket.student_first_name || ''} ${ticket.student_last_name || ''}`.trim() || 'Étudiant';
  }
  return `${ticket.teacher_first_name || ''} ${ticket.teacher_last_name || ''}`.trim() || 'Enseignant';
}

// Helper: Check and notify if message update
function checkMessageUpdate(newTicket, oldTicket) {
  if (!oldTicket || oldTicket.last_message_at === newTicket.last_message_at) return;
  if (newTicket.ticket_id === messagingState.activeTicketId) return;
  if (messagingState.notifiedTickets.has(newTicket.ticket_id)) return;
  
  const contact = getContactNameFromTicket(newTicket);
  displayNotificationBadge(newTicket, contact);
  messagingState.notifiedTickets.add(newTicket.ticket_id);
}

// Helper: Check and notify if new ticket
function checkNewTicket(newTicket, oldTicket) {
  if (oldTicket || newTicket.ticket_id === messagingState.activeTicketId) return;
  
  const contact = getContactNameFromTicket(newTicket);
  displayNotificationBadge(newTicket, contact);
  messagingState.notifiedTickets.add(newTicket.ticket_id);
}

// Helper: Refresh active ticket content
async function refreshActiveTicketContent() {
  if (!messagingState.activeTicketId) return;
  
  const details = await api(`messages/conversations/${messagingState.activeTicketId}?role=${USER.role}&user_id=${USER.id}`);
  if (!details.error) {
    renderConversationDetail(details.ticket, details.messages || []);
  }
}

// Main polling function
function startMessagePolling() {
  if (messagingState.pollingInterval) return;
  
  messagingState.pollingInterval = setInterval(async () => {
    const messagesContainer = document.getElementById('messagesContainer');
    if (!messagesContainer) return;
    
    try {
      const data = await api(`messages/conversations?role=${USER.role}&user_id=${USER.id}`);
      if (data.error) return;

      const newConversations = data.tickets || [];
      
      // Process each ticket for updates and new tickets
      newConversations.forEach(newTicket => {
        const oldTicket = messagingState.conversations.find(t => t.ticket_id === newTicket.ticket_id);
        checkMessageUpdate(newTicket, oldTicket);
        checkNewTicket(newTicket, oldTicket);
      });
      
      messagingState.conversations = newConversations;
      renderConversationList();
      await refreshActiveTicketContent();
    } catch (e) {
      console.error('Polling error:', e);
    }
  }, 3000);
}

// Arrêter le polling quand on quitte la page
function stopMessagePolling() {
  if (messagingState.pollingInterval) {
    clearInterval(messagingState.pollingInterval);
    messagingState.pollingInterval = null;
  }
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
  const closeBtn = document.getElementById('closeTicketBtn');
  
  if (header) header.innerHTML = `
    <div class="fw-semibold">Sélectionnez un ticket</div>
    <div class="text-sm text-neutral-500"></div>
  `;
  if (panel) panel.innerHTML = '<div class="text-center text-muted py-5">Aucune conversation sélectionnée.</div>';
  if (textarea) textarea.disabled = true;
  if (button) button.disabled = true;
  if (closeBtn) closeBtn.style.display = 'none';
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
  const closeBtn = document.getElementById('closeTicketBtn');
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

  // Mettre à jour seulement le contenu du header (pas le bouton qui est à côté)
  header.innerHTML = `
    <div class="fw-semibold">${ticket.subject}</div>
    <div class="text-sm text-neutral-500">${contact}</div>
    <span class="${badgeClass} text-uppercase text-xxs" style="display: inline-block; margin-top: 0.5rem;">${statusText}</span>
  `;
  
  // Afficher le bouton "Fermer" seulement si le ticket est OPEN
  const isClosed = (ticket.status || '').toLowerCase() === 'closed';
  if (closeBtn) {
    closeBtn.style.display = !isClosed ? 'block' : 'none';
  }

  const timeline = messages.map(msg => {
    const mine = msg.sender_role === USER.role;
    const align = mine ? 'flex-row-reverse text-end' : '';
    // Couleurs inversées: moi = cream, autres = bleu
    const bgColor = mine ? '#F0EBD8' : '#2563EB'; // fond
    const textColor = mine ? '#000000' : '#ffffff'; // texte
    const name = mine ? 'Moi' : msg.sender_role === 'teacher' ? 'Professeur' : msg.sender_role === 'admin' ? 'Admin' : 'Étudiant';
    const date = msg.created_at ? new Date(msg.created_at).toLocaleString() : '';
    return `
      <div class="d-flex ${align} mb-3">
        <div class="p-3 radius-12" style="max-width: 80%; background-color: ${bgColor};">
          <div class="fw-semibold text-xs mb-1" style="color: ${textColor} !important;">${name}</div>
          <div class="text-sm mb-1" style="color: ${textColor} !important;">${msg.body}</div>
          <div class="text-xxs" style="color: #A4B0F5 !important;">${date}</div>
        </div>
      </div>
    `;
  }).join('');

  panel.innerHTML = timeline || '<div class="text-center text-muted py-5">Aucun message pour le moment.</div>';

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
    showNotification('error', resp?.error || "Erreur lors de l'envoi");
    textarea.disabled = false;
    button.disabled = false;
  }
}

function notifyTicketForm(type, message) {
  const box = document.getElementById('ticketFormAlert');
  if (!box) return;
  if (!message) { box.style.display = 'none'; return; }
  
  let classes = 'alert d-flex align-items-center gap-2 mb-3';
  let iconClass = 'ri-information-line';
  
  if (type === 'success') {
    classes += ' alert-success';
    iconClass = 'ri-check-circle-line';
    box.style.backgroundColor = '#12664f';
    box.style.borderColor = '#12664f';
    box.style.color = '#f0ebd8';
  } else if (type === 'error') {
    classes += ' alert-danger';
    iconClass = 'ri-error-warning-line';
  } else {
    classes += ' alert-warning';
  }
  
  box.className = classes;
  box.innerHTML = `<i class="${iconClass}"></i><span>${message}</span>`;
  box.style.display = 'flex';
}

// Affiche la modal de création de ticket
function showNewTicketForm() {
  const modal = document.getElementById('newTicketModal');
  if (modal) {
    modal.style.display = 'flex';
    modal.style.alignItems = 'center';
    modal.style.justifyContent = 'center';
    // Focus sur le premier input
    document.getElementById('ticketSubject')?.focus();
  }
}

// Ferme la modal de création de ticket
function closeNewTicketForm() {
  const modal = document.getElementById('newTicketModal');
  if (modal) modal.style.display = 'none';
  // Réinitialiser le formulaire
  document.getElementById('ticketSubject').value = '';
  document.getElementById('ticketRecipientSearch').value = '';
  document.getElementById('ticketRecipientId').value = '';
  document.getElementById('ticketMessageInput').value = '';
  const preview = document.getElementById('recipientSelectedPreview');
  if (preview) { preview.style.display = 'none'; preview.textContent = ''; }
  messagingState.selectedRecipient = null;
  notifyTicketForm('', '');
}

// Ferme le ticket actuel (si ouvert)
async function closeCurrentTicket() {
  if (!messagingState.activeTicketId) return;
  
  if (!confirm('Êtes-vous sûr de vouloir fermer ce ticket ? Cela supprimera la conversation.')) {
    return;
  }
  
  const ticketId = messagingState.activeTicketId;
  const role = USER?.role;
  const userId = USER?.id;
  
  if (!role || !userId) {
    showNotification('error', 'Erreur : utilisateur non identifié.');
    return;
  }
  
  // Construire l'URL avec les paramètres de query
  const url = `messages/conversations/${ticketId}?role=${role}&user_id=${userId}`;
  
  try {
    const resp = await api(url, {
      method: 'DELETE'
    });
    
    if (resp && !resp.error) {
      messagingState.activeTicketId = null;
      messagingState.activeTicket = null;
      messagingState.notifiedTickets.delete(ticketId); // Retirer la notif si elle existait
      renderEmptyConversation();
      showNotification('success', 'Ticket supprimé avec succès.');
      await initMessagingCenter();
    } else {
      showNotification('error', resp?.error || 'Erreur lors de la fermeture du ticket.');
    }
  } catch (e) {
    console.error('Close ticket error:', e);
    showNotification('error', 'Erreur lors de la fermeture du ticket.');
  }
}

// Affiche une notification cliquable avec compteur
function displayNotificationBadge(ticket, contactName) {
  messagingState.notificationCount++;
  updateNotificationBadge();
  
  // Créer une notification cliquable
  const notif = document.createElement('div');
  notif.className = 'notification-badge';
  notif.style.cssText = `
    position: fixed;
    top: 80px;
    right: 20px;
    background-color: #12664f;
    color: #f0ebd8;
    padding: 1rem 1.5rem;
    border-radius: 0px;
    border: 2px solid #a4b0f5;
    box-shadow: 3px 3px 0px #a4b0f5;
    cursor: pointer;
    z-index: 9999;
    animation: slideIn 0.3s ease-in-out;
    max-width: 400px;
    font-family: Inter, sans-serif;
    font-size: 0.875rem;
  `;
  notif.innerHTML = `📧 ${contactName}<br><small>${ticket.subject}</small>`;
  
  // Clic = ouvre le ticket
  notif.onclick = () => {
    openConversation(ticket.ticket_id);
    // Retirer la notif et décrémenter le compteur
    messagingState.notificationCount--;
    messagingState.notifiedTickets.delete(ticket.ticket_id);
    updateNotificationBadge();
    notif.style.animation = 'slideOut 0.3s ease-in-out';
    setTimeout(() => notif.remove(), 300);
  };
  
  document.body.appendChild(notif);
  
  // Auto-remove après 5 secondes si pas cliqué
  setTimeout(() => {
    if (notif.parentElement) {
      notif.style.animation = 'slideOut 0.3s ease-in-out';
      setTimeout(() => notif.remove(), 300);
    }
  }, 5000);
}

// Mettre à jour le badge de compteur dans le menu
function updateNotificationBadge() {
  const badge = document.getElementById('messagingNotificationBadge');
  if (!badge) return;
  
  if (messagingState.notificationCount > 0) {
    badge.textContent = messagingState.notificationCount;
    badge.style.display = 'inline-flex';
  } else {
    badge.style.display = 'none';
  }
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
  // Sécurité: prévenir les soumissions en boucle
  const now = Date.now();
  if (now - messagingState.lastSubmitTime < messagingState.submitDebounceMs) {
    notifyTicketForm('error', 'Merci d\'attendre avant de créer un nouveau ticket.');
    return;
  }
  messagingState.lastSubmitTime = now;

  const subject = (document.getElementById('ticketSubject')?.value || '').trim();
  const message = (document.getElementById('ticketMessageInput')?.value || '').trim();
  const recipientId = Number.parseInt(document.getElementById('ticketRecipientId')?.value || '0', 10);

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
    notifyTicketForm('success', 'Ticket créé avec succès.');
    
    // Rafraîchir la liste et attendre un peu avant de fermer la modal
    await initMessagingCenter();
    
    setTimeout(() => {
      closeNewTicketForm();
    }, 1000);
  } else {
    notifyTicketForm('error', resp?.error || 'Impossible de créer le ticket.');
    messagingState.lastSubmitTime = 0; // Reset le timer en cas d'erreur
  }
}
