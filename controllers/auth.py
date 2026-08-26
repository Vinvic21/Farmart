# controllers/auth.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
)
from marshmallow import ValidationError

from extensions import db, jwt
from models import User, Profile, Cart
from schemas import (
    UserRegisterSchema,
    UserLoginSchema,
    UserResponseSchema,
)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')


@jwt.additional_claims_loader
def add_claims_to_access_token(identity):
    """Add user role and email to JWT claims."""
    user = db.session.get(User, int(identity))
    if user:
        return {
            'role': user.role,
            'email': user.email,
        }
    return {}


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    data = request.get_json(silent=True) or {}

    schema = UserRegisterSchema()
    try:
        validated_data = schema.load(data)
    except ValidationError as err:
        return jsonify({
            'success': False,
            'errors': err.messages,
            'message': 'Validation error'
        }), 400

    email = validated_data['email'].lower().strip()
    if User.query.filter_by(email=email).first():
        return jsonify({
            'success': False,
            'message': 'Email already registered. Please login.'
        }), 409

    user = User(email=email, role=validated_data.get('role', 'buyer'))
    user.password = validated_data['password']

    profile = Profile(
        phone=validated_data.get('phone'),
        location=validated_data.get('location'),
        verification_status='pending'
    )
    user.profile = profile

    if user.role == 'buyer':
        user.cart = Cart()

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Database error: {str(exc)}'
        }), 500

    response_schema = UserResponseSchema()
    return jsonify({
        'success': True,
        'message': 'User registered successfully',
        'user': response_schema.dump(user)
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login a user and return JWT tokens."""
    data = request.get_json(silent=True) or {}

    schema = UserLoginSchema()
    try:
        validated_data = schema.load(data)
    except ValidationError as err:
        return jsonify({
            'success': False,
            'errors': err.messages,
            'message': 'Validation error'
        }), 400

    email = validated_data['email'].lower().strip()
    user = User.query.filter_by(email=email).first()

    if not user or not user.verify_password(validated_data['password']):
        return jsonify({
            'success': False,
            'message': 'Invalid email or password'
        }), 401

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={'role': user.role, 'email': user.email}
    )
    refresh_token = create_refresh_token(
        identity=str(user.id),
        additional_claims={'role': user.role, 'email': user.email}
    )

    response_schema = UserResponseSchema()
    return jsonify({
        'success': True,
        'message': 'Login successful',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': response_schema.dump(user)
    }), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    """Create a new access token from a refresh token."""
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))

    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        }), 404

    access_token = create_access_token(
        identity=user_id,
        additional_claims={'role': user.role, 'email': user.email}
    )

    return jsonify({
        'success': True,
        'message': 'Token refreshed successfully',
        'access_token': access_token
    }), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Return the authenticated user profile."""
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))

    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        }), 404

    response_schema = UserResponseSchema()
    return jsonify({
        'success': True,
        'user': response_schema.dump(user)
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Client-side logout endpoint."""
    return jsonify({
        'success': True,
        'message': 'Logout successful. Please remove tokens on client side.'
    }), 200


@auth_bp.route('/verify-token', methods=['GET'])
@jwt_required()
def verify_token():
    """Validate the current token pair and claims."""
    user_id = get_jwt_identity()
    claims = get_jwt()

    return jsonify({
        'success': True,
        'valid': True,
        'user_id': user_id,
        'role': claims.get('role'),
        'email': claims.get('email')
    }), 200