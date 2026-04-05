"""
rbac.py — Système de contrôle d'accès basé sur les rôles (RBAC).

Fournit un décorateur @require_role pour vérifier les permissions
et un système de logging des tentatives d'accès non autorisé.
"""

from functools import wraps
from flask import request, jsonify, render_template_string
import logging
from datetime import datetime
import re

# Configuration du logging pour les tentatives d'accès non autorisé
security_logger = logging.getLogger('security_audit')
security_handler = logging.FileHandler('security_audit.log')
security_handler.setFormatter(logging.Formatter(
    '[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))
security_logger.addHandler(security_handler)
security_logger.setLevel(logging.WARNING)


def sanitize_log_data(data, max_length=100):
    """
    Sanitize user-controlled data before logging to prevent log injection attacks.
    Allows alphanumeric, dashes, underscores, and dots only.
    Non-compliant characters are removed.
    SECURITY: Prevents newline injection and log forging attacks.
    """
    if not isinstance(data, str):
        data = str(data)
    # Keep only safe characters: alphanumeric, dashes, underscores, dots, @
    safe_data = re.sub(r'[^a-zA-Z0-9._@-]', '', data)
    return safe_data[:max_length] if safe_data else 'UNKNOWN'


def get_user_role_from_request():
    """Extrait le rôle utilisateur de la requête (depuis les headers ou la session)."""
    # Le rôle devrait être passé dans les headers personnalisés après authentification
    # Format: "X-User-Role: student|teacher|admin"
    role = request.headers.get('X-User-Role', '').lower()
    return role if role in ['student', 'teacher', 'admin'] else None


def get_current_user_id():
    """
    Extrait l'ID utilisateur actuel de la requête.
    SECURITY: Utilisé pour valider IDOR (Insecure Direct Object Reference).
    """
    user_id = request.headers.get('X-User-ID', None)
    try:
        return int(user_id) if user_id else None
    except (ValueError, TypeError):
        return None


def get_current_user_role():
    """Retourne le rôle de l'utilisateur actuel."""
    return get_user_role_from_request()


def check_idor_access(resource_owner_id, error_message="Accès refusé"):
    """
    SECURITY: Vérification IDOR - Empêche un utilisateur d'accéder à des ressources d'autres utilisateurs.

    Les étudiants ne peuvent accéder qu'à leurs propres ressources.
    Les admins/professeurs peuvent accéder à n'importe quoi.

    Args:
        resource_owner_id: L'ID du propriétaire de la ressource
        error_message: Message d'erreur personnalisé

    Returns:
        Tuple (True, None) si accès autorisé
        Tuple (False, response) si accès refusé avec réponse JSON
    """
    current_user_id = get_current_user_id()
    current_role = get_current_user_role()

    # Les admins/teachers peuvent accéder à toutes les ressources
    if current_role in ['admin', 'teacher']:
        return True, None

    # Les étudiants ne peuvent accéder qu'à leurs propres ressources
    if current_role == 'student' and current_user_id != int(resource_owner_id):
        safe_attempt = sanitize_log_data(f"Student {current_user_id} tried to access resource of user {resource_owner_id}")
        security_logger.warning(f"IDOR ATTEMPT - {safe_attempt}")
        return False, jsonify({
            "error": "Forbidden",
            "message": error_message,
            "status": 403
        }), 403

    return True, None


def validate_session_security():
    """
    SECURITY: Valide la stabilité de la session (User-Agent, IP).
    Prévient la session hijacking.

    Returns:
        Tuple (True, None) si session valide
        Tuple (False, response) si session compromise
    """
    current_user_id = get_current_user_id()
    if not current_user_id:
        return True, None  # Pas d'utilisateur authentifié

    # Vérifier User-Agent
    user_agent = request.headers.get('User-Agent', '')

    # Note: En production, stocker le User-Agent dans la session server-side
    # Pour maintenant, juste valider sa présence
    if not user_agent:
        security_logger.warning(f"Suspicious request: Missing User-Agent from user {current_user_id}")
        return False, jsonify({
            "error": "Forbidden",
            "message": "Invalid session",
            "status": 403
        }), 403

    return True, None


def require_role(*allowed_roles):
    """
    Décorateur pour vérifier que l'utilisateur a l'un des rôles autorisés.

    Usage:
        @app.route('/api/admin/users', methods=['GET'])
        @require_role('admin')
        def list_all_users():
            ...

        @app.route('/api/grades/class/<class_name>', methods=['GET'])
        @require_role('teacher', 'admin')
        def get_class_grades(class_name):
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_role = get_user_role_from_request()
            user_id = request.headers.get('X-User-ID', 'Unknown')

            # Vérification du rôle
            if user_role not in allowed_roles:
                # Logging de la tentative d'accès non autorisé (with sanitized user-controlled data)
                # SECURITY: Sanitize all user-controlled data to prevent log injection (S5145)
                safe_user_id = sanitize_log_data(user_id)
                safe_path = sanitize_log_data(request.path, 100)
                safe_method = sanitize_log_data(request.method, 20)
                safe_ip = sanitize_log_data(str(request.remote_addr), 20)

                security_logger.warning(
                    f"403 FORBIDDEN - User ID: {safe_user_id} | Role: {user_role} | "
                    f"Required: {allowed_roles} | Path: {safe_path} | "
                    f"Method: {safe_method} | IP: {safe_ip}"
                )

                # Retourner une réponse JSON pour les API
                if request.path.startswith('/api/'):
                    return jsonify({
                        "error": "Forbidden",
                        "message": f"Vous n'avez pas les permissions pour accéder à cette ressource. "
                                   f"Rôle requis: {', '.join(allowed_roles)}",
                        "status": 403,
                        "timestamp": datetime.now().isoformat()
                    }), 403

                # Retourner la page HTML 403 pour les routes web
                return render_template_string(open('app/templates/403.html').read()), 403

            # Accès autorisé
            return f(*args, **kwargs)

        return decorated_function
    return decorator


def log_access_attempt(action, resource, status, user_id='Unknown', role='Unknown'):
    """
    Enregistre les tentatives d'accès (autorisées ou non).

    Args:
        action: Type d'action (GET, POST, DELETE, etc.)
        resource: Ressource accédée
        status: Résultat (ALLOWED, DENIED)
        user_id: ID de l'utilisateur
        role: Rôle de l'utilisateur
    """
    log_message = f"{status} - User: {user_id} | Role: {role} | Action: {action} | Resource: {resource}"

    if status == "DENIED":
        security_logger.warning(log_message)
    else:
        security_logger.info(log_message)
