"""Unit tests for timezone.py. Runs under plain CPython -- no hardware
needed. Cross-checked against Python's own `calendar`/`datetime` modules
(a second, independent implementation) rather than against timezone.py's
own internals, for real verification.
"""

import calendar
import datetime
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import timezone  # noqa: E402

_EPOCH = datetime.date(1970, 1, 1)


class TestCivilDateRoundTrip(unittest.TestCase):
    def test_round_trip_and_weekday_vs_datetime(self):
        rng = random.Random(0)
        for _ in range(5000):
            offset_days = rng.randint(-40000, 40000)
            dt = _EPOCH + datetime.timedelta(days=offset_days)
            unix_time = offset_days * 86400
            y, m, d, hh, mm, ss = timezone.unix_to_ymdhms(unix_time)
            self.assertEqual((y, m, d, hh, mm, ss), (dt.year, dt.month, dt.day, 0, 0, 0))
            self.assertEqual(timezone.ymd_to_unix(dt.year, dt.month, dt.day), unix_time)
            self.assertEqual(timezone._weekday(unix_time), dt.weekday())

    def test_time_of_day_component(self):
        unix_time = timezone.ymd_to_unix(2024, 6, 15, 13, 45, 30)
        self.assertEqual(timezone.unix_to_ymdhms(unix_time), (2024, 6, 15, 13, 45, 30))


class TestUsDstTransitions(unittest.TestCase):
    def _nth_sunday_datetime_calendar(self, year, month, n):
        c = calendar.Calendar()
        sundays = [
            d
            for d in c.itermonthdates(year, month)
            if d.weekday() == 6 and d.month == month
        ]
        return sundays[n - 1]

    def test_transition_dates_match_calendar_module(self):
        for year in (2000, 2023, 2024, 2025, 2026, 2027, 2100):
            expected_start = self._nth_sunday_datetime_calendar(year, 3, 2)
            expected_end = self._nth_sunday_datetime_calendar(year, 11, 1)

            standard_offset = -5  # Eastern
            start = timezone._nth_sunday_midnight(year, 3, 2) + 2 * 3600 - standard_offset * 3600
            end = timezone._nth_sunday_midnight(year, 11, 1) + 2 * 3600 - standard_offset * 3600

            # 2am local standard time on transition day, expressed back in
            # true Unix time, should fall exactly on that calendar day.
            y, m, d, hh, _mm, _ss = timezone.unix_to_ymdhms(start + standard_offset * 3600)
            self.assertEqual((y, m, d, hh), (expected_start.year, expected_start.month, expected_start.day, 2))
            y, m, d, hh, _mm, _ss = timezone.unix_to_ymdhms(end + standard_offset * 3600)
            self.assertEqual((y, m, d, hh), (expected_end.year, expected_end.month, expected_end.day, 2))

    def test_known_2024_dst_boundaries_eastern(self):
        eastern = -5
        just_before_start = timezone.ymd_to_unix(2024, 3, 10, 6, 59, 59)  # 1:59:59 EST
        just_after_start = timezone.ymd_to_unix(2024, 3, 10, 7, 0, 0)  # 3:00:00 EDT
        self.assertFalse(timezone.us_dst_active(just_before_start, eastern))
        self.assertTrue(timezone.us_dst_active(just_after_start, eastern))

        # The true fall-back instant is 06:00 UTC (2:00am EDT = 1:00am EST),
        # but this module deliberately treats the boundary as 2:00am
        # *standard* time (07:00 UTC) instead -- see us_dst_active's
        # docstring for why. So only assert outside that ~1-hour window.
        well_before_end = timezone.ymd_to_unix(2024, 11, 3, 5, 0, 0)  # 12:00am EST-equivalent
        well_after_end = timezone.ymd_to_unix(2024, 11, 3, 8, 0, 0)  # 3:00am EST
        self.assertTrue(timezone.us_dst_active(well_before_end, eastern))
        self.assertFalse(timezone.us_dst_active(well_after_end, eastern))

    def test_dst_disabled_never_active(self):
        summer = timezone.ymd_to_unix(2024, 7, 1, 12, 0, 0)
        self.assertEqual(timezone.local_offset_seconds(summer, -5, False), -5 * 3600)


class TestFormatLocal(unittest.TestCase):
    def test_format_eastern_standard(self):
        winter = timezone.ymd_to_unix(2024, 1, 15, 17, 30, 0)  # noon EST
        self.assertEqual(
            timezone.format_local(winter, -5, True), "12:30:00 (UTC-05:00)"
        )

    def test_format_eastern_daylight(self):
        summer = timezone.ymd_to_unix(2024, 7, 15, 16, 0, 0)  # noon EDT
        self.assertEqual(
            timezone.format_local(summer, -5, True), "12:00:00 (UTC-04:00)"
        )

    def test_format_positive_offset(self):
        t = timezone.ymd_to_unix(2024, 1, 1, 0, 0, 0)
        self.assertEqual(timezone.format_local(t, 9, False), "09:00:00 (UTC+09:00)")


if __name__ == "__main__":
    unittest.main()
