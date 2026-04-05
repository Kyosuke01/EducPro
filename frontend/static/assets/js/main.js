// ============================================
// MAIN.JS — Orchestrateur principal
// API helper, sidebar, router de sections, init
// ============================================

// Extraction sécurisée des données utilisateur
const userDataElement = document.getElementById('user-data');
const USER = userDataElement && userDataElement.textContent.trim() !== ''
  ? JSON.parse(userDataElement.textContent)
  : {};

// ============================================
// API Helper
// ============================================
async function api(path, options = {}) {
  try {
    const resp = await fetch(`/api/${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options
    });

    const contentType = resp.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      return await resp.json();
    }

    return await resp.text();
  } catch (e) {
    console.error('API Error:', e);
    return { error: e.message };
  }
}

// ============================================
// Sidebar menu builder
// ============================================
function generateSidebarMenu(role) {
  const menus = {
    admin: [
      { icon: 'ri-home-4-line',        label: 'Tableau de Bord',      id: 'dashboard' },
      { icon: 'ri-user-add-line',       label: 'Ajouter Utilisateur',  id: 'createUser' },
      { icon: 'ri-graduation-cap-line', label: 'Étudiants',            id: 'students' },
      { icon: 'ri-user-follow-line',    label: 'Professeurs',          id: 'teachers' },
      { icon: 'ri-book-2-line',         label: 'Classes',              id: 'classes' },
      { icon: 'ri-calendar-check-line', label: 'Emploi du Temps',      id: 'schedule' },
      { icon: 'ri-chat-3-line',         label: 'Messagerie',           id: 'messages' }
    ],
    teacher: [
      { icon: 'ri-home-4-line',         label: 'Tableau de Bord',      id: 'dashboard' },
      { icon: 'ri-book-2-line',         label: 'Mes Classes',          id: 'myClasses' },
      { icon: 'ri-file-list-line',      label: 'Évaluations',          id: 'evaluations' },
      { icon: 'ri-user-follow-line',    label: 'Saisir les Absences',  id: 'teacherAttendance' },
      { icon: 'ri-calendar-check-line', label: 'Mon Emploi du Temps',  id: 'mySchedule' },
      { icon: 'ri-pencil-line',         label: 'Saisir les Notes',     id: 'grades' },
      { icon: 'ri-chat-3-line',         label: 'Messagerie',           id: 'messages' }
    ],
    student: [
      { icon: 'ri-home-4-line',         label: 'Tableau de Bord',      id: 'dashboard' },
      { icon: 'ri-star-line',           label: 'Mes Notes',            id: 'myGrades' },
      { icon: 'ri-calendar-check-line', label: 'Mon Emploi du Temps',  id: 'mySchedule' },
      { icon: 'ri-user-line',           label: 'Mon Assiduité',        id: 'myAttendance' },
      { icon: 'ri-chat-3-line',         label: 'Messagerie',           id: 'messages' }
    ]
  };

  const menuItems = menus[role] || menus.student;
  document.getElementById('sidebarMenu').innerHTML = menuItems.map(item => `
    <li class="dropdown mb-3">
      <a href="javascript:void(0)" class="sidebar-menu-item" data-section="${item.id}"
        onclick="loadSection('${item.id}', event)">
        <i class="${item.icon}"></i>
        <span>${item.label}</span>
      </a>
    </li>
  `).join('');
}

// ============================================
// Section loader (router)
// ============================================
async function loadSection(sectionId, event) {
  event?.preventDefault?.();
  
  // Arrêter le polling des messages si on quitte cette section
  if (typeof stopMessagePolling === 'function') {
    stopMessagePolling();
  }

  // Mettre à jour le menu actif
  document.querySelectorAll('.sidebar-menu-item').forEach(item => item.classList.remove('active'));
  if (event?.target) {
    event.target.closest('.sidebar-menu-item')?.classList.add('active');
  } else {
    document.querySelector(`[data-section="${sectionId}"]`)?.classList.add('active');
  }

  const contentArea = document.getElementById('contentArea');
  contentArea.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Chargement...</span></div></div>';

  const setTitle = (title, subtitle = '') => {
    document.getElementById('pageTitle').textContent = title;
    document.getElementById('pageSubtitle').textContent = subtitle;
  };

  try {
    switch (sectionId) {
      case 'dashboard':
        setTitle('Tableau de Bord', `Bienvenue, ${USER.firstName} ${USER.lastName}`);
        contentArea.innerHTML = await getDashboardContent();
        await initDashboard();
        break;

      case 'createUser':
        setTitle('Gestion des Utilisateurs', 'Ajouter un étudiant ou un professeur');
        contentArea.innerHTML = await getCreateUserContent();
        await initCreateUser();
        break;

      case 'students':
        setTitle('Gestion des Étudiants', 'Liste de tous les étudiants');
        contentArea.innerHTML = await getStudentsContent();
        await initStudentsList();
        break;

      case 'teachers':
        setTitle('Gestion des Professeurs', 'Liste de tous les professeurs');
        contentArea.innerHTML = await getTeachersContent();
        await initTeachersList();
        break;

      case 'classes':
        setTitle('Gestion des Classes', 'Liste de toutes les classes');
        contentArea.innerHTML = await getClassesContent();
        await initClassesList();
        break;

      case 'schedule':
        setTitle('Emploi du Temps', 'Emplois du temps de toutes les classes');
        contentArea.innerHTML = await getScheduleContent();
        await initSchedule();
        break;

      case 'mySchedule':
        setTitle('Mon Emploi du Temps', '');
        contentArea.innerHTML = await getMyScheduleContent();
        await initMySchedule();
        break;

      case 'myClasses':
        setTitle('Mes Classes', '');
        contentArea.innerHTML = await getMyClassesContent();
        await initMyClasses();
        break;

      case 'evaluations':
        setTitle('Évaluations', 'Notes par matière');
        contentArea.innerHTML = await getEvaluationsContent();
        await initEvaluations();
        break;

      case 'grades':
        setTitle('Saisir les Notes', '');
        contentArea.innerHTML = await getGradesContent();
        await initGradesInput();
        break;

      case 'myGrades':
        setTitle('Mes Notes', '');
        contentArea.innerHTML = await getMyGradesContent();
        await initMyGrades();
        break;

      case 'myAttendance':
        setTitle('Mon Assiduité', '');
        contentArea.innerHTML = await getMyAttendanceContent();
        await initMyAttendance();
        break;

      case 'teacherAttendance':
        setTitle('Saisir les Absences', '');
        contentArea.innerHTML = await getTeacherAttendanceContent();
        await initTeacherAttendance();
        break;

      case 'messages':
        setTitle('Messagerie', 'Communiquer et gérer les tickets');
        contentArea.innerHTML = await getMessagesContent();
        await initMessagingCenter();
        break;

      case 'monProfil':
        setTitle('Mon Profil', 'Gérez vos informations personnelles');
        contentArea.innerHTML = await getMonProfilContent();
        initMonProfil();
        break;

      case 'parametres':
        setTitle('Paramètres', 'Configuration de votre compte');
        contentArea.innerHTML = await getParametresContent();
        await initParametres();
        break;

      default:
        setTitle('Tableau de Bord', `Bienvenue, ${USER.firstName} ${USER.lastName}`);
        contentArea.innerHTML = await getDashboardContent();
        await initDashboard();
    }
  } catch (e) {
    contentArea.innerHTML = `<div class="alert alert-danger">Erreur lors du chargement : ${e.message}</div>`;
    console.error('loadSection error:', e);
  }
}

// ============================================
// Chargement des notifications
// ============================================
document.addEventListener('DOMContentLoaded', async () => {
  const notifContainer = document.getElementById('notificationContainer');
  if (!notifContainer) return;

  try {
    const data = await api('notifications?limit=3');
    let notifications = data.notifications || [];

    if (notifications.length === 0 || data.error) {
      if (USER.role === 'admin') {
        notifications = [
          { title: 'Nouveau ticket', body: "L'utilisateur Jean Dupont a ouvert un ticket.", type: 'message' },
          { title: 'Mise à jour requise', body: 'Le système nécessite une mise à jour mineure.', type: 'system' },
          { title: 'Connexion échouée', body: 'Tentative de connexion en échec détectée.', type: 'alert' }
        ];
      } else if (USER.role === 'teacher') {
        notifications = [
          { title: 'Nouveau message étudiant', body: "Question sur le cours d'hier.", type: 'message' },
          { title: 'Rappel', body: 'Saisie des notes avant vendredi.', type: 'alert' }
        ];
      } else {
        notifications = [
          { title: 'Nouvelle note', body: 'Votre professeur a publié une nouvelle note.', type: 'grade' },
          { title: 'Nouveau message', body: 'Message concernant votre dernier devoir.', type: 'message' },
          { title: 'Absence enregistrée', body: 'Une absence a été signalée hier.', type: 'alert' }
        ];
      }
    }

    notifContainer.innerHTML = notifications.map(notif => {
      let icon = 'ri-notification-3-line';
      let bgColor = '#1d2d44';
      let iconColor = '#a4b0f5';
      
      if (notif.type === 'message') { 
        icon = 'ri-message-3-line'; 
        bgColor = '#1a4d6d';
        iconColor = '#60d5ff';
      }
      else if (notif.type === 'system' || notif.type === 'alert') { 
        icon = 'ri-error-warning-line'; 
        bgColor = '#6d4d1a';
        iconColor = '#ffb84d';
      }
      else if (notif.type === 'grade') { 
        icon = 'ri-star-line'; 
        bgColor = '#1a6d3f';
        iconColor = '#48d597';
      }

      return `
        <a href="javascript:void(0)" onclick="loadSection('messages')"
          class="d-flex align-items-start gap-3 text-decoration-none mb-3" style="padding: 12px; border-radius: 0px; transition: all 0.2s ease; cursor: pointer;">
          <div class="rounded-circle d-flex justify-content-center align-items-center flex-shrink-0" style="width: 40px; height: 40px; background-color: ${bgColor}; border-radius: 50%;">
            <i class="${icon} text-xl" style="color: ${iconColor};"></i>
          </div>
          <div>
            <h6 class="text-sm fw-medium mb-1" style="color: #f0ebd8;">${notif.title}</h6>
            <p class="text-xs mb-0" style="color: #a4b0f5;">${notif.body}</p>
          </div>
        </a>
      `;
    }).join('');

    const indicator = document.querySelector('.has-indicator span.bg-danger-600');
    if (indicator) {
      indicator.style.display = notifications.length > 0 ? 'block' : 'none';
    }

  } catch (e) {
    notifContainer.innerHTML = '<p class="text-xs text-neutral-500 text-center">Erreur de chargement</p>';
  }
});

// ============================================
// SEARCH USERS
// ============================================
let allUsers = [];

async function initSearch() {
  const searchInput = document.getElementById('searchInput');
  const searchForm = document.getElementById('searchForm');
  const searchResults = document.getElementById('searchResults');
  
  if (!searchInput || !searchForm) return;

  // Désactiver complètement la recherche pour les étudiants
  if (USER.role === 'student') {
    searchForm.style.display = 'none';
    return;
  }

  // Récupérer tous les utilisateurs au chargement
  try {
    allUsers = await api('users') || [];
    // Si c'est un objet avec une propriété 'users', l'extraire
    if (allUsers.users) {
      allUsers = allUsers.users;
    }
  } catch (e) {
    console.error('Error loading users for search:', e);
  }

  // Gérer la saisie
  searchInput.addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase().trim();
    
    if (!query) {
      searchResults.style.display = 'none';
      return;
    }

    // Filtrer les utilisateurs selon le rôle
    let filtered = allUsers.filter(user => {
      const username = (user.username || '').toLowerCase();
      const email = (user.email || '').toLowerCase();
      const matchQuery = username.includes(query) || email.includes(query);
      
      if (!matchQuery) return false;

      // Admin peut voir tout le monde
      if (USER.role === 'admin') return true;

      // Teacher peut voir seulement les étudiants
      if (USER.role === 'teacher') return user.role === 'student';

      return false;
    });

    // Afficher les résultats
    if (filtered.length > 0) {
      searchResults.innerHTML = filtered.map(user => `
        <div style="padding: 8px 12px; border-bottom: 1px solid #a4b0f5; cursor: pointer; color: #f0ebd8;" 
           onmouseover="this.style.backgroundColor='#12664f'" 
           onmouseout="this.style.backgroundColor='transparent'"
           onclick="showSearchResultProfile('${user.username}', '${user.email}', '${user.role}', event)">
          <div style="font-size: 0.9rem; font-weight: 500;">${user.username}</div>
          <div style="font-size: 0.8rem; color: #a4b0f5;">${user.email} <span style="margin-left: 8px; opacity: 0.7;">(${user.role})</span></div>
        </div>
      `).join('');
      searchResults.style.display = 'block';
    } else {
      searchResults.innerHTML = '<div style="padding: 12px; color: #a4b0f5; text-align: center; font-size: 0.9rem;">Aucun résultat</div>';
      searchResults.style.display = 'block';
    }
  });

  // Fermer on click outside
  document.addEventListener('click', (e) => {
    if (!e.target.closest('#searchForm')) {
      searchResults.style.display = 'none';
    }
  });
}

async function showSearchResultProfile(username, email, role, event) {
  event.stopPropagation();
  const searchResults = document.getElementById('searchResults');
  searchResults.style.display = 'none';
  document.getElementById('searchInput').value = '';
  
  const contentArea = document.getElementById('contentArea');
  contentArea.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-primary"></div></div>';

  try {
    // Récupérer les données complètes de l'utilisateur
    const userType = role === 'student' ? 'student' : 'teacher';
    const userEmail = email;
    
    // Appeler l'API pour rechercher l'utilisateur par email
    const response = await api(`users/${userType}?email=${encodeURIComponent(userEmail)}`);
    let user = null;
    
    // Chercher dans la réponse
    if (Array.isArray(response)) {
      user = response.find(u => (userType === 'student' ? u.mail_student : u.mail_teacher) === userEmail);
    }
    
    if (!user) {
      contentArea.innerHTML = '<div class="alert alert-warning">Utilisateur non trouvé</div>';
      return;
    }

    // Afficher le profil en mode viewer
    const names = username.split(' ');
    const firstName = names[0] || '';
    const lastName = names.slice(1).join(' ') || '';
    
    const isStudent = userType === 'student';
    const id = isStudent ? user.student_id : user.teacher_id;
    
    // HTML du profil
    contentArea.innerHTML = `
      <div class="card radius-8 overflow-hidden">
        <div class="card-body p-24">
          <div class="d-flex align-items-center justify-content-between mb-24">
            <h6 class="fw-semibold"><i class="ri-user-3-line text-primary me-2"></i>${firstName} ${lastName}</h6>
            <button type="button" class="btn btn-sm btn-light" onclick="history.back()">
              <i class="ri-arrow-left-line"></i> Retour
            </button>
          </div>

          <div class="row gap-3">
            <div class="col-md-6">
              <label class="form-label text-sm fw-medium mb-2">Prénom</label>
              <input type="text" class="form-control radius-8 bg-neutral-100 border-0 p-12" value="${firstName}" disabled>
            </div>
            <div class="col-md-6">
              <label class="form-label text-sm fw-medium mb-2">Nom</label>
              <input type="text" class="form-control radius-8 bg-neutral-100 border-0 p-12" value="${lastName}" disabled>
            </div>
          </div>

          <div class="row gap-3 mt-3">
            <div class="col-12">
              <label class="form-label text-sm fw-medium mb-2">Email</label>
              <input type="email" class="form-control radius-8 bg-neutral-100 border-0 p-12" value="${userEmail}" disabled>
            </div>
          </div>

          ${isStudent ? `
            <div class="row gap-3 mt-3">
              <div class="col-12">
                <label class="form-label text-sm fw-medium mb-2">Classe</label>
                <input type="text" class="form-control radius-8 bg-neutral-100 border-0 p-12" value="${user.class_name || '-'}" disabled>
              </div>
            </div>
          ` : `
            <div class="row gap-3 mt-3">
              <div class="col-12">
                <label class="form-label text-sm fw-medium mb-2">Matière</label>
                <input type="text" class="form-control radius-8 bg-neutral-100 border-0 p-12" value="${user.topic_name || '-'}" disabled>
              </div>
            </div>
          `}

          <div class="d-flex gap-2 mt-24">
            <button type="button" class="btn btn-primary radius-8" onclick="editSearchUser('${userType}', ${id}, '${firstName}', '${lastName}', '${userEmail}', '${isStudent ? user.class_name : user.topic_name || ''}')">
              <i class="ri-edit-line me-2"></i>Modifier
            </button>
            <button type="button" class="btn btn-danger radius-8" onclick="deleteSearchUser('${userType}', ${id})">
              <i class="ri-delete-bin-line me-2"></i>Supprimer
            </button>
          </div>
        </div>
      </div>
    `;
  } catch (e) {
    console.error('Error showing profile:', e);
    contentArea.innerHTML = '<div class="alert alert-danger">Erreur lors du chargement du profil</div>';
  }
}

async function editSearchUser(type, id, firstName, lastName, email, classOrTopic) {
  showEditUserForm(type, {
    [type === 'student' ? 'student_id' : 'teacher_id']: id,
    first_name: firstName,
    last_name: lastName,
    [type === 'student' ? 'mail_student' : 'mail_teacher']: email,
    [type === 'student' ? 'class_name' : 'topic_name']: classOrTopic
  });
}

async function deleteSearchUser(type, id) {
  if (!confirm("Voulez-vous vraiment supprimer cet utilisateur ? Cette action est irréversible.")) return;
  try {
    const resp = await fetch(`/api/users/${type}/${id}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' }
    });
    if (resp.ok) {
      alert('Utilisateur supprimé');
      loadSection('dashboard', null);
    } else {
      const js = await resp.json();
      alert('Erreur: ' + (js.error || 'inconnue'));
    }
  } catch (e) {
    alert('Erreur réseau');
  }
}

