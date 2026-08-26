import pytest
from flask_jwt_extended import create_access_token

from app import app
from extensions import db
from models import User, Animal, Cart, CartItem


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()


def _create_buyer(email="buyer@test.com"):
    buyer = User(email=email, role="buyer")
    buyer.set_password("password123")
    db.session.add(buyer)
    db.session.commit()
    return buyer


def _create_farmer_and_animal(status="available", price=1200.0, email="farmer@test.com"):
    farmer = User(email=email, role="farmer")
    farmer.set_password("password123")
    db.session.add(farmer)
    db.session.flush()

    animal = Animal(
        farmer_id=farmer.id,
        type="Cow",
        breed="Friesian",
        age=3,
        price=price,
        status=status,
        description="Healthy dairy cow",
    )
    db.session.add(animal)
    db.session.commit()
    return animal


def _auth_header(buyer_id):
    """Build a real JWT for the given user id, matching how login issues tokens."""
    with app.app_context():
        token = create_access_token(identity=str(buyer_id), additional_claims={"role": "buyer"})
    return {"Authorization": f"Bearer {token}"}


# ---------- GET /api/v1/cart ----------

def test_get_cart_requires_auth(client):
    response = client.get("/api/v1/cart")
    assert response.status_code == 401


def test_get_cart_creates_empty_cart_for_new_buyer(client):
    with app.app_context():
        buyer_id = _create_buyer().id

    response = client.get("/api/v1/cart", headers=_auth_header(buyer_id))
    assert response.status_code == 200
    data = response.get_json()
    assert data["buyer_id"] == buyer_id
    assert data["items"] == []

    with app.app_context():
        assert Cart.query.filter_by(buyer_id=buyer_id).count() == 1


def test_get_cart_is_idempotent(client):
    with app.app_context():
        buyer_id = _create_buyer().id
    headers = _auth_header(buyer_id)

    client.get("/api/v1/cart", headers=headers)
    client.get("/api/v1/cart", headers=headers)

    with app.app_context():
        assert Cart.query.filter_by(buyer_id=buyer_id).count() == 1


# ---------- POST /api/v1/cart/items ----------

