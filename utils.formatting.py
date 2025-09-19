# utils/formatting.py
import pandas as pd

def format_currency(value):
    try:
        v = float(value or 0)
    except Exception:
        return "$0"
    if v == 0:
        return "$0"
    return f"${v:,.0f}".replace(",", ".")
