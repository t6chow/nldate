"""Parse natural-language date expressions into ``datetime.date`` objects."""

import calendar
import re
from datetime import date, timedelta

MONTHS: dict[str, int] = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sept": 9,
    "sep": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}

WEEKDAYS: dict[str, int] = {
    "monday": 0,
    "mon": 0,
    "tuesday": 1,
    "tues": 1,
    "tue": 1,
    "wednesday": 2,
    "wed": 2,
    "thursday": 3,
    "thurs": 3,
    "thur": 3,
    "thu": 3,
    "friday": 4,
    "fri": 4,
    "saturday": 5,
    "sat": 5,
    "sunday": 6,
    "sun": 6,
}

ONES: dict[str, int] = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
}

TENS: dict[str, int] = {
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}

ORDINALS: dict[str, int] = {
    "first": 1,
    "second": 2,
    "third": 3,
    "fourth": 4,
    "fifth": 5,
    "sixth": 6,
    "seventh": 7,
    "eighth": 8,
    "ninth": 9,
    "tenth": 10,
    "eleventh": 11,
    "twelfth": 12,
    "thirteenth": 13,
    "fourteenth": 14,
    "fifteenth": 15,
    "sixteenth": 16,
    "seventeenth": 17,
    "eighteenth": 18,
    "nineteenth": 19,
    "twentieth": 20,
    "thirtieth": 30,
}
for _tens_word, _tens_value in (("twenty", 20), ("thirty", 30)):
    for _ord_word, _ord_value in list(ORDINALS.items())[:9]:
        if _tens_value + _ord_value <= 31:
            ORDINALS[f"{_tens_word}-{_ord_word}"] = _tens_value + _ord_value
            ORDINALS[f"{_tens_word} {_ord_word}"] = _tens_value + _ord_value

# Each unit maps to (months, days).
UNITS: dict[str, tuple[int, int]] = {
    "day": (0, 1),
    "days": (0, 1),
    "d": (0, 1),
    "week": (0, 7),
    "weeks": (0, 7),
    "wk": (0, 7),
    "wks": (0, 7),
    "w": (0, 7),
    "fortnight": (0, 14),
    "fortnights": (0, 14),
    "month": (1, 0),
    "months": (1, 0),
    "mo": (1, 0),
    "mos": (1, 0),
    "year": (12, 0),
    "years": (12, 0),
    "yr": (12, 0),
    "yrs": (12, 0),
    "y": (12, 0),
    "decade": (120, 0),
    "decades": (120, 0),
}

_MONTH_RE = "|".join(sorted(MONTHS, key=len, reverse=True))
_WEEKDAY_RE = "|".join(sorted(WEEKDAYS, key=len, reverse=True))
_ORDINAL_RE = "|".join(sorted(ORDINALS, key=len, reverse=True))
_DAY_RE = rf"(?:\d{{1,2}}|{_ORDINAL_RE})"
_WEEKDAY_PREFIX = rf"(?:(?:{_WEEKDAY_RE}) )?"

# "<month> <day> [<year>]", e.g. "december 1 2025", "dec 1".
_MONTH_DAY_YEAR = re.compile(
    rf"^{_WEEKDAY_PREFIX}(?P<month>{_MONTH_RE}) (?:the )?(?P<day>{_DAY_RE})"
    r"(?: (?:of )?(?P<year>\d{1,4}))?$"
)
# "<day> [of] <month> [<year>]", e.g. "1 december 2025", "first of dec".
_DAY_MONTH_YEAR = re.compile(
    rf"^{_WEEKDAY_PREFIX}(?:the )?(?P<day>{_DAY_RE}) (?:of )?(?P<month>{_MONTH_RE})"
    r"(?: (?P<year>\d{1,4}))?$"
)
# "<month> <year>", e.g. "december 2025".
_MONTH_YEAR = re.compile(rf"^(?P<month>{_MONTH_RE}) (?:of )?(?P<year>\d{{4}})$")
# "2025-12-01", "2025/12/01", "2025.12.01".
_ISO = re.compile(r"^(?P<year>\d{4})[-/.](?P<month>\d{1,2})[-/.](?P<day>\d{1,2})$")
# "12/01/2025", "12-1-25".
_NUMERIC = re.compile(r"^(?P<a>\d{1,2})[-/.](?P<b>\d{1,2})[-/.](?P<year>\d{4}|\d{2})$")
# "20251201".
_COMPACT = re.compile(r"^(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})$")

