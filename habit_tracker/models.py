from habit_tracker import db
from datetime import datetime
from habit_tracker import login_manager


# Required by Flask-login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Document):
    username = db.StringField(max_length=20, unique=True, required=True)
    email = db.StringField(max_length=120, unique=True, required=True)
    password = db.StringField(max_length=60, required=True)


class Habit(db.Document):
    name = db.StringField(max_length=30, unique=False, required=True)
    user = db.ReferenceField(User, required=True)
    active = db.BooleanField(default=True)
    points = db.IntField(min_value=1, max_value=5, default=3)
    date_created = db.DateTimeField(default=datetime.utcnow)
    dates_fulfilled = db.ListField(db.DateTimeField(default=datetime.utcnow))
