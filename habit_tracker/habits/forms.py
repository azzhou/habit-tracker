from flask_wtf import FlaskForm
from flask_login import current_user
from habit_tracker.documents import Habit
from wtforms import SubmitField, StringField
from wtforms.validators import DataRequired, Length, ValidationError


class AddHabitForm(FlaskForm):
    # inactive_habits = Habit.objects(user=current_user.id, active=False)
    name = StringField("Name", validators=[
        DataRequired(),
        Length(min=1, max=30, message="Habit name must be between 1 and 30 characters long.")
    ])
    submit = SubmitField("Add Habit")

    # User must not already have another habit with the same name
    def validate_name(self, name):
        if Habit.objects(user=current_user.id, name=name.data):
            raise ValidationError("You are already tracking that habit.")
