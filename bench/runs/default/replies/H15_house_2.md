**The bug isn't floating-point error. It's indentation.** `subtotal += line` sits outside the `for` loop, so it runs once, after the loop, and adds only the **last** item's line. That's why it breaks only when there's more than one item.

Traced by hand (I can't run it here): with items `[{"price": 10, "qty": 1}, {"price": 5, "qty": 1}]`, the current code returns `5.4` (only the $5 item, plus tax). The correct total is `16.2`. Floating-point error is off by a fraction of a cent, not by an entire item. Switching to `Decimal` alone would leave the totals just as wrong.

The fix is one indent:

```diff
 def order_total(items, tax_rate=0.08):
     subtotal = 0.0
     for item in items:
         line = item["price"] * item["qty"]
-    subtotal += line
+        subtotal += line
     return round(subtotal * (1 + tax_rate), 2)
```

A check to keep it from coming back:

```python
def test_order_total_sums_all_items():
    items = [{"price": 10, "qty": 1}, {"price": 5, "qty": 1}]
    assert order_total(items) == 16.2
```

This test returns `5.4` and fails on the current code. After the fix it should pass (not run).

**On Decimal:** it's still good practice for money, but it's a separate change with a cost. `order_total` would return `Decimal` instead of `float`, which can break callers that do float arithmetic, JSON-serialize the result, or compare against floats. If you want it, this is the version I'd use:

```python
from decimal import Decimal, ROUND_HALF_UP

def order_total(items, tax_rate="0.08"):
    subtotal = Decimal("0")
    for item in items:
        subtotal += Decimal(str(item["price"])) * item["qty"]
    total = subtotal * (1 + Decimal(str(tax_rate)))
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
```

`Decimal(str(...))` avoids carrying float representation errors into the Decimal. `ROUND_HALF_UP` gives conventional cent rounding, where the built-in `round()` uses banker's rounding. My recommendation is to ship the indentation fix now and do the Decimal conversion only after checking what the callers do with the return value.
