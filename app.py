from flask import Flask, jsonify
from extensions import db, ma
from flask_migrate import Migrate
from models import User, Profile, Animal, Cart, CartItem, Order, OrderItem
from controllers.animals import animals_bp
import os

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///farmart.db").replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
ma.init_app(app)

migrate = Migrate(app, db)

app.register_blueprint(animals_bp)

@app.route('/')
def home():
<<<<<<< Updated upstream
    return jsonify({"message": "Welcome to Farmrt"})
=======
    return jsonify({"message": "Welcome to Farmart"})

@app.route("/status")
def status():
    return jsonify(status="ok"), 200

>>>>>>> Stashed changes

if __name__ == '__main__':
    app.run(debug=True)