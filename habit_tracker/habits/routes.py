from flask import Blueprint, render_template, flash, redirect, url_for, request, abort
from flask_login import current_user, login_required
from habit_tracker.documents import Habit
from habit_tracker.habits.forms import AddHabitForm
from dateutil.parser import parse
from habit_tracker.habits.utils import (
    grid_date_labels, grid_month_labels,
    checklist_date_labels, checklist_default_values, checklist_routes
)


habits = Blueprint("habits", __name__)


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

    return render_template(
        "my_habits.html",
        new_habit_form=new_habit_form,
        habits=habit_list,
        checklist_date_labels=checklist_date_labels(num_days_in_checklist),
        checklist_default_values=checklist_default_values(habit_list, num_days_in_checklist),
        checklist_routes=checklist_routes(habit_list, num_days_in_checklist),
        grid_date_labels=grid_date_labels(),
        grid_month_labels=grid_month_labels(),
        title="My Habits"
    )


@habits.route("/habit/<string:slug>", methods=["GET", "POST"])
@login_required
def habit(slug):
    habit = Habit.objects(user=current_user.id, slug=slug).get_or_404()
    return render_template("habit.html", habit=habit)


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
