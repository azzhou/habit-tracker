from flask import Flask
from flask_mongoengine import MongoEngine
from habit_tracker.config import DevConfig
from flask_bcrypt import Bcrypt
from flask_login import LoginManager


# Initialize flask extensions
db = MongoEngine()
bcrypt = Bcrypt()
login_manager = LoginManager()

# Route that user will be redirected to if they access a page that requires login
login_manager.login_view = "users.login"
login_manager.login_message_category = "warning"


def create_app(config_class=DevConfig):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)
    # app.config.from_pyfile('private_config.cfg', silent=True)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # Import blueprint objects after db setup
    from habit_tracker.main.routes import main  # noqa 402
    from habit_tracker.users.routes import users  # noqa 402
    app.register_blueprint(main)
    app.register_blueprint(users)

    return app
