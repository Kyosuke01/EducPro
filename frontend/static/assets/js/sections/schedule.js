// ============================================
// EMPLOI DU TEMPS — Logique complète
// Grille CSS positionnelle avec heures sur les lignes
// et hauteur des cours proportionnelle à leur durée
// ============================================

// Constantes de la grille
const EDT_START_HOUR = 7;   // Heure de début de la grille (7h)
const EDT_END_HOUR = 20;    // Heure de fin de la grille (20h)
const EDT_CELL_HEIGHT = 64; // Hauteur en px pour 1 heure

// Palette de couleurs par matière (index circulaire)
const EDT_COLORS = [
  { bg: '#eef2ff', border: '#4f46e5', text: '#3730a3', badge: '#e0e7ff', badgeText: '#4338ca' },
  { bg: '#fff7ed', border: '#f97316', text: '#9a3412', badge: '#ffedd5', badgeText: '#c2410c' },
  { bg: '#f0fdf4', border: '#22c55e', text: '#15803d', badge: '#dcfce7', badgeText: '#16a34a' },
  { bg: '#fdf4ff', border: '#a855f7', text: '#7e22ce', badge: '#f3e8ff', badgeText: '#9333ea' },
  { bg: '#fff1f2', border: '#f43f5e', text: '#9f1239', badge: '#ffe4e6', badgeText: '#e11d48' },
  { bg: '#ecfeff', border: '#06b6d4', text: '#155e75', badge: '#cffafe', badgeText: '#0891b2' },
  { bg: '#fefce8', border: '#eab308', text: '#713f12', badge: '#fef9c3', badgeText: '#ca8a04' },
  { bg: '#fff8f0', border: '#fb923c', text: '#9a3412', badge: '#fed7aa', badgeText: '#ea580c' },
];

const _topicColorMap = {};
let _topicColorIndex = 0;

function getTopicColor(topicName) {
  if (!_topicColorMap[topicName]) {
    _topicColorMap[topicName] = EDT_COLORS[_topicColorIndex % EDT_COLORS.length];
    _topicColorIndex++;
  }
  return _topicColorMap[topicName];
}

function getDecimalHour(isoStr) {
  if (!isoStr) return 0;
  const d = new Date(isoStr);
  return d.getHours() + d.getMinutes() / 60;
}

function formatHHMM(isoStr) {
  if (!isoStr) return '--:--';
  const d = new Date(isoStr);
  return d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
}

