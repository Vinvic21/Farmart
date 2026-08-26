from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import Cart, CartItem, Animal
from schemas import cart_schema, cart_item_schema

cart_bp = Blueprint("cart", __name__, url_prefix="/api/v1/cart")


class CartController:
    #.........................................

    @staticmethod
    def get_or_create_cart(buyer_id):
        cart = Cart.query.filter_by(buyer_id=buyer_id).first()
        if not cart:
            cart = Cart(buyer_id=buyer_id)
            db.session.add(cart)
            db.session.commit()
        return cart

    @staticmethod
    def add_item(buyer_id, animal_id, quantity=1):
        animal = db.session.get(Animal, animal_id)
        if not animal:
            return None, "Animal not found"
        if animal.status != "available":
            return None, "This animal is not available for purchase"

        cart = CartController.get_or_create_cart(buyer_id)

        existing_item = CartItem.query.filter_by(cart_id=cart.id, animal_id=animal_id).first()
        if existing_item:
            existing_item.quantity += quantity
            db.session.commit()
            return existing_item, None

        item = CartItem(cart_id=cart.id, animal_id=animal_id, quantity=quantity)
        db.session.add(item)
        db.session.commit()
        return item, None

    @staticmethod
    def update_quantity(buyer_id, item_id, quantity):
        if quantity < 1:
            return None, "Quantity must be at least 1"

        item = db.session.get(CartItem, item_id)
        if not item:
            return None, "Cart item not found"
        if item.cart.buyer_id != buyer_id:
            return None, "Not authorized to modify this cart item"

        item.quantity = quantity
        db.session.commit()
        return item, None

    @staticmethod
    def remove_item(buyer_id, item_id):
        item = db.session.get(CartItem, item_id)
        if not item:
            return None, "Cart item not found"
        if item.cart.buyer_id != buyer_id:
            return None, "Not authorized to modify this cart item"

        db.session.delete(item)
        db.session.commit()
        return True, None


@cart_bp.route("", methods=["GET"])
@jwt_required()
def get_cart():
    buyer_id = int(get_jwt_identity())

    cart = CartController.get_or_create_cart(buyer_id)
    return jsonify(cart_schema.dump(cart)), 200


@cart_bp.route("/items", methods=["POST"])
@jwt_required()
def add_to_cart():
    buyer_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    animal_id = data.get("animal_id")
    quantity = data.get("quantity", 1)

    if not animal_id:
        return jsonify(error="animal_id is required"), 400

    item, error = CartController.add_item(buyer_id, animal_id, quantity)
    if error:
        return jsonify(error=error), 400

    return jsonify(cart_item_schema.dump(item)), 201


@cart_bp.route("/items/<int:id>", methods=["PATCH"])
@jwt_required()
def update_cart_item(id):
    buyer_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    quantity = data.get("quantity")

    if not quantity:
        return jsonify(error="quantity is required"), 400

    item, error = CartController.update_quantity(buyer_id, id, quantity)
    if error:
        return jsonify(error=error), 400

    return jsonify(cart_item_schema.dump(item)), 200


@cart_bp.route("/items/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_cart_item(id):
    buyer_id = int(get_jwt_identity())

    success, error = CartController.remove_item(buyer_id, id)
    if error:
        return jsonify(error=error), 400

    return jsonify(message="Item removed from cart"), 200