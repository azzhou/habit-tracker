from habit_tracker import db
from datetime import datetime
from habit_tracker import login_manager
from flask_login import UserMixin
from slugify import slugify


# Required by Flask-login
@login_manager.user_loader
def load_user(user_id):
    return User.objects(pk=user_id).first()


class User(db.Document, UserMixin):
    username = db.StringField(max_length=20, unique=True, required=True)
    email = db.StringField(max_length=120, unique=True, required=True)
    password = db.StringField(max_length=60, required=True)

    def __repr__(self):
        return f"User(username='{self.username}', email='{self.email}')"


class Habit(db.Document):
    name = db.StringField(max_length=30, unique=False, required=True)
    slug = db.StringField()
    user = db.ReferenceField(User, required=True, reverse_delete_rule=db.CASCADE, unique_with="name")
    active = db.BooleanField(default=True)
    points = db.IntField(min_value=1, max_value=5, default=3)
    date_created = db.DateTimeField(default=datetime.today)
    dates_fulfilled = db.ListField(db.DateTimeField(), default=list)

    def set_unique_slug(self):
        increment = 0
        slug = slugify(self.name) + "-" + str(increment)
        while Habit.objects(user=self.user, slug=slug):
            increment += 1
            slug = slugify(self.name) + "-" + str(increment)
        self.slug = slug

    def clean(self):
        if self.slug is None:
            self.set_unique_slug()

    def is_complete_today(self):
        return self.dates_fulfilled and self.dates_fulfilled[-1].date() == datetime.today().date()

    def set_complete_today(self):
        if not self.is_complete_today():
            self.dates_fulfilled.append(datetime.today())

    def set_incomplete_today(self):
        if self.is_complete_today():
            self.dates_fulfilled.pop()

    def __repr__(self):
        return f"Habit(name='{self.name}', user='{self.user.username}')"