// ============================================
// MODAL DE DÉTAIL D'UN COURS — créé une seule fois dans le DOM
// ============================================
function openCourseModal(courseJson) {
  const course = JSON.parse(decodeURIComponent(courseJson));
  const color = getTopicColor(course.topic_name);

  const timeLabel = `${formatHHMM(course.start_time)} – ${formatHHMM(course.end_time)}`;
  const teacherName = course.teacher_f_name
    ? `${course.teacher_f_name} ${course.teacher_l_name}`
    : 'Non renseigné';
  const room = course.room_name || 'Salle à définir';
  const className = course.class_name || '';

  const startH = getDecimalHour(course.start_time);
  const endH = getDecimalHour(course.end_time);
  const durationMin = Math.round((endH - startH) * 60);
  const durationLabel = durationMin >= 60
    ? `${Math.floor(durationMin / 60)}h${durationMin % 60 > 0 ? String(durationMin % 60).padStart(2, '0') : ''}`
    : `${durationMin} min`;

  const jsDayNames = ['Dimanche', 'Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi'];
  const dayName = jsDayNames[new Date(course.start_time).getDay()] || '';

  // Créer le modal s'il n'existe pas encore
  if (!document.getElementById('edtCourseModal')) {
    const el = document.createElement('div');
    el.id = 'edtCourseModal';
    el.innerHTML = `
      <div class="edt-modal-backdrop" onclick="closeCourseModal()"></div>
      <div class="edt-modal-card">
        <div id="edtModalAccent" class="edt-modal-accent"></div>
        <div class="edt-modal-header">
          <button class="edt-modal-close" onclick="closeCourseModal()"><i class="ri-close-line"></i></button>
          <div id="edtModalBadge" style="display:inline-flex; align-items:center; font-size:11px; font-weight:700; padding:3px 10px; border-radius:20px; margin-bottom:10px;"></div>
          <div id="edtModalTitle" style="font-size:22px; font-weight:800; color:#f0ebd8; line-height:1.2;"></div>
          <div id="edtModalDay" style="font-size:13px; color:#a4b0f5; margin-top:4px; font-weight:500;"></div>
        </div>
        <div class="edt-modal-body">
          <div class="edt-modal-row">
            <div id="edtModalTimeIcon" class="edt-modal-icon"><i class="ri-time-line"></i></div>
            <div><div class="edt-modal-label">Horaire</div><div id="edtModalTime" class="edt-modal-value"></div></div>
          </div>
          <div class="edt-modal-row">
            <div id="edtModalDurIcon" class="edt-modal-icon"><i class="ri-timer-line"></i></div>
            <div><div class="edt-modal-label">Durée</div><div id="edtModalDuration" class="edt-modal-value"></div></div>
          </div>
          <div class="edt-modal-row">
            <div id="edtModalTeacherIcon" class="edt-modal-icon"><i class="ri-user-3-line"></i></div>
            <div><div class="edt-modal-label">Professeur</div><div id="edtModalTeacher" class="edt-modal-value"></div></div>
          </div>
          <div class="edt-modal-row">
            <div id="edtModalRoomIcon" class="edt-modal-icon"><i class="ri-map-pin-2-line"></i></div>
            <div><div class="edt-modal-label">Salle</div><div id="edtModalRoom" class="edt-modal-value"></div></div>
          </div>
          <div id="edtModalClassRow" class="edt-modal-row">
            <div id="edtModalClassIcon" class="edt-modal-icon"><i class="ri-book-2-line"></i></div>
            <div><div class="edt-modal-label">Classe</div><div id="edtModalClass" class="edt-modal-value"></div></div>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(el);
  }

  const modal = document.getElementById('edtCourseModal');
  modal.style.display = 'flex';

  document.getElementById('edtModalAccent').style.background = color.border;
  document.getElementById('edtModalBadge').style.background = color.badge;
  document.getElementById('edtModalBadge').style.color = color.badgeText;
  document.getElementById('edtModalBadge').textContent = course.topic_name;
  document.getElementById('edtModalTitle').textContent = course.topic_name;
  document.getElementById('edtModalDay').textContent = dayName;
  document.getElementById('edtModalTime').textContent = timeLabel;
  document.getElementById('edtModalDuration').textContent = durationLabel;
  document.getElementById('edtModalTeacher').textContent = teacherName;
  document.getElementById('edtModalRoom').textContent = room;

  ['edtModalTimeIcon', 'edtModalDurIcon', 'edtModalTeacherIcon', 'edtModalRoomIcon', 'edtModalClassIcon'].forEach(id => {
    const el = document.getElementById(id);
    if (el) { el.style.background = color.badge; el.style.color = color.border; }
  });

  const classRow = document.getElementById('edtModalClassRow');
  if (className) {
    document.getElementById('edtModalClass').textContent = className;
    classRow.style.display = 'flex';
  } else {
    classRow.style.display = 'none';
  }

  document.body.style.overflow = 'hidden';
}

function closeCourseModal() {
  const modal = document.getElementById('edtCourseModal');
  if (modal) modal.style.display = 'none';
  document.body.style.overflow = '';
}

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closeCourseModal();
});

// ============================================
// RENDU DE LA GRILLE (CSS positionnelle — logique pure)
// ============================================
function renderScheduleGrid(className, dataList) {
  Object.keys(_topicColorMap).forEach(k => delete _topicColorMap[k]);
  _topicColorIndex = 0;

  const days = [
    { label: 'Lundi',    jsDay: 1 },
    { label: 'Mardi',    jsDay: 2 },
    { label: 'Mercredi', jsDay: 3 },
    { label: 'Jeudi',    jsDay: 4 },
    { label: 'Vendredi', jsDay: 5 },
  ];

  const totalHours = EDT_END_HOUR - EDT_START_HOUR;
  const gridHeight = totalHours * EDT_CELL_HEIGHT;

  const byDay = {};
  days.forEach(d => { byDay[d.jsDay] = []; });
  dataList.forEach(e => {
    const dayIndex = new Date(e.start_time).getDay();
    if (byDay[dayIndex]) byDay[dayIndex].push(e);
  });

  // Labels d'heures
  let hourLabels = '';
  for (let h = EDT_START_HOUR; h <= EDT_END_HOUR; h++) {
    const top = (h - EDT_START_HOUR) * EDT_CELL_HEIGHT;
    hourLabels += `<div class="edt-hour-label" style="top: ${top}px;"><span>${String(h).padStart(2, '0')}:00</span></div>`;
  }

  // Lignes horizontales
  let gridLines = '';
  for (let h = EDT_START_HOUR; h <= EDT_END_HOUR; h++) {
    const top = (h - EDT_START_HOUR) * EDT_CELL_HEIGHT;
    const isEven = (h - EDT_START_HOUR) % 2 === 0;
    gridLines += `<div class="edt-grid-line" style="top: ${top}px; height: 0.5px; background: ${isEven ? 'rgba(164,176,245,0.3)' : 'rgba(45,65,105,0.4)'};"></div>`;
  }

  // Colonnes des jours
  let dayColumns = '';
  days.forEach(({ label, jsDay }) => {
    const courses = byDay[jsDay];
    let courseCards = '';

    courses.forEach(course => {
      const startH = getDecimalHour(course.start_time);
      const endH = getDecimalHour(course.end_time);
      const duration = Math.max(0.5, endH - startH);
      if (startH < EDT_START_HOUR || endH > EDT_END_HOUR + 1) return;

      const topPx = (startH - EDT_START_HOUR) * EDT_CELL_HEIGHT;
      const heightPx = duration * EDT_CELL_HEIGHT - 4;
      const color = getTopicColor(course.topic_name);
      const timeLabel = `${formatHHMM(course.start_time)} – ${formatHHMM(course.end_time)}`;
      const teacherName = course.teacher_f_name ? `${course.teacher_f_name} ${course.teacher_l_name}` : '';
      const room = course.room_name || 'Salle à définir';
      const isShort = duration < 0.75;
      const isMini  = duration < 0.5;
      const courseData = encodeURIComponent(JSON.stringify(course));

      courseCards += `
        <div class="edt-course-card" style="
          top: ${topPx}px;
          height: ${heightPx}px;
          background: ${color.bg};
          border-left: 4px solid ${color.border};
          cursor: pointer;
        " onclick="openCourseModal('${courseData}')" title="Cliquer pour les détails">
          <div class="edt-course-time" style="background:${color.badge}; color:${color.badgeText};">${timeLabel}</div>
          ${!isMini ? `<div class="edt-course-topic" style="color:${color.text};">${course.topic_name}</div>` : ''}
          ${!isShort && teacherName ? `<div class="edt-course-meta" style="color:${color.text};"><i class="ri-user-3-line"></i> ${teacherName}</div>` : ''}
          ${!isShort ? `<div class="edt-course-meta" style="color:${color.text};"><i class="ri-map-pin-2-line"></i> ${room}</div>` : ''}
        </div>
      `;
    });

    dayColumns += `
      <div class="edt-day-column">
        <div class="edt-day-header">${label}</div>
        <div class="edt-day-body" style="height: ${gridHeight}px; position: relative;">
          ${gridLines}
          ${courseCards || '<div class="edt-empty-day"><i class="ri-moon-line"></i></div>'}
        </div>
      </div>
    `;
  });

  return `
    <div class="edt-scroll-outer" style="overflow-x:auto;">
      <div class="edt-wrapper" style="min-width: 780px;">
        <div class="edt-hours-col" style="height: ${gridHeight}px;">${hourLabels}</div>
        <div class="edt-days-container">${dayColumns}</div>
      </div>
    </div>
    ${buildScheduleLegend(dataList)}
  `;
}

function buildScheduleLegend(dataList) {
  const topics = [...new Set(dataList.map(e => e.topic_name).filter(Boolean))].sort();
  if (!topics.length) return '';

  const items = topics.map(topic => {
    const color = getTopicColor(topic);
    return `<div class="edt-legend-item"><div class="edt-legend-dot" style="background:${color.border};"></div>${topic}</div>`;
  }).join('');

  return `<div class="edt-legend">${items}</div>`;
}

// ============================================
// EDT — Admin (toutes les classes)
// ============================================
async function getScheduleContent() {
  return await loadTemplate('schedule');
}

async function initSchedule() {
  const data = await api('edt');
  const edtList = data.edt || [];
  globalThis.scheduleData = edtList;

  const tabsContainer = document.getElementById('scheduleTabs');
  const gridContainer = document.getElementById('scheduleGridContainer');
  const currentClassSpan = document.getElementById('scheduleCurrentClass');

  if (!tabsContainer || !gridContainer) return;

  const uniqueClasses = [...new Set(edtList.map(e => e.class_name))].sort();

  if (uniqueClasses.length === 0) {
    gridContainer.innerHTML = `
      <div class="card shadow-sm border-0 p-5 text-center">
        <i class="ri-calendar-2-line text-muted d-block mb-3" style="font-size: 3rem;"></i>
        <h6 class="text-muted">Aucun emploi du temps disponible</h6>
        <p class="text-sm text-neutral-500">Importez des données via le seed ou l'API.</p>
      </div>`;
    return;
  }

  globalThis.currentClass = uniqueClasses[0];

  tabsContainer.innerHTML = uniqueClasses.map(cls => `
    <button
      id="tab-${cls.replaceAll(/\s+/g, '-')}"
      class="edt-tab-btn ${cls === globalThis.currentClass ? 'edt-tab-btn--active' : ''}"
      onclick="changeScheduleClass('${cls}')">
      ${cls}
    </button>
  `).join('');

  if (currentClassSpan) currentClassSpan.textContent = globalThis.currentClass;
  gridContainer.innerHTML = renderScheduleGrid(globalThis.currentClass, edtList.filter(e => e.class_name === globalThis.currentClass));
}

function changeScheduleClass(cls) {
  globalThis.currentClass = cls;
  document.querySelectorAll('.edt-tab-btn').forEach(btn => btn.classList.remove('edt-tab-btn--active'));
  const activeBtn = document.getElementById(`tab-${cls.replaceAll(/\s+/g, '-')}`);
  if (activeBtn) activeBtn.classList.add('edt-tab-btn--active');
  const titleSpan = document.getElementById('scheduleCurrentClass');
  if (titleSpan) titleSpan.textContent = cls;
  const container = document.getElementById('scheduleGridContainer');
  if (!container) return;
  const filtered = (globalThis.scheduleData || []).filter(e => e.class_name === cls);
  container.innerHTML = renderScheduleGrid(cls, filtered);
}

// ============================================
// MON EDT — Étudiant / Professeur
// ============================================
async function getMyScheduleContent() {
  return await loadTemplate('schedule_my');
}

async function initMySchedule() {
  let data;
  let queryClass = null;

  if (USER.role === 'student') {
    data = await api(`edt/class/${encodeURIComponent(USER.className)}`);
    queryClass = USER.className;
  } else {
    data = await api(`edt/teacher/${encodeURIComponent(USER.lastName)}`);
  }

  const edtList = data.edt || [];
  const container = document.getElementById('myScheduleGridContainer');
  const labelEl = document.getElementById('myScheduleLabel');

  if (!container) return;

  if (edtList.length === 0) {
    container.innerHTML = `
      <div class="card shadow-sm border-0 p-5 text-center">
        <i class="ri-calendar-2-line text-muted d-block mb-3" style="font-size: 3rem;"></i>
        <h6 class="text-muted">Votre emploi du temps est vide</h6>
        <p class="text-sm text-neutral-500">Aucun cours n'a été planifié pour l'instant.</p>
      </div>`;
    return;
  }

  const weekLabel = USER.role === 'student'
    ? `Classe : ${USER.className}`
    : `${USER.firstName} ${USER.lastName} — ${USER.topicName || 'Professeur'}`;

  if (labelEl) labelEl.textContent = weekLabel;
  container.innerHTML = renderScheduleGrid(queryClass, edtList);
}
