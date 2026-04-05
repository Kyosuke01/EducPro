// ============================================
// PROFIL & PARAMÈTRES — 2FA, mot de passe
// ============================================

let current2FASecret = "";
let passwordChangeContext = null;

function setupOtpInputs(containerId) {
  setTimeout(() => {
    const container = document.getElementById(containerId);
    if (!container) return;
    const inputs = container.querySelectorAll('.otp-input');

    inputs.forEach((input, index) => {
      input.addEventListener('input', (e) => {
        if (e.target.value.length === 1 && index < inputs.length - 1) {
          inputs[index + 1].focus();
        }
      });

      input.addEventListener('keydown', (e) => {
        if (e.key === 'Backspace' && !e.target.value && index > 0) {
          inputs[index - 1].focus();
        }
      });

      input.addEventListener('paste', (e) => {
        e.preventDefault();
        const pasteData = e.clipboardData.getData('text').replaceAll(/\D/g, '').slice(0, 6);
        pasteData.split('').forEach((char, i) => {
          if (inputs[i]) {
            inputs[i].value = char;
            if (i < inputs.length - 1) inputs[i + 1].focus();
          }
        });
      });
    });
  }, 100);
}

// ============================================
// Profil
// ============================================
function getMonProfilContent() {
  return loadTemplate('profile');
}

function initMonProfil() {
  const roleText = USER.role === 'admin' ? 'Administrateur' : (USER.role === 'teacher' ? 'Professeur' : 'Étudiant');
  
  const fields = {
    profileLastName: USER.lastName || '-',
    profileFirstName: USER.firstName || '-',
    profileEmail: USER.email || '-',
    profileRole: roleText,
    profileFullName: `${USER.firstName || ''} ${USER.lastName || ''}`.trim() || '--',
    profileRoleBadge: roleText
  };

  for (const [id, val] of Object.entries(fields)) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  }

  // Ajouter les initiales
  const initialsEl = document.getElementById('profileInitials');
  if (initialsEl) {
    const firstName = USER.firstName || '';
    const lastName = USER.lastName || '';
    const initials = (firstName.charAt(0) + lastName.charAt(0)).toUpperCase() || '--';
    initialsEl.textContent = initials;
  }

  // Afficher classe pour les étudiants uniquement
  const classRow = document.getElementById('classRow');
  if (classRow) {
    if (USER.role === 'student') {
      classRow.style.display = 'flex';
      const classEl = document.getElementById('profileClass');
      if (classEl) classEl.textContent = USER.className || '-';
    } else {
      classRow.style.display = 'none';
    }
  }

  // Afficher spécialité pour les professeurs uniquement
  const specialtyRow = document.getElementById('specialtyRow');
  if (specialtyRow) {
    if (USER.role === 'teacher') {
      specialtyRow.style.display = 'flex';
      const specialtyEl = document.getElementById('profileSpecialty');
      if (specialtyEl) specialtyEl.textContent = USER.specialty || '-';
    } else {
      specialtyRow.style.display = 'none';
    }
  }
}

// ============================================
// Paramètres / 2FA
// ============================================
async function getParametresContent() {
  return await loadTemplate('settings');
}

async function initParametres() {
  // Mettre l'état du switch 2FA
  const switchEl = document.getElementById('switch2FA');
  if (switchEl) switchEl.checked = !!USER.has_2fa;

  const setupSection = document.getElementById('setup2FASection');
  if (!setupSection) return;

  if (USER.has_2fa) {
    setupSection.style.display = 'block';
    const content = document.getElementById('setup2FAContent');
    if (content) {
      content.innerHTML = '<div class="alert alert-success mt-1 mb-1"><i class="ri-shield-check-line me-2"></i> L\'A2F a été configurée et sécurise activement ce compte.</div>';
    }
  } else {
    setupSection.style.display = 'none';
  }
}

