from habit_tracker import db
from datetime import datetime


class User(db.Document):
    username = db.StringField(max_length=20, unique=True, required=True)
    email = db.StringField(max_length=120, unique=True, required=True)
    password = db.StringField(max_length=60, required=True)


class Habit(db.Document):
    name = db.StringField(max_length=30, unique=False, required=True)
    priority = db.IntField(min_value=1, max_value=3)
    dates = db.ListField(db.DateTimeField(default=datetime.utcnow))
