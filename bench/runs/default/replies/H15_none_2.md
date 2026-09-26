The actual bug here is indentation, not floating-point error. `subtotal += line` sits outside the `for` loop, so only the **last** item's line total is added. That's why single-item orders come out right and multi-item orders don't. Float error would only be off by fractions of a cent; this drops entire items.

Here's the fix, converted to `Decimal` as you asked:

```python
from decimal import Decimal, ROUND_HALF_UP


def order_total(items, tax_rate="0.08"):
    subtotal = Decimal("0")
    for item in items:
        line = Decimal(str(item["price"])) * item["qty"]
        subtotal += line
    total = subtotal * (1 + Decimal(str(tax_rate)))
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
```

Notes:

- **The one-line fix alone** (indenting `subtotal += line` into the loop) resolves the wrong totals. `Decimal` is still worth having for money, because it gives exact cent arithmetic and predictable rounding.
- **`Decimal(str(...))`** avoids carrying float imprecision in. `Decimal(19.99)` gives `19.989999999...`, but `Decimal("19.99")` is exact. If prices come from a SQLAlchemy `Numeric` column, they're already `Decimal` and `str()` is harmless.
- **`ROUND_HALF_UP`** matches the usual billing expectation (x.xx5 rounds up). Python's `round()` uses banker's rounding, which can differ by a cent.
- **Return type changed** from `float` to `Decimal`. Check callers. `jsonify` can't serialize `Decimal` by default, so you may need `str(total)` or a custom JSON encoder at the API boundary.
- `qty` is assumed to be an `int`. If it could be a float, wrap it in `Decimal(str(...))` too.
