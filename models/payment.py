from extensions import db
from datetime import datetime


class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String, nullable=False, default='mpesa')  # mpesa, cash, card, etc.
    status = db.Column(db.String, nullable=False, default='pending')  # pending, completed, failed
    transaction_ref = db.Column(db.String, unique=True, nullable=True)  # Safaricom's CheckoutRequestID
    created_at = db.Column(db.DateTime, default=datetime.now)

    order = db.relationship("Order", back_populates="payment")

    def __repr__(self):
        return f"<Payment {self.id} order_id={self.order_id} status={self.status}>"