from extensions import ma, db
from models import Cart


class CartSchema(ma.SQLAlchemyAutoSchema):
    #.........................................
    class Meta:
        model = Cart
        load_instance = True
        include_fk = True
        sqla_session = db.session

    total_items = ma.Integer(dump_only=True)
    total_amount = ma.Float(dump_only=True)
    items = ma.Nested("CartItemSchema", many=True, dump_only=True)


cart_schema = CartSchema()
carts_schema = CartSchema(many=True)