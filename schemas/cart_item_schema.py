from marshmallow import Schema, fields, validate, ValidationError, pre_load, post_load
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from models import CartItem


class CartItemSchema(SQLAlchemyAutoSchema):
    """
    Cart Item schema for serialization/deserialization
    
    Used for:
    - Displaying cart items
    - Calculating subtotals
    """
    
    class Meta:
        model = CartItem
        load_instance = True
        include_fk = True
    
    # Computed property (read-only)
    subtotal = fields.Float(dump_only=True)
    
    # Nested animal data
    animal = fields.Nested(
        'AnimalResponseSchema',
        only=('id', 'type', 'breed', 'price', 'status', 'farmer_id'),
        dump_only=True
    )
    
    # Farmer info (from the animal)
    farmer = fields.Nested(
        'UserResponseSchema',
        only=('id', 'email', 'role'),
        dump_only=True
    )


class CartItemCreateSchema(Schema):
    """
    Schema for adding an item to cart
    
    Used for:
    - POST /api/v1/cart/items - Add to cart
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
        validate=validate.Range(min=1, max=100),
        error_messages={
            'required': 'Quantity is required',
            'invalid': 'Quantity must be between 1 and 100'
        }
    )
    
    @pre_load
    def validate_quantity(self, data, **kwargs):
        """
        Validate quantity is positive and within limits
        """
        quantity = data.get('quantity', 0)
        
        if quantity < 1:
            raise ValidationError(
                {'quantity': 'Quantity must be at least 1'}
            )
        
        if quantity > 100:
            raise ValidationError(
                {'quantity': 'Quantity cannot exceed 100'}
            )
        
        return data
    
    @pre_load
    def validate_animal_id(self, data, **kwargs):
        """
        Validate animal_id is provided
        """
        if not data.get('animal_id'):
            raise ValidationError(
                {'animal_id': 'Animal ID is required'}
            )
        
        return data


class CartItemUpdateSchema(Schema):
    """
    Schema for updating cart item quantity
    
    Used for:
    - PUT /api/v1/cart/items/<id> - Update quantity
    """
    
    quantity = fields.Integer(
        required=True,
        validate=validate.Range(min=1, max=100),
        error_messages={
            'required': 'Quantity is required',
            'invalid': 'Quantity must be between 1 and 100'
        }
    )
    
    @pre_load
    def validate_quantity(self, data, **kwargs):
        """
        Validate quantity is positive and within limits
        """
        quantity = data.get('quantity', 0)
        
        if quantity < 1:
            raise ValidationError(
                {'quantity': 'Quantity must be at least 1'}
            )
        
        if quantity > 100:
            raise ValidationError(
                {'quantity': 'Quantity cannot exceed 100'}
            )
        
        return data
    
    @pre_load
    def validate_update_data(self, data, **kwargs):
        """
        Ensure quantity is provided
        """
        if not data:
            raise ValidationError(
                {'_schema': 'At least one field must be provided'}
            )
        
        if 'quantity' not in data:
            raise ValidationError(
                {'quantity': 'Quantity is required for update'}
            )
        
        return data


class CartItemRemoveSchema(Schema):
    """
    Schema for removing cart item (simple schema for validation)
    
    Used for:
    - DELETE /api/v1/cart/items/<id> - Remove from cart
    """
    
    # No fields needed, just for validation consistency
    pass


class CartItemResponseSchema(Schema):
    """
    Schema for cart item response with full details
    
    Used for:
    - Nested in CartResponseSchema
    - Cart item details
    """
    
    id = fields.Integer()
    cart_id = fields.Integer()
    animal_id = fields.Integer()
    quantity = fields.Integer()
    subtotal = fields.Float()
    
    # Animal details
    animal = fields.Nested(
        'AnimalResponseSchema',
        only=('id', 'type', 'breed', 'price', 'status', 'description', 'image_url')
    )
    
    # Farmer details
    farmer = fields.Nested(
        'UserResponseSchema',
        only=('id', 'email', 'role')
    )
    
    class Meta:
        fields = (
            'id', 'cart_id', 'animal_id', 'quantity', 
            'subtotal', 'animal', 'farmer'
        )


class CartItemBulkCreateSchema(Schema):
    """
    Schema for bulk adding items to cart
    
    Used for:
    - Bulk add operations
    """
    
    items = fields.List(
        fields.Nested('CartItemCreateSchema'),
        required=True,
        validate=validate.Length(min=1, max=20),
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
        
        if len(items) > 20:
            raise ValidationError(
                {'items': 'Cannot add more than 20 items at once'}
            )
        
        # Check for duplicate animal_ids
        animal_ids = [item.get('animal_id') for item in items if item.get('animal_id')]
        if len(animal_ids) != len(set(animal_ids)):
            raise ValidationError(
                {'items': 'Duplicate animal IDs found in request'}
            )
        
        return data


class CartItemSummarySchema(Schema):
    """
    Schema for cart item summary (lightweight)
    
    Used for:
    - Quick cart preview
    - Mini cart display
    """
    
    id = fields.Integer()
    animal_id = fields.Integer()
    quantity = fields.Integer()
    subtotal = fields.Float()
    
    # Minimal animal info
    animal = fields.Nested(
        'AnimalResponseSchema',
        only=('id', 'type', 'breed', 'price')
    )

    class Meta:
        fields = ('id', 'animal_id', 'quantity', 'subtotal', 'animal')


cart_item_schema = CartItemSchema()
cart_items_schema = CartItemSchema(many=True)