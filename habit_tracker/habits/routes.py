from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import current_user, login_required
from habit_tracker.models import Habit
from habit_tracker.habits.forms import create_daily_habits_form, AddHabitForm


habits = Blueprint("habits", __name__)


@habits.route("/my_habits/", methods=["GET", "POST"])
@login_required
def my_habits():
    habit_list = Habit.objects(user=current_user.id, active=True)
    daily_habits_form = create_daily_habits_form(habit_list)
    new_habit_form = AddHabitForm()
    if daily_habits_form.validate_on_submit():
        all_complete = True
        for habit in habit_list:
            if getattr(daily_habits_form, habit.name).data:
                habit.set_complete_today()
            else:
                habit.set_incomplete_today()
                all_complete = False
            habit.save()
        if all_complete:
            flash("Nice work! You have made progress on all of your habits today!", category="success")
        else:
            flash("Your habits have been updated!", category="info")
    return render_template(
        "my_habits.html",
        daily_habits_form=daily_habits_form,
        new_habit_form=new_habit_form,
        habits=habit_list,
        title="My Habits"
    )


@habits.route("/new_habit", methods=["POST"])
@login_required
def new_habit():
    form = AddHabitForm()
    if form.validate_on_submit():
        Habit(
            name=form.name.data,
            user=current_user.id,
            points=form.points.data
        ).save()
        flash(f"You have added '{form.name.data}' to your tracked habits!", category="success")
    else:
        flash(f"You are already tracking '{form.name.data}'.", category="warning")
    return redirect(url_for("habits.my_habits"))


@habits.route("/habit/<string:slug>", methods=["GET", "POST"])
@login_required
def habit(slug):
    habit = Habit.objects(slug=slug, user=current_user.id).get_or_404()
    return render_template("habit.html", habit=habit)


@habits.route("/habit/<string:slug>/delete", methods=["POST"])
@login_required
def delete_habit(slug):
    habit = Habit.objects(slug=slug, user=current_user.id).get_or_404()
    habit.delete()
    flash("Your habit has been deleted!", category="success")
    return redirect(url_for("habits.my_habits"))
