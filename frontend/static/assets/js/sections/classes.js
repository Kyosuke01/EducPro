// ============================================
// CLASSES — Admin & Professeur
// ============================================

async function getClassesContent() {
  return await loadTemplate('classes_list');
}

async function initClassesList() {
  const data = await api('classes');
  const classes = data.classes || [];
  const tbody = document.getElementById('classesTableBody');
  if (!tbody) return;

  if (!classes.length) {
    tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-24">Aucune classe trouvée</td></tr>';
    return;
  }

  tbody.innerHTML = classes.map(cls => {
    const teacherName = cls.teacher_first_name
      ? `${cls.teacher_first_name} ${cls.teacher_last_name}`
      : 'Non assigné';
    const capacityBadge = (cls.current_size || 0) >= cls.max_capacity
      ? '<span class="badge bg-danger-100 text-danger-600">Complet</span>'
      : '<span class="badge bg-success-100 text-success-600">Disponible</span>';

    return `
      <tr class="align-middle">
        <td class="ps-24">
          <div class="d-flex align-items-center gap-3">
            <div class="w-40-px h-40-px rounded-3 bg-primary-100 text-primary-600 d-flex justify-content-center align-items-center fw-bold">
              <i class="ri-book-3-line text-lg"></i>
            </div>
            <div>
              <h6 class="text-sm fw-medium mb-0">${cls.name}</h6>
              <small class="text-neutral-500">${teacherName}</small>
            </div>
          </div>
        </td>
        <td><div class="text-sm fw-semibold">${cls.current_size || 0}</div></td>
        <td>${capacityBadge}</td>
        <td>
          <button onclick="showClassDetail('${cls.name.replaceAll("'", "\\'")}' )"
            class="btn btn-sm btn-light radius-8 d-flex align-items-center gap-2">
            <i class="ri-eye-line"></i> Voir
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

async function showClassDetail(className) {
  const contentArea = document.getElementById('contentArea');
  contentArea.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-primary"></div></div>';

  const [classData, teacherData] = await Promise.all([
    api(`classes/${encodeURIComponent(className)}/students`),
    USER.role === 'admin' ? api('teachers') : Promise.resolve({})
  ]);

  const students = classData.students || [];
  const classInfo = classData.class_info || {};
  const currentSize = classData.current_size || students.length;
  const teacherName = classInfo.teacher_first_name
    ? `${classInfo.teacher_first_name} ${classInfo.teacher_last_name}`
    : 'Non assigné';

  // Charger le template de détail
  contentArea.innerHTML = await loadTemplate('classes_detail');

  // Remplir les infos de la classe
  const nameEl = document.getElementById('classDetailName');
  const effectifEl = document.getElementById('classDetailEffectif');
  if (nameEl) nameEl.textContent = className;
  if (effectifEl) effectifEl.textContent = `Effectif : ${currentSize} / ${classInfo.max_capacity || 35}`;

  // Bloc assignation
  const assignBlock = document.getElementById('classAssignmentBlock');
  if (assignBlock) {
    if (USER.role === 'admin') {
      const teachers = (teacherData.teachers || []).map(t => {
        const selected = classInfo.homeroom_teacher_id === t.teacher_id ? 'selected' : '';
        return `<option value="${t.teacher_id}" ${selected}>${t.first_name} ${t.last_name}${t.topic_name ? ' · ' + t.topic_name : ''}</option>`;
      }).join('');

      assignBlock.innerHTML = `
        <label class="form-label text-sm fw-medium">Professeur principal</label>
        <select id="classTeacherSelect" class="form-select mb-2">
          <option value="">Sélectionner</option>
          ${teachers}
        </select>
        <button class="btn btn-sm btn-outline-primary"
          onclick="assignTeacherToClass(${classInfo.class_id}, '${className.replaceAll("'", "\\'")}')">
          Enregistrer
        </button>
      `;
    } else {
      assignBlock.innerHTML = `<p class="text-sm text-neutral-500 mb-0">Professeur principal : <strong>${teacherName}</strong></p>`;
    }
  }

  // Bouton retour
  const backBtn = document.getElementById('editUserBackBtn');
  // (le template classes_detail utilise onclick="loadSection('classes', event)" directement)

  // Tableau des étudiants
  const tbody = document.getElementById('classDetailStudentsBody');
  if (tbody) {
    tbody.innerHTML = students.length
      ? students.map(s => `<tr><td>${s.last_name} ${s.first_name}</td><td>${s.mail_student || '-'}</td></tr>`).join('')
      : '<tr><td colspan="2" class="text-center text-muted">Aucun étudiant</td></tr>';
  }
}

async function assignTeacherToClass(classId, className) {
  const select = document.getElementById('classTeacherSelect');
  if (!select) return;
  const teacherId = Number.parseInt(select.value || '0', 10);
  if (!teacherId) { alert('Veuillez sélectionner un professeur.'); return; }

  const res = await api(`classes/${classId}/assign-teacher`, {
    method: 'PUT',
    body: JSON.stringify({ teacher_id: teacherId })
  });

  if (res && !res.error) {
    alert('Professeur assigné.');
    showClassDetail(className);
  } else {
    alert(res?.error || "Impossible d'assigner ce professeur.");
  }
}

async function getMyClassesContent() {
  return await loadTemplate('classes_teacher');
}

async function initMyClasses() {
  const data = await api(`edt/teacher/${encodeURIComponent(USER.lastName)}`);
  const edtList = data.edt || [];
  const uniqueClasses = [...new Set(edtList.map(e => e.class_name))];

  const container = document.getElementById('myClassesCards');
  if (!container) return;

  if (!uniqueClasses.length) {
    container.innerHTML = '<div class="col-12"><p class="text-muted">Aucune classe assignée</p></div>';
    return;
  }

  const cards = await Promise.all(uniqueClasses.map(async cls => {
    const studData = await api(`classes/${encodeURIComponent(cls)}/students`);
    const nbStudents = studData.students ? studData.students.length : 0;
    return `
      <div class="col-sm-6 col-lg-4">
        <div class="card border">
          <div class="card-body">
            <h6>${cls}</h6>
            <p class="text-sm text-secondary-light">${nbStudents} étudiants</p>
            <button class="btn btn-sm btn-primary" onclick="showClassDetail('${cls}')">Voir Classe</button>
          </div>
        </div>
      </div>
    `;
  }));

  container.innerHTML = cards.join('');
}
