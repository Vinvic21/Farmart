

from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request
from flask_jwt_extended.exceptions import NoAuthorizationError
from jwt.exceptions import PyJWTError


def role_required(*allowed_roles):
    
    if not allowed_roles:
        raise ValueError("role_required() needs at least one allowed role")

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                verify_jwt_in_request()
            except (NoAuthorizationError, PyJWTError):
                return jsonify(error="Missing or invalid authentication token"), 401

            claims = get_jwt()
            role = claims.get("role")

            if role not in allowed_roles:
                return jsonify(error="You do not have permission to perform this action"), 403

            return fn(*args, **kwargs)

        return wrapper

    return decorator