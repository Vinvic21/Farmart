from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import User, Profile
from schemas import user_schema


users_bp = Blueprint('users', __name__, url_prefix='/api/v1/users')


def _current_user():
    return db.session.get(User, int(get_jwt_identity()))


@users_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user = _current_user()
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    return jsonify({'success': True, 'user': user_schema.dump(user)}), 200


@users_bp.route('/profile', methods=['PATCH'])
@jwt_required()
def update_profile():
    user = _current_user()
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    data = request.get_json(silent=True) or {}
    profile = user.profile or Profile(user_id=user.id)
    allowed_fields = ('first_name', 'last_name', 'phone', 'location', 'bio')

    for field in allowed_fields:
        if field in data:
            setattr(profile, field, data[field])

    user.profile = profile
    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Database error: {exc}'}), 500

    return jsonify({'success': True, 'message': 'Profile updated successfully', 'user': user_schema.dump(user)}), 200