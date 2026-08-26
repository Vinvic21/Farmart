import pytest
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




def test_get_cart_requires_buyer_id(client):
    response = client.get("/cart")
    assert response.status_code == 400
    assert "buyer_id" in response.get_json()["error"]


def test_get_cart_creates_empty_cart_for_new_buyer(client):
    with app.app_context():
        buyer = _create_buyer()
        buyer_id = buyer.id

    response = client.get(f"/cart?buyer_id={buyer_id}")
    assert response.status_code == 200
    data = response.get_json()
    assert data["buyer_id"] == buyer_id
    assert data["items"] == []

    with app.app_context():
        assert Cart.query.filter_by(buyer_id=buyer_id).count() == 1


def test_get_cart_is_idempotent(client):
    with app.app_context():
        buyer = _create_buyer()
        buyer_id = buyer.id

    client.get(f"/cart?buyer_id={buyer_id}")
    client.get(f"/cart?buyer_id={buyer_id}")

    with app.app_context():
        assert Cart.query.filter_by(buyer_id=buyer_id).count() == 1



def test_add_item_to_cart(client):
    with app.app_context():
        buyer_id = _create_buyer().id
        animal_id = _create_farmer_and_animal().id

    response = client.post(
        "/cart/items",
        json={"buyer_id": buyer_id, "animal_id": animal_id, "quantity": 2},
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["animal_id"] == animal_id
    assert data["quantity"] == 2


def test_add_item_defaults_quantity_to_one(client):
    with app.app_context():
        buyer_id = _create_buyer().id
        animal_id = _create_farmer_and_animal().id

    response = client.post(
        "/cart/items", json={"buyer_id": buyer_id, "animal_id": animal_id}
    )
    assert response.status_code == 201
    assert response.get_json()["quantity"] == 1


def test_add_item_missing_fields(client):
    with app.app_context():
        buyer_id = _create_buyer().id

    response = client.post("/cart/items", json={"buyer_id": buyer_id})
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_add_item_animal_not_found(client):
    with app.app_context():
        buyer_id = _create_buyer().id

    response = client.post(
        "/cart/items", json={"buyer_id": buyer_id, "animal_id": 9999, "quantity": 1}
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "Animal not found"


def test_add_item_animal_not_available(client):
    with app.app_context():
        buyer_id = _create_buyer().id
        animal_id = _create_farmer_and_animal(status="sold").id

    response = client.post(
        "/cart/items", json={"buyer_id": buyer_id, "animal_id": animal_id, "quantity": 1}
    )
    assert response.status_code == 400
    assert "not available" in response.get_json()["error"]


def test_add_existing_item_increments_quantity(client):
    with app.app_context():
        buyer_id = _create_buyer().id
        animal_id = _create_farmer_and_animal().id

    client.post(
        "/cart/items", json={"buyer_id": buyer_id, "animal_id": animal_id, "quantity": 1}
    )
    response = client.post(
        "/cart/items", json={"buyer_id": buyer_id, "animal_id": animal_id, "quantity": 2}
    )
    assert response.status_code == 201
    assert response.get_json()["quantity"] == 3

    with app.app_context():
        assert CartItem.query.filter_by(animal_id=animal_id).count() == 1



def test_update_cart_item_quantity(client):
    with app.app_context():
        buyer_id = _create_buyer().id
        animal_id = _create_farmer_and_animal().id
    add = client.post(
        "/cart/items", json={"buyer_id": buyer_id, "animal_id": animal_id, "quantity": 1}
    )
    item_id = add.get_json()["id"]

    response = client.patch(
        f"/cart/items/{item_id}", json={"buyer_id": buyer_id, "quantity": 5}
    )
    assert response.status_code == 200
    assert response.get_json()["quantity"] == 5


def test_update_cart_item_missing_fields(client):
    with app.app_context():
        buyer_id = _create_buyer().id

    response = client.patch("/cart/items/1", json={"buyer_id": buyer_id})
    assert response.status_code == 400


def test_update_cart_item_quantity_below_one(client):
    with app.app_context():
        buyer_id = _create_buyer().id
        animal_id = _create_farmer_and_animal().id
    add = client.post(
        "/cart/items", json={"buyer_id": buyer_id, "animal_id": animal_id, "quantity": 1}
    )
    item_id = add.get_json()["id"]

    response = client.patch(
        f"/cart/items/{item_id}", json={"buyer_id": buyer_id, "quantity": 0}
    )
    assert response.status_code == 400
    # KNOWN BUG: quantity=0 is falsy, so `all([buyer_id, quantity])`
    assert response.get_json()["error"] == "buyer_id and quantity are required"


def test_update_cart_item_not_found(client):
    with app.app_context():
        buyer_id = _create_buyer().id

    response = client.patch(
        "/cart/items/9999", json={"buyer_id": buyer_id, "quantity": 2}
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "Cart item not found"


def test_update_cart_item_wrong_owner(client):
    with app.app_context():
        buyer_id = _create_buyer(email="buyer1@test.com").id
        other_buyer_id = _create_buyer(email="buyer2@test.com").id
        animal_id = _create_farmer_and_animal().id
    add = client.post(
        "/cart/items", json={"buyer_id": buyer_id, "animal_id": animal_id, "quantity": 1}
    )
    item_id = add.get_json()["id"]

    response = client.patch(
        f"/cart/items/{item_id}", json={"buyer_id": other_buyer_id, "quantity": 3}
    )
    assert response.status_code == 400
    assert "Not authorized" in response.get_json()["error"]


# ---------- DELETE /cart/items/<id> ----------

def test_delete_cart_item(client):
    with app.app_context():
        buyer_id = _create_buyer().id
        animal_id = _create_farmer_and_animal().id
    add = client.post(
        "/cart/items", json={"buyer_id": buyer_id, "animal_id": animal_id, "quantity": 1}
    )
    item_id = add.get_json()["id"]

    response = client.delete(f"/cart/items/{item_id}", json={"buyer_id": buyer_id})
    assert response.status_code == 200
    assert response.get_json()["message"] == "Item removed from cart"

    with app.app_context():
        assert CartItem.query.get(item_id) is None


def test_delete_cart_item_via_query_param(client):
    with app.app_context():
        buyer_id = _create_buyer().id
        animal_id = _create_farmer_and_animal().id
    add = client.post(
        "/cart/items", json={"buyer_id": buyer_id, "animal_id": animal_id, "quantity": 1}
    )
    item_id = add.get_json()["id"]

    response = client.delete(f"/cart/items/{item_id}?buyer_id={buyer_id}")
    assert response.status_code == 200


def test_delete_cart_item_missing_buyer_id(client):
    response = client.delete("/cart/items/1")
    assert response.status_code == 400
    assert "buyer_id" in response.get_json()["error"]


def test_delete_cart_item_not_found(client):
    with app.app_context():
        buyer_id = _create_buyer().id

    response = client.delete("/cart/items/9999", json={"buyer_id": buyer_id})
    assert response.status_code == 400
    assert response.get_json()["error"] == "Cart item not found"


def test_delete_cart_item_wrong_owner(client):
    with app.app_context():
        buyer_id = _create_buyer(email="buyer1@test.com").id
        other_buyer_id = _create_buyer(email="buyer2@test.com").id
        animal_id = _create_farmer_and_animal().id
    add = client.post(
        "/cart/items", json={"buyer_id": buyer_id, "animal_id": animal_id, "quantity": 1}
    )
    item_id = add.get_json()["id"]

    response = client.delete(
        f"/cart/items/{item_id}", json={"buyer_id": other_buyer_id}
    )
    assert response.status_code == 400
    assert "Not authorized" in response.get_json()["error"]