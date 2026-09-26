The test is correct; the bug is in `apply_discount`. The docstring says `pct` must be "between 0 and 100 inclusive", but the guard uses `pct >= 100`, which rejects 100. So `apply_discount(80, 100)` raises `ValueError` instead of returning `0`.

I'd fix the function rather than the test. Changing the test would hide a real bug and leave the code contradicting its own contract:

```diff
 def apply_discount(price, pct):
     """Return price after a pct% discount. pct must be between 0 and 100 inclusive."""
-    if pct < 0 or pct >= 100:
+    if pct < 0 or pct > 100:
         raise ValueError("pct out of range")
     return round(price * (1 - pct / 100), 2)
```

With that change, every assertion in `test_apply_discount` holds:
- `apply_discount(100, 10)` returns `90.0`
- `apply_discount(59.99, 0)` returns `59.99`
- `apply_discount(80, 100)` returns `0.0`
- `apply_discount(50, 101)` raises

If a 100% discount really should be disallowed, the fix is different. Update the docstring to "0 inclusive to 100 exclusive" and change the test's third assertion to `pytest.raises(ValueError)`. Just tell me if that's the case, since it's a product decision rather than a test fix.
