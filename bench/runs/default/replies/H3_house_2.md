Reusing the existing `format_brl` helper:

```diff
 class Order:
     def __init__(self, items):
         self.items = items  # list of (price, qty)
+
+    def formatted_total(self):
+        return format_brl(sum(price * qty for price, qty in self.items))
```

Quick check:

```python
assert Order([(10.5, 2), (1234.0, 1)]).formatted_total() == "R$ 1.255,00"
assert Order([]).formatted_total() == "R$ 0,00"
```

**Not verified.** I couldn't run this; the expected strings come from reading `format_brl`, not from output.

- **Assumption:** `Order` has no `total` method, so this computes the sum inline. If other code needs the raw number, split it into `total()` plus `formatted_total()`.
- **Noticed, did not touch:** if prices are `float`s, sums can pick up rounding error (e.g. `0.1 * 3`). The 2-decimal formatting hides this in the display, but stored or compared totals could be off by a cent. The fix is `Decimal` prices, which is outside this request.
