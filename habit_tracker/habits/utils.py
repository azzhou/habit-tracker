from datetime import date, timedelta
from calendar import month_abbr
from flask import url_for


def date_range(start_date, end_date, reverse=False):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n) if not reverse else end_date - timedelta(n)


def _grid_start_date(end_date):
    """
    Returns the date of the first date shown in the habits history grid
    i.e. the Sunday representing the top-left corner of the grid
    """
    last_sunday = (
        end_date
        if end_date.weekday() == 6  # date is Sunday
        else end_date - timedelta(days=end_date.weekday() + 1)
    )
    return last_sunday - timedelta(weeks=52)


def grid_month_labels(end_date=date.today()):
    """
    This generates a list of month labels for the habits history grid.
    Month labels line up with the columns that contain the months' first days.
    """
    start_date = _grid_start_date(end_date)
    labels = []
    saturday_date = start_date + timedelta(days=6)  # end of first week
    while saturday_date <= end_date:
        # Add abbr for month if start of month occurs during this week
        labels.append(
            month_abbr[saturday_date.month]
            if saturday_date.day <= 7
            else ""
        )
        saturday_date += timedelta(weeks=1)

    return labels


def grid_date_labels(end_date=date.today()):
    """
    Returns list of formatted dates for one-year habit history grid.
    These labels show up in tooltips when hovering over squares in the grid.
    """
    start_date = _grid_start_date(end_date)
    return [d.strftime("%b %-d, %Y") for d in date_range(start_date, end_date, reverse=True)]


def _checklist_start_date(num_days, end_date):
    return end_date - timedelta(num_days - 1)


def checklist_date_labels(num_days, end_date=date.today()):
    start_date = _checklist_start_date(num_days, end_date)
    return [date.strftime("%-m/%-d") for date in date_range(start_date, end_date, reverse=True)]


def checklist_default_values(habits, num_days, end_date=date.today()):
    start_date = _checklist_start_date(num_days, end_date)
    return {habit.id: [habit.is_complete(date) for date in date_range(start_date, end_date, reverse=True)]
            for habit in habits}


def checklist_routes(habits, num_days, end_date=date.today()):
    start_date = _checklist_start_date(num_days, end_date)
    return {habit.id: [url_for("habits.update_habit", slug=habit.slug, date=str(date))
                       for date in date_range(start_date, end_date, reverse=True)]
            for habit in habits}
