from flask import Blueprint, render_template, flash
from flask_login import current_user, login_required
from habit_tracker.models import Habit
from habit_tracker.habits.forms import create_daily_habits_form


habits = Blueprint("habits", __name__)


@habits.route("/my_habits/", methods=["GET", "POST"])
@login_required
def my_habits():
    habit_list = Habit.objects(user=current_user.id, active=True)
    form = create_daily_habits_form(habit_list)
    if form.validate_on_submit():
        all_complete = True
        for habit in habit_list:
            if getattr(form, habit.name).data:
                habit.set_complete_today()
            else:
                habit.set_incomplete_today()
                all_complete = False
            habit.save()
        if all_complete:
            flash("Nice work! You have made progress on all of your habits today!", category="success")
        else:
            flash("Your habits have been updated!", category="info")
    return render_template("my_habits.html", form=form, habits=habit_list)
