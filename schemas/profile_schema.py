from extensions import ma, db
from models import Profile


class ProfileSchema(ma.SQLAlchemyAutoSchema):
    #.........................................
    class Meta:
        model = Profile
        load_instance = True
        include_fk = True
        sqla_session = db.session


profile_schema = ProfileSchema()
profiles_schema = ProfileSchema(many=True)