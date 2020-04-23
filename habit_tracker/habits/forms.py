from flask_wtf import FlaskForm
from flask_login import current_user
from habit_tracker.documents import Habit
from wtforms import SubmitField, StringField
from wtforms.validators import DataRequired, Length, ValidationError


class AddHabitForm(FlaskForm):
    name = StringField("Name", validators=[
        DataRequired(),
        Length(min=1, max=30, message="Habit name must be between 1 and 30 characters long.")
    ])
    submit = SubmitField("Add Habit")

    # User must not already have another habit with the same name
    def validate_name(self, name):
        if Habit.objects(user=current_user.id, name=name.data):
            raise ValidationError("You are already tracking that habit.")


class RenameHabitForm(FlaskForm):
    current_name = StringField("Current Name")
    new_name = StringField("New name", validators=[
        DataRequired(),
        Length(min=1, max=30, message="Habit name must be between 1 and 30 characters long.")
    ])
    submit = SubmitField("Submit")

    # New name must be different from current_name and other habit names that the user is tracking
    def validate_new_name(self, name):
        if self.new_name.data == self.current_name.data:
            raise ValidationError("The new habit name must be different from the current name.")
        elif Habit.objects(user=current_user.id, name=name.data):
            raise ValidationError(f"You are already tracking another habit named '{name.data}'.")
