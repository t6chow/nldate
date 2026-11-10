# nldate

Parse natural-language date expressions into `datetime.date` objects.

```python
from datetime import date
from nldate import parse

parse("5 days before December 1st, 2025")  # date(2025, 11, 26)
parse("next Tuesday", today=date(2026, 11, 10))  # date(2026, 11, 17)
parse("1 year and 2 months after yesterday")
```

`parse(s, today=None)` raises `ValueError` for anything it doesn't recognize.

## Supported formats

- **Absolute dates**: `December 1st, 2025`, `Dec. 1 2025`, `1 December 2025`,
  `the first of December`, `December 2025`, `2025-12-01`, `2025/12/01`,
  `20251201`, `12/01/2025`, `12-1-25`. Dates without a year use the current year.
- **Keywords**: `today`, `now`, `tomorrow`, `yesterday`, `the day after tomorrow`,
  `the day before yesterday`.
- **Weekdays**: `Friday`, `this Friday`, `this coming Friday` (the next occurrence,
  including today), `next Friday` (strictly after today), `last Friday`
  (strictly before today), `Monday next week`.
- **Relative to today**: `in 3 days`, `in a week`, `3 days ago`, `5 days from now`,
  `next week`, `last month`, `next year`, `first day of next month`,
  `last day of this month`.
- **Offsets from any date expression**: `<duration> before|after|from <date>`,
  e.g. `two weeks from tomorrow`, `a week from next Friday`,
  `1 year, 2 months, and 3 days after 2025-01-01`.

Durations combine days, weeks, fortnights, months, years, and decades, with
numbers as digits or words (`twenty-one`, `a couple of`). Adding months or
years clamps to the end of the month (`1 month after January 31` is Feb 28).

## Development

```sh
uv run pytest
uv run mypy src/
uv run ruff check
uv run ruff format --check
```
