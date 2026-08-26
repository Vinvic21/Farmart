# models/animal.py
from extensions import db



class Animal(db.Model):
    __tablename__ = "animals"


    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    type = db.Column(db.String, nullable=False)      
    breed = db.Column(db.String)
    age = db.Column(db.Integer)
    price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String, default="available")  
    description = db.Column(db.Text)

    farmer = db.relationship("User", back_populates="animals")

    def is_available(self):
        """Whether this animal can currently be added to a cart / ordered."""
        return self.status == "available"

    def __repr__(self):
        return f"<Animal {self.id} ({self.type}, {self.breed}) owned by farmer_id={self.farmer_id}>"