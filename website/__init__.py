from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from pymongo.mongo_client import MongoClient
from flask_pymongo import PyMongo
import mysec
import os

db = SQLAlchemy()
DB_NAME = "database.db"

employees = None
department = None

def create_app():
    global employees, department
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    app.config["MONGO_URI"] = os.getenv('MONGO_URI')
    mongo = PyMongo(app)
    client = MongoClient(app.config["MONGO_URI"])
    d_b = client['employee_department']
    groups = d_b.groups
    department = d_b.department
    employees = d_b.employee

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User, Note

    with app.app_context():
        db.create_all()

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app



def create_database(app):
    if not path.exists('website/' + DB_NAME):
        db.create_all(app=app)
        print('Created Database!')

# def create_database(app):
#     if not path.exists('website/' + DB_NAME):
#         with app.app_context():
#             db.create_all()
#         print('Created Database!')