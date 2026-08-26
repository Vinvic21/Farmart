from marshmallow import Schema, fields, validate, post_load
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from models import Profile


class ProfileSchema(SQLAlchemyAutoSchema):
    """Profile schema for serialization/deserialization"""
    
    class Meta:
        model = Profile
        load_instance = True
        include_fk = True
    
    phone = fields.String(
        validate=validate.Length(max=20),
        allow_none=True
    )
    
    location = fields.String(
        validate=validate.Length(max=255),
        allow_none=True
    )
    
    verification_status = fields.String(
        validate=validate.OneOf(['pending', 'verified', 'rejected']),
        load_default='pending'
    )
    
    @post_load
    def create_profile(self, data, **kwargs):
        return Profile(**data)


class ProfileUpdateSchema(Schema):
    """Schema for updating profile"""
    
    phone = fields.String(validate=validate.Length(max=20))
    location = fields.String(validate=validate.Length(max=255))
    verification_status = fields.String(validate=validate.OneOf(['pending', 'verified', 'rejected']))