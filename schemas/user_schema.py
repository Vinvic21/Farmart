from extensions import ma, db
from models import User


class UserSchema(ma.SQLAlchemyAutoSchema):
    #.........................................
    # Serializes/deserializes the User model. password_hash never leaves
    # the server; "password" is write-only and hashed via the model setter.
    class Meta:
        model = User
        load_instance = True
        include_fk = True
        exclude = ("password_hash",)
        sqla_session = db.session

    password = ma.String(load_only=True)
    profile = ma.Nested("ProfileSchema", exclude=("user_id",), dump_only=True)
    # Single source of truth for "display name" — first_name/last_name live

    name = ma.Method("get_name", dump_only=True)

    def get_name(self, obj):
        profile = getattr(obj, "profile", None)
        first = (getattr(profile, "first_name", None) or "").strip()
        last = (getattr(profile, "last_name", None) or "").strip()
        full = f"{first} {last}".strip()
        return full or None


user_schema = UserSchema()
users_schema = UserSchema(many=True)