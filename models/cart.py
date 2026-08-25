from extensions import db
from datetime import datetime

class Cart(db.Model):
    __tablename__ = "carts"


    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    buyer = db.relationship("User", back_populates="cart")
    items = db.relationship("CartItem", back_populates= "cart", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Cart {self.id} for buyer_id={self.buyer_id}>"