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
      let color = 'primary';
      if (notif.type === 'message') { icon = 'ri-message-3-line'; color = 'info'; }
      else if (notif.type === 'system' || notif.type === 'alert') { icon = 'ri-error-warning-line'; color = 'warning'; }
      else if (notif.type === 'grade') { icon = 'ri-star-line'; color = 'success'; }

      return `
        <a href="javascript:void(0)" onclick="loadSection('messages')"
          class="d-flex align-items-start gap-3 text-neutral-900 text-hover-primary-600 text-decoration-none mb-3">
          <div class="w-40-px h-40-px rounded-circle bg-${color}-50 d-flex justify-content-center align-items-center flex-shrink-0">
            <i class="${icon} text-${color} text-xl"></i>
          </div>
          <div>
            <h6 class="text-sm fw-medium mb-1">${notif.title}</h6>
            <p class="text-xs text-neutral-500 mb-0">${notif.body}</p>
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
// INIT
// ============================================
function init() {
  if (!USER.firstName) return;

  document.getElementById('userName').textContent = `${USER.firstName} ${USER.lastName}`;
  document.getElementById('userRole').textContent =
    USER.role === 'admin' ? 'Administrateur' :
    USER.role === 'teacher' ? 'Professeur' : 'Étudiant';
  document.getElementById('userAvatar').textContent = USER.firstName.charAt(0).toUpperCase();

  generateSidebarMenu(USER.role);
  loadSection('dashboard', { preventDefault: () => {} });
}

// Lancer l'init
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
