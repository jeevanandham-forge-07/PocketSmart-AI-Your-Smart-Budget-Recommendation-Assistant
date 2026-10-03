import html
import json
from typing import Any


def format_currency(amount: float, currency: str = "INR") -> str:
    """Format float amount with commas and currency symbol"""
    try:
        val = float(amount)
        if currency.upper() == "INR":
            # Indian numbering format formatting
            s, *d = str(f"{val:.2f}").partition(".")
            r = []
            for i, c in enumerate(reversed(s)):
                if i == 3 or (i > 3 and (i - 3) % 2 == 0):
                    r.append(",")
                r.append(c)
            formatted = "".join(reversed(r))
            return f"₹ {formatted}.{d[0]}" if d else f"₹ {formatted}"
        else:
            return f"{currency} {val:,.2f}"
    except Exception:
        return f"{currency} {amount}"


def sanitize_text(text: str) -> str:
    """Sanitize user input against XSS"""
    if not text:
        return ""
    return html.escape(text.strip())


def safe_json_loads(data: str, default: Any = None) -> Any:
    """Safely parse JSON string"""
    if not data:
        return default if default is not None else {}
    try:
        return json.loads(data)
    except Exception:
        return default if default is not None else {}
