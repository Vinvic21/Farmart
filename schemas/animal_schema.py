from marshmallow import Schema, fields, validate, pre_load, post_load, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from models import Animal


class AnimalSchema(SQLAlchemyAutoSchema):
    """Base Animal schema for serialization/deserialization"""
    
    class Meta:
        model = Animal
        load_instance = True
        include_fk = True
    
    type = fields.String(
        required=True,
        validate=validate.OneOf([
            'Cow', 'Goat', 'Sheep', 'Chicken', 'Pig', 'Rabbit',
            'Duck', 'Turkey', 'Donkey', 'Horse', 'Camel', 'Fish'
        ])
    )
    
    breed = fields.String(
        required=True,
        validate=validate.Length(min=2, max=50)
    )
    
    age = fields.Integer(
        validate=validate.Range(min=0, max=240),
        allow_none=True
    )
    
    price = fields.Float(
        required=True,
        validate=validate.Range(min=0)
    )
    
    status = fields.String(
        validate=validate.OneOf(['available', 'sold', 'pending']),
        load_default='available'
    )
    
    description = fields.String(
        validate=validate.Length(max=500),
        allow_none=True
    )
    
    farmer = fields.Nested('UserResponseSchema', only=('id', 'email', 'role'))
    
    @post_load
    def create_animal(self, data, **kwargs):
        return Animal(**data)


class AnimalCreateSchema(Schema):
    """Schema for creating a new animal"""
    
    type = fields.String(
        required=True,
        validate=validate.OneOf([
            'Cow', 'Goat', 'Sheep', 'Chicken', 'Pig', 'Rabbit',
            'Duck', 'Turkey', 'Donkey', 'Horse', 'Camel', 'Fish'
        ])
    )
    
    breed = fields.String(
        required=True,
        validate=validate.Length(min=2, max=50)
    )
    
    age = fields.Integer(
        validate=validate.Range(min=0, max=240),
        allow_none=True
    )
    
    price = fields.Float(
        required=True,
        validate=validate.Range(min=0)
    )
    
    status = fields.String(
        validate=validate.OneOf(['available', 'sold', 'pending']),
        load_default='available'
    )
    
    description = fields.String(
        validate=validate.Length(max=500),
        allow_none=True
    )


class AnimalUpdateSchema(Schema):
    """Schema for updating an animal"""
    
    type = fields.String(
        validate=validate.OneOf([
            'Cow', 'Goat', 'Sheep', 'Chicken', 'Pig', 'Rabbit',
            'Duck', 'Turkey', 'Donkey', 'Horse', 'Camel', 'Fish'
        ])
    )
    
    breed = fields.String(validate=validate.Length(min=2, max=50))
    age = fields.Integer(validate=validate.Range(min=0, max=240))
    price = fields.Float(validate=validate.Range(min=0))
    status = fields.String(validate=validate.OneOf(['available', 'sold', 'pending']))
    description = fields.String(validate=validate.Length(max=500))
    
    @pre_load
    def validate_update_data(self, data, **kwargs):
        if not data:
            raise ValidationError('At least one field must be provided')
        return data


class AnimalFilterSchema(Schema):
    """Schema for filtering animals"""
    
    type = fields.String()
    breed = fields.String()
    min_age = fields.Integer(validate=validate.Range(min=0))
    max_age = fields.Integer(validate=validate.Range(min=0))
    min_price = fields.Float(validate=validate.Range(min=0))
    max_price = fields.Float(validate=validate.Range(min=0))
    status = fields.String(validate=validate.OneOf(['available', 'sold', 'pending']))
    search = fields.String()
    
    @pre_load
    def validate_age_range(self, data, **kwargs):
        if data.get('min_age') and data.get('max_age'):
            if data['min_age'] > data['max_age']:
                raise ValidationError({'max_age': 'Maximum age must be greater than minimum age'})
        return data
    
    @pre_load
    def validate_price_range(self, data, **kwargs):
        if data.get('min_price') and data.get('max_price'):
            if data['min_price'] > data['max_price']:
                raise ValidationError({'max_price': 'Maximum price must be greater than minimum price'})
        return data


class AnimalResponseSchema(Schema):
    """Schema for animal response (includes farmer details)"""
    
    id = fields.Integer()
    farmer_id = fields.Integer()
    type = fields.String()
    breed = fields.String()
    age = fields.Integer()
    price = fields.Float()
    status = fields.String()
    description = fields.String()
    created_at = fields.DateTime()
    
    farmer = fields.Nested(
        'UserResponseSchema',
        only=('id', 'email', 'role')
    )
    
    class Meta:
        fields = (
            'id', 'farmer_id', 'type', 'breed', 'age', 'price',
            'status', 'description', 'created_at', 'farmer'
        )


animal_schema = AnimalSchema()
animals_schema = AnimalResponseSchema(many=True)