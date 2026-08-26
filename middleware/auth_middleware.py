# middleware/auth_middleware.py

from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from extensions import db
from models import User


def _normalize_roles(allowed_roles):
    if isinstance(allowed_roles, str):
        return {allowed_roles}
    return set(allowed_roles)


def role_required(allowed_roles):
    """Restrict access based on the authenticated user's role."""
    required_roles = _normalize_roles(allowed_roles)

    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            user_role = claims.get('role')

            if user_role not in required_roles:
                return jsonify({
                    'success': False,
                    'message': f'Access denied. Required roles: {", ".join(sorted(required_roles))}'
                }), 403

            user_id = get_jwt_identity()
            user = db.session.get(User, int(user_id)) if user_id is not None else None

            if not user:
                return jsonify({
                    'success': False,
                    'message': 'User not found'
                }), 404

            kwargs['current_user'] = user
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def farmer_required(fn):
    """Decorator for farmer-only routes."""
    return role_required(['farmer'])(fn)


def buyer_required(fn):
    """Decorator for buyer-only routes."""
    return role_required(['buyer'])(fn)


def admin_required(fn):
    """Decorator for admin-only routes."""
    return role_required(['admin'])(fn)


def farmer_or_admin_required(fn):
    """Decorator for farmer or admin routes."""
    return role_required(['farmer', 'admin'])(fn)


def get_current_user():
    """Get the current user from the JWT identity."""
    try:
        user_id = get_jwt_identity()
        if not user_id:
            return None
        return db.session.get(User, int(user_id))
    except Exception:
        return None