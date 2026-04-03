// ============================================
// TEMPLATES.JS — Helper de chargement de templates HTML statiques
// ============================================

const _templateCache = {};

/**
 * Charge un template HTML depuis /static/templates/sections/{name}.html
 * Met en cache le résultat pour éviter des fetches répétés.
 * @param {string} name - Nom du fichier sans extension
 * @returns {Promise<string>} Le contenu HTML du template
 */
async function loadTemplate(name) {
  if (_templateCache[name]) return _templateCache[name];
  const res = await fetch(`/static/templates/sections/${name}.html`);
  if (!res.ok) throw new Error(`Template "${name}" introuvable (${res.status})`);
  const html = await res.text();
  _templateCache[name] = html;
  return html;
}
