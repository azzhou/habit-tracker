from flask_wtf import FlaskForm
from wtforms import BooleanField, SubmitField


def create_daily_habits_form(habits):
    class DailyHabitsForm(FlaskForm):
        submit = SubmitField("Update")
    for habit in habits:
        habit_label = " ".join([word.capitalize() for word in habit.name.split()])
        setattr(
            DailyHabitsForm,
            habit.name,
            BooleanField(habit_label, default=habit.is_complete_today())
        )
    form = DailyHabitsForm()
    return form
