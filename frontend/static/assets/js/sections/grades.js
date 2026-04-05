// ============================================
// NOTES & ÉVALUATIONS
// ============================================

async function getEvaluationsContent() {
  return await loadTemplate('grades_evaluations');
}

async function initEvaluations() {
  const titleEl = document.getElementById('evaluationsTitle');
  if (titleEl) titleEl.textContent = `Évaluations — ${USER.topicName || 'Toutes matières'}`;

  const data = await api(`grades/topic/${encodeURIComponent(USER.topicName || '')}`);
  const grades = data.grades || [];

  // Récupérer les noms des étudiants en parallèle
  const studentIds = [...new Set(grades.map(g => g.student_id))];
  const studentNames = {};
  await Promise.all(studentIds.map(async sid => {
    const sData = await api(`students/${sid}`);
    if (sData.first_name) studentNames[sid] = `${sData.last_name} ${sData.first_name}`;
  }));

  const tbody = document.getElementById('evaluationsTableBody');
  if (!tbody) return;

  if (!grades.length) {
    tbody.innerHTML = '<tr><td colspan="3" class="text-center text-muted">Aucune note trouvée</td></tr>';
    return;
  }

  tbody.innerHTML = grades.map(g => {
    const studentName = studentNames[g.student_id] || `Étudiant #${g.student_id}`;
    const badgeClass = g.grade >= 10 ? 'bg-success' : 'bg-danger';
    return `
      <tr>
        <td>${studentName}</td>
        <td>${g.topic_name}</td>
        <td><span class="badge ${badgeClass}">${g.grade}/20</span></td>
      </tr>
    `;
  }).join('');
}

async function getGradesContent() {
  return await loadTemplate('grades_input');
}

async function initGradesInput() {
  const edtData = await api(`edt/teacher/${encodeURIComponent(USER.lastName)}`);
  const edtList = edtData.edt || [];
  const uniqueClasses = [...new Set(edtList.map(e => e.class_name))];

  const select = document.getElementById('gradeClassSelect');
  if (select) {
    select.innerHTML = '<option value="">Sélectionnez une classe</option>'
      + uniqueClasses.map(cls => `<option value="${cls}">${cls}</option>`).join('');
  }

  const topicInput = document.getElementById('gradeTopicInput');
  if (topicInput) topicInput.value = USER.topicName || '';
}

async function loadGradeStudents() {
  const className = document.getElementById('gradeClassSelect').value;
  const area = document.getElementById('gradeStudentsArea');
  if (!className) { area.innerHTML = ''; return; }

  const data = await api(`classes/${encodeURIComponent(className)}/students`);
  const students = data.students || [];

  const rows = students.map(s => `
    <tr>
      <td>${s.last_name} ${s.first_name}</td>
      <td>
        <input type="number" class="form-control form-control-sm grade-input"
          data-student-id="${s.student_id}" min="0" max="20" step="0.5">
      </td>
    </tr>
  `).join('');

  area.innerHTML = `
    <div class="table-responsive mt-3">
      <table class="table">
        <thead><tr><th>Étudiant</th><th>Note / 20</th></tr></thead>
        <tbody>${rows || '<tr><td colspan="2" class="text-center text-muted">Aucun étudiant</td></tr>'}</tbody>
      </table>
    </div>
    <button class="btn btn-primary mt-3" onclick="submitGrades()">Enregistrer les Notes</button>
    <div id="gradeMessage" class="mt-2"></div>
  `;
}

async function submitGrades() {
  const topicName = document.getElementById('gradeTopicInput').value;
  const inputs = document.querySelectorAll('.grade-input');
  const msgEl = document.getElementById('gradeMessage');
  let count = 0;

  for (const input of inputs) {
    const val = Number.parseFloat(input.value);
    if (!Number.isNaN(val)) {
      const studentId = Number.parseInt(input.dataset.studentId);
      await api('grades', {
        method: 'POST',
        body: JSON.stringify({ grade: val, student_id: studentId, topic_name: topicName })
      });
      count++;
    }
  }

  if (msgEl) {
    msgEl.innerHTML = count > 0
      ? `<div class="alert alert-success">${count} note(s) enregistrée(s) avec succès.</div>`
      : '<div class="alert alert-warning">Aucune note à enregistrer.</div>';
  }
}

