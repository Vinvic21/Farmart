from extensions import db
from datetime import datetime


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String, unique=True, nullable=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String, nullable=False, default='pending')  # pending, confirmed, rejected, paid
    total_amount = db.Column(db.Float, nullable=False)

    # delivery details for the buyer
    recipient_first_name = db.Column(db.String, nullable=False)
    recipient_last_name = db.Column(db.String, nullable=False)
    recipient_phone = db.Column(db.String, nullable=False)
    delivery_address = db.Column(db.String, nullable=False)
    preferred_delivery_date = db.Column(db.Date, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.now)

    buyer = db.relationship("User", back_populates="orders")
    items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payment = db.relationship("Payment", back_populates="order", uselist=False, cascade="all, delete-orphan")

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items)

    def __repr__(self):
        return f"<Order {self.id} buyer_id={self.buyer_id} status={self.status}>"