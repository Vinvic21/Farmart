import pytest
from flask_jwt_extended import create_access_token

from app import app
from extensions import db
from models import User, Profile


@pytest.fixture
def client():
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI='sqlite:///:memory:')
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def _create_user():
    user = User(email='profile@example.com', role='buyer')
    user.set_password('password123')
    user.profile = Profile(first_name='Jane', last_name='Doe', phone='0712345678', location='Nairobi')
    db.session.add(user)
    db.session.commit()
    return user.id


def _auth_header(user_id):
    with app.app_context():
        token = create_access_token(identity=str(user_id), additional_claims={'role': 'buyer'})
    return {'Authorization': f'Bearer {token}'}


def test_buyer_can_view_and_update_profile(client):
    with app.app_context():
        user_id = _create_user()

    headers = _auth_header(user_id)
    response = client.get('/api/v1/users/profile', headers=headers)
    assert response.status_code == 200
    assert response.get_json()['user']['profile']['first_name'] == 'Jane'

    response = client.patch(
        '/api/v1/users/profile',
        json={'first_name': 'Janet', 'last_name': 'Smith', 'bio': 'Buyer in Nairobi'},
        headers=headers,
    )
    assert response.status_code == 200
    profile = response.get_json()['user']['profile']
    assert profile['first_name'] == 'Janet'
    assert profile['last_name'] == 'Smith'
    assert profile['bio'] == 'Buyer in Nairobi'