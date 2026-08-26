from marshmallow import Schema, fields, validate, ValidationError, pre_load, post_load
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from models import OrderItem


class OrderItemSchema(SQLAlchemyAutoSchema):
    """
    Order Item schema for serialization
    
    Used for:
    - Displaying order items
    - Calculating subtotals
    - Order item management
    """
    
    class Meta:
        model = OrderItem
        load_instance = True
        include_fk = True
    
    # Computed property
    subtotal = fields.Float(dump_only=True)
    
    # Nested animal data
    animal = fields.Nested(
        'AnimalResponseSchema',
        only=('id', 'type', 'breed', 'price', 'status', 'description')
    )
    
    # Farmer info
    farmer = fields.Nested(
        'UserResponseSchema',
        only=('id', 'email', 'role')
    )
    
    class Meta:
        fields = (
            'id', 'order_id', 'animal_id', 'farmer_id',
            'quantity', 'price_at_purchase', 'status', 
            'subtotal', 'animal', 'farmer'
        )


class OrderItemCreateSchema(Schema):
    """
    Schema for creating order items
    
    Used for:
    - Internal order creation
    - Checkout processing
    """
    
    animal_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1),
        error_messages={
            'required': 'Animal ID is required',
            'invalid': 'Animal ID must be a positive integer'
        }
    )
    
    quantity = fields.Integer(
        required=True,
        validate=validate.Range(min=1),
        error_messages={
            'required': 'Quantity is required',
            'invalid': 'Quantity must be at least 1'
        }
    )
    
    price_at_purchase = fields.Float(
        required=True,
        validate=validate.Range(min=0),
        error_messages={
            'required': 'Price at purchase is required',
            'invalid': 'Price cannot be negative'
        }
    )
    
    farmer_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1),
        error_messages={
            'required': 'Farmer ID is required',
            'invalid': 'Farmer ID must be a positive integer'
        }
    )
    
    @pre_load
    def validate_order_item(self, data, **kwargs):
        """
        Validate order item data
        """
        if data.get('quantity', 0) < 1:
            raise ValidationError(
                {'quantity': 'Quantity must be at least 1'}
            )
        
        if data.get('price_at_purchase', -1) < 0:
            raise ValidationError(
                {'price_at_purchase': 'Price cannot be negative'}
            )
        
        return data
    
    @post_load
    def prepare_order_item(self, data, **kwargs):
        """
        Prepare order item data
        """
        # Ensure status is set to pending by default
        if 'status' not in data:
            data['status'] = 'pending'
        
        return data


class OrderItemUpdateSchema(Schema):
    """
    Schema for updating order item status
    
    Used for:
    - Farmer confirm/reject individual items
    - Bulk status updates
    """
    
    status = fields.String(
        required=True,
        validate=validate.OneOf(['pending', 'confirmed', 'rejected']),
        error_messages={
            'required': 'Status is required',
            'invalid': 'Status must be one of: pending, confirmed, rejected'
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


class OrderItemBulkUpdateSchema(Schema):
    """
    Schema for bulk updating order items
    
    Used for:
    - Bulk confirm/reject by farmer
    """
    
    items = fields.List(
        fields.Nested('OrderItemUpdateSchema'),
        required=True,
        validate=validate.Length(min=1, max=50),
        error_messages={
            'required': 'Items list is required',
            'invalid': 'At least one item must be provided'
        }
    )
    
    @pre_load
    def validate_items(self, data, **kwargs):
        """
        Validate items list
        """
        items = data.get('items', [])
        
        if not items:
            raise ValidationError(
                {'items': 'At least one item must be provided'}
            )
        
        if len(items) > 50:
            raise ValidationError(
                {'items': 'Cannot update more than 50 items at once'}
            )
        
        # Check for duplicate item IDs
        item_ids = [item.get('id') for item in items if item.get('id')]
        if len(item_ids) != len(set(item_ids)):
            raise ValidationError(
                {'items': 'Duplicate item IDs found in request'}
            )
        
        return data


class OrderItemResponseSchema(Schema):
    """
    Schema for order item response
    
    Used for:
    - Order item details
    - Nested in order responses
    """
    
    id = fields.Integer()
    order_id = fields.Integer()
    animal_id = fields.Integer()
    farmer_id = fields.Integer()
    quantity = fields.Integer()
    price_at_purchase = fields.Float()
    status = fields.String()
    subtotal = fields.Float()
    
    # Animal details
    animal = fields.Nested(
        'AnimalResponseSchema',
        only=('id', 'type', 'breed', 'price')
    )
    
    # Farmer details
    farmer = fields.Nested(
        'UserResponseSchema',
        only=('id', 'email', 'role')
    )
    
    class Meta:
        fields = (
            'id', 'order_id', 'animal_id', 'farmer_id',
            'quantity', 'price_at_purchase', 'status',
            'subtotal', 'animal', 'farmer'
        )


class OrderItemSummarySchema(Schema):
    """
    Schema for order item summary (lightweight)
    
    Used for:
    - Quick order preview
    - Order history view
    """
    
    id = fields.Integer()
    animal_id = fields.Integer()
    quantity = fields.Integer()
    price_at_purchase = fields.Float()
    subtotal = fields.Float()
    
    # Minimal animal info
    animal = fields.Nested(
        'AnimalResponseSchema',
        only=('id', 'type', 'breed')
    )
    
    class Meta:
        fields = ('id', 'animal_id', 'quantity', 'price_at_purchase', 'subtotal', 'animal')


class OrderItemStatsSchema(Schema):
    """
    Schema for order item statistics
    
    Used for:
    - Farmer analytics
    - Dashboard statistics
    """
    
    total_items_sold = fields.Integer()
    total_revenue = fields.Float()
    average_price = fields.Float()
    
    # Breakdown by animal type
    by_type = fields.Dict(
        keys=fields.String(),
        values=fields.Integer()
    )
    
    # Breakdown by month
    by_month = fields.List(
        fields.Dict(
            keys=fields.String(),
            values=fields.Float()
        )
    )
    
    class Meta:
        fields = (
            'total_items_sold', 'total_revenue', 'average_price',
            'by_type', 'by_month'
        )