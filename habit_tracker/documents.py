from habit_tracker import db
from datetime import datetime, date
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
    date_created = db.DateTimeField(default=lambda: date.today())
    dates_completed = db.SortedListField(db.DateTimeField(), default=list)

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

    def is_complete(self, date):
        # DateTimeField converts date types to datetime types, so need to combine when checking
        return datetime.combine(date, datetime.min.time()) in self.dates_completed

    def set_complete(self, date):
        if not self.is_complete(date):
            # Mongoengine documentation recommends update + push, but list doesn't get sorted that way
            self.dates_completed.append(date)
            self.save()
            self.reload()

    def set_incomplete(self, date):
        if self.is_complete(date):
            self.update(pull__dates_completed=date)
            self.save()
            self.reload()

    def __repr__(self):
        return f"Habit(name='{self.name}', user='{self.user.username}')"
