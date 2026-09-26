Here's a `formatted_total` method that reuses your existing `format_brl` helper:

```diff
 class Order:
     def __init__(self, items):
         self.items = items  # list of (price, qty)
+
+    def formatted_total(self):
+        total = sum(price * qty for price, qty in self.items)
+        return format_brl(total)
```

For example, `Order([(10.5, 2), (1234.0, 1)]).formatted_total()` returns `"R$ 1.255,00"`.

If prices are floats, rounding errors can show up in larger sums. If these are real money values, consider storing prices as `Decimal`. `format_brl` works with `Decimal` unchanged.
