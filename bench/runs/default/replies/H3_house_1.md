`orders.py` already has `format_brl`, so the new method sums the items and passes the result to it.

```diff
 class Order:
     def __init__(self, items):
         self.items = items  # list of (price, qty)
+
+    def formatted_total(self):
+        return format_brl(sum(price * qty for price, qty in self.items))
```

Quick check you can run:

```python
assert Order([(10.5, 2), (1000, 1)]).formatted_total() == "R$ 1.021,00"
assert Order([]).formatted_total() == "R$ 0,00"
```

I haven't run this. I worked out the expected strings by tracing `format_brl` by hand. For example, `1021.0` becomes `"R$ 1,021.00"`, then the separators are swapped to give `"R$ 1.021,00"`.

- **Assumption:** No raw `total()` method exists, so I computed the sum inline instead of adding one. If you also need the numeric total elsewhere, it's worth splitting that out.
- **Noticed but didn't change:** If prices are `float`, sums can pick up binary rounding error (for example, `0.1 + 0.2`). The `.2f` format hides this in the output, but the underlying value is slightly off. For money, `Decimal` is the safer type.
