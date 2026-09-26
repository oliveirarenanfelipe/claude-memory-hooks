The actual bug isn't floating-point error. It's indentation:

```python
    for item in items:
        line = item["price"] * item["qty"]
    subtotal += line          # <- outside the loop
```

`subtotal += line` runs once, after the loop finishes, so only the **last** item is counted. That's why single-item orders are correct and multi-item orders are wrong. Float error would show up as off-by-a-cent discrepancies, not whole items missing.

The minimal fix is to indent that line:

```python
def order_total(items, tax_rate=0.08):
    subtotal = 0.0
    for item in items:
        line = item["price"] * item["qty"]
        subtotal += line
    return round(subtotal * (1 + tax_rate), 2)
```

That alone should fix the totals you're seeing.

Switching to `Decimal` is still a good idea for money, since floats can produce cent-level rounding errors (e.g. `round(2.675, 2) == 2.67`). Here's the Decimal version with the indentation fix included:

```python
from decimal import Decimal, ROUND_HALF_UP

def order_total(items, tax_rate=Decimal("0.08")):
    subtotal = Decimal("0")
    for item in items:
        line = Decimal(str(item["price"])) * item["qty"]
        subtotal += line
    total = subtotal * (1 + Decimal(str(tax_rate)))
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
```

Notes on this version:
- `Decimal(str(...))` avoids inheriting float artifacts if prices arrive as floats (`Decimal(0.1)` is `0.1000000000000000055...`, but `Decimal("0.1")` is exact). If your SQLAlchemy columns are `Numeric`, prices are already `Decimal` and the `str()` is harmless.
- It returns a `Decimal`, not a `float`. Callers that serialize to JSON (e.g. `jsonify`) will need to convert it, typically with `str(total)`, or they'll raise `TypeError`.
- `ROUND_HALF_UP` matches the usual billing convention. Python's `round()` uses banker's rounding, so a few totals may differ by a cent from before. That's intended, but worth knowing if you compare against old records.
