from extensions import ma, db
from models import OrderItem


class OrderItemSchema(ma.SQLAlchemyAutoSchema):
    #.........................................
    class Meta:
        model = OrderItem
        load_instance = True
        include_fk = True
        sqla_session = db.session

    subtotal = ma.Float(dump_only=True)
    animal = ma.Nested(
        "AnimalSchema",
        only=("id", "type", "breed", "price", "status"),
        dump_only=True,
    )


order_item_schema = OrderItemSchema()
order_items_schema = OrderItemSchema(many=True)