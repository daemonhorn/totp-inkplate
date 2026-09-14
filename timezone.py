"""Local-time display formatting: a fixed UTC offset plus optional US DST.

This only affects how times are *displayed* (e.g. the "valid until" line).
TOTP itself always uses true Unix UTC time -- see totp.py / normal_mode.py.

Deliberately does not use time.localtime()/time.gmtime(): those behave
differently between CPython (localtime applies the host's real timezone)
and MicroPython (always UTC-naive, and this board's epoch is 2000-01-01,
not 1970-01-01) -- exactly the kind of platform epoch/timezone mismatch
that caused a real TOTP-correctness bug earlier in this project. So all
calendar math here is pure integer arithmetic (Howard Hinnant's
civil_from_days/days_from_civil, public domain), giving identical,
CPython-testable results on both platforms, with no dependency on any
platform time function's epoch or timezone behavior.
"""

_SECONDS_PER_DAY = 86400


def _days_from_civil(y, m, d):
    y -= 1 if m <= 2 else 0
    era = (y if y >= 0 else y - 399) // 400
    yoe = y - era * 400
    doy = (153 * (m + (-3 if m > 2 else 9)) + 2) // 5 + d - 1
    doe = yoe * 365 + yoe // 4 - yoe // 100 + doy
    return era * 146097 + doe - 719468


def _civil_from_days(z):
    z += 719468
    era = (z if z >= 0 else z - 146096) // 146097
    doe = z - era * 146097
    yoe = (doe - doe // 1460 + doe // 36524 - doe // 146096) // 365
    y = yoe + era * 400
    doy = doe - (365 * yoe + yoe // 4 - yoe // 100)
    mp = (5 * doy + 2) // 153
    d = doy - (153 * mp + 2) // 5 + 1
    m = mp + 3 if mp < 10 else mp - 9
    return (y + (1 if m <= 2 else 0), m, d)


def _weekday(unix_time):
    """0=Monday .. 6=Sunday. 1970-01-01 (day 0) was a Thursday."""
    days = int(unix_time) // _SECONDS_PER_DAY
    return (days + 3) % 7


def unix_to_ymdhms(unix_time):
    """True Unix time -> (year, month, day, hour, minute, second)."""
    unix_time = int(unix_time)
    days, secs = divmod(unix_time, _SECONDS_PER_DAY)
    y, m, d = _civil_from_days(days)
    hh, rem = divmod(secs, 3600)
    mm, ss = divmod(rem, 60)
    return y, m, d, hh, mm, ss


def ymd_to_unix(y, m, d, hh=0, mm=0, ss=0):
    return _days_from_civil(y, m, d) * _SECONDS_PER_DAY + hh * 3600 + mm * 60 + ss


def _nth_sunday_midnight(year, month, n):
    """True-Unix-time midnight of the nth Sunday of `month` in `year`."""
    first_of_month = ymd_to_unix(year, month, 1)
    days_to_first_sunday = (6 - _weekday(first_of_month)) % 7
    return first_of_month + (days_to_first_sunday + 7 * (n - 1)) * _SECONDS_PER_DAY


def us_dst_active(unix_time, standard_offset_hours):
    """Whether US DST is in effect at `unix_time` (true Unix UTC seconds).

    US rule: DST runs from 2:00am local *standard* time on the 2nd Sunday
    of March to 2:00am local *standard* time on the 1st Sunday of November.
    (The real rule specifies the November end in local *daylight* time,
    2:00am, which is the same instant as 1:00am standard time -- using
    standard time for both endpoints trades an hour of precision right at
    the transition itself, around 1-2am on the transition day, for a much
    simpler calculation. Irrelevant to TOTP correctness either way, since
    this module only affects a display label.)
    """
    year, _m, _d, _hh, _mm, _ss = unix_to_ymdhms(unix_time)
    offset_s = standard_offset_hours * 3600
    dst_start = _nth_sunday_midnight(year, 3, 2) + 2 * 3600 - offset_s
    dst_end = _nth_sunday_midnight(year, 11, 1) + 2 * 3600 - offset_s
    return dst_start <= unix_time < dst_end


def local_offset_seconds(unix_time, standard_offset_hours, observe_us_dst):
    offset_s = standard_offset_hours * 3600
    if observe_us_dst and us_dst_active(unix_time, standard_offset_hours):
        offset_s += 3600
    return offset_s


def format_local(unix_time, standard_offset_hours, observe_us_dst):
    """'HH:MM:SS (UTC-05:00)'-style string for `unix_time` (true Unix UTC)."""
    offset_s = local_offset_seconds(unix_time, standard_offset_hours, observe_us_dst)
    _y, _m, _d, hh, mm, ss = unix_to_ymdhms(unix_time + offset_s)
    offset_hh, rem_s = divmod(abs(offset_s), 3600)
    offset_mm = rem_s // 60
    sign = "-" if offset_s < 0 else "+"
    return "%02d:%02d:%02d (UTC%s%02d:%02d)" % (hh, mm, ss, sign, offset_hh, offset_mm)
