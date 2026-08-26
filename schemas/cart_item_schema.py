from marshmallow import validate
from extensions import ma, db
from models import CartItem


class CartItemSchema(ma.SQLAlchemyAutoSchema):
    #.........................................
    class Meta:
        model = CartItem
        load_instance = True
        include_fk = True
        sqla_session = db.session

    quantity = ma.Integer(validate=validate.Range(min=1, max=100))
    subtotal = ma.Float(dump_only=True)
    animal = ma.Nested("AnimalSchema", dump_only=True)


cart_item_schema = CartItemSchema()
cart_items_schema = CartItemSchema(many=True)