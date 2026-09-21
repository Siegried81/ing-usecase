"""Date precision parsing for campaign start/end dates.

Campaign dates are stored at the precision actually known from the source
(YYYY, YYYY-MM, YYYY-Qn or YYYY-MM-DD), not padded to a fake exact date.
This module turns such a string into the period of dates the true value
could fall on, and from there into the attribution window scoring.py
matches anomalies against.
"""

import calendar
import re
from datetime import date, timedelta

ATTRIBUTION_TAIL_DAYS = 21

_DAY_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_MONTH_RE = re.compile(r"^(\d{4})-(\d{2})$")
_QUARTER_RE = re.compile(r"^(\d{4})-Q([1-4])$")
_YEAR_RE = re.compile(r"^(\d{4})$")


class DateTooImprecise(Exception):
    """Raised when a date string gives only a year - too wide to window."""


def parse_period(date_str):
    """Return (period_start, period_end, precision) for a date string.

    precision is one of 'day', 'month', 'quarter'. Raises DateTooImprecise
    for a bare year, ValueError for an unrecognized format.
    """
    m = _DAY_RE.match(date_str)
    if m:
        y, mo, d = (int(x) for x in m.groups())
        d0 = date(y, mo, d)
        return d0, d0, "day"

    m = _MONTH_RE.match(date_str)
    if m:
        y, mo = (int(x) for x in m.groups())
        last_day = calendar.monthrange(y, mo)[1]
        return date(y, mo, 1), date(y, mo, last_day), "month"

    m = _QUARTER_RE.match(date_str)
    if m:
        y, q = int(m.group(1)), int(m.group(2))
        start_month = (q - 1) * 3 + 1
        end_month = start_month + 2
        last_day = calendar.monthrange(y, end_month)[1]
        return date(y, start_month, 1), date(y, end_month, last_day), "quarter"

    if _YEAR_RE.match(date_str):
        raise DateTooImprecise(date_str)

    raise ValueError(f"Unrecognized campaign date format: {date_str!r}")


def attribution_window(start_date_str, end_date_str=None):
    """Return (window_start, window_end) as date objects for matching
    anomalies to a campaign.

    window_start is the earliest date the campaign could plausibly have
    started. window_end is the latest plausible start/end of the campaign's
    known period, plus ATTRIBUTION_TAIL_DAYS. Raises DateTooImprecise if
    start_date_str is a bare year.
    """
    period_start, period_end, _precision = parse_period(start_date_str)
    tail_anchor = period_end
    if end_date_str:
        _end_start, end_period_end, _ = parse_period(end_date_str)
        tail_anchor = end_period_end

    window_end = tail_anchor + timedelta(days=ATTRIBUTION_TAIL_DAYS)
    return period_start, window_end
