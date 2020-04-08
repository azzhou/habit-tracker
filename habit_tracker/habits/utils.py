from datetime import date, timedelta
from calendar import month_abbr


def _grid_start_date(end_date=date.today()):
    """Returns the date of the first Sunday shown in the habits history grid"""
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
    """Returns list of formatted dates for one-year habit history grid"""
    start_date = _grid_start_date(end_date)
    return [d.strftime("%b %-d, %Y")
            for d in (start_date + timedelta(i)
                      for i in range((end_date - start_date).days + 1))]


def checkbox_dates(num_days, end_date=date.today()):
    return [end_date - timedelta(d) for d in range(num_days)]
