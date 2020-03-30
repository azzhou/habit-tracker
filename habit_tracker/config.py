class Config:
    """Base Flask configuration values"""
    DEBUG = False
    TESTING = False
    SECRET_KEY = "secretkey"
    MONGODB_HOST = "mongodb://localhost/habit_tracker"


class DevConfig(Config):
    DEBUG = True


class ProdConfig(Config):
    pass
