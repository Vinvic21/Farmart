from marshmallow import Schema, fields, validate, ValidationError, pre_load, post_load
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from models import User


class UserSchema(SQLAlchemyAutoSchema):
    """Base User schema for serialization"""
    
    class Meta:
        model = User
        load_instance = True
        include_fk = True
        exclude = ('password_hash',)
    
    password = fields.String(
        required=False,
        load_only=True,
        validate=validate.Length(min=6, max=128)
    )
    confirm_password = fields.String(
        required=False,
        load_only=True
    )
    
    role = fields.String(
        validate=validate.OneOf(['farmer', 'buyer', 'admin']),
        load_default='buyer'
    )
    
    email = fields.Email(required=True, validate=validate.Length(max=255))
    
    profile = fields.Nested('ProfileSchema', exclude=('user_id',), required=False)
    
    @pre_load
    def validate_password_match(self, data, **kwargs):
        if data.get('password') and data.get('confirm_password'):
            if data['password'] != data['confirm_password']:
                raise ValidationError({'confirm_password': 'Passwords do not match'})
        return data
    
    @post_load
    def make_user(self, data, **kwargs):
        password = data.pop('password', None)
        data.pop('confirm_password', None)
        
        user = User(**data)
        if password:
            user.password = password
        return user


class UserRegisterSchema(Schema):
    """Schema for user registration"""
    
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=6))
    confirm_password = fields.String(required=True)
    role = fields.String(validate=validate.OneOf(['farmer', 'buyer']), load_default='buyer')
    phone = fields.String(validate=validate.Length(max=20))
    location = fields.String(validate=validate.Length(max=255))
    
    @pre_load
    def validate_password_match(self, data, **kwargs):
        if data.get('password') and data.get('confirm_password'):
            if data['password'] != data['confirm_password']:
                raise ValidationError({'confirm_password': 'Passwords do not match'})
        return data
    
    @post_load
    def create_user_dict(self, data, **kwargs):
        data.pop('confirm_password', None)
        if 'role' not in data:
            data['role'] = 'buyer'
        return data


class UserLoginSchema(Schema):
    """Schema for user login"""
    
    email = fields.Email(required=True)
    password = fields.String(required=True)
    
    @pre_load
    def validate_login_data(self, data, **kwargs):
        if not data.get('email'):
            raise ValidationError({'email': 'Email is required'})
        if not data.get('password'):
            raise ValidationError({'password': 'Password is required'})
        return data


class UserResponseSchema(Schema):
    """Schema for user response (excludes sensitive data)"""
    
    id = fields.Integer()
    email = fields.Email()
    role = fields.String()
    created_at = fields.DateTime()
    profile = fields.Nested('ProfileSchema', exclude=('user_id',))
    
    class Meta:
        fields = ('id', 'email', 'role', 'created_at', 'profile')