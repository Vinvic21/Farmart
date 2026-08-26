import pytest
from app import app
from extensions import db
from models import User, Animal


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()


def _create_farmer_and_animal(status="available"):
    farmer = User(email=f"farmer_{status}@test.com", role="farmer")
    farmer.set_password("password123")
    db.session.add(farmer)
    db.session.flush()

    animal = Animal(
        farmer_id=farmer.id,
        type="Cow",
        breed="Friesian",
        age=3,
        price=1200.0,
        status=status,
        description="Healthy dairy cow",
    )
    db.session.add(animal)
    db.session.commit()
    return animal


def test_get_animals_empty(client):
    response = client.get("/api/v1/animals")
    assert response.status_code == 200
    data = response.get_json()
    assert data["animals"] == []
    assert data["total"] == 0


def test_get_animals_returns_available_only(client):
    with app.app_context():
        _create_farmer_and_animal(status="available")
        _create_farmer_and_animal(status="sold")

    response = client.get("/api/v1/animals")
    assert response.status_code == 200
    data = response.get_json()
    assert data["total"] == 1
    assert data["animals"][0]["status"] == "available"


def test_get_animal_by_id(client):
    with app.app_context():
        animal = _create_farmer_and_animal()
        animal_id = animal.id

    response = client.get(f"/api/v1/animals/{animal_id}")
    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == animal_id
    assert data["breed"] == "Friesian"


def test_get_animal_not_found(client):
    response = client.get("/api/v1/animals/9999")
    assert response.status_code == 404