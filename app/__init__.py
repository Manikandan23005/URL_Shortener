from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os

db = SQLAlchemy()
 
def create_app():
    app = Flask(__name__,template_folder='templates', static_folder='static')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./site.db'
    #app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost:5432/postgresdb'
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"
    )
    
    limiter.init_app(app)
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    bcrypt = Bcrypt(app)

    from app.models import User
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    from app.route import register_routes
    register_routes(app, db, bcrypt, limiter)

    migrate=Migrate(app, db)
    return app

