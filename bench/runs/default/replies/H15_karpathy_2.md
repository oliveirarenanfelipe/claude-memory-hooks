The wrong totals aren't caused by floating point. The problem is indentation: `subtotal += line` sits outside the `for` loop, so it runs once after the loop and adds only the **last** item's line. That's why single-item orders look right and multi-item orders don't. Float error would show up as a cent off at most, not whole missing items.

Here's the fix plus the Decimal conversion you asked for. Decimal is still worthwhile for money:

```python
from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")


def order_total(items, tax_rate="0.08"):
    subtotal = Decimal("0")
    for item in items:
        line = Decimal(str(item["price"])) * item["qty"]
        subtotal += line  # now inside the loop
    total = subtotal * (1 + Decimal(str(tax_rate)))
    return total.quantize(CENT, rounding=ROUND_HALF_UP)
```

Notes:

- **The indentation is the actual bug fix.** If you'd rather keep floats for now, moving that one line into the loop is enough to fix the totals.
- `Decimal(str(...))` avoids carrying float noise into the Decimal. `Decimal(19.99)` would give `19.989999999999998436805981327779591083526611328125`. It's better if prices are stored as `Numeric` in SQLAlchemy, which returns `Decimal` directly. `str()` is harmless in that case.
- `ROUND_HALF_UP` is the usual choice for money. Python's `round()` uses banker's rounding (half-to-even), so some results may change by a cent compared to before.
- **The return type is now `Decimal`, not `float`.** Check the callers. `jsonify` can't serialize `Decimal` by default, so convert with `str(total)` or configure your JSON provider. Mixing `Decimal` and `float` in arithmetic raises `TypeError`.
- `tax_rate` now defaults to the string `"0.08"`, and passing a float still works because of the `str()` conversion.
