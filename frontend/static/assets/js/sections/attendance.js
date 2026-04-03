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
  const att = records.length > 0 ? records[0] : { late: 0, absent: 0 };

  const abEl = document.getElementById('attendanceAbsent');
  const ltEl = document.getElementById('attendanceLate');
  if (abEl) abEl.textContent = att.absent;
  if (ltEl) ltEl.textContent = att.late;
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
    <div id="attMessage" class="mt-2"></div>
  `;
}

async function markAttendance(studentId, late, absent, btn) {
  btn.disabled = true;
  const res = await api('attendance', {
    method: 'POST',
    body: JSON.stringify({ student_id: studentId, late, absent })
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