// ============================================
// INIT
// ============================================
function init() {
  if (!USER.firstName) return;

  document.getElementById('userName').textContent = `${USER.firstName} ${USER.lastName}`;
  document.getElementById('userRole').textContent =
    USER.role === 'admin' ? 'Administrateur' :
    USER.role === 'teacher' ? 'Professeur' : 'Étudiant';
  document.getElementById('userAvatar').textContent = USER.firstName.charAt(0).toUpperCase();

  // Afficher la date du jour
  const currentDateEl = document.getElementById('currentDate');
  if (currentDateEl) {
    const today = new Date();
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    const dateStr = today.toLocaleDateString('fr-FR', options);
    currentDateEl.textContent = dateStr.charAt(0).toUpperCase() + dateStr.slice(1);
  }

  generateSidebarMenu(USER.role);
  
  // Fermer le dropdown du profil quand on clique sur un item du menu
  document.querySelectorAll('.sidebar-menu-item').forEach(item => {
    item.addEventListener('click', () => {
      const dropdownButton = document.querySelector('.profile-dropdown__button');
      if (dropdownButton) {
        const dropdown = new bootstrap.Dropdown(dropdownButton);
        dropdown.hide();
      }
    });
  });
  
  initSearch();
  loadSection('dashboard', { preventDefault: () => {} });
}

// Lancer l'init
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
