from extensions import ma, db
from models import Payment


class PaymentSchema(ma.SQLAlchemyAutoSchema):
    #.........................................
    class Meta:
        model = Payment
        load_instance = True
        include_fk = True
        sqla_session = db.session


payment_schema = PaymentSchema()
payments_schema = PaymentSchema(many=True)