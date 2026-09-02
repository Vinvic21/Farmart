from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import Animal, CartItem, OrderItem
from schemas import animal_schema, animals_schema
from middleware import farmer_required, farmer_or_admin_required

animals_bp = Blueprint("animals", __name__, url_prefix="/api/v1/animals")


class AnimalController:
    #.........................................

    MAX_PER_PAGE = 50
    DEFAULT_PER_PAGE = 10
    DEFAULT_STATUS = "available"

    @staticmethod
    def get_all_animals(filters, page, per_page):
        query = Animal.query
        query = AnimalController._apply_filters(query, filters)

        per_page = min(per_page, AnimalController.MAX_PER_PAGE)
        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_animal_by_id(animal_id):
        return db.session.get(Animal, animal_id)

    @staticmethod
    def _apply_filters(query, filters):
        if filters.get("type"):
            query = query.filter(Animal.type.ilike(f"%{filters['type']}%"))

        if filters.get("breed"):
            query = query.filter(Animal.breed.ilike(f"%{filters['breed']}%"))

        status = filters.get("status") or AnimalController.DEFAULT_STATUS
        query = query.filter(Animal.status == status)

        if filters.get("min_price") is not None:
            query = query.filter(Animal.price >= filters["min_price"])
        if filters.get("max_price") is not None:
            query = query.filter(Animal.price <= filters["max_price"])

        if filters.get("min_age") is not None:
            query = query.filter(Animal.age >= filters["min_age"])
        if filters.get("max_age") is not None:
            query = query.filter(Animal.age <= filters["max_age"])

        return query


def _parse_filters():
    
    return {
        "type": request.args.get("type"),
        "breed": request.args.get("breed"),
        "status": request.args.get("status"),
        "min_price": request.args.get("min_price", type=float),
        "max_price": request.args.get("max_price", type=float),
        "min_age": request.args.get("min_age", type=int),
        "max_age": request.args.get("max_age", type=int),
    }


@animals_bp.route("", methods=["GET"])
def get_animals():
    filters = _parse_filters()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", AnimalController.DEFAULT_PER_PAGE, type=int)

    paginated = AnimalController.get_all_animals(filters, page, per_page)

    return jsonify({
        "animals": animals_schema.dump(paginated.items),
        "page": paginated.page,
        "per_page": paginated.per_page,
        "total": paginated.total,
        "pages": paginated.pages,
    }), 200


@animals_bp.route("/<int:id>", methods=["GET"])
def get_animal(id):
    animal = AnimalController.get_animal_by_id(id)
    if not animal:
        return jsonify(error="Animal not found"), 404
    return jsonify(animal_schema.dump(animal)), 200


@animals_bp.route("", methods=["POST"])
@farmer_required
def create_animal(current_user):
    
    data = request.get_json(silent=True) or {}

    try:
        animal = animal_schema.load(data)
    except ValidationError as err:
        return jsonify(errors=err.messages), 400

    animal.farmer_id = current_user.id

    db.session.add(animal)
    db.session.commit()

    return jsonify(animal_schema.dump(animal)), 201


@animals_bp.route("/<int:id>", methods=["PATCH"])
@farmer_or_admin_required
def update_animal(id, current_user):
    #.........................................
    animal = AnimalController.get_animal_by_id(id)
    if not animal:
        return jsonify(error="Animal not found"), 404

    if animal.farmer_id != current_user.id and not current_user.is_admin():
        return jsonify(error="Not authorized to modify this animal"), 403

    data = request.get_json(silent=True) or {}

    try:
        animal = animal_schema.load(data, instance=animal, partial=True)
    except ValidationError as err:
        return jsonify(errors=err.messages), 400

    db.session.commit()

    return jsonify(animal_schema.dump(animal)), 200


@animals_bp.route("/<int:id>", methods=["DELETE"])
@farmer_or_admin_required
def delete_animal(id, current_user):
    #.........................................
    animal = AnimalController.get_animal_by_id(id)
    if not animal:
        return jsonify(error="Animal not found"), 404

    if animal.farmer_id != current_user.id and not current_user.is_admin():
        return jsonify(error="Not authorized to delete this animal"), 403

    # Buyers may have this animal sitting in an open cart — that's not a
    # real transaction, just a pending selection, so it's safe to clear
    # those out on delete rather than let them block it.
    CartItem.query.filter_by(animal_id=id).delete()

    # An animal that's part of any order (even a rejected one) can't be
    # hard-deleted: OrderItem.animal_id is a required FK, and history like
    # farmer revenue depends on being able to look the animal back up.
    # Delist it instead so it disappears from the marketplace without
    # breaking past orders.
    has_order_history = db.session.query(
        OrderItem.query.filter_by(animal_id=id).exists()
    ).scalar()

    if has_order_history:
        animal.status = "removed"
        db.session.commit()
        return jsonify(message="Animal has order history, so it was delisted instead of deleted"), 200

    try:
        db.session.delete(animal)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        animal.status = "removed"
        db.session.commit()
        return jsonify(message="Animal has order history, so it was delisted instead of deleted"), 200

    return jsonify(message="Animal deleted successfully"), 200