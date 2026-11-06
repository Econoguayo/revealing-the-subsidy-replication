"""Shared number formatter for every table script in this folder.

Decimal rounding half up at the printed precision. Floating-point noise is removed first by
formatting the value to ten decimals, so that an exact half in the model (for example 0.9375 or
18.75) rounds up in print. Values in the CSV and JSON files are never altered. A value that
rounds to zero prints without a minus sign. Blank, "None" and missing entries print as "--".
"""
from decimal import Decimal, ROUND_HALF_UP


def f(x, nd=2):
    if x in ("", "None", None):
        return "--"
    out = str(Decimal(f"{float(x):.10f}").quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP))
    return out[1:] if out.startswith("-") and float(out) == 0 else out
