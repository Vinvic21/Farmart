from extensions import db
from datetime import datetime

class Cart(db.Model):
    __tablename__ = "carts"


    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    buyer = db.relationship("User", back_populates="cart")
    items = db.relationship("CartItem", back_populates= "cart", cascade="all, delete-orphan")

    @property
    def total_items(self):
        """Total quantity of all items in the cart."""
        return sum(item.quantity for item in self.items)

    @property
    def total_amount(self):
        """Total monetary value of everything in the cart."""
        return sum(item.subtotal for item in self.items)

    def clear(self):
        """Remove every item from the cart."""
        for item in list(self.items):
            db.session.delete(item)
        self.items = []

    def __repr__(self):
        return f"<Cart {self.id} for buyer_id={self.buyer_id}>"