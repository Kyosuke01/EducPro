// ============================================
// DASHBOARD — Stats dynamiques + Graphiques
// ============================================

async function getDashboardContent() {
  try {
    const html = await loadTemplate('dashboard');
    return html;
  } catch (e) {
    return `<div class="alert alert-danger">Erreur chargement template dashboard : ${e.message}</div>`;
  }
}

async function initDashboard() {
  try {
    configureAttendanceCardForRole();

    if (USER.role === 'admin') {
      const [studentsData, teachersData, classesData, attendanceStatsData] = await Promise.all([
        api('students'),
        api('teachers'),
        api('classes'),
        getAttendanceStats() // Récupère stats d'attendance globales
      ]);
      const nbStudents = (studentsData && studentsData.students) ? studentsData.students.length : 0;
      const nbTeachers = (teachersData && teachersData.teachers) ? teachersData.teachers.length : 0;
      const nbClasses = (classesData && classesData.classes) ? classesData.classes.length : 0;

      globalThis.dashboardChartData = {
        role: 'admin',
        categories: ['Étudiants', 'Professeurs', 'Classes'],
        series: [{ name: 'Total', data: [nbStudents, nbTeachers, nbClasses] }],
        attendanceStats: attendanceStatsData
      };

      renderStatsCards([
        { title: 'Total Étudiants', value: nbStudents, icon: 'ri-graduation-cap-line', color: 'warning-600' },
        { title: 'Total Professeurs', value: nbTeachers, icon: 'ri-user-follow-line', color: 'blue-600' },
        { title: 'Total Classes', value: nbClasses, icon: 'ri-book-2-line', color: 'purple-600' },
        { title: 'Plateforme', value: 'Active', icon: 'ri-check-double-line', color: 'success-600' }
      ]);
      setChartTitle('Répartition de la plateforme');

    } else if (USER.role === 'teacher') {
      const edtData = await api(`edt/teacher/${encodeURIComponent(USER.lastName || '')}`);
      const edtList = (edtData && edtData.edt) ? edtData.edt : [];
      const teacherClasses = [...new Set(edtList.map(e => e.class_name).filter(Boolean))];
      const attendanceStatsData = await getAttendanceStatsForTeacherSlots(edtList);
      const nbSlots = edtList.length;
      const uniqueClasses = teacherClasses.length;
      const hoursByDay = calculateTeacherHoursByDay(edtList);

      globalThis.dashboardChartData = {
        role: 'teacher',
        categories: ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi'],
        series: [{ name: 'Heures de cours', data: hoursByDay }],
        attendanceStats: attendanceStatsData
      };

      renderStatsCards([
        { title: 'Mes Créneaux', value: nbSlots, icon: 'ri-calendar-line', color: 'warning-600' },
        { title: 'Mes Classes', value: uniqueClasses, icon: 'ri-book-2-line', color: 'blue-600' },
        { title: 'Matière', value: USER.topicName || '-', icon: 'ri-file-list-line', color: 'purple-600' },
        { title: 'Statut', value: 'Actif', icon: 'ri-check-double-line', color: 'success-600' }
      ]);
      setChartTitle('Heures de cours par jour de la semaine');

    } else {
      const [gradesData, attendanceData] = await Promise.all([
        api(`grades/student/${USER.id}`),
        api(`attendance/student/${USER.id}`)
      ]);

      const grades = (gradesData && gradesData.grades) ? gradesData.grades : [];
      const avg = grades.length > 0 ? (grades.reduce((s, g) => s + g.grade, 0) / grades.length).toFixed(1) : '-';
      const events = (attendanceData && Array.isArray(attendanceData.attendance))
        ? attendanceData.attendance
        : [];
      const lateCount = events.filter(e => e.status === 'late').length;
      const absentCount = events.filter(e => e.status === 'absent').length;

      globalThis.dashboardChartData = {
        role: 'student',
        categories: grades.map(g => g.topic_name.substring(0, 6)),
        series: [{ name: 'Mes Notes', data: grades.map(g => g.grade) }],
        attendanceStats: {
          onTime: (lateCount === 0 && absentCount === 0) ? 1 : 0,
          late: lateCount,
          absent: absentCount,
          total: Math.max(1, lateCount + absentCount)
        }
      };

      renderStatsCards([
        { title: 'Moyenne Générale', value: avg + '/20', icon: 'ri-star-line', color: 'warning-600' },
        { title: 'Classe', value: USER.className || '-', icon: 'ri-book-2-line', color: 'blue-600' },
        { title: 'Absences', value: absentCount, icon: 'ri-alarm-line', color: 'danger-600' },
        { title: 'Retards', value: lateCount, icon: 'ri-time-line', color: 'purple-600' }
      ]);
      setChartTitle('Évolution de mes notes récentes');
    }

    renderDashboardCharts();
    await renderRecentActivities();

  } catch (e) {
    const area = document.getElementById('dashboardStatsCards');
    if (area) area.innerHTML = `<div class="alert alert-danger col-12">Erreur dashboard : ${e.message}</div>`;
  }
}

