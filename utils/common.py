
from datetime import datetime, date, timedelta


def get_calendar_week():
    """
    Returns list for selection
    """
    week_list = []
    for week_date in range(1, 54):
        week_list.append((str(week_date), "W" + str(week_date)))
    return week_list


def get_week_dates(week_name, year=None):
    """
    Returns the start (Monday) and end (Sunday) dates of the given week.
    week_name: str, e.g., 'KW52'
    year: int, defaults to current year
    """
    if not year:
        year = date.today().year

    week_number = int(week_name.replace('KW', ''))
    
    # ISO week: Monday is day 1, Sunday is day 7
    first_day = datetime.fromisocalendar(year, week_number, 1)  # Monday
    last_day = datetime.fromisocalendar(year, week_number, 7)   # Sunday
    return first_day, last_day

def get_current_week_date_range(new_iso_week=None):
    today = date.today()
    iso_year_today, current_week, _ = today.isocalendar()

    # Use the provided iso_week and iso_year if given, otherwise default to current
    week = new_iso_week or current_week
    year = iso_year_today

    # ISO weeks start on Monday
    # The first ISO week always has January 4th in it
    first_day_of_year = date(year, 1, 4)
    first_monday = first_day_of_year - timedelta(days=first_day_of_year.isoweekday() - 1)
    start_date = first_monday + timedelta(weeks=week - 1)
    end_date = start_date + timedelta(days=6)

    return start_date, end_date
