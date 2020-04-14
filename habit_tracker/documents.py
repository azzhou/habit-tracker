from habit_tracker import db
from datetime import datetime, date, timedelta
from habit_tracker import login_manager
from flask_login import UserMixin
from slugify import slugify


# Required by Flask-login
@login_manager.user_loader
def load_user(user_id):
    """Callback for reloading a user object from the user id stored in the session"""
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
    date_created = db.DateTimeField(default=lambda: date.today())

    meta = {
        "indexes": [
            "user",  # used as a filter in nearly all Habit queries
        ]
    }

    def set_unique_slug(self):
        """Set a unique url-friendly slug based on the habit name"""
        increment = 0
        slug = slugify(self.name) + "-" + str(increment)
        while Habit.objects(user=self.user, slug=slug):
            increment += 1
            slug = slugify(self.name) + "-" + str(increment)
        self.slug = slug

    def clean(self):
        """Perform validation / data cleaning that is run when document is saved"""
        # Default slug generated here because it depends on another class attribute
        if self.slug is None:
            self.set_unique_slug()

    def is_valid_date(self, date):
        """Check if a date is valid"""
        return date <= date.today()

    def is_complete(self, date):
        """Check if a habit had been completed on a given date"""
        date_with_time = datetime.combine(date, datetime.min.time())
        streak = HabitStreak.objects(
            habit=self.id,
            start__lte=date_with_time,
            end__gte=date_with_time
        ).first()
        return streak is not None

    def set_complete(self, date):
        """Set a habit as complete on a given date"""
        if not self.is_valid_date(date) or self.is_complete(date):
            return
        date_with_time = datetime.combine(date, datetime.min.time())
        previous_day = date_with_time - timedelta(1)
        next_day = date_with_time + timedelta(1)
        left_streak = HabitStreak.objects(habit=self.id, end=previous_day).first()
        right_streak = HabitStreak.objects(habit=self.id, start=next_day).first()

        # Add date to new or existing HabitStreak
        if left_streak is not None:
            if right_streak is not None:
                # Combine two streaks that meet at the date argument
                left_streak.end = right_streak.end
                right_streak.delete()
            else:
                # Combine date with only left_streak
                left_streak.end = date_with_time
            left_streak.save()
        elif right_streak is not None:
            # Combine date with only right_streak
            right_streak.start = date_with_time
            right_streak.save()
        else:
            # Create new streak
            HabitStreak(start=date_with_time, end=date_with_time, habit=self.id).save()

    def set_incomplete(self, date):
        """Set a habit as incomplete on a given date"""
        if not self.is_valid_date(date):
            return
        date_with_time = datetime.combine(date, datetime.min.time())
        streak = HabitStreak.objects(
            habit=self.id,
            start__lte=date_with_time,
            end__gte=date_with_time
        ).first()
        if not streak:
            return

        # Remove date from the HabitStreak that contains it
        if date_with_time == streak.start:
            if date_with_time == streak.end:
                # Delete one-day streak
                streak.delete()
            else:
                # Remove date at start of a multi-day streak
                streak.start += timedelta(1)
                streak.save()
        elif date_with_time == streak.end:
            # Remove date at end of a multi-day streak
            streak.end -= timedelta(1)
            streak.save()
        else:
            # Remove date from within a multi-day streak, i.e. split streak into two streaks
            left_streak_end = date_with_time - timedelta(1)
            right_streak_start = date_with_time + timedelta(1)
            right_streak_end = streak.end
            streak.end = left_streak_end
            streak.save()
            HabitStreak(start=right_streak_start, end=right_streak_end, habit=self.id).save()

    def toggle_complete(self, date):
        """Set a habit as completed if it is currently incomplete, otherwise set it as incomplete"""
        if not self.is_valid_date(date):
            return
        if self.is_complete(date):
            self.set_incomplete(date)
        else:
            self.set_complete(date)

    def get_longest_streak(self):
        """Get the number of days in the longest continuous completion streak for the habit"""
        longest_streak = HabitStreak.objects(habit=self.id).order_by("-streak_length").first()
        return longest_streak.streak_length if longest_streak else 0

    def __repr__(self):
        return f"Habit(name='{self.name}', user='{self.user.username}')"


class HabitStreak(db.Document):
    """Document that represents a streak of continuous days of habit completion

    This is stored in its own collection rather than as an EmbeddedDocumentListField within
    the Habit documents in order to allow for efficient querying of dates.
    """

    start = db.DateTimeField(required=True)
    """Inclusive start date of a streak of habit completions"""

    end = db.DateTimeField(required=True)
    """Inclusive end date of a streak of habit completions"""

    streak_length = db.IntField(required=True, default=1)
    habit = db.ReferenceField(Habit, required=True, reverse_delete_rule=db.CASCADE, unique_with="start")
    user = db.ReferenceField(User, reverse_delete_rule=db.CASCADE)

    meta = {
        "indexes": [
            ("habit", "start", "end"),  # frequently filtered when setting/checking habit completion
            ("habit", "-streak_length")  # used to efficiently get the longest streak for a habit
        ]
    }

    def clean(self):
        """Perform validation / data cleaning that is run when document is saved"""
        # Default user reference is set here because it depends on another class attribute
        if self.user is None:
            self.user = Habit.objects.get(id=self.habit.id).user
        # Update streak length
        self.streak_length = (self.end - self.start).days + 1

    def __repr__(self):
        start_str = f"date({self.start.strftime('%Y,%-m,%-d')})"
        end_str = f"date({self.end.strftime('%Y,%-m,%-d')})"
        return f"HabitStreak(start={start_str}, end={end_str})"
