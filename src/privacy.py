"""
Privacy guard for personal data (candidate lists contain names and partial IDs).

Rule: aggregate to counts immediately; never write personal columns to interim/processed
and never commit them to Git. (POPIA: process only what the purpose requires.)
"""
import re

import pandas as pd

PERSONAL_PATTERNS = re.compile(
    r"(^|_)(id|id_?no|id_?number|identity|surname|first_?name|full_?name|initials|"
    r"name|dob|birth|cell|phone|email|address)($|_)", re.IGNORECASE)

# columns that contain "name" but are NOT personal
KEEP = {"party_name", "municipality_name", "muni_name", "province_name", "ward_name"}


def personal_columns(df: pd.DataFrame) -> list:
    return [c for c in df.columns
            if str(c).lower() not in KEEP and PERSONAL_PATTERNS.search(str(c).lower())]


def drop_personal(df: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    """Drop personal columns. Check the printed list - patterns can miss odd headers."""
    cols = personal_columns(df)
    if verbose:
        print("Dropping personal columns:", cols or "none found - CHECK MANUALLY")
    return df.drop(columns=cols)