async function toggle2FASection() {
  const isChecked = document.getElementById('switch2FA').checked;
  const setupSection = document.getElementById('setup2FASection');

  if (isChecked) {
    setupSection.style.display = 'block';
    // Charger le template du formulaire QR
    const content = document.getElementById('setup2FAContent');
    if (content) {
      content.innerHTML = await loadTemplate('settings_2fa_setup');
      setupOtpInputs('dashboard-otp-container');
    }
    try {
      const res = await fetch('/api/auth/2fa/generate?email=' + encodeURIComponent(USER.email || 'user'));
      if (res.ok) {
        const data = await res.json();
        current2FASecret = data.secret;
        document.getElementById('qr-code-img').src = 'https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=' + encodeURIComponent(data.uri);
        document.getElementById('manual-key-text').innerHTML = '<strong>' + data.secret + '</strong>';
        document.getElementById('manual-key-text').style.filter = 'blur(5px)';
      } else {
        alert('Erreur lors de la génération du code 2FA.');
      }
    } catch (e) {
      console.error(e);
    }
  } else {
    if (USER.has_2fa) {
      try {
        const res = await fetch('/api/auth/2fa/disable', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: USER.id, role: USER.role })
        });
        if (res.ok) {
          USER.has_2fa = false;
          // Synchroniser la session Flask
          await fetch('/session/sync-2fa', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ has_2fa: false })
          });
          // Recharger la vue paramètres
          const contentArea = document.getElementById('contentArea');
          contentArea.innerHTML = await getParametresContent();
          await initParametres();
        } else {
          document.getElementById('switch2FA').checked = true;
        }
      } catch (e) {
        document.getElementById('switch2FA').checked = true;
      }
    } else {
      setupSection.style.display = 'none';
      current2FASecret = "";
    }
  }
}

function showNotice(type, message) {
  const box = document.getElementById('param-alert');
  if (!box) return;
  if (type === 'success') { box.style.display = 'none'; return; }
  const classes = type === 'error'
    ? 'alert alert-danger d-flex align-items-center gap-2 mb-3'
    : 'alert alert-warning d-flex align-items-center gap-2 mb-3';
  box.className = classes;
  box.innerHTML = `<i class="ri-information-line"></i><span>${message}</span>`;
  box.style.display = 'flex';
}

function openPassword2FAModal(payload, formRef) {
  passwordChangeContext = { payload, formRef };
  const modal = document.getElementById('password2faModal');
  if (!modal) return;
  modal.style.display = 'flex';
  const input = modal.querySelector('input[name="password2faCode"]');
  if (input) { input.value = ''; setTimeout(() => input.focus(), 50); }
}

function closePassword2FAModal(reset = false) {
  const modal = document.getElementById('password2faModal');
  if (modal) modal.style.display = 'none';
  if (reset) passwordChangeContext = null;
}

async function submitPasswordChange(payload, code, formRef) {
  try {
    const res = await fetch('/api/users/change-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...payload, code: code || undefined })
    });
    if (res.ok) {
      showNotice('warning', 'Mot de passe mis à jour.');
      formRef?.reset?.();
      closePassword2FAModal(true);
    } else {
      const err = await res.json();
      showNotice('error', err.error || 'Erreur lors de la mise à jour.');
    }
  } catch (ex) {
    showNotice('error', 'Erreur serveur.');
  }
}

function confirmPasswordChangeWithCode() {
  const modal = document.getElementById('password2faModal');
  if (!modal || !passwordChangeContext) return;
  const input = modal.querySelector('input[name="password2faCode"]');
  const code = (input?.value || '').trim();
  if (code.length !== 6) {
    input?.focus();
    return showNotice('warning', 'Veuillez saisir un code à 6 chiffres.');
  }
  submitPasswordChange(passwordChangeContext.payload, code, passwordChangeContext.formRef);
}

async function validate2FA() {
  const inputs = document.querySelectorAll('#dashboard-otp-container .otp-input');
  const code = Array.from(inputs).map(i => i.value).join('');
  if (code.length === 6) {
    try {
      const res = await fetch('/api/auth/2fa/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: USER.id, role: USER.role, secret: current2FASecret, code })
      });
      if (res.ok) {
        USER.has_2fa = true;
        // Synchroniser la session Flask
        await fetch('/session/sync-2fa', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ has_2fa: true })
        });
        const contentArea = document.getElementById('contentArea');
        contentArea.innerHTML = await getParametresContent();
        await initParametres();
      } else {
        let errText = '';
        try {
          const ctype = res.headers.get('content-type') || '';
          if (ctype.includes('application/json')) {
            const err = await res.json();
            errText = err?.error || JSON.stringify(err);
          } else {
            errText = await res.text();
          }
        } catch { errText = 'Réponse non lisible'; }
        showNotice('error', errText || 'Erreur inattendue');
      }
    } catch (e) {
      showNotice('error', 'Erreur réseau ou serveur.');
    }
  } else {
    showNotice('warning', 'Veuillez entrer un code à 6 chiffres.');
  }
}

async function changePassword(e) {
  e.preventDefault();
  const form = e.target;
  const pwdInputs = form.querySelectorAll('input[type="password"]');
  const old_password = pwdInputs[0]?.value || '';
  const new_password = pwdInputs[1]?.value || '';
  if (new_password.length < 6) return showNotice('warning', 'Le nouveau mot de passe est trop court.');
  const payload = { user_id: USER.id, role: USER.role, old_password, new_password };
  if (USER.has_2fa) { openPassword2FAModal(payload, form); return; }
  submitPasswordChange(payload, null, form);
}
