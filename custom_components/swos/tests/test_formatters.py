# custom_components/swos/tests/test_formatters.py
"""Tests for DateTimeFormatterFromMiliseconds."""


import pytest
from custom_components.swos.formatters import DateTimeFormatterFromMiliseconds


def test_datetime_formatter_ok():
    f = DateTimeFormatterFromMiliseconds()
    # 366100 // 100 = 3661 s => 0d 1h 1m 1s
    assert f.format(366100) == "0:01:01:01"


def test_datetime_formatter_none_and_invalid():
    f = DateTimeFormatterFromMiliseconds()
    # None and non-numeric input should return None
    assert f.format(None) is None
    assert f.format("not-a-number") is None


def test_datetime_formatter_negative_to_zero():
    f = DateTimeFormatterFromMiliseconds()
    # negative values are clamped to zero
    assert f.format(-500) == "0:00:00:00"


def test_datetime_formatter_str_input():
    f = DateTimeFormatterFromMiliseconds()
    # numeric string input should be accepted
    assert f.format("366100") == "0:01:01:01"


def test_datetime_formatter_more_than_day():
    f = DateTimeFormatterFromMiliseconds()
    # 9006100 // 100 = 90061 s => 1d 1h 1m 1s
    assert f.format(9006100) == "1:01:01:01"


@pytest.mark.parametrize(
    "inp,expected",
    [
        (None, None),
        ("not-int", None),
        (-5000, "0:00:00:00"),  # clamped to >= 0
        (0, "0:00:00:00"),
        (24 * 3600 * 100, "1:00:00:00"),  # exactly 1 day in ms
    ],
)
def test_datetimeformatter_edges(inp, expected):
    f = DateTimeFormatterFromMiliseconds()
    assert f.format(inp) == expected
