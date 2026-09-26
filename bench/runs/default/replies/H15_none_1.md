The actual bug here isn't floating-point error. It's indentation: `subtotal += line` is outside the `for` loop, so only the **last** item's line total gets added. That's why single-item orders look right and multi-item orders are wrong.

```python
    for item in items:
        line = item["price"] * item["qty"]
    subtotal += line          # runs once, after the loop
```

Float error would make totals off by fractions of a cent at most. `round(..., 2)` would usually hide that. It wouldn't drop whole items.

Here's the fix, converted to `Decimal` as you asked. That's still worthwhile for money:

```python
from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")


def order_total(items, tax_rate="0.08"):
    subtotal = Decimal("0")
    for item in items:
        line = Decimal(str(item["price"])) * item["qty"]
        subtotal += line
    total = subtotal * (1 + Decimal(str(tax_rate)))
    return total.quantize(CENT, rounding=ROUND_HALF_UP)
```

Notes:
- **Indentation fix:** `subtotal += line` is now inside the loop. This change alone fixes the bug you're seeing.
- **`Decimal(str(...))`:** this avoids carrying float imprecision into the Decimal (`Decimal(0.1)` is `0.1000000000000000055...`). If prices come from a SQLAlchemy `Numeric` column, they're already `Decimal`, and `str()` round-trips them harmlessly.
- **`ROUND_HALF_UP`:** Python's `round()` uses banker's rounding (half-to-even), which usually isn't what billing expects.
- **Return type:** it's now `Decimal`, not `float`. Callers that do float math on the result, or that JSON-serialize it, may need adjusting. Flask's default JSON provider can't serialize `Decimal`, so you'd need `str(total)` or a custom provider.
- **`qty`:** this assumes an `int`. If it can be fractional, wrap it in `Decimal(str(...))` too.

I haven't run this. A quick test with two or more items, e.g. `[{"price": 10, "qty": 1}, {"price": 5, "qty": 2}]` → `Decimal("21.60")`, would confirm the fix.
