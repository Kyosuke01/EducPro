// ============================================
// ASSIDUITÉ — Étudiant & Professeur
// ============================================

async function getMyAttendanceContent() {
  const html = await loadTemplate('attendance_student');
  // Les données seront injectées dans initMyAttendance() après rendu
  return html;
}

async function initMyAttendance() {
  const data = await api(`attendance/student/${USER.id}`);
  const records = data.attendance || [];
  const att = records.reduce((acc, row) => {
    if (row.status === 'absent') acc.absent += 1;
    if (row.status === 'late') acc.late += 1;
    return acc;
  }, { late: 0, absent: 0 });

  const abEl = document.getElementById('attendanceAbsent');
  const ltEl = document.getElementById('attendanceLate');
  if (abEl) abEl.textContent = att.absent;
  if (ltEl) ltEl.textContent = att.late;

  await renderAttendanceCourseDetails(records);
}

function formatAttendanceDate(value) {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString('fr-FR');
}

async function renderAttendanceCourseDetails(records) {
  const box = document.getElementById('attendanceCourseDetailsBox');
  if (!box) return;

  const eventRows = records.filter(r => r.status === 'absent' || r.status === 'late');
  if (!eventRows.length) {
    box.innerHTML = '<div class="text-center text-muted py-3">Aucune absence ni retard enregistré.</div>';
    return;
  }

  const edtIds = [...new Set(eventRows.map(r => r.edt_id).filter(Boolean))];
  const [edtData, myScheduleData] = await Promise.all([
    api('edt'),
    api(`edt/class/${encodeURIComponent(USER.className || '')}`)
  ]);

  const allEdt = edtData?.edt || [];
  const classEdt = myScheduleData?.edt || [];
  const edtMap = new Map();
  allEdt.forEach(row => { if (row.edt_id) edtMap.set(row.edt_id, row); });
  classEdt.forEach(row => { if (row.edt_id) edtMap.set(row.edt_id, row); });

  const detailsRows = eventRows.map(row => {
    const course = row.edt_id ? edtMap.get(row.edt_id) : null;
    const topic = course?.topic_name || 'Cours non trouvé';
    const teacher = course ? `${course.teacher_f_name || ''} ${course.teacher_l_name || ''}`.trim() : '-';
    const statusBadge = row.status === 'absent'
      ? '<span class="badge bg-danger-100 text-danger-700">Absence</span>'
      : '<span class="badge bg-warning-100 text-warning-700">Retard</span>';

    return `
      <tr>
        <td>${statusBadge}</td>
        <td>${topic}</td>
        <td>${teacher || '-'}</td>
        <td>${formatAttendanceDate(row.date_attendance)}</td>
      </tr>
    `;
  }).join('');

  box.innerHTML = `
    <div class="table-responsive">
      <table class="table table-hover mb-0">
        <thead>
          <tr>
            <th>Type</th>
            <th>Cours</th>
            <th>Professeur</th>
            <th>Date</th>
          </tr>
        </thead>
        <tbody>${detailsRows}</tbody>
      </table>
    </div>
  `;
}

async function getTeacherAttendanceContent() {
  const html = await loadTemplate('attendance_teacher');
  return html;
}

async function initTeacherAttendance() {
  const edtData = await api(`edt/teacher/${encodeURIComponent(USER.lastName)}`);
  const edtList = edtData.edt || [];
  const uniqueClasses = [...new Set(edtList.map(e => e.class_name))];

  const select = document.getElementById('attClassSelect');
  if (!select) return;
  select.innerHTML = '<option value="">Sélectionnez une classe</option>'
    + uniqueClasses.map(cls => `<option value="${cls}">${cls}</option>`).join('');
}

async function loadAttendanceStudents() {
  const className = document.getElementById('attClassSelect').value;
  const area = document.getElementById('attStudentsArea');
  if (!className) { area.innerHTML = ''; return; }

  const data = await api(`classes/${encodeURIComponent(className)}/students`);
  const students = data.students || [];

  const rows = students.map(s => `
    <tr>
      <td>${s.last_name} ${s.first_name}</td>
      <td>
        <div class="d-flex gap-2">
          <button class="btn btn-xs btn-outline-warning" onclick="markAttendance(${s.student_id}, 1, 0, this)">+1 Retard</button>
          <button class="btn btn-xs btn-outline-danger" onclick="markAttendance(${s.student_id}, 0, 1, this)">+1 Absence</button>
        </div>
      </td>
    </tr>
  `).join('');

  area.innerHTML = `
    <div class="table-responsive mt-3">
      <table class="table">
        <thead><tr><th>Étudiant</th><th>Action</th></tr></thead>
        <tbody>${rows || '<tr><td colspan="2" class="text-center text-muted">Aucun étudiant trouvé</td></tr>'}</tbody>
      </table>
    </div>
    <div class="d-flex align-items-center gap-2 mb-2">
      <button class="btn btn-primary btn-sm" onclick="saveAttendanceChanges()">Sauvegarder</button>
      <small class="text-muted">Les actions +1 sont enregistrées immédiatement.</small>
    </div>
    <div id="attMessage" class="mt-2"></div>
  `;
}

function saveAttendanceChanges() {
  const msgEl = document.getElementById('attMessage');
  if (msgEl) {
    msgEl.innerHTML = '<div class="alert alert-info">Toutes les actions ont déjà été sauvegardées.</div>';
    setTimeout(() => { msgEl.innerHTML = ''; }, 2000);
  }
}

async function markAttendance(studentId, late, absent, btn) {
  btn.disabled = true;
  const className = document.getElementById('attClassSelect')?.value || '';
  const edtData = className ? await api(`edt/class/${encodeURIComponent(className)}`) : { edt: [] };
  const classEdt = edtData.edt || [];
  const matchedEdt = classEdt.find(e =>
    (e.teacher_l_name || '').toLowerCase() === (USER.lastName || '').toLowerCase()
  );

  const res = await api('attendance', {
    method: 'POST',
    body: JSON.stringify({
      student_id: studentId,
      late,
      absent,
      date_attendance: matchedEdt?.start_time ? matchedEdt.start_time.slice(0, 10) : undefined
    })
  });

  if (!res.error) {
    const msgEl = document.getElementById('attMessage');
    if (msgEl) {
      msgEl.innerHTML = `<div class="alert alert-success">Action enregistrée pour l'étudiant #${studentId}</div>`;
      setTimeout(() => msgEl.innerHTML = '', 2000);
    }
  }
  btn.disabled = false;
}