// Récupère les statistiques d'attendance (retards globaux)
async function getAttendanceStats(className = null) {
  try {
    let url = 'attendance/stats';
    if (className) {
      url = `attendance/class/${encodeURIComponent(className)}`;
    }
    
    const data = await api(url);
    
    if (className && data.attendance) {
      // Calcul des stats pour une classe à partir des événements ATTENDANCE.status
      const lateCount = data.attendance.filter(a => a.status === 'late').length;
      const absentCount = data.attendance.filter(a => a.status === 'absent').length;
      const totalCount = data.attendance.length;
      const onTimeCount = Math.max(0, totalCount - lateCount - absentCount);
      return { late: lateCount, absent: absentCount, onTime: onTimeCount, total: totalCount };
    } else if (data.stats) {
      // Réponse depuis endpoint stats
      return data.stats;
    } else if (data.attendance) {
      // Fallback événementiel
      const totalLate = data.attendance.filter(a => a.status === 'late').length;
      const totalAbsent = data.attendance.filter(a => a.status === 'absent').length;
      const totalCount = data.attendance.length;
      return { late: totalLate, absent: totalAbsent, onTime: Math.max(0, totalCount - totalLate - totalAbsent), total: totalCount };
    }
    
    return { late: 0, absent: 0, onTime: 0, total: 0 };
  } catch (e) {
    console.warn('Erreur stats attendance:', e);
    return { late: 0, absent: 0, onTime: 0, total: 0 };
  }
}

async function getAttendanceStatsForClasses(classNames = []) {
  if (!classNames.length) {
    return { late: 0, absent: 0, onTime: 0, total: 0 };
  }

  const classStats = await Promise.all(classNames.map(name => getAttendanceStats(name)));
  return classStats.reduce((acc, current) => ({
    late: acc.late + (current.late || 0),
    absent: acc.absent + (current.absent || 0),
    onTime: acc.onTime + (current.onTime || 0),
    total: acc.total + (current.total || 0)
  }), { late: 0, absent: 0, onTime: 0, total: 0 });
}

async function getAttendanceStatsForTeacherSlots(teacherEdtList = []) {
  if (!teacherEdtList.length) {
    return { late: 0, absent: 0, onTime: 0, total: 0 };
  }

  const teacherEdtIds = new Set(teacherEdtList.map(row => row.edt_id));
  const classNames = [...new Set(teacherEdtList.map(row => row.class_name).filter(Boolean))];
  const classResponses = await Promise.all(classNames.map(name => api(`attendance/class/${encodeURIComponent(name)}`)));
  const scopedEvents = classResponses
    .flatMap(resp => resp?.attendance || [])
    .filter(event => teacherEdtIds.has(event.edt_id));

  const late = scopedEvents.filter(event => event.status === 'late').length;
  const absent = scopedEvents.filter(event => event.status === 'absent').length;
  const total = scopedEvents.length;
  const onTime = Math.max(0, total - late - absent);

  return { late, absent, onTime, total };
}

let dashboardMainChartInstance = null;
let dashboardAttendanceChartInstance = null;

function calculateTeacherHoursByDay(edtList = []) {
  const hours = [0, 0, 0, 0, 0];
  edtList.forEach(entry => {
    const start = new Date(entry.start_time);
    const end = new Date(entry.end_time);
    const jsDay = start.getDay();
    if (jsDay < 1 || jsDay > 5) return;
    const duration = Math.max(0, (end - start) / (1000 * 60 * 60));
    hours[jsDay - 1] += duration;
  });
  return hours.map(v => Number(v.toFixed(2)));
}

// Remplit les 4 cartes de stats dans le template
function renderStatsCards(cards) {
  const container = document.getElementById('dashboardStatsCards');
  if (!container) return;
  container.innerHTML = cards.map(card => `
    <div class="col-xxl-3 col-sm-6">
      <div class="card shadow-1 radius-8 h-100">
        <div class="card-body p-20">
          <div class="d-flex flex-wrap align-items-center gap-3 mb-16">
            <div class="w-44-px h-44-px bg-${card.color} rounded-circle d-flex justify-content-center align-items-center text-white">
              <i class="${card.icon} text-xl"></i>
            </div>
            <p class="fw-medium text-primary-light mb-1">${card.title}</p>
          </div>
          <h6 class="mb-0">${card.value}</h6>
        </div>
      </div>
    </div>
  `).join('');
}

