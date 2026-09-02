from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import User, Profile, Animal
from schemas import user_schema, animals_schema


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


@users_bp.route('/<int:user_id>', methods=['GET'])
def get_public_profile(user_id):
    #.........................................
    # Public, read-only "view profile" endpoint — no login required, since
    # a buyer should be able to check a farmer's contact details/
    # verification before deciding to register or buy. Hand-built (not
    # user_schema) so email/password_hash can never leak here — only what
    # a buyer should be able to see.
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    profile = user.profile
    first = (getattr(profile, 'first_name', None) or '').strip()
    last = (getattr(profile, 'last_name', None) or '').strip()
    full_name = f"{first} {last}".strip() or None

    public_user = {
        'id': user.id,
        'name': full_name,
        'role': user.role,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'profile': {
            'phone': profile.phone if profile else None,
            'location': profile.location if profile else None,
            'bio': profile.bio if profile else None,
            'verification_status': profile.verification_status if profile else 'pending',
        },
    }

    # Bonus: if this is a farmer, show their other active listings so a
    # buyer viewing the profile can browse more from them.
    listings = []
    if user.role == 'farmer':
        animals = (
            Animal.query.filter_by(farmer_id=user.id, status='available')
            .order_by(Animal.id.desc())
            .limit(12)
            .all()
        )
        listings = animals_schema.dump(animals)

    return jsonify({'success': True, 'user': public_user, 'listings': listings}), 200