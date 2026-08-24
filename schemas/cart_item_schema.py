from extensions import ma
from models import CartItem
from schemas.animal_schema import AnimalSchema


class CartItemSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = CartItem
        load_instance = True
        include_fk = True

    animal = ma.Nested(AnimalSchema)


cart_item_schema = CartItemSchema()
cart_items_schema = CartItemSchema(many=True)