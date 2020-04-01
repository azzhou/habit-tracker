from flask import Blueprint, render_template
from flask_login import current_user, login_required
from habit_tracker.models import Habit


habits = Blueprint("habits", __name__)


@habits.route("/habits/")
@login_required
def habit_list():
    habit_list = Habit.objects(user=current_user.id, active=True)
    return render_template("habits.html", habits=habit_list)
