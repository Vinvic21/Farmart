
from extensions import db

class Profile(db.Model):
    __tablename__ = "profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    phone = db.Column(db.String)
    location = db.Column(db.String)
    verification_status = db.Column(db.String, default="pending")

    user = db.relationship("User", back_populates="profile")

    def __repr__(self):
        return f"<Profile {self.id} for user_id={self.user_id}>"