function setChartTitle(title) {
  const el = document.getElementById('dashboardChartTitleText');
  if (el) el.textContent = title;
}

function configureAttendanceCardForRole() {
  const mainChartWrapper = document.getElementById('mainChartWrapper');
  const attendanceCardWrapper = document.getElementById('attendanceCardWrapper');
  const attendanceChartTitleText = document.getElementById('attendanceChartTitleText');

  if (USER.role === 'admin') {
    if (mainChartWrapper) {
      mainChartWrapper.classList.remove('col-lg-8');
      mainChartWrapper.classList.add('col-lg-12');
    }
    if (attendanceCardWrapper) {
      attendanceCardWrapper.remove();
    }
    return;
  }

  if (USER.role === 'student' && attendanceChartTitleText) {
    attendanceChartTitleText.textContent = 'Mes retards et Absences';
  } else if (USER.role === 'teacher' && attendanceChartTitleText) {
    attendanceChartTitleText.textContent = 'Absences/Retards des étudiants';
  }
}

function renderDashboardCharts() {
  const data = globalThis.dashboardChartData;
  if (!data) return;
  const unifiedChartHeight = 315;

  const options = {
    series: data.series,
    chart: {
      type: data.role === 'student' ? 'area' : 'bar',
      height: unifiedChartHeight,
      toolbar: { show: false },
      fontFamily: 'Inter, sans-serif'
    },
    colors: ['#6962E9'],
    fill: {
      type: data.role === 'student' ? 'gradient' : 'solid',
      gradient: {
        shadeIntensity: 1,
        opacityFrom: 0.4,
        opacityTo: 0.05,
        stops: [0, 90, 100]
      }
    },
    dataLabels: { enabled: false },
    stroke: { curve: 'smooth', width: 3, colors: ['#6962E9'] },
    xaxis: { categories: data.categories },
    grid: { borderColor: '#f1f1f1' }
  };

  const chartEl = document.querySelector('#mainChart');
  if (!chartEl) return;
  if (dashboardMainChartInstance) {
    dashboardMainChartInstance.destroy();
    dashboardMainChartInstance = null;
  }
  chartEl.innerHTML = '';
  dashboardMainChartInstance = new ApexCharts(chartEl, options);
  dashboardMainChartInstance.render();

  // Graphique Doughnut pour les retards (visible pour tous les rôles)
  if (data.role !== 'admin') {
    renderAttendanceChart();
  }
}

function renderAttendanceChart() {
  const chartEl = document.querySelector('#attendanceChart');
  if (!chartEl) return;
  const unifiedChartHeight = 315;

  // Récupère les vraies données d'attendance depuis le dashboard
  const stats = globalThis.dashboardChartData?.attendanceStats || { late: 0, onTime: 100, absent: 0, total: 100 };
  
  // Calcul des valeurs en fonction du rôle
  const lateCount = stats.late || 0;
  const absentCount = stats.absent || 0;
  const isStudent = USER.role === 'student';
  const isTeacher = USER.role === 'teacher';
  const showIssuesOnly = isStudent || isTeacher;
  const hasNoAttendanceIssue = showIssuesOnly && absentCount === 0 && lateCount === 0;
  const series = hasNoAttendanceIssue
    ? [1]
    : (showIssuesOnly ? [absentCount, lateCount] : [stats.onTime || 0, lateCount]);
  const labels = hasNoAttendanceIssue
    ? ['Présence parfaite']
    : (showIssuesOnly ? ['Absences', 'Retards'] : ['À l\'heure', 'En retard']);
  const totalCount = Math.max(1, series.reduce((s, n) => s + n, 0));

  const options = {
    series,
    chart: {
      type: 'donut',
      height: unifiedChartHeight,
      toolbar: { show: false },
      fontFamily: 'Inter, sans-serif'
    },
    labels,
    colors: hasNoAttendanceIssue ? ['#22c55e'] : ['#6962E9', '#a4b0f5'],
    dataLabels: {
      enabled: true,
      formatter: function(val) {
        return Math.round(val) + '%';
      },
      style: {
        colors: ['#111827'],
        fontSize: '14px',
        fontWeight: 'bold'
      },
      dropShadow: {
        enabled: true,
        color: '#000000',
        top: 1,
        left: 1,
        blur: 2,
        opacity: 0.8
      }
    },
    stroke: {
      width: showIssuesOnly ? 0 : 2,
      colors: showIssuesOnly ? ['transparent'] : ['#e5e7eb']
    },
    plotOptions: {
      pie: {
        donut: {
          size: '65%'
        }
      }
    },
    legend: {
      position: 'bottom',
      labels: {
        colors: '#111827',
        fontSize: '12px'
      }
    },
    tooltip: {
      theme: 'light',
      y: {
        formatter: function(val) {
          if (hasNoAttendanceIssue) {
            return 'Aucune absence ni retard';
          }
          const percentage = Math.round((val / totalCount) * 100);
           return val + (showIssuesOnly ? ' occurrence(s)' : ' étudiants') + ' (' + percentage + '%)';
         }
       }
     }
  };

  if (dashboardAttendanceChartInstance) {
    dashboardAttendanceChartInstance.destroy();
    dashboardAttendanceChartInstance = null;
  }
  chartEl.innerHTML = '';
  dashboardAttendanceChartInstance = new ApexCharts(chartEl, options);
  dashboardAttendanceChartInstance.render();
}

