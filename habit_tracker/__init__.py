from flask import Flask
from flask_mongoengine import MongoEngine
from flask_bcrypt import Bcrypt
from flask_login import LoginManager


# Initialize flask extensions
db = MongoEngine()
bcrypt = Bcrypt()
login_manager = LoginManager()

# Route that user will be redirected to if they access a page that requires login
login_manager.login_view = "users.login"
login_manager.login_message_category = "warning"


def create_app(config="dev"):
    """Set up Habit Tracker application.

    Application factory that allows for multiple instances of the application with different settings.

    Args:
        config (str): Abbreviation for a configuration class.

    Returns:
        [Flask]: Flask application.
    """

    cfg_dict = {
        "dev": "habit_tracker.config.DevConfig",
        "prod": "habit_tracker.config.ProdConfig"
    }
    config_class = cfg_dict.get(config)
    if config_class is None:
        raise ValueError(f"The 'config' arg must be one of {list(cfg_dict.keys())}.")

    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # Import blueprint objects after db setup
    from habit_tracker.main.routes import main  # noqa 402
    from habit_tracker.users.routes import users  # noqa 402
    from habit_tracker.habits.routes import habits  # noqa 402
    from habit_tracker.errors.handlers import errors  # noqa 402
    app.register_blueprint(main)
    app.register_blueprint(users)
    app.register_blueprint(habits)
    app.register_blueprint(errors)

    return app
