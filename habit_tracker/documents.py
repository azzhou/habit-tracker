from habit_tracker import db
from datetime import datetime, date, timedelta
from habit_tracker import login_manager
from flask_login import UserMixin
from slugify import slugify
from enum import Enum


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


class HabitStatus(Enum):
    COMPLETE = 1
    INCOMPLETE = 2
    INACTIVE = 3


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

    def is_active_date(self, date):
        """Check if a habit is active on a given date"""
        return self.date_created.date() <= date <= date.today()

    def get_completion_status(self, date):
        """Return whether a habit is complete, incomplete, or inactive on a given date.

        Args:
            date (datetime.date): Date for which we are checking a habit's status.

        Returns:
            HabitStatus: Enum representing habit completion status.
        """
        date_with_time = datetime.combine(date, datetime.min.time())
        if not self.is_active_date(date):
            return HabitStatus.INACTIVE
        streak = HabitStreak.objects(
            habit=self.id,
            start__lte=date_with_time,
            end__gte=date_with_time
        ).first()
        return HabitStatus.COMPLETE if streak is not None else HabitStatus.INCOMPLETE

    def get_completion_status_range(self, start_date, end_date):
        """Get a list of habit completion statuses between a start and end date.

        Args:
            start_date (datetime.date): Inclusive start date of range.
            end_date (datetime.date): Inclusive end date of range.

        Returns:
            list[HabitStatus]: List containing completion status of a habit for the range of dates.
        """
        start_date = datetime.combine(start_date, datetime.min.time())
        end_date = datetime.combine(end_date, datetime.min.time())
        # List has incomplete status as default
        completion_list = [HabitStatus.INCOMPLETE] * ((end_date - start_date).days + 1)
        streaks = HabitStreak.objects(
            habit=self.id,
            start__lte=end_date,
            end__gte=start_date
        )
        # Replace those that are complete
        for streak in streaks:
            start = max(0, (streak.start - start_date).days)
            end = min(len(completion_list), (streak.end - start_date).days + 1)
            completion_list[start:end] = [HabitStatus.COMPLETE] * (end - start)
        # Replace those that are inactive
        if start_date < self.date_created:
            inactive_days = (self.date_created - start_date).days
            completion_list[:inactive_days] = [HabitStatus.INACTIVE] * inactive_days
        return completion_list

    def set_complete(self, date):
        """Set a habit as complete on a given date"""
        if (not self.is_active_date(date) or
                self.get_completion_status(date) == HabitStatus.COMPLETE):
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
        if not self.is_active_date(date):
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
        if not self.is_active_date(date):
            return
        if self.get_completion_status(date) == HabitStatus.COMPLETE:
            self.set_incomplete(date)
        else:
            self.set_complete(date)

    def get_longest_streaks(self, num=1):
        """Get the longest `num` streaks for the habit"""
        return HabitStreak.objects(habit=self.id).order_by("-streak_length")[:num]

    def get_recent_streaks(self, num=1):
        """Get the most recent `num` streaks for the habit"""
        return HabitStreak.objects(habit=self.id).order_by("-start")[:num]

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

    streak_length = db.IntField()
    habit = db.ReferenceField(Habit, required=True, reverse_delete_rule=db.CASCADE, unique_with="start")
    user = db.ReferenceField(User, reverse_delete_rule=db.CASCADE)

    meta = {
        "indexes": [
            # frequently filtered when setting/checking habit completion
            ("habit", "start", "end"),

            # used to efficiently get the longest streak for a habit
            ("habit", "-streak_length")
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
