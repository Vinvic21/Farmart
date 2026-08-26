import pytest

from app import app
from extensions import db
from middleware.auth_middleware import role_required


@app.route('/api/v1/test/protected-farmer', methods=['GET'])
@role_required(['farmer'])
def protected_farmer_route():
    return {'success': True, 'message': 'farmer access ok'}


@pytest.fixture
def client():
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        JWT_SECRET_KEY='test-secret-key-for-auth-suite-1234567890'
    )

    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def test_register_login_and_refresh(client):
    payload = {
        'email': 'farmer.auth@example.com',
        'password': 'secret123',
        'confirm_password': 'secret123',
        'role': 'farmer',
        'phone': '1234567890',
        'location': 'Nairobi'
    }

    response = client.post('/api/v1/auth/register', json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] is True
    assert data['user']['email'] == payload['email']
    assert 'password_hash' not in data['user']

    login = client.post('/api/v1/auth/login', json={
        'email': payload['email'],
        'password': payload['password']
    })
    assert login.status_code == 200
    login_data = login.get_json()
    assert login_data['success'] is True
    assert login_data['user']['role'] == 'farmer'
    assert 'access_token' in login_data and 'refresh_token' in login_data

    me = client.get(
        '/api/v1/auth/me',
        headers={'Authorization': f"Bearer {login_data['access_token']}"}
    )
    assert me.status_code == 200
    assert me.get_json()['user']['email'] == payload['email']

    refreshed = client.post(
        '/api/v1/auth/refresh',
        headers={'Authorization': f"Bearer {login_data['refresh_token']}"}
    )
    assert refreshed.status_code == 200
    assert 'access_token' in refreshed.get_json()


def test_register_rejects_duplicate_email(client):
    payload = {
        'email': 'buyer.auth@example.com',
        'password': 'secret123',
        'confirm_password': 'secret123',
        'role': 'buyer'
    }

    first = client.post('/api/v1/auth/register', json=payload)
    second = client.post('/api/v1/auth/register', json=payload)

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.get_json()['message'] == 'Email already registered. Please login.'


def test_login_rejects_bad_credentials(client):
    client.post('/api/v1/auth/register', json={
        'email': 'bad.credentials@example.com',
        'password': 'secret123',
        'confirm_password': 'secret123',
        'role': 'buyer'
    })

    response = client.post('/api/v1/auth/login', json={
        'email': 'bad.credentials@example.com',
        'password': 'wrong-password'
    })

    assert response.status_code == 401
    assert response.get_json()['success'] is False


def test_role_required_blocks_non_matching_role(client):
    buyer_payload = {
        'email': 'buyer.role.test@example.com',
        'password': 'secret123',
        'confirm_password': 'secret123',
        'role': 'buyer'
    }

    client.post('/api/v1/auth/register', json=buyer_payload)
    login = client.post('/api/v1/auth/login', json={
        'email': buyer_payload['email'],
        'password': buyer_payload['password']
    })
    token = login.get_json()['access_token']

    response = client.get(
        '/api/v1/test/protected-farmer',
        headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == 403
    assert response.get_json()['success'] is False