async function getMyGradesContent() {
  return await loadTemplate('grades_my');
}

async function initMyGrades() {
  const data = await api(`grades/student/${USER.id}`);
  const grades = data.grades || [];

  // Moyenne générale
  const allGrades = grades.map(g => g.grade);
  const globalAvg = allGrades.length > 0
    ? (allGrades.reduce((s, n) => s + n, 0) / allGrades.length).toFixed(1)
    : '-';

  const avgEl = document.getElementById('myGradesAverage');
  if (avgEl) avgEl.textContent = `${globalAvg}/20`;

  // Grouper par matière
  const byTopic = {};
  grades.forEach(g => {
    if (!byTopic[g.topic_name]) byTopic[g.topic_name] = [];
    byTopic[g.topic_name].push(g.grade);
  });

  const tbody = document.getElementById('myGradesTableBody');
  if (!tbody) return;

  if (!grades.length) {
    tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Aucune note trouvée</td></tr>';
    return;
  }

  const rows = [];
  for (const [topic, notes] of Object.entries(byTopic)) {
    const avg = (notes.reduce((s, n) => s + n, 0) / notes.length).toFixed(1);
    const statusClass = avg >= 14 ? 'bg-success' : avg >= 10 ? 'bg-warning' : 'bg-danger';
    const statusText = avg >= 14 ? 'Bon' : avg >= 10 ? 'Moyen' : 'Insuffisant';
    notes.forEach(note => {
      rows.push(`
        <tr>
          <td>${topic}</td>
          <td>${USER.className}</td>
          <td>${note}/20</td>
          <td>${avg}/20</td>
          <td><span class="badge ${statusClass}">${statusText}</span></td>
        </tr>
      `);
    });
  }

  tbody.innerHTML = rows.join('');

  // Rendre le graphique Radar
  renderRadarChart(byTopic);
}

function renderRadarChart(byTopic) {
  const chartEl = document.getElementById('gradesRadarChart');
  if (!chartEl) return;

  // Préparer les données pour le graphique Radar
  const categories = Object.keys(byTopic);
  const averages = Object.values(byTopic).map(notes => 
    (notes.reduce((s, n) => s + n, 0) / notes.length).toFixed(1)
  );

  if (categories.length === 0) {
    chartEl.innerHTML = '<div class="text-center text-secondary-light py-5">Aucune note disponible</div>';
    return;
  }

  const options = {
    series: [{
      name: 'Moyenne par Matière',
      data: averages
    }],
    chart: {
      type: 'radar',
      height: 450,
      toolbar: { show: false },
      fontFamily: 'Inter, sans-serif'
    },
    colors: ['#f0ebd8'],
    stroke: {
      width: 2
    },
    fill: {
      opacity: 0.15
    },
    markers: {
      size: 5,
      colors: ['#f0ebd8'],
      strokeColors: '#fff',
      strokeWidth: 2
    },
    xaxis: {
      categories: categories,
      labels: {
        show: true,
        style: {
          colors: '#a4b0f5',
          fontSize: '12px'
        }
      }
    },
    yaxis: {
      min: 0,
      max: 20,
      tickAmount: 4,
      labels: {
        style: {
          colors: '#a4b0f5',
          fontSize: '12px'
        }
      }
    },
    tooltip: {
      theme: 'dark',
      y: {
        formatter: function(val) {
          return val.toFixed(1) + '/20';
        }
      }
    },
    grid: {
      borderColor: 'rgba(164, 176, 245, 0.1)'
    }
  };

  const radarChart = new ApexCharts(chartEl, options);
  radarChart.render();
}
