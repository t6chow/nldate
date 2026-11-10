from datetime import date

import pytest

from nldate import parse

# Tuesday, November 10, 2026.
TODAY = date(2026, 11, 10)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("December 1st, 2025", date(2025, 12, 1)),
        ("December 1, 2025", date(2025, 12, 1)),
        ("Dec 1 2025", date(2025, 12, 1)),
        ("Dec. 1, 2025", date(2025, 12, 1)),
        ("1 December 2025", date(2025, 12, 1)),
        ("1st of December, 2025", date(2025, 12, 1)),
        ("the first of December 2025", date(2025, 12, 1)),
        ("December twenty-first, 2025", date(2025, 12, 21)),
        ("Monday, December 1, 2025", date(2025, 12, 1)),
        ("December 2025", date(2025, 12, 1)),
        ("December 25", date(2026, 12, 25)),
        ("2025-12-01", date(2025, 12, 1)),
        ("2025/12/01", date(2025, 12, 1)),
        ("20251201", date(2025, 12, 1)),
        ("12/01/2025", date(2025, 12, 1)),
        ("12-1-25", date(2025, 12, 1)),
        ("25/12/2025", date(2025, 12, 25)),
    ],
)
def test_absolute_dates(text: str, expected: date) -> None:
    assert parse(text, today=TODAY) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("today", date(2026, 11, 10)),
        ("Today", date(2026, 11, 10)),
        ("tomorrow", date(2026, 11, 11)),
        ("yesterday", date(2026, 11, 9)),
        ("the day after tomorrow", date(2026, 11, 12)),
        ("the day before yesterday", date(2026, 11, 8)),
    ],
)
def test_keywords(text: str, expected: date) -> None:
    assert parse(text, today=TODAY) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("next Tuesday", date(2026, 11, 17)),
        ("last Tuesday", date(2026, 11, 3)),
        ("this Tuesday", date(2026, 11, 10)),
        ("next Friday", date(2026, 11, 13)),
        ("last Friday", date(2026, 11, 6)),
        ("Friday", date(2026, 11, 13)),
        ("next tues", date(2026, 11, 17)),
        ("this coming Friday", date(2026, 11, 13)),
        ("Monday next week", date(2026, 11, 16)),
    ],
)
def test_weekdays(text: str, expected: date) -> None:
    assert parse(text, today=TODAY) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("in 3 days", date(2026, 11, 13)),
        ("in a week", date(2026, 11, 17)),
        ("in two weeks", date(2026, 11, 24)),
        ("3 days ago", date(2026, 11, 7)),
        ("a month ago", date(2026, 10, 10)),
        ("5 days from now", date(2026, 11, 15)),
        ("a couple of weeks ago", date(2026, 10, 27)),
        ("twenty-one days from now", date(2026, 12, 1)),
        ("next week", date(2026, 11, 17)),
        ("last month", date(2026, 10, 10)),
        ("next year", date(2027, 11, 10)),
    ],
)
def test_relative_to_today(text: str, expected: date) -> None:
    assert parse(text, today=TODAY) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("5 days before December 1st, 2025", date(2025, 11, 26)),
        ("1 year and 2 months after yesterday", date(2028, 1, 9)),
        ("two weeks from tomorrow", date(2026, 11, 25)),
        ("a week from next Friday", date(2026, 11, 20)),
        ("1 year, 2 months, and 3 days after 2025-01-01", date(2026, 3, 4)),
        ("3 days after the day after tomorrow", date(2026, 11, 15)),
        ("the day after December 31, 2025", date(2026, 1, 1)),
    ],
)
def test_offsets_from_dates(text: str, expected: date) -> None:
    assert parse(text, today=TODAY) == expected


def test_month_arithmetic_clamps_to_end_of_month() -> None:
    assert parse("1 month after January 31, 2025") == date(2025, 2, 28)
    assert parse("1 year after February 29, 2024") == date(2025, 2, 28)


def test_first_and_last_day_of_month() -> None:
    assert parse("first day of next month", today=TODAY) == date(2026, 12, 1)
    assert parse("last day of this month", today=TODAY) == date(2026, 11, 30)


def test_whitespace_and_case_are_ignored() -> None:
    assert parse("  NEXT   tuesday  ", today=TODAY) == date(2026, 11, 17)


def test_today_defaults_to_current_date() -> None:
    assert parse("today") == date.today()


@pytest.mark.parametrize(
    "text",
    [
        "",
        "   ",
        "not a date",
        "banana",
        "February 30, 2025",
        "13/13/2025",
        "5 bananas from now",
        "next blursday",
    ],
)
def test_invalid_input_raises_value_error(text: str) -> None:
    with pytest.raises(ValueError):
        parse(text, today=TODAY)
