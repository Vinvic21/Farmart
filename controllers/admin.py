from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from extensions import db
from models import User, Profile, Animal, Order, OrderItem, CartItem
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


@admin_bp.route("/revenue", methods=["GET"])
@admin_required
def get_farmer_revenue(current_user):
    #.........................................
    # Every buyer payment currently lands in one shared M-Pesa account, so
    # the admin needs to see how much of that money is actually owed to
    # each farmer before dispersing payouts. "Owed" = the farmer's share of
    # orders that have actually been paid for.
    rows = (
        db.session.query(
            User.id.label("farmer_id"),
            db.func.coalesce(
                db.func.sum(OrderItem.price_at_purchase * OrderItem.quantity), 0
            ).label("total_revenue"),
            db.func.count(db.distinct(OrderItem.order_id)).label("paid_orders"),
        )
        .join(OrderItem, OrderItem.farmer_id == User.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.status == "paid")
        .group_by(User.id)
        .order_by(db.desc("total_revenue"))
        .all()
    )

    farmers = []
    for row in rows:
        farmer = db.session.get(User, row.farmer_id)
        dumped = user_schema.dump(farmer)
        farmers.append({
            "farmer_id": row.farmer_id,
            "name": dumped.get("name"),
            "email": dumped.get("email"),
            "total_revenue": float(row.total_revenue),
            "paid_orders": row.paid_orders,
        })

    total_revenue = sum(f["total_revenue"] for f in farmers)

    return jsonify({
        "success": True,
        "total_revenue": total_revenue,
        "farmers": farmers,
    }), 200


@admin_bp.route("/revenue/<int:farmer_id>", methods=["GET"])
@admin_required
def get_farmer_revenue_detail(current_user, farmer_id):
    #.........................................
    farmer = db.session.get(User, farmer_id)
    if not farmer or farmer.role != "farmer":
        return jsonify({"success": False, "message": "Farmer not found"}), 404

    items = (
        db.session.query(OrderItem)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(OrderItem.farmer_id == farmer_id, Order.status == "paid")
        .order_by(Order.created_at.desc())
        .all()
    )

    line_items = []
    total_revenue = 0.0
    for item in items:
        subtotal = item.price_at_purchase * item.quantity
        total_revenue += subtotal
        line_items.append({
            "order_id": item.order_id,
            "order_number": item.order.order_number,
            "date": item.order.created_at.isoformat() if item.order.created_at else None,
            "animal": f"{item.animal.breed} {item.animal.type}".strip() if item.animal else None,
            "quantity": item.quantity,
            "price_at_purchase": item.price_at_purchase,
            "subtotal": subtotal,
        })

    return jsonify({
        "success": True,
        "farmer": user_schema.dump(farmer),
        "total_revenue": total_revenue,
        "orders": line_items,
    }), 200


@admin_bp.route("/animals", methods=["GET"])
@admin_required
def get_all_animals(current_user):
    status = request.args.get("status")
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)

    query = Animal.query
    if status:
        query = query.filter_by(status=status)
    else:
        # Delisted animals (order history prevented a hard delete) shouldn't
        # clutter the default moderation view — admin can still pull them
        # up explicitly with ?status=removed if needed.
        query = query.filter(Animal.status != "removed")

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

    # Same constraint as the farmer-facing delete: clear stale cart entries,
    # but delist (don't hard-delete) if the animal has real order history,
    # since OrderItem.animal_id is a required FK and order/revenue records
    # depend on being able to look the animal back up.
    CartItem.query.filter_by(animal_id=animal_id).delete()

    has_order_history = db.session.query(
        OrderItem.query.filter_by(animal_id=animal_id).exists()
    ).scalar()

    if has_order_history:
        animal.status = "removed"
        db.session.commit()
        return jsonify({"success": True, "message": "Animal has order history, so it was delisted instead of deleted"}), 200

    try:
        db.session.delete(animal)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        animal.status = "removed"
        db.session.commit()
        return jsonify({"success": True, "message": "Animal has order history, so it was delisted instead of deleted"}), 200

    return jsonify({"success": True, "message": "Animal deleted successfully"}), 200