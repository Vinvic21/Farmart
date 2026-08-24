from extensions import ma
from models import Cart
from schemas.cart_item_schema import CartItemSchema


class CartSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Cart
        load_instance = True
        include_fk = True

    items = ma.Nested(CartItemSchema, many=True)


cart_schema = CartSchema()