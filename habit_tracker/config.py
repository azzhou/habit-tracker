import os


class Config:
    """Base Flask configuration values"""
    DEBUG = False
    TESTING = False
    SECRET_KEY = "secretkey"
    MONGODB_HOST = "mongodb://localhost/habit_tracker"


class DevConfig(Config):
    DEBUG = True


class ProdConfig(Config):
    user = os.environ["ATLAS_USER"]
    password = os.environ["ATLAS_PASS"]
    MONGODB_HOST = (f"mongodb+srv://{user}:{password}@habittracker-abi1c.mongodb.net/"
                    "habit_tracker?retryWrites=true&w=majority")
    SECRET_KEY = os.environ["SECRET_KEY"]
