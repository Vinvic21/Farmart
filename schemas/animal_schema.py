from marshmallow import validate
from extensions import ma, db
from models import Animal


class AnimalSchema(ma.SQLAlchemyAutoSchema):
    #.........................................
    # Base schema used for listing, creating, updating a single animal.
    class Meta:
        model = Animal
        load_instance = True
        include_fk = True
        sqla_session = db.session

    type = ma.String(required=True, validate=validate.Length(min=2, max=50))
    breed = ma.String(required=True, validate=validate.Length(min=2, max=50))
    price = ma.Float(required=True, validate=validate.Range(min=0))
    status = ma.String(validate=validate.OneOf(["available", "pending", "sold"]))

    # farmer_id is set server-side from the logged in user, never from the client
    farmer_id = ma.Integer(dump_only=True)
    farmer = ma.Nested("UserSchema", only=("id", "email", "role"), dump_only=True)


animal_schema = AnimalSchema()
animals_schema = AnimalSchema(many=True)