from extensions import ma, db
from models import Order


class OrderSchema(ma.SQLAlchemyAutoSchema):
    #.........................................
    class Meta:
        model = Order
        load_instance = True
        include_fk = True
        sqla_session = db.session

    total_items = ma.Integer(dump_only=True)
    items = ma.Nested("OrderItemSchema", many=True, dump_only=True)
    payment = ma.Nested("PaymentSchema", dump_only=True)
    buyer = ma.Nested("UserSchema", only=("id", "email", "role"), dump_only=True)


order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)