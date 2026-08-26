# middleware/auth_middleware.py

from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request
from models import User


def role_required(allowed_roles):
    """
    Decorator to restrict access based on user role
    
    Usage:
        @role_required(['admin', 'farmer'])
        def some_route():
            ...
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                # Verify JWT exists and is valid
                verify_jwt_in_request()
                
                # Get user claims
                claims = get_jwt()
                user_role = claims.get('role', '')
                
                if user_role not in allowed_roles:
                    return jsonify({
                        'success': False,
                        'message': f'Access denied. Required roles: {", ".join(allowed_roles)}'
                    }), 403
                
                # Check if user exists and is active
                user_id = claims.get('sub')
                user = User.query.get(int(user_id))
                
                if not user:
                    return jsonify({
                        'success': False,
                        'message': 'User not found'
                    }), 404
                
                if not user.is_active:
                    return jsonify({
                        'success': False,
                        'message': 'Account is disabled'
                    }), 403
                
                # Pass user to route if needed
                kwargs['current_user'] = user
                
                return fn(*args, **kwargs)
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Authentication error: {str(e)}'
                }), 401
        
        return wrapper
    return decorator


def farmer_required(fn):
    """Decorator for farmer-only routes"""
    return role_required(['farmer'])(fn)


def buyer_required(fn):
    """Decorator for buyer-only routes"""
    return role_required(['buyer'])(fn)


def admin_required(fn):
    """Decorator for admin-only routes"""
    return role_required(['admin'])(fn)


def farmer_or_admin_required(fn):
    """Decorator for farmer or admin routes"""
    return role_required(['farmer', 'admin'])(fn)


def get_current_user():
    """Helper to get current user from JWT"""
    try:
        verify_jwt_in_request()
        claims = get_jwt()
        user_id = claims.get('sub')
        return User.query.get(int(user_id))
    except:
        return None