from flask import Flask
from flask_mongoengine import MonoEngine
from flaskblog.config import DevConfig


db = MonoEngine()


def create_app(config_class=DevConfig):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)
    app.config.from_pyfile('private_config.cfg', silent=True)

    db.init_app(app)

    return app
