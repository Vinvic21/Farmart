from flask import Blueprint, request, jsonify
from flask_jwt_extended import (create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt,
)

from extensions import db, jwt
from models import User, Profile, Cart
from schemas import user_schema

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')


@jwt.additional_claims_loader
def add_claims_to_access_token(identity):
    #.........................................
    # Add user role and email to JWT claims.
    user = db.session.get(User, int(identity))
    if user:
        return {'role': user.role, 'email': user.email}
    return {}


@auth_bp.route('/register', methods=['POST'])
def register():
    #.........................................
    data = request.get_json(silent=True) or {}

    email = (data.get('email') or '').strip().lower()
    password = data.get('password')
    confirm_password = data.get('confirm_password')
    role = data.get('role', 'buyer')

    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password are required'}), 400

    if confirm_password is not None and password != confirm_password:
        return jsonify({'success': False, 'message': 'Passwords do not match'}), 400

    if role not in ('farmer', 'buyer'):
        return jsonify({'success': False, 'message': 'Role must be either farmer or buyer'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Email already registered. Please login.'}), 409

    user = User(email=email, role=role)
    user.password = password
    user.profile = Profile(
        phone=data.get('phone'),
        location=data.get('location'),
        verification_status='pending',
    )

    if user.role == 'buyer':
        user.cart = Cart()

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Database error: {str(exc)}'}), 500

    return jsonify({
        'success': True,
        'message': 'User registered successfully',
        'user': user_schema.dump(user),
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    #.........................................
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password')

    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password are required'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.verify_password(password):
        return jsonify({'success': False, 'message': 'Invalid email or password'}), 401

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={'role': user.role, 'email': user.email},
    )
    refresh_token = create_refresh_token(
        identity=str(user.id),
        additional_claims={'role': user.role, 'email': user.email},
    )

    return jsonify({
        'success': True,
        'message': 'Login successful',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user_schema.dump(user),
    }), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    #.........................................
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))

    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    access_token = create_access_token(
        identity=user_id,
        additional_claims={'role': user.role, 'email': user.email},
    )

    return jsonify({'success': True, 'message': 'Token refreshed successfully', 'access_token': access_token}), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    #.........................................
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))

    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    return jsonify({'success': True, 'user': user_schema.dump(user)}), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    #.........................................
    return jsonify({'success': True, 'message': 'Logout successful. Please remove tokens on client side.'}), 200


@auth_bp.route('/verify-token', methods=['GET'])
@jwt_required()
def verify_token():
    #.........................................
    user_id = get_jwt_identity()
    claims = get_jwt()

    return jsonify({
        'success': True,
        'valid': True,
        'user_id': user_id,
        'role': claims.get('role'),
        'email': claims.get('email'),
    }), 200