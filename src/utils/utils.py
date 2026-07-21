import calendar
import pandas as pd

MONTH_MAP = {}
for i in range(1, 13):
    MONTH_MAP[calendar.month_name[i].lower()] = i
    MONTH_MAP[calendar.month_abbr[i].lower()] = i

def clean_currency(val):
    val = str(val)
    val = val.replace("$", "")
    val = val.replace(",", "")
    result = pd.to_numeric(val, errors="coerce")
    return round(result, 2)  # 保留兩位小數

def clean_numeric(val):
    val = str(val)
    result = pd.to_numeric(val, errors="coerce")
    return round(result)  # 加這行

def extract_month(filename):
    filename = filename.lower()
    parts = filename.split('-')
    for part in parts:
        if part in MONTH_MAP:
            return MONTH_MAP[part]
    return None