from flask import Blueprint, render_template, flash, redirect, url_for, request, abort
from flask_login import current_user, login_required
from habit_tracker.documents import Habit
from habit_tracker.habits.forms import AddHabitForm
from dateutil.parser import parse
from habit_tracker.habits.utils import create_habit_history_grid, create_habit_checklist


habits = Blueprint("habits", __name__)

# Set break points that determine segmentation of completion rates used to color the habit history grid
HISTORY_GRID_BREAKS = [0, 0.25, 0.5, 0.75, 1]


@habits.route("/my_habits/", methods=["GET", "POST"])
@login_required
def my_habits():
    habit_list = Habit.objects(user=current_user.id, active=True)
    num_days_in_checklist = 7

    new_habit_form = AddHabitForm()
    if new_habit_form.validate_on_submit():
        Habit(name=new_habit_form.name.data, user=current_user.id).save()
        flash(f"You have added '{new_habit_form.name.data}' to your tracked habits!", category="success")
        return redirect(url_for("habits.my_habits"))

    checklist = create_habit_checklist(habits=habit_list, num_days=num_days_in_checklist)
    history_grid = create_habit_history_grid(habits=habit_list, break_points=HISTORY_GRID_BREAKS)
    return render_template(
        "my_habits.html",
        new_habit_form=new_habit_form,
        habits=habit_list,
        checklist=checklist,
        history_grid=history_grid,
        title="My Habits"
    )


@habits.route("/habit/<string:slug>", methods=["GET", "POST"])
@login_required
def habit(slug):
    habit = Habit.objects(user=current_user.id, slug=slug).get_or_404()
    return render_template("habit.html", habit=habit, title=habit.name)


@habits.route("/habit/<string:slug>/update", methods=["POST"])
@login_required
def update_habit(slug):
    habit = Habit.objects(user=current_user.id, slug=slug).get_or_404()
    date_string = request.args.get("date")
    if date_string:
        try:
            my_date = parse(date_string).date()
            habit.toggle_complete(my_date)
        except ValueError:
            return abort(400)
    else:
        return abort(400)
    flash(f"'{habit.name}' has been updated!", category="success")
    return redirect(url_for("habits.my_habits"))


@habits.route("/habit/<string:slug>/delete", methods=["POST"])
@login_required
def delete_habit(slug):
    habit = Habit.objects(user=current_user.id, slug=slug).get_or_404()
    habit.delete()
    flash("Your habit has been deleted!", category="success")
    return redirect(url_for("habits.my_habits"))
