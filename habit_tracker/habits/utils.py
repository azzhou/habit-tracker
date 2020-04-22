from bisect import bisect
from calendar import month_abbr
from collections import namedtuple
from datetime import date, timedelta
from flask import url_for
from habit_tracker.documents import HabitStatus
from pandas import Series


def date_range(start_date, end_date, reverse=False):
    """Generator that yields datetime.date objects between specified start and end dates.

    Args:
        start_date (datetime.date): Inclusive start date of the range.
        end_date (datetime.date): Inclusive end date of the range.
        reverse (bool, optional): Whether dates should be yielded from end to start. Defaults to False.

    Yields:
        datetime.date: Current date in the range that is yielded.
    """
    for n in range((end_date - start_date).days + 1):
        yield start_date + timedelta(n) if not reverse else end_date - timedelta(n)


def _grid_start_date(end_date):
    """Calculates the first date shown in the habit history grid.

    Only meant for use in the `create_habit_history_grid` function.

    Args:
        end_date (datetime.date): Inclusive end date that is shown in the habit history grid.

    Returns:
        datetime: The date of the first Sunday shown in the top-left corner of the habit history grid.
    """
    last_sunday = (
        end_date
        if end_date.weekday() == 6  # date is Sunday
        else end_date - timedelta(days=end_date.weekday() + 1)
    )
    first_sunday = last_sunday - timedelta(weeks=52)
    return first_sunday


def _grid_month_labels(start_date, end_date):
    """Creates a list of month labels for the habit history grid.

    Only meant for use in the `create_habit_history_grid` function.

    Args:
        start_date (datetime.date): Inclusive start date that is shown in the habit history grid.
        end_date (datetime.date): Inclusive end date that is shown in the habit history grid.

    Returns:
        list[str]: List of labels for each column in the grid. Only list positions referring to
                   columns (weeks) of the grid that contain the first of a month have a
                   month abbreviation, and the rest are empty.
    """
    labels = []
    end_of_week = start_date + timedelta(days=6)
    while end_of_week <= end_date:
        # Add abbreviation for month if start of month occurs during this week
        labels.append(
            month_abbr[end_of_week.month]
            if end_of_week.day <= 7
            else ""
        )
        end_of_week += timedelta(weeks=1)

    return labels


def _grid_squares(habits, break_points, start_date, end_date):
    """Calculate values needed to render squares in the habit history grid.

    Only meant for use in the `create_habit_history_grid` function.

    Args:
        habits (iterable): Habit document objects used in the grid.
        break_points (list[int]): Break points used to divide up habit completion rates into levels.
        start_date (datetime.date): Inclusive start date that is shown in the habit history grid.
        end_date (datetime.date): Inclusive end date that is shown in the habit history grid.

    Returns:
        list[GridSquare]: List of namedtuples that have values used in the habit history grid.
    """
    GridSquare = namedtuple("GridSquare", ["num_complete", "num_active", "level", "date_label"])

    grid = []
    curr_date = start_date

    completion_per_habit = (
        [habit.get_completion_status_range(start_date, end_date) for habit in habits]
        if len(habits) > 0
        else [[None] * ((end_date - start_date).days + 1)]
    )

    completion_per_day = zip(*completion_per_habit)

    for one_day_completion in completion_per_day:
        num_complete = one_day_completion.count(HabitStatus.COMPLETE)
        num_incomplete = one_day_completion.count(HabitStatus.INCOMPLETE)
        num_active = num_complete + num_incomplete
        ratio = num_complete / num_active if num_active > 0 else 0
        level = bisect(break_points, ratio) - 1
        date_label = curr_date.strftime("%b %-d, %Y")
        curr_date += timedelta(1)
        grid.append(GridSquare(
            num_complete=num_complete,
            num_active=num_active,
            level=level,
            date_label=date_label)
        )

    return grid


def create_habit_history_grid(habits, break_points, end_date=date.today()):
    """Produce values and labels necessary to render a habit history grid for a user.

    Args:
        habits (iterable): Habit document objects used in the grid.
        break_points (list[int]): Break points used to divide up habit completion rates into levels.
        end_date (datetime.date): Inclusive end date that is shown in the habit history grid.

    Returns:
        Grid: namedtuple that includes month labels and a list of GridSquare namedtuples.
    """
    start_date = _grid_start_date(end_date)
    month_labels = _grid_month_labels(start_date, end_date)
    squares = _grid_squares(habits, break_points, start_date, end_date)
    Grid = namedtuple("Grid", ["month_labels", "squares"])
    return Grid(month_labels=month_labels, squares=squares)


def create_habit_checklist(habits, num_days, end_date=date.today()):
    """Produce the pieces necessary to render a habit checklist.

    Args:
        habits (iterable): Habit document objects used in the checklist.
        num_days (int): The number of days that are shown in the checklist.
        end_date (datetime.date, optional): Last day shown in the checklist. Defaults to date.today().

    Returns:
        HabitChecklist: namedtuple with dictionaries of labels, values, and routes used in checklist.
    """
    start_date = end_date - timedelta(num_days - 1)
    date_labels = [date.strftime("%-m/%-d") for date in date_range(start_date, end_date, reverse=True)]
    completion_statuses = {
        habit.id: [
            # Jinja templates don't support Enum classes, so use the name instead
            habit.get_completion_status(date).name
            for date in date_range(start_date, end_date, reverse=True)
        ]
        for habit in habits
    }
    routes = {
        habit.id: [
            url_for("habits.update_habit", slug=habit.slug, date=str(date))
            for date in date_range(start_date, end_date, reverse=True)
        ]
        for habit in habits
    }
    HabitChecklist = namedtuple("HabitChecklist", ["date_labels", "completion", "routes"])
    return HabitChecklist(date_labels=date_labels, completion=completion_statuses, routes=routes)


def habit_strength(habit, num_points, window_size):
    end_date = date.today()
    start_date = end_date - timedelta(num_points - 1)
    completion = habit.get_completion_status_range(start_date, end_date)
    completion_bin = [1 if c == HabitStatus.COMPLETE else 0 for c in completion]
    return Series(data=moving_avg(completion_bin, window_size),
                  index=list(date_range(start_date, end_date)),
                  name="Habit Strength")


def moving_avg(nums, window_size):
    extended_nums = [0] * window_size + nums
    moving_avg = []
    current_sum = 0
    start, end = 0, window_size
    while end < len(extended_nums):
        current_sum += extended_nums[end] - extended_nums[start]
        moving_avg.append(current_sum / window_size)
        start += 1
        end += 1
    return moving_avg
