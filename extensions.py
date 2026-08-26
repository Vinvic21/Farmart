# extensions.py

import os
from datetime import timedelta

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_marshmallow import Marshmallow

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
bcrypt = Bcrypt()
ma = Marshmallow()


def init_extensions(app):
    """Initialize all extensions with the app"""
    app.config.setdefault("JWT_SECRET_KEY", os.environ.get("JWT_SECRET_KEY", "farmart-dev-jwt-secret-key-please-change"))
    app.config.setdefault("JWT_ACCESS_TOKEN_EXPIRES", timedelta(hours=1))
    app.config.setdefault("JWT_REFRESH_TOKEN_EXPIRES", timedelta(days=30))
    app.config.setdefault("JWT_TOKEN_LOCATION", ["headers"])
    app.config.setdefault("JWT_HEADER_NAME", "Authorization")
    app.config.setdefault("JWT_HEADER_TYPE", "Bearer")

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}})
    bcrypt.init_app(app)
    ma.init_app(app)

    @jwt.unauthorized_loader
    def unauthorized_response(callback):
        return {"success": False, "message": "Missing or invalid token"}, 401

    @jwt.invalid_token_loader
    def invalid_token_response(callback):
        return {"success": False, "message": "Invalid token"}, 401

    @jwt.expired_token_loader
    def expired_token_response(callback):
        return {"success": False, "message": "Token has expired"}, 401

    return app