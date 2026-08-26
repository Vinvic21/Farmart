from datetime import datetime

from extensions import db, bcrypt


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=False, default='buyer')
    created_at = db.Column(db.DateTime, default=datetime.now)

    profile = db.relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    animals = db.relationship("Animal", back_populates="farmer", cascade="all, delete-orphan")
    cart = db.relationship("Cart", back_populates="buyer", uselist=False, cascade="all, delete-orphan")
    orders = db.relationship("Order", back_populates="buyer", cascade="all, delete-orphan")

    @property
    def password(self):
        raise AttributeError('Password is write-only.')

    @password.setter
    def password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def set_password(self, password):
        self.password = password

    def verify_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def check_password(self, password):
        return self.verify_password(password)

    def is_farmer(self):
        return self.role == 'farmer'

    def is_buyer(self):
        return self.role == 'buyer'

    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f"<User {self.id} {self.email} ({self.role})>"