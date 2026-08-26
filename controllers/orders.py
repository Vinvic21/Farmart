from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from sqlalchemy.orm import joinedload
from datetime import datetime

from extensions import db
from models import Order, OrderItem, Cart, CartItem, Animal, User
from schemas import (
    OrderCreateSchema,
    OrderUpdateSchema,
    OrderResponseSchema,
    OrderItemUpdateSchema
)

orders_bp = Blueprint('orders', __name__, url_prefix='/api/v1/orders')


@orders_bp.route('/', methods=['GET'])
@jwt_required()
def get_orders():
    """
    Get orders (role-filtered)
    - Buyers see their own orders
    - Farmers see incoming orders with their animals
    - Admins see all orders
    ---
    tags:
      - Orders
    security:
      - JWT: []
    responses:
      200: List of orders
    """
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        }), 404
    
    # Admin can see all orders
    if user.is_admin():
        orders = Order.query.options(
            joinedload(Order.items).joinedload(OrderItem.animal)
        ).order_by(Order.created_at.desc()).all()
    
    # Buyer sees their own orders
    elif user.is_buyer():
        orders = Order.query.options(
            joinedload(Order.items).joinedload(OrderItem.animal)
        ).filter_by(buyer_id=user.id).order_by(Order.created_at.desc()).all()
    
    # Farmer sees orders containing their animals
    elif user.is_farmer():
        # Get all order items where this farmer is the supplier
        order_ids = db.session.query(OrderItem.order_id).filter_by(farmer_id=user.id).distinct()
        orders = Order.query.options(
            joinedload(Order.items).joinedload(OrderItem.animal)
        ).filter(Order.id.in_(order_ids)).order_by(Order.created_at.desc()).all()
    
    else:
        return jsonify({
            'success': False,
            'message': 'Invalid user role'
        }), 403
    
    schema = OrderResponseSchema(many=True)
    
    return jsonify({
        'success': True,
        'orders': schema.dump(orders)
    }), 200


@orders_bp.route('/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id):
    """
    Get a specific order
    ---
    tags:
      - Orders
    security:
      - JWT: []
    responses:
      200: Order details
      403: Not authorized
      404: Order not found
    """
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        }), 404
    
    order = Order.query.options(
        joinedload(Order.items).joinedload(OrderItem.animal)
    ).get(order_id)
    
    if not order:
        return jsonify({
            'success': False,
            'message': 'Order not found'
        }), 404
    
    # Check authorization
    is_owner = order.buyer_id == user.id
    is_admin = user.is_admin()
    is_supplier = OrderItem.query.filter_by(order_id=order.id, farmer_id=user.id).first() is not None
    
    if not (is_owner or is_admin or is_supplier):
        return jsonify({
            'success': False,
            'message': 'You are not authorized to view this order'
        }), 403
    
    schema = OrderResponseSchema()
    
    return jsonify({
        'success': True,
        'order': schema.dump(order)
    }), 200


@orders_bp.route('/checkout', methods=['POST'])
@jwt_required()
def checkout():
    """
    Checkout: Convert cart to order, clear cart, mark animals as pending
    ---
    tags:
      - Orders
    security:
      - JWT: []
    responses:
      201: Order created successfully
      400: Cart is empty or validation error
      404: User not found
    """
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        }), 404
    
    # Get cart
    cart = Cart.query.options(
        joinedload(Cart.items).joinedload(CartItem.animal)
    ).filter_by(buyer_id=user.id).first()
    
    if not cart or cart.total_items == 0:
        return jsonify({
            'success': False,
            'message': 'Cart is empty'
        }), 400
    
    # Validate checkout data
    data = request.get_json()
    schema = OrderCreateSchema()
    try:
        validated_data = schema.load(data)
    except ValidationError as err:
        return jsonify({
            'success': False,
            'errors': err.messages,
            'message': 'Validation error'
        }), 400
    
    # Check all items are available
    for item in cart.items:
        animal = item.animal
        if not animal or not animal.is_available():
            return jsonify({
                'success': False,
                'message': f'Animal {animal.id if animal else "unknown"} is no longer available'
            }), 409
    
    # Generate order number
    order_number = f"FMT-{datetime.utcnow().strftime('%Y%m%d')}-{Order.query.count() + 1:04d}"
    
    # Create order
    order = Order(
        buyer_id=user.id,
        status='pending',
        total_amount=cart.total_amount
    )
    
    try:
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        # Create order items and update animal status
        for cart_item in cart.items:
            animal = cart_item.animal
            
            order_item = OrderItem(
                order_id=order.id,
                animal_id=cart_item.animal_id,
                farmer_id=animal.farmer_id,
                quantity=cart_item.quantity,
                price_at_purchase=animal.price,
                status='pending'
            )
            db.session.add(order_item)
            
            # Mark animal as pending
            animal.status = 'pending'
        
        # Clear cart
        cart.clear()
        
        # Create payment record (will be completed by payment controller)
        # This is handled separately
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Database error: {str(e)}'
        }), 500
    
    schema = OrderResponseSchema()
    
    return jsonify({
        'success': True,
        'message': 'Order created successfully',
        'order': schema.dump(order)
    }), 201


@orders_bp.route('/<int:order_id>/confirm', methods=['PATCH'])
@jwt_required()
def confirm_order(order_id):
    """
    Confirm an order (Farmer only)
    ---
    tags:
      - Orders
    security:
      - JWT: []
    responses:
      200: Order confirmed
      403: Not authorized
      404: Order not found
    """
    return update_order_status(order_id, 'confirmed')


@orders_bp.route('/<int:order_id>/reject', methods=['PATCH'])
@jwt_required()
def reject_order(order_id):
    """
    Reject an order (Farmer only)
    ---
    tags:
      - Orders
    security:
      - JWT: []
    responses:
      200: Order rejected
      403: Not authorized
      404: Order not found
    """
    return update_order_status(order_id, 'rejected')


def update_order_status(order_id, new_status):
    """
    Helper function to update order status
    Only farmers who own animals in the order can confirm/reject
    """
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        }), 404
    
    # Only farmers can confirm/reject
    if not user.is_farmer():
        return jsonify({
            'success': False,
            'message': 'Only farmers can confirm or reject orders'
        }), 403
    
    # Get order
    order = Order.query.get(order_id)
    
    if not order:
        return jsonify({
            'success': False,
            'message': 'Order not found'
        }), 404
    
    # Check if farmer has any items in this order
    farmer_items = OrderItem.query.filter_by(order_id=order.id, farmer_id=user.id).all()
    
    if not farmer_items:
        return jsonify({
            'success': False,
            'message': 'You do not have any items in this order'
        }), 403
    
    # Update status for all farmer's items
    for item in farmer_items:
        item.status = new_status
    
    # Check if all items in order are confirmed/rejected
    all_items = OrderItem.query.filter_by(order_id=order.id).all()
    