def test_add_item_to_cart(client):
    with app.app_context():
        buyer_id = _create_buyer().id
        animal_id = _create_farmer_and_animal().id
    headers = _auth_header(buyer_id)

    response = client.post(
        "/api/v1/cart/items",
        json={"animal_id": animal_id, "quantity": 2},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["animal_id"] == animal_id
    assert data["quantity"] == 2


def test_add_item_defaults_quantity_to_one(client):
    with app.app_context():
        buyer_id = _create_buyer().id
        animal_id = _create_farmer_and_animal().id
    headers = _auth_header(buyer_id)

    response = client.post(
        "/api/v1/cart/items", json={"animal_id": animal_id}, headers=headers
    )
    assert response.status_code == 201
    assert response.get_json()["quantity"] == 1


def test_add_item_missing_fields(client):
    with app.app_context():
        buyer_id = _create_buyer().id
    headers = _auth_header(buyer_id)

    response = client.post("/api/v1/cart/items", json={}, headers=headers)
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_add_item_animal_not_found(client):
    with app.app_context():
        buyer_id = _create_buyer().id
    headers = _auth_header(buyer_id)

    response = client.post(
        "/api/v1/cart/items", json={"animal_id": 9999, "quantity": 1}, headers=headers
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "Animal not found"


def test_add_item_animal_not_available(client):
    with app.app_context():
        buyer_id = _create_buyer().id
        animal_id = _create_farmer_and_animal(status="sold").id
    headers = _auth_header(buyer_id)

    response = client.post(
        "/api/v1/cart/items", json={"animal_id": animal_id, "quantity": 1}, headers=headers
    )
    assert response.status_code == 400
    assert "not available" in response.get_json()["error"]


def test_add_existing_item_increments_quantity(client):
    with app.app_context():
        buyer_id = _create_buyer().id
        animal_id = _create_farmer_and_animal().id
    headers = _auth_header(buyer_id)

    client.post("/api/v1/cart/items", json={"animal_id": animal_id, "quantity": 1}, headers=headers)
    response = client.post(
        "/api/v1/cart/items", json={"animal_id": animal_id, "quantity": 2}, headers=headers
    )
    assert response.status_code == 201
    assert response.get_json()["quantity"] == 3

    with app.app_context():
        assert CartItem.query.filter_by(animal_id=animal_id).count() == 1


# ---------- PATCH /api/v1/cart/items/<id> ----------

def test_update_cart_item_quantity(client):
    with app.app_context():
        buyer_id = _create_buyer().id
        animal_id = _create_farmer_and_animal().id
    headers = _auth_header(buyer_id)
    add = client.post("/api/v1/cart/items", json={"animal_id": animal_id, "quantity": 1}, headers=headers)
    item_id = add.get_json()["id"]

    response = client.patch(
        f"/api/v1/cart/items/{item_id}", json={"quantity": 5}, headers=headers
    )
    assert response.status_code == 200
    assert response.get_json()["quantity"] == 5


def test_update_cart_item_missing_fields(client):
    with app.app_context():
        buyer_id = _create_buyer().id
    headers = _auth_header(buyer_id)

    response = client.patch("/api/v1/cart/items/1", json={}, headers=headers)
    assert response.status_code == 400


def test_update_cart_item_quantity_below_one(client):
    with app.app_context():
        buyer_id = _create_buyer().id
        animal_id = _create_farmer_and_animal().id
    headers = _auth_header(buyer_id)
    add = client.post("/api/v1/cart/items", json={"animal_id": animal_id, "quantity": 1}, headers=headers)
    item_id = add.get_json()["id"]

    response = client.patch(
        f"/api/v1/cart/items/{item_id}", json={"quantity": 0}, headers=headers
    )
    assert response.status_code == 400
    # KNOWN BUG (unchanged behaviour): quantity=0 is falsy, so `not quantity` -> "quantity is required"
    assert response.get_json()["error"] == "quantity is required"


def test_update_cart_item_not_found(client):
    with app.app_context():
        buyer_id = _create_buyer().id
    headers = _auth_header(buyer_id)

    response = client.patch(
        "/api/v1/cart/items/9999", json={"quantity": 2}, headers=headers
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "Cart item not found"


def test_update_cart_item_wrong_owner(client):
    with app.app_context():
        buyer_id = _create_buyer(email="buyer1@test.com").id
        other_buyer_id = _create_buyer(email="buyer2@test.com").id
        animal_id = _create_farmer_and_animal().id
    add = client.post(
        "/api/v1/cart/items", json={"animal_id": animal_id, "quantity": 1}, headers=_auth_header(buyer_id)
    )
    item_id = add.get_json()["id"]

    response = client.patch(
        f"/api/v1/cart/items/{item_id}", json={"quantity": 3}, headers=_auth_header(other_buyer_id)
    )
    assert response.status_code == 400
    assert "Not authorized" in response.get_json()["error"]


# ---------- DELETE /api/v1/cart/items/<id> ----------

def test_delete_cart_item(client):
    with app.app_context():
        buyer_id = _create_buyer().id
        animal_id = _create_farmer_and_animal().id
    headers = _auth_header(buyer_id)
    add = client.post("/api/v1/cart/items", json={"animal_id": animal_id, "quantity": 1}, headers=headers)
    item_id = add.get_json()["id"]

    response = client.delete(f"/api/v1/cart/items/{item_id}", headers=headers)
    assert response.status_code == 200
    assert response.get_json()["message"] == "Item removed from cart"

    with app.app_context():
        assert CartItem.query.get(item_id) is None


def test_delete_cart_item_requires_auth(client):
    response = client.delete("/api/v1/cart/items/1")
    assert response.status_code == 401


def test_delete_cart_item_not_found(client):
    with app.app_context():
        buyer_id = _create_buyer().id
    headers = _auth_header(buyer_id)

    response = client.delete("/api/v1/cart/items/9999", headers=headers)
    assert response.status_code == 400
    assert response.get_json()["error"] == "Cart item not found"


def test_delete_cart_item_wrong_owner(client):
    with app.app_context():
        buyer_id = _create_buyer(email="buyer1@test.com").id
        other_buyer_id = _create_buyer(email="buyer2@test.com").id
        animal_id = _create_farmer_and_animal().id
    add = client.post(
        "/api/v1/cart/items", json={"animal_id": animal_id, "quantity": 1}, headers=_auth_header(buyer_id)
    )
    item_id = add.get_json()["id"]

    response = client.delete(
        f"/api/v1/cart/items/{item_id}", headers=_auth_header(other_buyer_id)
    )
    assert response.status_code == 400
    assert "Not authorized" in response.get_json()["error"]