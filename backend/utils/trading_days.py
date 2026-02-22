"""Trading day utilities - holidays, trading day checks, and projection calculations."""
from datetime import datetime, timedelta, timezone, date
from typing import Set, List, Dict, Optional
import logging

logger = logging.getLogger("server")


def _easter_date(year: int) -> date:
    """Calculate Easter Sunday using the Anonymous Gregorian algorithm."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    ell = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * ell) // 451
    month = (h + ell - 7 * m + 114) // 31
    day = ((h + ell - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def _observe(d: date) -> date:
    """If holiday falls on weekend, return the observed weekday."""
    if d.weekday() == 5:  # Saturday -> Friday
        return d - timedelta(days=1)
    elif d.weekday() == 6:  # Sunday -> Monday
        return d + timedelta(days=1)
    return d


def get_us_market_holidays(year: int) -> Set[str]:
    """Generate US stock market holidays for a given year.
    Returns set of date strings in YYYY-MM-DD format."""
    holidays = set()

    # Fixed holidays (adjusted for weekend observance)
    holidays.add(_observe(date(year, 1, 1)).isoformat())    # New Year's Day
    holidays.add(_observe(date(year, 6, 19)).isoformat())   # Juneteenth
    holidays.add(_observe(date(year, 7, 4)).isoformat())    # Independence Day
    holidays.add(_observe(date(year, 12, 25)).isoformat())  # Christmas

    # MLK Day - 3rd Monday of January
    d = date(year, 1, 1)
    while d.weekday() != 0:
        d += timedelta(days=1)
    holidays.add((d + timedelta(weeks=2)).isoformat())

    # Presidents' Day - 3rd Monday of February
    d = date(year, 2, 1)
    while d.weekday() != 0:
        d += timedelta(days=1)
    holidays.add((d + timedelta(weeks=2)).isoformat())

    # Good Friday - 2 days before Easter
    easter = _easter_date(year)
    holidays.add((easter - timedelta(days=2)).isoformat())

    # Memorial Day - Last Monday of May
    d = date(year, 5, 31)
    while d.weekday() != 0:
        d -= timedelta(days=1)
    holidays.add(d.isoformat())

    # Labor Day - 1st Monday of September
    d = date(year, 9, 1)
    while d.weekday() != 0:
        d += timedelta(days=1)
    holidays.add(d.isoformat())

    # Thanksgiving - 4th Thursday of November
    d = date(year, 11, 1)
    while d.weekday() != 3:
        d += timedelta(days=1)
    holidays.add((d + timedelta(weeks=3)).isoformat())

    return holidays


def get_holidays_for_range(start_year: int, end_year: int) -> Set[str]:
    """Get all US market holidays for a range of years."""
    holidays = set()
    for y in range(start_year, end_year + 1):
        holidays |= get_us_market_holidays(y)
    return holidays


def is_trading_day(dt: datetime, holidays: Set[str] = None) -> bool:
    """Check if a date is a trading day (weekday and not a holiday)."""
    if dt.weekday() >= 5:
        return False
    if holidays and dt.strftime("%Y-%m-%d") in holidays:
        return False
    return True


def get_quarter(dt: datetime) -> int:
    """Get calendar quarter number (1-4)."""
    return (dt.month - 1) // 3 + 1


def project_quarterly_growth(
    starting_value: float,
    start_date: datetime,
    trading_days_target: int = 250,
    holidays: Set[str] = None,
) -> Dict:
    """Project account growth using quarterly fixed daily profit formula.

    Formula: Daily Profit = round((Account Value at Quarter Start / 980) * 15, 2)
    Daily profit is fixed for the entire quarter, recalculated at each new quarter.

    Args:
        starting_value: Current account value
        start_date: Date to start projection from
        trading_days_target: Number of trading days to project (default 250 = ~1 year)
        holidays: Set of holiday date strings (YYYY-MM-DD)

    Returns dict with projected_value, total_profit, quarter_breakdown, trading_days
    """
    if holidays is None:
        holidays = get_holidays_for_range(start_date.year, start_date.year + 6)

    balance = starting_value
    current_date = start_date

    # Advance to first trading day
    while not is_trading_day(current_date, holidays):
        current_date += timedelta(days=1)

    current_quarter = get_quarter(current_date)
    current_year = current_date.year
    daily_profit = round((balance / 980) * 15, 2)

    trading_days = 0
    quarter_breakdown = []
    q_start_balance = balance
    q_days = 0

    while trading_days < trading_days_target:
        if not is_trading_day(current_date, holidays):
            current_date += timedelta(days=1)
            continue

        new_q = get_quarter(current_date)
        new_y = current_date.year
        if new_y != current_year or new_q != current_quarter:
            quarter_breakdown.append({
                "quarter": f"Q{current_quarter} {current_year}",
                "trading_days": q_days,
                "daily_profit": daily_profit,
                "start_value": round(q_start_balance, 2),
                "end_value": round(balance, 2),
                "quarter_profit": round(balance - q_start_balance, 2),
            })
            daily_profit = round((balance / 980) * 15, 2)
            current_quarter = new_q
            current_year = new_y
            q_start_balance = balance
            q_days = 0

        balance = round(balance + daily_profit, 2)
        trading_days += 1
        q_days += 1
        current_date += timedelta(days=1)

    # Append final quarter
    quarter_breakdown.append({
        "quarter": f"Q{current_quarter} {current_year}",
        "trading_days": q_days,
        "daily_profit": daily_profit,
        "start_value": round(q_start_balance, 2),
        "end_value": round(balance, 2),
        "quarter_profit": round(balance - q_start_balance, 2),
    })

    return {
        "projected_value": round(balance, 2),
        "total_profit": round(balance - starting_value, 2),
        "trading_days": trading_days,
        "quarter_breakdown": quarter_breakdown,
    }
