from flask_wtf import FlaskForm  # noqa 902
from flask_login import current_user
from habit_tracker.models import Habit
from wtforms import BooleanField, SubmitField, StringField, IntegerField
from wtforms.validators import DataRequired, Length, ValidationError, NumberRange


def create_daily_habits_form(habits):
    class DailyHabitsForm(FlaskForm):
        submit = SubmitField("Update")
    for habit in habits:
        setattr(
            DailyHabitsForm,
            habit.name,
            BooleanField(habit.name, default=habit.is_complete_today())
        )
    form = DailyHabitsForm()
    return form


class AddHabitForm(FlaskForm):
    # inactive_habits = Habit.objects(user=current_user.id, active=False)
    name = StringField("Name", validators=[
        DataRequired(),
        Length(min=1, max=50, message="Name must be between 1 and 50 characters long.")
    ])
    points = IntegerField("Points", validators=[NumberRange(min=1, max=5)], default=3)
    submit = SubmitField("Add Habit")

    # User must not already have another habit with the same name
    def validate_name(self, name):
        if Habit.objects(user=current_user.id, name=name.data):
            raise ValidationError("You have previously added that habit.")
