from flask import Blueprint, request, jsonify
from models import Animal
from schemas.animal_schema import animal_schema, animals_schema

animals_bp = Blueprint("animals", __name__, url_prefix="/animals")


class AnimalController:
    

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
        return Animal.query.get(animal_id)

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