import pytest
from flask_jwt_extended import create_access_token

from app import app
from extensions import db
from models import User, Animal, Cart, CartItem, Order, OrderItem


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()


def _create_user(email, role):
    """Create a user (with a cart, if a buyer) and return their id."""
    user = User(email=email, role=role)
    user.set_password("password123")
    db.session.add(user)
    db.session.flush()
    if role == "buyer":
        db.session.add(Cart(buyer_id=user.id))
    db.session.commit()
    return user.id


def _create_animal(farmer_id, status="available", price=500.0):
    animal = Animal(
        farmer_id=farmer_id, type="Cow", breed="Friesian", age=3,
        price=price, status=status, description="Healthy dairy cow",
    )
    db.session.add(animal)
    db.session.commit()
    return animal.id


def _auth_header(user_id, role):
    with app.app_context():
        token = create_access_token(identity=str(user_id), additional_claims={"role": role})
    return {"Authorization": f"Bearer {token}"}


CHECKOUT_PAYLOAD = {
    "recipient_first_name": "Jane",
    "recipient_last_name": "Doe",
    "recipient_phone": "0712345678",
    "delivery_address": "123 Farm Road, Nairobi",
}


def _checkout(client, buyer_id, animal_id, quantity=1, payload=None):
    headers = _auth_header(buyer_id, "buyer")
    client.post(
        "/api/v1/cart/items",
        json={"animal_id": animal_id, "quantity": quantity},
        headers=headers,
    )
    return client.post(
        "/api/v1/orders/checkout",
        json=payload if payload is not None else CHECKOUT_PAYLOAD,
        headers=headers,
    )


def test_checkout_requires_delivery_details(client):
    with app.app_context():
        farmer_id = _create_user("farmer@test.com", "farmer")
        buyer_id = _create_user("buyer@test.com", "buyer")
        animal_id = _create_animal(farmer_id)

    response = _checkout(client, buyer_id, animal_id, payload={})
    assert response.status_code == 400
    assert "errors" in response.get_json()


def test_checkout_empty_cart_is_rejected(client):
    with app.app_context():
        buyer_id = _create_user("buyer@test.com", "buyer")

    response = client.post(
        "/api/v1/orders/checkout", json=CHECKOUT_PAYLOAD, headers=_auth_header(buyer_id, "buyer")
    )
    assert response.status_code == 400
    assert response.get_json()["message"] == "Cart is empty"


def test_checkout_creates_order_and_clears_cart(client):
    with app.app_context():
        farmer_id = _create_user("farmer@test.com", "farmer")
        buyer_id = _create_user("buyer@test.com", "buyer")
        animal_id = _create_animal(farmer_id, price=500.0)

    response = _checkout(client, buyer_id, animal_id, quantity=2)
    assert response.status_code == 201
    data = response.get_json()["order"]
    assert data["status"] == "pending"
    assert data["total_amount"] == 1000.0
    assert data["total_items"] == 2
    assert len(data["items"]) == 1
    assert data["items"][0]["farmer_id"] == farmer_id
    assert data["order_number"]

    with app.app_context():
        # animal reserved, cart emptied
        refreshed_animal = db.session.get(Animal, animal_id)
        assert refreshed_animal.status == "pending"
        cart = Cart.query.filter_by(buyer_id=buyer_id).first()
        assert cart.items == []


def test_checkout_rejects_unavailable_animal(client):
    with app.app_context():
        farmer_id = _create_user("farmer@test.com", "farmer")
        buyer_id = _create_user("buyer@test.com", "buyer")
        animal_id = _create_animal(farmer_id, status="available")

    headers = _auth_header(buyer_id, "buyer")
    client.post("/api/v1/cart/items", json={"animal_id": animal_id, "quantity": 1}, headers=headers)

    with app.app_context():
        db.session.get(Animal, animal_id).status = "sold"
        db.session.commit()

    response = client.post("/api/v1/orders/checkout", json=CHECKOUT_PAYLOAD, headers=headers)
    assert response.status_code == 409


def test_buyer_can_view_own_order(client):
    with app.app_context():
        farmer_id = _create_user("farmer@test.com", "farmer")
        buyer_id = _create_user("buyer@test.com", "buyer")
        animal_id = _create_animal(farmer_id)

    order_id = _checkout(client, buyer_id, animal_id).get_json()["order"]["id"]

    response = client.get(f"/api/v1/orders/{order_id}", headers=_auth_header(buyer_id, "buyer"))
    assert response.status_code == 200
    assert response.get_json()["order"]["id"] == order_id


def test_stranger_cannot_view_order(client):
    with app.app_context():
        farmer_id = _create_user("farmer@test.com", "farmer")
        buyer_id = _create_user("buyer@test.com", "buyer")
        stranger_id = _create_user("stranger@test.com", "buyer")
        animal_id = _create_animal(farmer_id)

    order_id = _checkout(client, buyer_id, animal_id).get_json()["order"]["id"]

    response = client.get(f"/api/v1/orders/{order_id}", headers=_auth_header(stranger_id, "buyer"))
    assert response.status_code == 403


def test_farmer_confirm_updates_item_and_order_status(client):
    with app.app_context():
        farmer_id = _create_user("farmer@test.com", "farmer")
        buyer_id = _create_user("buyer@test.com", "buyer")
        animal_id = _create_animal(farmer_id)

    order_id = _checkout(client, buyer_id, animal_id).get_json()["order"]["id"]

    response = client.patch(f"/api/v1/orders/{order_id}/confirm", headers=_auth_header(farmer_id, "farmer"))
    assert response.status_code == 200
    data = response.get_json()["order"]
    assert data["status"] == "confirmed"
    assert data["items"][0]["status"] == "confirmed"


def test_farmer_reject_releases_animal(client):
    with app.app_context():
        farmer_id = _create_user("farmer@test.com", "farmer")
        buyer_id = _create_user("buyer@test.com", "buyer")
        animal_id = _create_animal(farmer_id)

    order_id = _checkout(client, buyer_id, animal_id).get_json()["order"]["id"]

    response = client.patch(f"/api/v1/orders/{order_id}/reject", headers=_auth_header(farmer_id, "farmer"))
    assert response.status_code == 200
    data = response.get_json()["order"]
    assert data["status"] == "rejected"

    with app.app_context():
        assert db.session.get(Animal, animal_id).status == "available"


def test_buyer_cannot_confirm_order(client):
    with app.app_context():
        farmer_id = _create_user("farmer@test.com", "farmer")
        buyer_id = _create_user("buyer@test.com", "buyer")
        animal_id = _create_animal(farmer_id)

    order_id = _checkout(client, buyer_id, animal_id).get_json()["order"]["id"]

    response = client.patch(f"/api/v1/orders/{order_id}/confirm", headers=_auth_header(buyer_id, "buyer"))
    assert response.status_code == 403


def test_unrelated_farmer_cannot_confirm_order(client):
    with app.app_context():
        farmer_id = _create_user("farmer@test.com", "farmer")
        other_farmer_id = _create_user("other_farmer@test.com", "farmer")
        buyer_id = _create_user("buyer@test.com", "buyer")
        animal_id = _create_animal(farmer_id)

    order_id = _checkout(client, buyer_id, animal_id).get_json()["order"]["id"]

    response = client.patch(
        f"/api/v1/orders/{order_id}/confirm", headers=_auth_header(other_farmer_id, "farmer")
    )
    assert response.status_code == 403


def test_orders_requires_auth(client):
    response = client.get("/api/v1/orders/")
    assert response.status_code == 401