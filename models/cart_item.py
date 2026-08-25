from extensions import db
from datetime import datetime

class CartItem(db.Model):
    __tablename__ = "cart_items"

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey("carts.id"), nullable=False)
    animal_id = db.Column(db.Integer, db.ForeignKey("animals.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.now)

    cart = db.relationship("Cart", back_populates="items")
    animal = db.relationship("Animal")

    __table_args__ = (
        db.UniqueConstraint('cart_id', 'animal_id', name='unique_cart_animal'),
    )

    def __repr__(self):
        return f"<CartItem {self.id} (cart_id={self.cart_id}, animal_id={self.animal_id}, quantity={self.quantity})>"