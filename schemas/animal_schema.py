from extensions import ma
from models import Animal


class AnimalSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Animal
        load_instance = True
        include_fk = True  # includes farmer_id


animal_schema = AnimalSchema()
animals_schema = AnimalSchema(many=True)