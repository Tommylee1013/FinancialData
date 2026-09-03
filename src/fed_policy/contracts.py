from __future__ import annotations

from datetime import date

import pandas as pd

MONTH_CODES = {1: "F", 2: "G", 3: "H", 4: "J", 5: "K", 6: "M", 7: "N", 8: "Q", 9: "U", 10: "V", 11: "X", 12: "Z"}


def contract_symbol(meeting_date: str | date | pd.Timestamp) -> str:
    meeting = pd.Timestamp(meeting_date)
    return f"ZQ{MONTH_CODES[meeting.month]}{meeting.year}"


def next_contract_symbol(meeting_date: str | date | pd.Timestamp) -> str:
    meeting = pd.Timestamp(meeting_date) + pd.offsets.MonthBegin(1)
    return f"ZQ{MONTH_CODES[meeting.month]}{meeting.year}"
