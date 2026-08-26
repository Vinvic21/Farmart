# schemas/__init__.py

"""
Marshmallow schemas for data serialization/deserialization
"""

# User schemas
from .user_schema import (
    UserSchema,
    UserRegisterSchema,
    UserLoginSchema,
    UserResponseSchema,
)

# Profile schemas
from .profile_schema import (
    ProfileSchema,
    ProfileUpdateSchema
)

# Animal schemas
from .animal_schema import (
    AnimalSchema,
    AnimalCreateSchema,
    AnimalUpdateSchema,
    AnimalFilterSchema,
    AnimalResponseSchema
)

# Cart schemas
from .cart_schema import (
    CartSchema,
    CartCreateSchema,
    CartUpdateSchema,
    CartResponseSchema,
    CartClearSchema,
    CartSummarySchema
)

# Cart Item schemas
from .cart_item_schema import (
    CartItemSchema,
    CartItemCreateSchema,
    CartItemUpdateSchema,
    CartItemRemoveSchema,
    CartItemResponseSchema,
    CartItemBulkCreateSchema,
    CartItemSummarySchema
)

# Order schemas
from .order_schema import (
    OrderSchema,
    OrderCreateSchema,
    OrderUpdateSchema,
    OrderStatusUpdateSchema,
    OrderResponseSchema,
    OrderListResponseSchema,
    FarmerOrderResponseSchema,
    OrderHistorySchema,
    OrderTrackingSchema,
    OrderAnalyticsSchema
)

# Order Item schemas
from .order_item_schema import (
    OrderItemSchema,
    OrderItemCreateSchema,
    OrderItemUpdateSchema,
    OrderItemBulkUpdateSchema,
    OrderItemResponseSchema,
    OrderItemSummarySchema,
    OrderItemStatsSchema
)


__all__ = [
    # User
    'UserSchema',
    'UserRegisterSchema',
    'UserLoginSchema',
    'UserResponseSchema',
    
    # Profile
    'ProfileSchema',
    'ProfileUpdateSchema',
    
    # Animal
    'AnimalSchema',
    'AnimalCreateSchema',
    'AnimalUpdateSchema',
    'AnimalFilterSchema',
    'AnimalResponseSchema',
    
    # Cart
    'CartSchema',
    'CartCreateSchema',
    'CartUpdateSchema',
    'CartResponseSchema',
    'CartClearSchema',
    'CartSummarySchema',
    
    # Cart Item
    'CartItemSchema',
    'CartItemCreateSchema',
    'CartItemUpdateSchema',
    'CartItemRemoveSchema',
    'CartItemResponseSchema',
    'CartItemBulkCreateSchema',
    'CartItemSummarySchema',
    
    # Order
    'OrderSchema',
    'OrderCreateSchema',
    'OrderUpdateSchema',
    'OrderStatusUpdateSchema',
    'OrderResponseSchema',
    'OrderListResponseSchema',
    'FarmerOrderResponseSchema',
    'OrderHistorySchema',
    'OrderTrackingSchema',
    'OrderAnalyticsSchema',
    
    # Order Item
    'OrderItemSchema',
    'OrderItemCreateSchema',
    'OrderItemUpdateSchema',
    'OrderItemBulkUpdateSchema',
    'OrderItemResponseSchema',
    'OrderItemSummarySchema',
    'OrderItemStatsSchema',
    
    
]