// ============================================
// MAIN.JS — Orchestrateur principal
// API helper, sidebar, router de sections, init
// ============================================

// Extraction sécurisée des données utilisateur
const userDataElement = document.getElementById('user-data');
const USER = userDataElement && userDataElement.textContent.trim() !== ''
  ? JSON.parse(userDataElement.textContent)
  : {};
const SKELETON_MODE = new URLSearchParams(window.location.search).get('skeleton') === '1';

// ============================================
// API Helper
// ============================================
async function api(path, options = {}) {
  if (SKELETON_MODE) {
    return {};
  }
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
      { icon: 'ri-pencil-line',         label: 'Saisir les Notes',     id: 'grades' },
      { icon: 'ri-user-follow-line',    label: 'Saisir les Absences',  id: 'teacherAttendance' },
      { icon: 'ri-calendar-check-line', label: 'Mon Emploi du Temps',  id: 'mySchedule' },
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

  // Garde-fou RBAC frontend : un professeur n'accède jamais à la vue globale des classes.
  if (USER.role === 'teacher' && sectionId === 'classes') {
    sectionId = 'myClasses';
  }
  
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
      let bgColor = '#eef2ff';
      let iconColor = '#1f2937';
      
      if (notif.type === 'message') { 
        icon = 'ri-message-3-line'; 
        bgColor = '#dbeafe';
        iconColor = '#1d4ed8';
      }
      else if (notif.type === 'system' || notif.type === 'alert') { 
        icon = 'ri-error-warning-line'; 
        bgColor = '#fef3c7';
        iconColor = '#92400e';
      }
      else if (notif.type === 'grade') { 
        icon = 'ri-star-line'; 
        bgColor = '#dcfce7';
        iconColor = '#166534';
      }

      return `
        <a href="javascript:void(0)" onclick="loadSection('messages')"
          class="d-flex align-items-start gap-3 text-decoration-none mb-3" style="padding: 12px; border-radius: 10px; transition: all 0.2s ease; cursor: pointer;">
          <div class="rounded-circle d-flex justify-content-center align-items-center flex-shrink-0" style="width: 40px; height: 40px; background-color: ${bgColor}; border-radius: 50%;">
            <i class="${icon} text-xl" style="color: ${iconColor};"></i>
          </div>
          <div>
            <h6 class="text-sm fw-medium mb-1" style="color: #1f2937;">${notif.title}</h6>
            <p class="text-xs mb-0" style="color: #6b7280;">${notif.body}</p>
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
let allClasses = [];
let activeSearchResults = [];

function normalizeSearchValue(value) {
  return (value || '').toString().toLowerCase().trim();
}

function escapeHtml(value) {
  return (value || '')
    .toString()
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function hideSearchDropdown() {
  const searchResults = document.getElementById('searchResults');
  if (searchResults) {
    searchResults.style.display = 'none';
  }
}

function normalizeSearchDropdownPosition(searchResults) {
  if (!searchResults) return;
  searchResults.style.position = 'absolute';
  searchResults.style.top = 'calc(100% + 6px)';
  searchResults.style.left = '0';
  searchResults.style.width = '100%';
  searchResults.style.zIndex = '20000';
}

function buildSearchableItems(query) {
  const q = normalizeSearchValue(query);
  if (!q) return [];

  const userItems = allUsers
    .filter(item => {
      if (USER.role === 'teacher') {
        return item.role === 'student';
      }
      return true;
    })
    .filter(item => {
      const fullName = normalizeSearchValue(item.displayName);
      const email = normalizeSearchValue(item.email);
      const role = normalizeSearchValue(item.roleLabel);
      const classOrTopic = normalizeSearchValue(item.classOrTopic);
      return fullName.includes(q) || email.includes(q) || role.includes(q) || classOrTopic.includes(q);
    })
    .map(item => ({ type: 'user', ...item }));

  if (USER.role !== 'admin') {
    return userItems;
  }

  const classItems = allClasses
    .filter(cls => {
      const className = normalizeSearchValue(cls.name);
      const teacherName = normalizeSearchValue(cls.teacherName);
      return className.includes(q) || teacherName.includes(q);
    })
    .map(cls => ({ type: 'class', ...cls }));

  return [...userItems, ...classItems].slice(0, 30);
}

function renderSearchResults(results, searchResults) {
  activeSearchResults = results;
  normalizeSearchDropdownPosition(searchResults);

  if (!results.length) {
    searchResults.innerHTML = '<div style="padding: 8px 12px; border-bottom: 1px solid #e5e7eb; color: #6b7280; font-size: 0.9rem;">Aucun résultat</div>';
    searchResults.style.display = 'block';
    return;
  }

  searchResults.innerHTML = results.map((item, index) => {
    if (item.type === 'class') {
      return `
        <div class="search-result-item" data-result-index="${index}" style="padding: 8px 12px; border-bottom: 1px solid #e5e7eb; cursor: pointer; color: #1f2937;">
          <div style="font-size: 0.9rem; font-weight: 500;"><i class="ri-book-2-line me-1"></i>${escapeHtml(item.name)}</div>
          <div style="font-size: 0.8rem; color: #6b7280;">Classe <span style="margin-left: 8px; opacity: 0.7;">(${escapeHtml(item.teacherName || 'Non assigné')})</span></div>
        </div>
      `;
    }

    return `
      <div class="search-result-item" data-result-index="${index}" style="padding: 8px 12px; border-bottom: 1px solid #e5e7eb; cursor: pointer; color: #1f2937;">
        <div style="font-size: 0.9rem; font-weight: 500;">${escapeHtml(item.displayName)}</div>
        <div style="font-size: 0.8rem; color: #6b7280;">${escapeHtml(item.email)} <span style="margin-left: 8px; opacity: 0.7;">(${escapeHtml(item.roleLabel)})</span></div>
      </div>
    `;
  }).join('');

  searchResults.querySelectorAll('.search-result-item').forEach(node => {
    node.addEventListener('mouseover', () => { node.style.backgroundColor = '#f3f4f6'; });
    node.addEventListener('mouseout', () => { node.style.backgroundColor = 'transparent'; });
    node.addEventListener('click', (event) => {
      const idx = Number.parseInt(node.dataset.resultIndex || '-1', 10);
      handleSearchResultClick(idx, event);
    });
  });

  searchResults.style.display = 'block';
}

async function handleSearchResultClick(index, event) {
  event?.stopPropagation?.();
  const item = activeSearchResults[index];
  if (!item) return;

  hideSearchDropdown();
  const searchInput = document.getElementById('searchInput');
  if (searchInput) searchInput.value = '';

  if (item.type === 'class') {
    if (typeof showClassDetail === 'function') {
      if (document.getElementById('classesTableBody')) {
        await showClassDetail(item.name);
      } else {
        await loadSection('classes', { preventDefault: () => {} });
        await showClassDetail(item.name);
      }
    }
    return;
  }

  if (USER.role === 'admin') {
    const userType = item.role === 'student' ? 'student' : 'teacher';
    if (typeof showEditUserForm === 'function') {
      await showEditUserForm(userType, item.rawData);
      return;
    }
  }

  if (USER.role === 'teacher' && item.role === 'student') {
    await showTeacherStudentModal(item.rawData);
    return;
  }

  await showSearchResultProfile(item.displayName, item.email, item.role, event);
}

function ensureTeacherStudentModal() {
  let modalEl = document.getElementById('teacherStudentModal');
  if (modalEl) return modalEl;

  const html = `
    <div class="modal fade" id="teacherStudentModal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-lg modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title"><i class="ri-user-3-line me-2"></i>Détail étudiant</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body" id="teacherStudentModalBody">
            <div class="text-center py-4"><div class="spinner-border text-primary"></div></div>
          </div>
        </div>
      </div>
    </div>
  `;
  document.body.insertAdjacentHTML('beforeend', html);
  return document.getElementById('teacherStudentModal');
}

async function showTeacherStudentModal(student) {
  const modalEl = ensureTeacherStudentModal();
  const bodyEl = document.getElementById('teacherStudentModalBody');
  const modal = bootstrap.Modal.getOrCreateInstance(modalEl);

  bodyEl.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary"></div></div>';
  modal.show();

  try {
    const [attendanceData, edtData] = await Promise.all([
      api(`attendance/student/${student.student_id}`),
      api(`edt/teacher/${encodeURIComponent(USER.lastName || '')}`)
    ]);

    const teacherEdt = edtData?.edt || [];
    const teacherEdtIds = new Set(teacherEdt.map(e => e.edt_id));
    const scopedEvents = (attendanceData?.attendance || []).filter(a => teacherEdtIds.has(a.edt_id));
    const absentCount = scopedEvents.filter(a => a.status === 'absent').length;
    const lateCount = scopedEvents.filter(a => a.status === 'late').length;

    const rows = scopedEvents.slice(0, 10).map(a => `
      <tr>
        <td>${a.status === 'absent' ? 'Absence' : 'Retard'}</td>
        <td>${a.date_attendance ? new Date(a.date_attendance).toLocaleDateString('fr-FR') : '-'}</td>
      </tr>
    `).join('');

    bodyEl.innerHTML = `
      <div class="row g-3">
        <div class="col-md-6">
          <label class="form-label fw-medium">Nom</label>
          <input class="form-control bg-neutral-100 border-0" value="${escapeHtml(student.last_name || '')}" disabled>
        </div>
        <div class="col-md-6">
          <label class="form-label fw-medium">Prénom</label>
          <input class="form-control bg-neutral-100 border-0" value="${escapeHtml(student.first_name || '')}" disabled>
        </div>
        <div class="col-md-6">
          <label class="form-label fw-medium">Email</label>
          <input class="form-control bg-neutral-100 border-0" value="${escapeHtml(student.mail_student || '')}" disabled>
        </div>
        <div class="col-md-6">
          <label class="form-label fw-medium">Classe</label>
          <input class="form-control bg-neutral-100 border-0" value="${escapeHtml(student.class_name || '-')}" disabled>
        </div>
      </div>

      <div class="mt-4">
        <h6 class="fw-semibold mb-2">Assiduité dans mes cours</h6>
        <div class="d-flex gap-3 mb-3">
          <span class="badge bg-danger-100 text-danger-700">Absences: ${absentCount}</span>
          <span class="badge bg-warning-100 text-warning-700">Retards: ${lateCount}</span>
        </div>
        <div class="table-responsive">
          <table class="table table-sm">
            <thead>
              <tr><th>Type</th><th>Date</th></tr>
            </thead>
            <tbody>
              ${rows || '<tr><td colspan="2" class="text-center text-muted">Aucun événement dans vos cours</td></tr>'}
            </tbody>
          </table>
        </div>
      </div>
    `;
  } catch (e) {
    bodyEl.innerHTML = '<div class="alert alert-danger">Impossible de charger les informations de l’étudiant.</div>';
  }
}

async function initSearch() {
  const searchInput = document.getElementById('searchInput');
  const searchForm = document.getElementById('searchForm');
  const searchResults = document.getElementById('searchResults');
  
  if (!searchInput || !searchForm) return;
  normalizeSearchDropdownPosition(searchResults);

  // Désactiver complètement la recherche pour les étudiants
  if (USER.role === 'student') {
    searchForm.style.display = 'none';
    return;
  }

  // Récupérer les sources de recherche
  try {
    allUsers = [];
    allClasses = [];

    if (USER.role === 'admin') {
      const [studentsResponse, teachersResponse, classesResponse] = await Promise.all([
        api('students'),
        api('teachers'),
        api('classes')
      ]);

      const students = Array.isArray(studentsResponse)
        ? studentsResponse
        : (studentsResponse?.students || []);
      const teachers = Array.isArray(teachersResponse)
        ? teachersResponse
        : (teachersResponse?.teachers || []);
      const classes = classesResponse?.classes || [];

      allUsers = [
        ...students.map(student => ({
          role: 'student',
          roleLabel: 'student',
          displayName: `${student.first_name || ''} ${student.last_name || ''}`.trim() || 'Étudiant',
          email: student.mail_student || '',
          classOrTopic: student.class_name || '',
          rawData: student
        })),
        ...teachers.map(teacher => ({
          role: 'teacher',
          roleLabel: 'teacher',
          displayName: `${teacher.first_name || ''} ${teacher.last_name || ''}`.trim() || 'Professeur',
          email: teacher.mail_teacher || '',
          classOrTopic: teacher.topic_name || '',
          rawData: teacher
        }))
      ];

      allClasses = classes.map(cls => ({
        name: cls.name || '',
        teacherName: cls.teacher_first_name
          ? `${cls.teacher_first_name} ${cls.teacher_last_name || ''}`.trim()
          : 'Non assigné'
      }));
    } else {
      if (USER.role === 'teacher') {
        const [edtResponse, studentsResponse] = await Promise.all([
          api(`edt/teacher/${encodeURIComponent(USER.lastName || '')}`),
          api('students')
        ]);
        const teacherEdt = edtResponse?.edt || [];
        const classScope = new Set(teacherEdt.map(row => row.class_name).filter(Boolean));
        const allStudents = studentsResponse?.students || [];
        const scopedStudents = allStudents.filter(student => classScope.has(student.class_name));

        allUsers = scopedStudents.map(student => ({
          role: 'student',
          roleLabel: 'student',
          displayName: `${student.first_name || ''} ${student.last_name || ''}`.trim() || 'Étudiant',
          email: student.mail_student || '',
          classOrTopic: student.class_name || '',
          rawData: student
        }));
      } else {
        let usersResponse = await api('users');
        if (usersResponse && usersResponse.users) {
          usersResponse = usersResponse.users;
        }
        const rawUsers = Array.isArray(usersResponse) ? usersResponse : [];
        allUsers = rawUsers.map(user => ({
          role: user.role,
          roleLabel: user.role,
          displayName: user.username || '',
          email: user.email || '',
          classOrTopic: '',
          rawData: user
        }));
      }
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
    const filtered = buildSearchableItems(query);
    renderSearchResults(filtered, searchResults);
  });

  // Fermer on click outside
  document.addEventListener('click', (e) => {
    if (!e.target.closest('#searchForm')) {
      hideSearchDropdown();
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

  if (SKELETON_MODE) {
    document.documentElement.setAttribute('data-theme', 'light');
    document.body.classList.add('skeleton-mode');
    generateSidebarMenu(USER.role);
    loadSection('dashboard', { preventDefault: () => {} });
    return;
  }

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