_SEPARATORS: dict[str, int] = {
    "before": -1,
    "prior to": -1,
    "earlier than": -1,
    "after": 1,
    "from": 1,
    "following": 1,
    "later than": 1,
    "past": 1,
}
_SEPARATOR_RE = re.compile(
    r" (" + "|".join(sorted(_SEPARATORS, key=len, reverse=True)) + r") "
)


def _add(base: date, months: int = 0, days: int = 0) -> date:
    """Shift a date by months (clamping the day) and then by days."""
    total = base.year * 12 + (base.month - 1) + months
    year, month = divmod(total, 12)
    month += 1
    if not 1 <= year <= 9999:
        raise ValueError("resulting date is out of range")
    day = min(base.day, calendar.monthrange(year, month)[1])
    return date(year, month, day) + timedelta(days=days)


def _normalize(s: str) -> str:
    s = s.strip().lower()
    s = s.replace(",", " ").replace("'s", "")
    s = re.sub(r"(?<=[a-z])\.", "", s)  # "dec." -> "dec"
    s = s.rstrip(".!?")
    s = re.sub(r"\b(\d+)(?:st|nd|rd|th)\b", r"\1", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _parse_year(text: str) -> int:
    year = int(text)
    if len(text) <= 2:
        year += 2000
    return year


def _parse_day(text: str) -> int:
    if text.isdigit():
        return int(text)
    return ORDINALS[text]


def _number(tokens: list[str], i: int) -> tuple[int, int] | None:
    """Parse a cardinal number starting at tokens[i].

    Returns (value, index after the number) or None.
    """
    if i >= len(tokens):
        return None
    tok = tokens[i]
    if tok.isdigit():
        return int(tok), i + 1
    if tok in ("a", "an"):
        nxt = tokens[i + 1] if i + 1 < len(tokens) else ""
        if nxt == "couple":
            j = i + 2
            if j < len(tokens) and tokens[j] == "of":
                j += 1
            return 2, j
        if nxt == "dozen":
            return 12, i + 2
        if nxt == "hundred":
            return 100, i + 2
        return 1, i + 1
    if tok == "couple":
        j = i + 1
        if j < len(tokens) and tokens[j] == "of":
            j += 1
        return 2, j
    if tok == "dozen":
        return 12, i + 1
    if tok in ONES:
        value = ONES[tok]
        if i + 1 < len(tokens) and tokens[i + 1] == "hundred":
            return value * 100, i + 2
        return value, i + 1
    if tok in TENS:
        value = TENS[tok]
        if i + 1 < len(tokens) and tokens[i + 1] in ONES and ONES[tokens[i + 1]] < 10:
            return value + ONES[tokens[i + 1]], i + 2
        return value, i + 1
    return None


def _parse_duration(s: str) -> tuple[int, int] | None:
    """Parse e.g. "1 year and 2 months" into (months, days), or None."""
    tokens = s.replace("-", " ").split()
    if not tokens:
        return None
    months = days = 0
    i = 0
    while i < len(tokens):
        if tokens[i] == "and":
            i += 1
            if i >= len(tokens):
                return None
        num = _number(tokens, i)
        if num is None:
            # A bare unit, e.g. "the day after" or "week from today".
            if tokens[i] == "the" and i + 1 < len(tokens):
                i += 1
            value = 1
        else:
            value, i = num
        if i >= len(tokens) or tokens[i] not in UNITS:
            return None
        unit_months, unit_days = UNITS[tokens[i]]
        months += value * unit_months
        days += value * unit_days
        i += 1
    return months, days


def _weekday(today: date, target: int, mode: str) -> date:
    diff = target - today.weekday()
    if mode == "next":
        return today + timedelta(days=diff % 7 or 7)
    if mode == "last":
        return today - timedelta(days=(-diff) % 7 or 7)
    # "this"/bare weekday: the upcoming occurrence, including today.
    return today + timedelta(days=diff % 7)


def _absolute(s: str, today: date) -> date | None:
    if m := _ISO.match(s) or _COMPACT.match(s):
        return date(int(m["year"]), int(m["month"]), int(m["day"]))
    if m := _NUMERIC.match(s):
        a, b = int(m["a"]), int(m["b"])
        month, day = (b, a) if a > 12 >= b else (a, b)
        return date(_parse_year(m["year"]), month, day)
    for pattern in (_MONTH_DAY_YEAR, _DAY_MONTH_YEAR):
        if m := pattern.match(s):
            year = _parse_year(m["year"]) if m["year"] else today.year
            return date(year, MONTHS[m["month"]], _parse_day(m["day"]))
    if m := _MONTH_YEAR.match(s):
        return date(int(m["year"]), MONTHS[m["month"]], 1)
    return None


def _relative(s: str, today: date) -> date | None:
    simple = {
        "today": 0,
        "now": 0,
        "tonight": 0,
        "tomorrow": 1,
        "tmrw": 1,
        "yesterday": -1,
    }
    if s in simple:
        return today + timedelta(days=simple[s])

    if m := re.fullmatch(
        rf"(?:(?:this )?(next|last|this|coming|past|previous) )?({_WEEKDAY_RE})", s
    ):
        aliases = {"coming": "this", "past": "last", "previous": "last"}
        mode = aliases.get(m[1], m[1] or "this")
        return _weekday(today, WEEKDAYS[m[2]], mode)

    if m := re.fullmatch(
        rf"(?:({_WEEKDAY_RE}) (next|last|this) week|(next|last|this) week ({_WEEKDAY_RE}))",
        s,
    ):
        name = m[1] or m[4]
        which = m[2] or m[3]
        monday = today - timedelta(days=today.weekday())
        offset = {"next": 7, "last": -7, "this": 0}[which]
        return monday + timedelta(days=offset + WEEKDAYS[name])

    if m := re.fullmatch(r"(next|last|previous|this) (day|week|month|year|decade)", s):
        sign = {"next": 1, "last": -1, "previous": -1, "this": 0}[m[1]]
        unit_months, unit_days = UNITS[m[2]]
        return _add(today, sign * unit_months, sign * unit_days)

    if m := re.fullmatch(
        r"(first|last) day of (?:the )?(next|last|previous|this|current) (month|year)",
        s,
    ):
        sign = {"next": 1, "last": -1, "previous": -1}.get(m[2], 0)
        if m[3] == "month":
            start = _add(today.replace(day=1), months=sign)
            if m[1] == "first":
                return start
            return _add(start, months=1) - timedelta(days=1)
        year = today.year + sign
        return date(year, 1, 1) if m[1] == "first" else date(year, 12, 31)

    m = re.fullmatch(r"(?:in|within) (.+?)(?: time)?", s)
    if m and (dur := _parse_duration(m[1])) is not None:
        return _add(today, *dur)

    m = re.fullmatch(r"(.+) (ago|later|hence|from now|from today|earlier)", s)
    if m and (dur := _parse_duration(m[1])) is not None:
        sign = -1 if m[2] in ("ago", "earlier") else 1
        return _add(today, sign * dur[0], sign * dur[1])

    # "<duration> before/after <date expression>", e.g. "2 weeks from tomorrow".
    for sep in _SEPARATOR_RE.finditer(s):
        left, right = s[: sep.start()], s[sep.end() :]
        dur = _parse_duration(left)
        if dur is None:
            continue
        try:
            base = _parse(right, today)
        except ValueError:
            continue
        sign = _SEPARATORS[sep[1]]
        return _add(base, sign * dur[0], sign * dur[1])

    return None


def _parse(s: str, today: date) -> date:
    s = re.sub(r"^(?:on|the|by|until|due) ", "", s) if " " in s else s
    for parser in (_absolute, _relative):
        result = parser(s, today)
        if result is not None:
            return result
    raise ValueError(f"unrecognized date: {s!r}")


def parse(s: str, today: date | None = None) -> date:
    """Parse a natural-language date string into a ``datetime.date``.

    ``today`` is the reference date for relative expressions such as
    "next Tuesday" or "in 3 days"; it defaults to the current date.

    Raises ``ValueError`` if the string is not a recognized date.
    """
    if today is None:
        today = date.today()
    normalized = _normalize(s)
    if not normalized:
        raise ValueError("empty date string")
    try:
        return _parse(normalized, today)
    except (OverflowError, KeyError) as e:
        raise ValueError(f"unrecognized date: {s!r}") from e
