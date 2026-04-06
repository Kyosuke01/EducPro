// ============================================
// GESTION UTILISATEURS — Admin
// Étudiants, Professeurs, Création, Édition, Suppression
// ============================================

async function deleteUser(type, id) {
  if (!confirm("Voulez-vous vraiment supprimer cet utilisateur ? Cette action est irréversible.")) return;
  try {
    const resp = await fetch(`/api/users/${type}/${id}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' }
    });
    if (resp.ok) {
      alert('Utilisateur supprimé');
      loadSection(type + 's', null);
    } else {
      const js = await resp.json();
      alert('Erreur: ' + (js.error || 'inconnue'));
    }
  } catch (e) { alert('Erreur réseau'); }
}

async function showEditUserForm(type, user) {
  const contentArea = document.getElementById('contentArea');
  contentArea.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-primary"></div></div>';

  const classesData = await api('classes');
  const classesList = classesData.classes || [];

  contentArea.innerHTML = await loadTemplate('users_edit');

  const isStudent = type === 'student';
  const id = isStudent ? user.student_id : user.teacher_id;

  // Titre et bouton retour
  const titleEl = document.getElementById('editUserTitle');
  if (titleEl) titleEl.innerHTML = `<i class="ri-edit-line text-primary me-2"></i>Éditer ${isStudent ? "l'étudiant" : "le professeur"}`;

  const backBtn = document.getElementById('editUserBackBtn');
  if (backBtn) backBtn.setAttribute('onclick', `loadSection('${type}s', event)`);

  // Pré-remplir les champs
  document.getElementById('editUserFirstName').value = user.first_name || '';
  document.getElementById('editUserLastName').value = user.last_name || '';
  document.getElementById('editUserEmail').value = isStudent ? (user.mail_student || '') : (user.mail_teacher || '');

  if (isStudent) {
    const classSelect = document.getElementById('editUserClass');
    classSelect.innerHTML = '<option value="">-- Sélectionner une classe --</option>'
      + classesList.map(c => `<option value="${c.name}" ${user.class_name === c.name ? 'selected' : ''}>${c.name}</option>`).join('');
    document.getElementById('editStudentFields').style.display = 'block';
    document.getElementById('editTeacherFields').style.display = 'none';
  } else {
    document.getElementById('editUserTopic').value = user.topic_name || '';
    document.getElementById('editStudentFields').style.display = 'none';
    document.getElementById('editTeacherFields').style.display = 'block';
  }

  // Lier le submit
  const form = document.getElementById('editUserForm');
  if (form) {
    form.onsubmit = (e) => submitEditUser(e, type, id);
  }
}

async function submitEditUser(e, type, id) {
  e.preventDefault();
  const btn = document.getElementById('editUserBtn');
  const alertBox = document.getElementById('editUserAlert');
  const payload = {
    first_name: document.getElementById('editUserFirstName').value,
    last_name: document.getElementById('editUserLastName').value,
    email: document.getElementById('editUserEmail').value,
  };
  if (type === 'student') payload.class_name = document.getElementById('editUserClass').value;
  else payload.topic_name = document.getElementById('editUserTopic').value;

  btn.disabled = true;
  btn.innerText = 'Enregistrement...';
  try {
    const resp = await fetch(`/api/users/${type}/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await resp.json();
    if (resp.ok) {
      alertBox.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
      setTimeout(() => loadSection(type + 's', null), 1500);
    } else {
      alertBox.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
    }
  } catch (err) {
    alertBox.innerHTML = `<div class="alert alert-danger">Erreur ${err.message}</div>`;
  } finally {
    btn.disabled = false;
    btn.innerText = "Mettre à jour";
  }
}

async function getCreateUserContent() {
  return await loadTemplate('users_create');
}

async function initCreateUser() {
  const classesData = await api('classes');
  const classesList = classesData.classes || [];
  const select = document.getElementById('newUserClass');
  if (select) {
    select.innerHTML = '<option value="">-- Sélectionner une classe --</option>'
      + classesList.map(c => `<option value="${c.name}">${c.name}</option>`).join('');
  }
}

function toggleUserTypeFields() {
  const type = document.getElementById('newUserType').value;
  if (type === 'student') {
    document.getElementById('studentFields').classList.remove('d-none');
    document.getElementById('teacherFields').classList.add('d-none');
    document.getElementById('newUserClass').required = true;
    document.getElementById('newUserTopic').required = false;
  } else {
    document.getElementById('studentFields').classList.add('d-none');
    document.getElementById('teacherFields').classList.remove('d-none');
    document.getElementById('newUserClass').required = false;
    document.getElementById('newUserTopic').required = true;
  }
}

async function submitCreateUser(e) {
  e.preventDefault();
  const btn = document.getElementById('createUserBtn');
  const alertBox = document.getElementById('createUserAlert');
  const payload = {
    user_type: document.getElementById('newUserType').value,
    first_name: document.getElementById('newUserFirstName').value,
    last_name: document.getElementById('newUserLastName').value,
    email: document.getElementById('newUserEmail').value,
    password: document.getElementById('newUserPassword').value,
  };
  if (payload.user_type === 'student') payload.class_name = document.getElementById('newUserClass').value;
  else payload.topic_name = document.getElementById('newUserTopic').value;

  btn.disabled = true;
  btn.innerText = 'Création en cours...';
  try {
    const resp = await fetch('/api/users/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await resp.json();
    if (resp.ok) {
      alertBox.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
      document.getElementById('createUserForm').reset();
      toggleUserTypeFields();
    } else {
      alertBox.innerHTML = `<div class="alert alert-danger">${data.error || 'Erreur inconnue'}</div>`;
    }
  } catch (err) {
    alertBox.innerHTML = `<div class="alert alert-danger">Erreur: ${err.message}</div>`;
  } finally {
    btn.disabled = false;
    btn.innerText = "Créer l'utilisateur";
  }
}

async function getStudentsContent() {
  return await loadTemplate('users_students');
}

async function initStudentsList() {
  const data = await api('students');
  const students = data.students || [];
  const tbody = document.getElementById('studentsTableBody');
  if (!tbody) return;

  // Afficher/cacher colonne Actions si admin
  if (USER.role === 'admin') {
    document.querySelectorAll('.js-admin-col').forEach(el => el.style.display = '');
    const addBtn = document.getElementById('studentsAddButton');
    if (addBtn) addBtn.innerHTML = `<button class="btn btn-sm btn-primary radius-8" onclick="loadSection('createUser')"><i class="ri-add-line me-1"></i>Ajouter</button>`;
  }

  if (!students.length) {
    tbody.innerHTML = `<tr><td colspan="${USER.role === 'admin' ? '4' : '3'}" class="text-center text-muted py-24">Aucun étudiant trouvé</td></tr>`;
    return;
  }

  const colors = ['primary', 'success', 'warning', 'info', 'danger'];
  // Helper function to deterministically select color based on user ID
  const getColorFromId = (id) => {
    const hash = id.toString().codePointAt(0) + id.toString().length;
    return colors[hash % colors.length];
  };

  tbody.innerHTML = students.map(s => {
    const initial = s.first_name ? s.first_name.charAt(0).toUpperCase() : '?';
    const colorClass = getColorFromId(s.student_id);
    const adminActions = USER.role === 'admin' ? `
      <td>
        <div class="d-flex align-items-center gap-2">
          <button class="btn btn-sm btn-light radius-8 d-flex align-items-center justify-content-center w-32-px h-32-px"
            onclick='showEditUserForm("student", ${JSON.stringify(s).replaceAll("'", "&apos;")})'>
            <i class="ri-edit-2-line text-primary"></i>
          </button>
          <button class="btn btn-sm btn-light radius-8 d-flex align-items-center justify-content-center w-32-px h-32-px"
            onclick="deleteUser('student', ${s.student_id})">
            <i class="ri-delete-bin-line text-danger"></i>
          </button>
        </div>
      </td>` : '';
    return `
      <tr class="align-middle">
        <td>
          <div class="d-flex align-items-center gap-3">
            <div class="w-40-px h-40-px rounded-circle bg-${colorClass}-100 text-${colorClass}-600 d-flex justify-content-center align-items-center fw-bold text-sm">
              ${initial}
            </div>
            <div>
              <h6 class="text-sm fw-medium mb-0">${s.last_name} ${s.first_name}</h6>
              <span class="text-xs" style="color: #4b5563;">${s.mail_student || '-'}</span>
            </div>
          </div>
        </td>
        <td><span class="badge bg-neutral-200 text-neutral-600 rounded-pill px-12 py-6">${s.class_name || '-'}</span></td>
        <td><span class="badge bg-success-100 text-success-600 px-12 py-6 rounded-pill"><i class="ri-check-line me-1"></i>Actif</span></td>
        ${adminActions}
      </tr>
    `;
  }).join('');
}

async function getTeachersContent() {
  return await loadTemplate('users_teachers');
}

async function initTeachersList() {
  const data = await api('teachers');
  const teachers = data.teachers || [];
  const tbody = document.getElementById('teachersTableBody');
  if (!tbody) return;

  // Afficher/cacher colonne Actions si admin
  if (USER.role === 'admin') {
    document.querySelectorAll('.js-admin-col').forEach(el => el.style.display = '');
    const addBtn = document.getElementById('teachersAddButton');
    if (addBtn) addBtn.innerHTML = `<button class="btn btn-sm btn-primary radius-8" onclick="loadSection('createUser')"><i class="ri-add-line me-1"></i>Ajouter</button>`;
  }

  if (!teachers.length) {
    tbody.innerHTML = `<tr><td colspan="${USER.role === 'admin' ? '4' : '3'}" class="text-center text-muted py-24">Aucun professeur trouvé</td></tr>`;
    return;
  }

  tbody.innerHTML = teachers.map(t => {
    const initial = t.first_name ? t.first_name.charAt(0).toUpperCase() : '?';
    const colorClass = t.is_admin ? 'warning' : 'primary';
    const roleBadge = t.is_admin
      ? '<span class="badge bg-warning-100 text-warning-600 px-12 py-6 rounded-pill"><i class="ri-shield-user-line me-1"></i>Admin</span>'
      : '<span class="badge bg-info-100 text-info-600 px-12 py-6 rounded-pill"><i class="ri-presentation-line me-1"></i>Professeur</span>';

    const adminActions = USER.role === 'admin' ? `
      <td>
        <div class="d-flex align-items-center gap-2">
          <button class="btn btn-sm btn-light radius-8 d-flex align-items-center justify-content-center w-32-px h-32-px"
            onclick='showEditUserForm("teacher", ${JSON.stringify(t).replaceAll("'", "&apos;")})'>
            <i class="ri-edit-2-line text-primary"></i>
          </button>
          ${!t.is_admin ? `<button class="btn btn-sm btn-light radius-8 d-flex align-items-center justify-content-center w-32-px h-32-px" onclick="deleteUser('teacher', ${t.teacher_id})"><i class="ri-delete-bin-line text-danger"></i></button>` : ''}
        </div>
      </td>` : '';

    return `
      <tr class="align-middle">
        <td>
          <div class="d-flex align-items-center gap-3">
            <div class="w-40-px h-40-px rounded-circle bg-${colorClass}-100 text-${colorClass}-600 d-flex justify-content-center align-items-center fw-bold text-sm">
              ${initial}
            </div>
            <div>
              <h6 class="text-sm fw-medium mb-0">${t.last_name} ${t.first_name}</h6>
              <span class="text-xs" style="color: #4b5563;">${t.mail_teacher || '-'}</span>
            </div>
          </div>
        </td>
        <td><span class="badge bg-neutral-200 text-neutral-600 rounded-pill px-12 py-6">${t.topic_name || 'Administration'}</span></td>
        <td>${roleBadge}</td>
        ${adminActions}
      </tr>
    `;
  }).join('');
}
