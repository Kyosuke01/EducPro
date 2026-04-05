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
      const [edtData, attendanceStatsData] = await Promise.all([
        api(`edt/teacher/${encodeURIComponent(USER.lastName || '')}`),
        getAttendanceStats(USER.className) // Stats de la classe du prof
      ]);
      const edtList = (edtData && edtData.edt) ? edtData.edt : [];
      const nbSlots = edtList.length;
      const uniqueClasses = [...new Set(edtList.map(e => e.class_name))].length;

      globalThis.dashboardChartData = {
        role: 'teacher',
        categories: ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi'],
        series: [{ name: 'Heures de cours', data: [4, 6, 2, 8, 4] }],
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
      const att = (attendanceData && attendanceData.attendance && attendanceData.attendance.length > 0)
        ? attendanceData.attendance[0]
        : { late: 0, absent: 0 };

      globalThis.dashboardChartData = {
        role: 'student',
        categories: grades.map(g => g.topic_name.substring(0, 6)),
        series: [{ name: 'Mes Notes', data: grades.map(g => g.grade) }],
        attendanceStats: {
          onTime: att.absent === 0 ? 1 : 0, // Si pas absent, en retard ou à l'heure
          late: att.late || 0,
          absent: att.absent || 0,
          total: Math.max(1, (att.late || 0) + (att.absent || 0))
        }
      };

      renderStatsCards([
        { title: 'Moyenne Générale', value: avg + '/20', icon: 'ri-star-line', color: 'warning-600' },
        { title: 'Classe', value: USER.className || '-', icon: 'ri-book-2-line', color: 'blue-600' },
        { title: 'Absences', value: att.absent || 0, icon: 'ri-calendar-x-line', color: 'danger-600' },
        { title: 'Retards', value: att.late || 0, icon: 'ri-time-line', color: 'purple-600' }
      ]);
      setChartTitle('Évolution de mes notes récentes');
    }

    renderDashboardCharts();

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
      // Calcul des stats pour une classe
      const lateCount = data.attendance.filter(a => a.late > 0).length;
      const onTimeCount = data.attendance.filter(a => a.late === 0).length;
      return { late: lateCount, onTime: onTimeCount, total: data.attendance.length };
    } else if (data.stats) {
      // Réponse depuis endpoint stats
      return data.stats;
    } else if (data.attendance) {
      // Fallback pour stats globales
      let totalLate = 0, totalAbsent = 0;
      data.attendance.forEach(a => {
        totalLate += a.late || 0;
        totalAbsent += a.absent || 0;
      });
      return { late: totalLate, absent: totalAbsent, onTime: Math.max(1, data.attendance.length - totalLate) };
    }
    
    return { late: 0, onTime: 100, total: 100 };
  } catch (e) {
    console.warn('Erreur stats attendance:', e);
    return { late: 0, onTime: 100, total: 100 };
  }
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

function renderDashboardCharts() {
  const data = globalThis.dashboardChartData;
  if (!data) return;

  const options = {
    series: data.series,
    chart: {
      type: data.role === 'student' ? 'area' : 'bar',
      height: 300,
      toolbar: { show: false },
      fontFamily: 'Inter, sans-serif'
    },
    colors: ['#F0EBD8'],
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
    stroke: { curve: 'smooth', width: 3 },
    xaxis: { categories: data.categories },
    grid: { borderColor: '#f1f1f1' }
  };

  const chartEl = document.querySelector('#mainChart');
  if (!chartEl) return;
  const chart = new ApexCharts(chartEl, options);
  chart.render();

  // Graphique Doughnut pour les retards (visible pour tous les rôles)
  renderAttendanceChart();
}

function renderAttendanceChart() {
  const chartEl = document.querySelector('#attendanceChart');
  if (!chartEl) return;

  // Récupère les vraies données d'attendance depuis le dashboard
  const stats = globalThis.dashboardChartData?.attendanceStats || { late: 0, onTime: 100, absent: 0, total: 100 };
  
  // Calcul des valeurs en fonction du rôle
  let lateCount = stats.late || 0;
  let onTimeCount = stats.onTime || 0;
  
  // Si c'est un étudiant avec données détaillées
  if (stats.absent !== undefined) {
    onTimeCount = Math.max(0, (stats.total || 1) - lateCount - (stats.absent || 0));
  }
  
  // Évite la division par zéro
  const totalCount = Math.max(1, lateCount + onTimeCount);

  const options = {
    series: [onTimeCount, lateCount],
    chart: {
      type: 'donut',
      height: 320,
      toolbar: { show: false },
      fontFamily: 'Inter, sans-serif'
    },
    labels: ['À l\'heure', 'En retard'],
    colors: ['#12664f', '#a4b0f5'],
    dataLabels: {
      enabled: true,
      formatter: function(val) {
        return Math.round(val) + '%';
      },
      style: {
        colors: ['#f0ebd8'],
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
      width: 3,
      colors: ['#0d1321']
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
        colors: '#a4b0f5',
        fontSize: '12px'
      }
    },
    tooltip: {
      theme: 'dark',
      y: {
        formatter: function(val) {
          const percentage = Math.round((val / totalCount) * 100);
          return val + ' étudiants (' + percentage + '%)';
        }
      }
    }
  };

  const chart = new ApexCharts(chartEl, options);
  chart.render();
}
