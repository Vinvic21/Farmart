from marshmallow import Schema, fields, validate, ValidationError, pre_load, post_load
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from models import Order
from datetime import datetime


class OrderSchema(SQLAlchemyAutoSchema):
    """
    Base Order schema for serialization/deserialization
    
    Used for:
    - GET /api/v1/orders - Listing orders
    - GET /api/v1/orders/<id> - Single order
    """
    
    class Meta:
        model = Order
        load_instance = True
        include_fk = True
        exclude = ('created_at',)
    
    # Computed property (read-only)
    total_items = fields.Integer(dump_only=True)
    
    # Nested items
    items = fields.Nested('OrderItemSchema', many=True, dump_only=True)
    payment = fields.Nested('PaymentSchema', dump_only=True)
    
    # Buyer info
    buyer = fields.Nested(
        'UserResponseSchema',
        only=('id', 'email', 'role'),
        dump_only=True
    )


class OrderCreateSchema(Schema):
    """
    Schema for creating an order (checkout)
    
    Used for:
    - POST /api/v1/orders/checkout - Checkout
    """
    
    shipping_address = fields.String(
        required=True,
        validate=validate.Length(min=5, max=500),
        error_messages={
            'required': 'Shipping address is required',
            'invalid': 'Shipping address must be between 5 and 500 characters'
        }
    )
    
    delivery_instructions = fields.String(
        validate=validate.Length(max=500),
        allow_none=True,
        error_messages={
            'invalid': 'Delivery instructions cannot exceed 500 characters'
        }
    )
    
    payment_method = fields.String(
        required=True,
        validate=validate.OneOf(['mpesa', 'stripe', 'bank_transfer']),
        error_messages={
            'required': 'Payment method is required',
            'invalid': 'Payment method must be one of: mpesa, stripe, bank_transfer'
        }
    )
    
    phone_number = fields.String(
        validate=validate.Length(max=20),
        allow_none=True,
        error_messages={
            'invalid': 'Phone number cannot exceed 20 characters'
        }
    )
    
    @pre_load
    def validate_order_data(self, data, **kwargs):
        """
        Validate order creation data
        """
        if not data.get('shipping_address'):
            raise ValidationError(
                {'shipping_address': 'Shipping address is required'}
            )
        
        if not data.get('payment_method'):
            raise ValidationError(
                {'payment_method': 'Payment method is required'}
            )
        
        return data
    
    @post_load
    def prepare_order_data(self, data, **kwargs):
        """
        Prepare data for order creation
        """
        # Ensure payment_method is lowercase
        if data.get('payment_method'):
            data['payment_method'] = data['payment_method'].lower()
        
        return data


class OrderUpdateSchema(Schema):
    """
    Schema for updating order status
    
    Used for:
    - Internal order status updates
    - Admin order management
    """
    
    status = fields.String(
        validate=validate.OneOf([
            'pending', 'confirmed', 'rejected', 
            'paid', 'delivered', 'cancelled'
        ]),
        error_messages={
            'invalid': 'Status must be one of: pending, confirmed, rejected, paid, delivered, cancelled'
        }
    )
    
    @pre_load
    def validate_update_data(self, data, **kwargs):
        """
        Ensure at least one field is provided
        """
        if not data:
            raise ValidationError(
                {'_schema': 'At least one field must be provided'}
            )
        
        if 'status' not in data:
            raise ValidationError(
                {'status': 'Status is required for update'}
            )
        
        return data


class OrderStatusUpdateSchema(Schema):
    """
    Schema for updating order status (farmer confirm/reject)
    
    Used for:
    - PATCH /api/v1/orders/<id>/confirm
    - PATCH /api/v1/orders/<id>/reject
    """
    
    status = fields.String(
        required=True,
        validate=validate.OneOf(['confirmed', 'rejected']),
        error_messages={
            'required': 'Status is required',
            'invalid': 'Status must be either confirmed or rejected'
        }
    )
    
    note = fields.String(
        validate=validate.Length(max=500),
        allow_none=True,
        error_messages={
            'invalid': 'Note cannot exceed 500 characters'
        }
    )
    
    @pre_load
    def validate_status_update(self, data, **kwargs):
        """
        Validate status update
        """
        if not data.get('status'):
            raise ValidationError(
                {'status': 'Status is required'}
            )
        
        return data