function formatRelativeDate(value) {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '-';
  return date.toLocaleString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

function buildActivityRow(iconClass, iconBgClass, iconTextClass, action, detail, dateText) {
  return `
    <tr class="align-middle">
      <td class="ps-24">
        <div class="d-flex align-items-center gap-3">
          <div class="w-40-px h-40-px rounded-circle ${iconBgClass} ${iconTextClass} d-flex justify-content-center align-items-center">
            <i class="${iconClass} text-lg"></i>
          </div>
          <h6 class="text-sm fw-medium mb-0">${action}</h6>
        </div>
      </td>
      <td><span class="text-xs text-neutral-500">${detail}</span></td>
      <td><span class="badge bg-neutral-100 text-neutral-600 px-12 py-6 rounded-pill">${dateText}</span></td>
    </tr>
  `;
}

async function renderRecentActivities() {
  const tbody = document.getElementById('recentActivitiesBody');
  if (!tbody) return;

  const activities = [];
  const now = new Date();
  const loginAt = window.sessionStorage.getItem('dashboard_login_at') || now.toISOString();
  window.sessionStorage.setItem('dashboard_login_at', loginAt);

  activities.push({
    iconClass: 'ri-login-circle-line',
    iconBgClass: 'bg-success-100',
    iconTextClass: 'text-success-600',
    action: 'Connexion réussie',
    detail: 'Session active sur EducPro',
    dateText: formatRelativeDate(loginAt)
  });

  if (USER.role === 'student') {
    const attendanceData = await api(`attendance/student/${USER.id}`);
    const events = attendanceData?.attendance || [];
    if (events.length > 0) {
      const lastEvent = events[0];
      const eventLabel = lastEvent.status === 'absent' ? 'Absence enregistrée' : 'Retard enregistré';
      activities.push({
        iconClass: 'ri-alarm-warning-line',
        iconBgClass: 'bg-warning-100',
        iconTextClass: 'text-warning-600',
        action: eventLabel,
        detail: 'Mise à jour de votre assiduité',
        dateText: formatRelativeDate(lastEvent.date_attendance)
      });
    }
  } else if (USER.role === 'teacher') {
    const edtData = await api(`edt/teacher/${encodeURIComponent(USER.lastName || '')}`);
    const edtList = edtData?.edt || [];
    if (edtList.length > 0) {
      activities.push({
        iconClass: 'ri-calendar-check-line',
        iconBgClass: 'bg-primary-100',
        iconTextClass: 'text-primary-600',
        action: 'Emploi du temps synchronisé',
        detail: `${edtList.length} créneau(x) chargé(s)`,
        dateText: formatRelativeDate(edtList[0].start_time)
      });
    }
  } else if (USER.role === 'admin') {
    const [studentsData, teachersData] = await Promise.all([api('students'), api('teachers')]);
    const studentCount = studentsData?.students?.length || 0;
    const teacherCount = teachersData?.teachers?.length || 0;
    activities.push({
      iconClass: 'ri-shield-check-line',
      iconBgClass: 'bg-info-100',
      iconTextClass: 'text-info-600',
      action: 'État du système',
      detail: `${studentCount} étudiants / ${teacherCount} professeurs actifs`,
      dateText: formatRelativeDate(now.toISOString())
    });

    activities.push({
      iconClass: 'ri-shield-warning-line',
      iconBgClass: 'bg-warning-100',
      iconTextClass: 'text-warning-700',
      action: 'Sécurité',
      detail: 'Aucune alerte de sécurité critique',
      dateText: formatRelativeDate(now.toISOString())
    });
  }

  activities.push({
    iconClass: 'ri-refresh-line',
    iconBgClass: 'bg-success-100',
    iconTextClass: 'text-success-700',
    action: 'Version système',
    detail: 'Système à jour',
    dateText: formatRelativeDate(now.toISOString())
  });

  tbody.innerHTML = activities
    .slice(0, 3)
    .map(item => buildActivityRow(
      item.iconClass,
      item.iconBgClass,
      item.iconTextClass,
      item.action,
      item.detail,
      item.dateText
    ))
    .join('');
}
