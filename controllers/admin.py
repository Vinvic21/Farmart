from flask import Blueprint, request, jsonify
from extensions import db
from models import User, Profile, Animal, Order
from schemas import user_schema, users_schema, animals_schema
from middleware import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/api/v1/admin")


@admin_bp.route("/stats", methods=["GET"])
@admin_required
def get_stats(current_user):
    #.........................................
    total_users = User.query.count()
    total_farmers = User.query.filter_by(role="farmer").count()
    total_buyers = User.query.filter_by(role="buyer").count()
    total_animals = Animal.query.count()
    available_animals = Animal.query.filter_by(status="available").count()
    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(status="pending").count()
    pending_verifications = Profile.query.filter_by(verification_status="pending").count()

    total_revenue = db.session.query(
        db.func.coalesce(db.func.sum(Order.total_amount), 0)
    ).filter(Order.status == "paid").scalar()

    return jsonify({
        "success": True,
        "stats": {
            "total_users": total_users,
            "total_farmers": total_farmers,
            "total_buyers": total_buyers,
            "total_animals": total_animals,
            "available_animals": available_animals,
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "pending_verifications": pending_verifications,
            "total_revenue": total_revenue,
        },
    }), 200


@admin_bp.route("/users", methods=["GET"])
@admin_required
def get_users(current_user):
    #.........................................
    role = request.args.get("role")

    query = User.query
    if role:
        query = query.filter_by(role=role)

    users = query.order_by(User.created_at.desc()).all()

    return jsonify({"success": True, "users": users_schema.dump(users)}), 200


@admin_bp.route("/users/<int:user_id>", methods=["GET"])
@admin_required
def get_user(current_user, user_id):
    #.........................................
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404

    return jsonify({"success": True, "user": user_schema.dump(user)}), 200


@admin_bp.route("/users/<int:user_id>/verify", methods=["PATCH"])
@admin_required
def verify_user(current_user, user_id):
    #.........................................
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404

    if not user.profile:
        return jsonify({"success": False, "message": "This user has no profile to verify"}), 400

    data = request.get_json(silent=True) or {}
    new_status = data.get("verification_status", "verified")
    if new_status not in ("pending", "verified"):
        return jsonify({"success": False, "message": "verification_status must be 'pending' or 'verified'"}), 400

    user.profile.verification_status = new_status
    db.session.commit()

    return jsonify({"success": True, "message": "Verification status updated", "user": user_schema.dump(user)}), 200


@admin_bp.route("/users/<int:user_id>", methods=["DELETE"])
@admin_required
def delete_user(current_user, user_id):
    #.........................................
    if user_id == current_user.id:
        return jsonify({"success": False, "message": "You cannot delete your own admin account"}), 400

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({"success": True, "message": "User deleted successfully"}), 200


@admin_bp.route("/animals", methods=["GET"])
@admin_required
def get_all_animals(current_user):
    status = request.args.get("status")
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)

    query = Animal.query
    if status:
        query = query.filter_by(status=status)

    paginated = query.order_by(Animal.id.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "success": True,
        "animals": animals_schema.dump(paginated.items),
        "page": paginated.page,
        "per_page": paginated.per_page,
        "total": paginated.total,
        "pages": paginated.pages,
    }), 200


@admin_bp.route("/animals/<int:animal_id>", methods=["DELETE"])
@admin_required
def delete_animal(current_user, animal_id):
    #.........................................
    animal = db.session.get(Animal, animal_id)
    if not animal:
        return jsonify({"success": False, "message": "Animal not found"}), 404

    db.session.delete(animal)
    db.session.commit()

    return jsonify({"success": True, "message": "Animal deleted successfully"}), 200