class OrderResponseSchema(Schema):
    """
    Schema for order response with all details
    
    Used for:
    - GET /api/v1/orders/<id> - Full order details
    """
    
    id = fields.Integer()
    buyer_id = fields.Integer()
    order_number = fields.String()
    status = fields.String()
    total_amount = fields.Float()
    total_items = fields.Integer()
    created_at = fields.DateTime()
    shipping_address = fields.String()
    delivery_instructions = fields.String(allow_none=True)
    payment_method = fields.String()
    
    # Nested relations
    items = fields.Nested('OrderItemSchema', many=True)
    payment = fields.Nested('PaymentSchema')
    buyer = fields.Nested(
        'UserResponseSchema',
        only=('id', 'email', 'role')
    )
    
    class Meta:
        fields = (
            'id', 'buyer_id', 'order_number', 'status', 
            'total_amount', 'total_items', 'created_at',
            'shipping_address', 'delivery_instructions', 'payment_method',
            'items', 'payment', 'buyer'
        )


class OrderListResponseSchema(Schema):
    """
    Schema for order list response (lightweight)
    
    Used for:
    - GET /api/v1/orders - List view
    """
    
    id = fields.Integer()
    order_number = fields.String()
    status = fields.String()
    total_amount = fields.Float()
    total_items = fields.Integer()
    created_at = fields.DateTime()
    
    # Buyer info (minimal)
    buyer = fields.Nested(
        'UserResponseSchema',
        only=('id', 'email', 'role')
    )
    
    class Meta:
        fields = (
            'id', 'order_number', 'status', 
            'total_amount', 'total_items', 'created_at',
            'buyer'
        )


class FarmerOrderResponseSchema(Schema):
    """
    Schema for farmer's view of orders
    
    Used for:
    - GET /api/v1/orders - Farmer view
    """
    
    id = fields.Integer()
    order_number = fields.String()
    created_at = fields.DateTime()
    order_status = fields.String()
    total_amount = fields.Float()
    
    # Only show items belonging to this farmer
    items = fields.Nested(
        'OrderItemSchema',
        many=True,
        only=('id', 'animal_id', 'quantity', 'price_at_purchase', 'subtotal', 'status')
    )
    
    buyer = fields.Nested(
        'UserResponseSchema',
        only=('id', 'email', 'role')
    )
    
    class Meta:
        fields = (
            'id', 'order_number', 'created_at',
            'order_status', 'total_amount', 'items', 'buyer'
        )


class OrderHistorySchema(Schema):
    """
    Schema for order history
    
    Used for:
    - Order tracking and history
    """
    
    id = fields.Integer()
    order_number = fields.String()
    status = fields.String()
    total_amount = fields.Float()
    created_at = fields.DateTime()
    
    # Summary fields for history view
    item_count = fields.Integer()
    farmer_count = fields.Integer()
    
    class Meta:
        fields = (
            'id', 'order_number', 'status', 'total_amount',
            'created_at', 'item_count', 'farmer_count'
        )


class OrderTrackingSchema(Schema):
    """
    Schema for order tracking status
    
    Used for:
    - Tracking individual order status
    """
    
    order_id = fields.Integer()
    order_number = fields.String()
    status = fields.String()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
    
    # Status timeline
    status_history = fields.List(
        fields.Dict(
            keys=fields.String(),
            values=fields.DateTime()
        )
    )
    
    # Current status details
    status_details = fields.Method("get_status_details")
    
    def get_status_details(self, obj):
        """
        Get detailed status information
        """
        status_messages = {
            'pending': 'Order is pending confirmation from farmers',
            'confirmed': 'All farmers have confirmed the order',
            'rejected': 'Order has been rejected by a farmer',
            'paid': 'Payment has been completed',
            'delivered': 'Order has been delivered',
            'cancelled': 'Order has been cancelled'
        }
        
        return {
            'status': obj.get('status'),
            'message': status_messages.get(obj.get('status'), 'Unknown status'),
            'updated_at': obj.get('updated_at')
        }
    
    class Meta:
        fields = (
            'order_id', 'order_number', 'status',
            'created_at', 'updated_at', 'status_history',
            'status_details'
        )


class OrderAnalyticsSchema(Schema):
    """
    Schema for order analytics
    
    Used for:
    - Dashboard statistics
    - Admin analytics
    """
    
    total_orders = fields.Integer()
    pending_orders = fields.Integer()
    confirmed_orders = fields.Integer()
    rejected_orders = fields.Integer()
    completed_orders = fields.Integer()
    total_revenue = fields.Float()
    average_order_value = fields.Float()
    
    # Time-based breakdown
    orders_by_day = fields.List(
        fields.Dict(
            keys=fields.String(),
            values=fields.Integer()
        )
    )
    
    revenue_by_day = fields.List(
        fields.Dict(
            keys=fields.String(),
            values=fields.Float()
        )
    )
    
    class Meta:
        fields = (
            'total_orders', 'pending_orders', 'confirmed_orders',
            'rejected_orders', 'completed_orders', 'total_revenue',
            'average_order_value', 'orders_by_day', 'revenue_by_day'
        )