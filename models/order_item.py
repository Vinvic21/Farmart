from extensions import db


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    animal_id = db.Column(db.Integer, db.ForeignKey('animals.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price_at_purchase = db.Column(db.Float, nullable=False)  # snapshot, so historical orders stay accurate

    order = db.relationship("Order", back_populates="items")
    animal = db.relationship("Animal")

    def __repr__(self):
        return f"<OrderItem {self.id} order_id={self.order_id} animal_id={self.animal_id} qty={self.quantity}>"