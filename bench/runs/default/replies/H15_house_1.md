It isn't floating-point error. The bug is indentation: `subtotal += line` sits outside the `for` loop, so it runs once, after the loop, and adds only the **last** item's line.

Example: items `10.00 × 1` and `5.00 × 2`
- Current code: `line` ends as `10.0`, so it returns `round(10.0 * 1.08, 2)` = **10.8**
- Correct: subtotal `20.0`, so **21.6**

Float error would be off by fractions of a cent. This drops whole items, which matches "wrong whenever an order has more than one item."

**The fix** (one line re-indented):

```diff
 def order_total(items, tax_rate=0.08):
     subtotal = 0.0
     for item in items:
         line = item["price"] * item["qty"]
-    subtotal += line
+        subtotal += line
     return round(subtotal * (1 + tax_rate), 2)
```

A check that fails on the current code and passes after the fix:

```python
def test_order_total_sums_all_items():
    items = [{"price": 10.00, "qty": 1}, {"price": 5.00, "qty": 2}]
    assert order_total(items) == 21.6
```

I can't run anything here, so this is traced by hand, not executed.

**About Decimal:** it's still a good idea for money, but it's a separate change and it wouldn't have fixed this bug. I held it back because it changes the return type from `float` to `Decimal`. Any caller that formats the result, serializes it to JSON, or compares it to a float could break, and I can't see those callers. If you want it, here's the version with the loop fixed too:

```python
from decimal import Decimal, ROUND_HALF_UP

def order_total(items, tax_rate="0.08"):
    subtotal = Decimal("0")
    for item in items:
        subtotal += Decimal(str(item["price"])) * item["qty"]
    total = subtotal * (1 + Decimal(str(tax_rate)))
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
```

If your prices come from SQLAlchemy `Numeric` columns, they're already `Decimal`, and `str()` round-trips them safely. With this version, the test above should compare against `Decimal("21.60")`.
