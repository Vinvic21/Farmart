from marshmallow import Schema, fields, validate, ValidationError, pre_load, post_load
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from models import Cart


class CartSchema(SQLAlchemyAutoSchema):
    """
    Base Cart schema for serialization/deserialization
    
    Used for:
    - GET /api/v1/cart - Returning cart data
    - Internal cart operations
    """
    
    class Meta:
        model = Cart
        load_instance = True
        include_fk = True
    
    # Computed properties (read-only)
    total_items = fields.Integer(dump_only=True)
    total_amount = fields.Float(dump_only=True)
    
    # Nested items
    items = fields.Nested('CartItemSchema', many=True, dump_only=True)
    
    # Buyer info
    buyer = fields.Nested(
        'UserResponseSchema',
        only=('id', 'email', 'role'),
        dump_only=True
    )


class CartCreateSchema(Schema):
    """
    Schema for creating a cart (internal use)
    
    Used for:
    - Auto-creating cart for new buyers
    """
    
    buyer_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1),
        error_messages={
            'required': 'Buyer ID is required',
            'invalid': 'Buyer ID must be a positive integer'
        }
    )


class CartUpdateSchema(Schema):
    """
    Schema for updating cart (internal use)
    
    Used for:
    - Cart maintenance operations
    """
    
    # No fields needed for cart itself, items are managed separately
    pass


class CartResponseSchema(Schema):
    """
    Schema for cart response with detailed information
    
    Used for:
    - GET /api/v1/cart - Complete cart response
    """
    
    id = fields.Integer()
    buyer_id = fields.Integer()
    total_items = fields.Integer()
    total_amount = fields.Float()
    
    # Items with details
    items = fields.List(
        fields.Nested('CartItemResponseSchema')
    )
    
    # Grouped by farmer for UI
    grouped_items = fields.Method("get_grouped_items")
    
    def get_grouped_items(self, obj):
        """
        Group cart items by farmer for frontend display
        """
        grouped = {}
        
        if hasattr(obj, 'items'):
            for item in obj.items:
                if hasattr(item, 'animal') and item.animal:
                    farmer_id = item.animal.farmer_id
                    
                    if farmer_id not in grouped:
                        grouped[farmer_id] = {
                            'farmer_id': farmer_id,
                            'items': [],
                            'subtotal': 0
                        }
                    
                    grouped[farmer_id]['items'].append({
                        'id': item.id,
                        'animal_id': item.animal_id,
                        'quantity': item.quantity,
                        'subtotal': item.subtotal,
                        'animal': {
                            'id': item.animal.id,
                            'type': item.animal.type,
                            'breed': item.animal.breed,
                            'price': item.animal.price,
                            'status': item.animal.status
                        }
                    })
                    
                    grouped[farmer_id]['subtotal'] += item.subtotal
        
        # Convert to list
        return list(grouped.values())
    
    class Meta:
        fields = (
            'id', 'buyer_id', 'total_items', 
            'total_amount', 'items', 'grouped_items'
        )


class CartClearSchema(Schema):
    """
    Schema for clearing cart (validation only)
    
    Used for:
    - DELETE /api/v1/cart/clear
    """
    
    # No fields needed, just for validation consistency
    pass


class CartSummarySchema(Schema):
    """
    Schema for cart summary (lightweight)
    
    Used for:
    - Cart icon in navbar
    - Quick cart preview
    """
    
    total_items = fields.Integer()
    total_amount = fields.Float()
    item_count_by_farmer = fields.Method("get_item_count_by_farmer")
    
    def get_item_count_by_farmer(self, obj):
        """
        Count items per farmer for quick display
        """
        counts = {}
        
        if hasattr(obj, 'items'):
            for item in obj.items:
                if hasattr(item, 'animal') and item.animal:
                    farmer_id = item.animal.farmer_id
                    counts[farmer_id] = counts.get(farmer_id, 0) + item.quantity
        
        return counts
    
    class Meta:
        fields = ('total_items', 'total_amount', 'item_count_by_farmer')


cart_schema = CartSchema()
cart_summaries_schema = CartSummarySchema(many=True)