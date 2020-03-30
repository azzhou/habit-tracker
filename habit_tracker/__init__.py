from flask import Flask
from flask_mongoengine import MongoEngine
from habit_tracker.config import DevConfig


db = MongoEngine()


def create_app(config_class=DevConfig):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)
    # app.config.from_pyfile('private_config.cfg', silent=True)

    db.init_app(app)

    # Import blueprint objects after db setup
    from habit_tracker.main.routes import main  # noqa 402
    app.register_blueprint(main)

    return app
