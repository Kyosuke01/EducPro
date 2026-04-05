"""
rbac.py — Système de contrôle d'accès basé sur les rôles (RBAC).

Fournit un décorateur @require_role pour vérifier les permissions
et un système de logging des tentatives d'accès non autorisé.
"""

from functools import wraps
from flask import request, jsonify, render_template_string
import logging
from datetime import datetime

# Configuration du logging pour les tentatives d'accès non autorisé
security_logger = logging.getLogger('security_audit')
security_handler = logging.FileHandler('security_audit.log')
security_handler.setFormatter(logging.Formatter(
    '[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))
security_logger.addHandler(security_handler)
security_logger.setLevel(logging.WARNING)


def get_user_role_from_request():
    """Extrait le rôle utilisateur de la requête (depuis les headers ou la session)."""
    # Le rôle devrait être passé dans les headers personnalisés après authentification
    # Format: "X-User-Role: student|teacher|admin"
    role = request.headers.get('X-User-Role', '').lower()
    return role if role in ['student', 'teacher', 'admin'] else None


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
                # Logging de la tentative d'accès non autorisé
                security_logger.warning(
                    f"403 FORBIDDEN - User ID: {user_id} | Role: {user_role} | "
                    f"Required: {allowed_roles} | Path: {request.path} | "
                    f"Method: {request.method} | IP: {request.remote_addr}"
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
