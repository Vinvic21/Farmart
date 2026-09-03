from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from middleware.auth_middleware import buyer_required
from sqlalchemy.orm import joinedload
from datetime import datetime

from extensions import db
from models import Order, OrderItem, Cart, CartItem, User
from schemas import order_schema, orders_schema

orders_bp = Blueprint('orders', __name__, url_prefix='/api/v1/orders')


def _parse_delivery_details(data):
    # Manual validation for checkout delivery details. Returns
    # (validated_dict, error_message) - error_message is None on success.
    required_fields = (
        'recipient_first_name', 'recipient_last_name',
        'recipient_phone', 'delivery_address',
    )
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        return None, f"Missing required field(s): {', '.join(missing)}"

    preferred_delivery_date = None
    raw_date = data.get('preferred_delivery_date')
    if raw_date:
        try:
            preferred_delivery_date = datetime.strptime(raw_date, '%Y-%m-%d').date()
        except ValueError:
            return None, 'preferred_delivery_date must be in YYYY-MM-DD format'

    return {
        'recipient_first_name': data['recipient_first_name'],
        'recipient_last_name': data['recipient_last_name'],
        'recipient_phone': data['recipient_phone'],
        'delivery_address': data['delivery_address'],
        'preferred_delivery_date': preferred_delivery_date,
    }, None


@orders_bp.route('/', methods=['GET'])
@jwt_required()
def get_orders():
    # Buyers see their own orders, farmers see incoming orders with their
    # animals, admins see everything.
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))

    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    if user.is_admin():
        orders = Order.query.options(
            joinedload(Order.items).joinedload(OrderItem.animal)
        ).order_by(Order.created_at.desc()).all()

    elif user.is_buyer():
        orders = Order.query.options(
            joinedload(Order.items).joinedload(OrderItem.animal)
        ).filter_by(buyer_id=user.id).order_by(Order.created_at.desc()).all()

    elif user.is_farmer():
        order_ids = db.session.query(OrderItem.order_id).filter_by(farmer_id=user.id).distinct()
        orders = Order.query.options(
            joinedload(Order.items).joinedload(OrderItem.animal)
        ).filter(Order.id.in_(order_ids)).order_by(Order.created_at.desc()).all()

    else:
        return jsonify({'success': False, 'message': 'Invalid user role'}), 403

    return jsonify({'success': True, 'orders': orders_schema.dump(orders)}), 200


@orders_bp.route('/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id):
    #.........................................
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))

    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    order = Order.query.options(
        joinedload(Order.items).joinedload(OrderItem.animal)
    ).get(order_id)

    if not order:
        return jsonify({'success': False, 'message': 'Order not found'}), 404

    is_owner = order.buyer_id == user.id
    is_admin = user.is_admin()
    is_supplier = OrderItem.query.filter_by(order_id=order.id, farmer_id=user.id).first() is not None

    if not (is_owner or is_admin or is_supplier):
        return jsonify({'success': False, 'message': 'You are not authorized to view this order'}), 403

    return jsonify({'success': True, 'order': order_schema.dump(order)}), 200


@orders_bp.route('/checkout', methods=['POST'])
@buyer_required
def checkout():
    #.........................................
    # Converts the buyer's cart into a confirmed order and clears the cart.
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))

    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    cart = Cart.query.options(
        joinedload(Cart.items).joinedload(CartItem.animal)
    ).filter_by(buyer_id=user.id).first()

    if not cart or cart.total_items == 0:
        return jsonify({'success': False, 'message': 'Cart is empty'}), 400

    data = request.get_json(silent=True) or {}
    delivery_details, error = _parse_delivery_details(data)
    if error:
        return jsonify({'success': False, 'message': error}), 400

    for item in cart.items:
        animal = item.animal
        if not animal or not animal.is_available():
            return jsonify({
                'success': False,
                'message': f'Animal {animal.id if animal else "unknown"} is no longer available'
            }), 409

    order_number = f"FMT-{datetime.utcnow().strftime('%Y%m%d')}-{Order.query.count() + 1:04d}"

    order = Order(
        order_number=order_number,
        buyer_id=user.id,
        status='confirmed',
        total_amount=cart.total_amount,
        **delivery_details,
    )

    try:
        db.session.add(order)
        db.session.flush()

        for cart_item in cart.items:
            animal = cart_item.animal

            order_item = OrderItem(
                order_id=order.id,
                animal_id=cart_item.animal_id,
                farmer_id=animal.farmer_id,
                quantity=cart_item.quantity,
                price_at_purchase=animal.price,
                status='confirmed',
            )
            db.session.add(order_item)
            animal.status = 'pending'

        cart.clear()

        # Payment is initiated separately after checkout
        # (see POST /api/v1/payments/initiate).

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500

    return jsonify({
        'success': True,
        'message': 'Order created successfully',
        'order': order_schema.dump(order),
    }), 201


@orders_bp.route('/<int:order_id>/confirm', methods=['PATCH'])
@jwt_required()
def confirm_order(order_id):
    #.........................................
    return update_order_status(order_id, 'confirmed')


@orders_bp.route('/<int:order_id>/reject', methods=['PATCH'])
@jwt_required()
def reject_order(order_id):
    #.........................................
    return update_order_status(order_id, 'rejected')


def update_order_status(order_id, new_status):
    #.........................................
    # Only farmers who own animals in the order can confirm/reject, and
    # only for their own OrderItems (multi-farmer orders update per-item).
    # The parent Order.status is then derived from all of its items.
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))

    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    if not user.is_farmer():
        return jsonify({'success': False, 'message': 'Only farmers can confirm or reject orders'}), 403

    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({'success': False, 'message': 'Order not found'}), 404

    farmer_items = OrderItem.query.filter_by(order_id=order.id, farmer_id=user.id).all()
    if not farmer_items:
        return jsonify({'success': False, 'message': 'You do not have any items in this order'}), 403

    for item in farmer_items:
        item.status = new_status
        if new_status == 'rejected' and item.animal:
            item.animal.status = 'available'

    all_items = OrderItem.query.filter_by(order_id=order.id).all()
    if any(item.status == 'rejected' for item in all_items):
        order.status = 'rejected'
    elif all(item.status == 'confirmed' for item in all_items):
        order.status = 'confirmed'
    else:
        order.status = 'pending'

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500

    return jsonify({
        'success': True,
        'message': f'Order items {new_status}',
        'order': order_schema.dump(order),
    }), 200