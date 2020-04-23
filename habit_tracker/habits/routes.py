from flask import Blueprint, render_template, flash, redirect, url_for, request, abort, Response
from flask_login import current_user, login_required
from habit_tracker.documents import Habit
from habit_tracker.habits.forms import AddHabitForm, RenameHabitForm
from datetime import date
from dateutil.parser import parse
from habit_tracker.habits.utils import create_habit_history_grid, create_habit_checklist, habit_strength
from matplotlib.backends.backend_svg import FigureCanvasSVG
from matplotlib.figure import Figure
from matplotlib.ticker import PercentFormatter
from matplotlib.dates import DateFormatter
from io import BytesIO


habits = Blueprint("habits", __name__)

# Set break points that determine segmentation of completion rates used to color the habit history grid
HISTORY_GRID_BREAKS = [0, 0.25, 0.5, 0.75, 1]


@habits.route("/my_habits/", methods=["GET", "POST"])
@login_required
def my_habits():
    habit_list = Habit.objects(user=current_user.id, active=True).order_by("date_created")
    num_days_in_checklist = 7

    new_habit_form = AddHabitForm()
    if new_habit_form.validate_on_submit():
        Habit(name=new_habit_form.name.data, user=current_user.id).save()
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
    longest_streaks = habit.get_longest_streaks(num=5)
    history_grid = create_habit_history_grid(habits=[habit], break_points=HISTORY_GRID_BREAKS)

    rename_habit_form = RenameHabitForm()
    rename_habit_form.current_name.data = habit.name

    if rename_habit_form.validate_on_submit():
        habit.name = rename_habit_form.new_name.data
        habit.slug = None
        habit.save()
        return redirect(url_for("habits.habit", slug=habit.slug))
    elif request.method == "GET":
        rename_habit_form.new_name.data = habit.name

    return render_template(
        "habit.html",
        habit=habit,
        title=habit.name,
        history_grid=history_grid,
        longest_streaks=longest_streaks,
        rename_habit_form=rename_habit_form
    )


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
    return redirect(url_for("habits.my_habits"))


@habits.route("/habit/<string:slug>/delete", methods=["POST"])
@login_required
def delete_habit(slug):
    habit = Habit.objects(user=current_user.id, slug=slug).get_or_404()
    name = habit.name
    habit.delete()
    flash(f"'{name}' has been deleted!", category="success")
    return redirect(url_for("habits.my_habits"))


@habits.route("/habit/<string:slug>/strength")
def plot_habit_strength(slug, max_points=60, window_size=14):
    habit = Habit.objects(user=current_user.id, slug=slug).get_or_404()

    # Determine number of dates to plot
    max_points = min(max_points, 365)
    min_points = 7
    habit_age = (date.today() - habit.date_created.date()).days
    num_points = min(max_points, max(habit_age, min_points))

    habit_strength_ts = habit_strength(habit, num_points, window_size)
    fig = Figure(figsize=(8, 5))

    axis = fig.add_subplot(1, 1, 1, ylim=(0, 1))
    axis.fill_between(
        x=habit_strength_ts.index,
        y1=0,
        y2=habit_strength_ts.values,
        color="grey"
    )

    # Format axes
    date_format = DateFormatter("%b %-d")
    axis.xaxis.set_major_formatter(date_format)
    axis.yaxis.set_major_formatter(PercentFormatter(xmax=1))
    axis.xaxis.set_ticks_position("none")
    axis.yaxis.set_ticks_position("none")
    axis.grid(color="#c9c9c9", axis="y")
    axis.margins(x=0)

    # Format spines (plot outline)
    for side in ["top", "right", "bottom", "left"]:
        axis.spines[side].set_color("#c9c9c9")

    # Reduce margins around border of plot
    fig.tight_layout()

    output = BytesIO()
    FigureCanvasSVG(fig).print_svg(output)
    return Response(output.getvalue(), mimetype="image/svg+xml")
